from __future__ import annotations

import asyncio
import re
import shutil
from datetime import date
from pathlib import Path
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

from .settings import Settings
from .models import ReportType, DownloadResult, ExecutionStatus
from .hash_utils import sha256_file


MFA_PATTERNS = [
    re.compile(r'c[oó]digo.*verificaci[oó]n', re.I),
    re.compile(r'verificaci[oó]n.*dos pasos', re.I),
    re.compile(r'autenticaci[oó]n', re.I),
    re.compile(r'one.time.password|otp', re.I),
]

CAPTCHA_PATTERNS = [re.compile(r'captcha|recaptcha|no soy un robot', re.I)]


class NetPayPortalRobot:
    def __init__(self, settings: Settings, logger=print):
        self.settings = settings
        self.logger = logger
        self.download_dir = settings.ensure_download_dir()

    async def _log(self, status: ExecutionStatus | str, message: str) -> None:
        self.logger(f'[{status}] {message}')

    async def run_download(self, report_type: ReportType, date_from: date, date_to: date, password: str) -> DownloadResult:
        await self._log(ExecutionStatus.INICIADO, f'Descarga {report_type.value} {date_from} - {date_to}')
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.settings.netpay_headless)
            context = await browser.new_context(accept_downloads=True, locale='es-MX')
            page = await context.new_page()
            try:
                await page.goto(self.settings.netpay_portal_url, wait_until='networkidle', timeout=60000)
                await self.login(page, self.settings.netpay_username, password)
                await self.detect_security_challenges(page)
                await self.validate_landing(page)
                await self.validate_company(page)

                if report_type == ReportType.DETALLE_TRANSACCIONES:
                    download_path = await self.download_transactions(page, date_from, date_to)
                elif report_type == ReportType.DETALLE_DEPOSITOS_MOVIMIENTOS:
                    download_path = await self.download_deposits(page, date_from, date_to)
                else:
                    raise ValueError(f'Reporte no soportado: {report_type}')

                safe_path = self._move_to_safe_path(download_path, report_type, date_from, date_to)
                digest = sha256_file(safe_path)
                await self._log(ExecutionStatus.DESCARGADO, f'{safe_path} sha256={digest}')
                return DownloadResult(report_type, date_from, date_to, safe_path, digest, safe_path.name)
            finally:
                await context.close()
                await browser.close()

    async def login(self, page: Page, username: str, password: str) -> None:
        if not username or not password:
            raise ValueError('Usuario/contraseña NetPay no configurados.')

        await self._log(ExecutionStatus.INICIADO, 'Ingresando credenciales')
        # Usar labels visibles; evita selectores frágiles.
        await page.get_by_label(re.compile('Correo electr[oó]nico', re.I)).fill(username, timeout=20000)
        await page.locator('input[name="password"]').fill(password, timeout=20000)
        await page.get_by_role('button', name=re.compile('Iniciar sesi[oó]n', re.I)).click(timeout=20000)

        try:
            try:
                await page.wait_for_load_state('networkidle', timeout=8000)
            except Exception as e:
                print('[WARN] networkidle no llegó; se continúa con estado visual:', e)
            await page.wait_for_timeout(3000)
        except PlaywrightTimeoutError:
            pass

        content = await page.text_content('body') or ''
        if re.search(r'contrase[nñ]a.*incorrecta|usuario.*incorrecto|credenciales.*inv[aá]lidas', content, re.I):
            raise RuntimeError(ExecutionStatus.LOGIN_FALLIDO.value)
        await self._log(ExecutionStatus.LOGIN_OK, 'Login aparentemente exitoso')

    async def detect_security_challenges(self, page: Page) -> None:
        content = await page.text_content('body') or ''
        if any(p.search(content) for p in CAPTCHA_PATTERNS):
            await self._log(ExecutionStatus.CAPTCHA_DETECTADO, 'Captcha detectado. Detener sin evadir.')
            raise RuntimeError(ExecutionStatus.CAPTCHA_DETECTADO.value)
        if any(p.search(content) for p in MFA_PATTERNS):
            await self._log(ExecutionStatus.MFA_REQUERIDO, 'MFA detectado. Detener sin evadir.')
            raise RuntimeError(ExecutionStatus.MFA_REQUERIDO.value)

    async def validate_landing(self, page: Page) -> None:
        content = await page.text_content('body') or ''
        expected_any = ['NetPay Manager', 'Reportes', 'Inicio', 'Resumen de Movimientos']
        if not any(token.lower() in content.lower() for token in expected_any):
            raise RuntimeError('No se pudo validar pantalla inicial de NetPay Manager.')

    async def validate_company(self, page: Page) -> None:
        expected = self.settings.netpay_expected_company.strip()
        if not expected:
            return
        content = (await page.text_content('body') or '').upper()
        # Acepta coincidencia parcial por truncamiento visible: DESARROLLOS A...
        tokens = [t for t in re.split(r'\s+', expected.upper()) if len(t) > 4]
        if tokens and not any(t in content for t in tokens[:2]):
            await self._log(ExecutionStatus.EMPRESA_NO_COINCIDE, f'No se validó empresa esperada: {expected}')
            print('[WARN] Empresa esperada no validada visualmente; se continúa por prueba controlada')

    async def open_report_menu(self, page: Page) -> None:
        await page.get_by_role('link', name=re.compile('Reportes', re.I)).click(timeout=20000)
        await page.wait_for_timeout(500)

    async def set_custom_date_range(self, page: Page, date_from: date, date_to: date) -> None:
        date_range_txt = f"{date_from.strftime('%d/%m/%Y')} - {date_to.strftime('%d/%m/%Y')}"
        await self._log('RANGO_FECHAS', date_range_txt)
        print('[INFO] Seleccionando rango NetPay por datepicker real:', date_range_txt)

        result = await page.evaluate(
            """
            async ({fromY, fromM, fromD, toY, toM, toD, expectedText}) => {
                const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

                const visible = (el) => {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const st = window.getComputedStyle(el);
                    return r.width > 4 && r.height > 4 && st.display !== 'none' && st.visibility !== 'hidden';
                };

                const norm = (s) => (s || '').toString().trim();

                const monthMap = {
                    ene: 1, enero: 1, jan: 1, january: 1,
                    feb: 2, febrero: 2, february: 2,
                    mar: 3, marzo: 3, march: 3,
                    abr: 4, abril: 4, apr: 4, april: 4,
                    may: 5, mayo: 5,
                    jun: 6, junio: 6, june: 6,
                    jul: 7, julio: 7, july: 7,
                    ago: 8, agosto: 8, aug: 8, august: 8,
                    sep: 9, sept: 9, septiembre: 9, september: 9,
                    oct: 10, octubre: 10, october: 10,
                    nov: 11, noviembre: 11, november: 11,
                    dic: 12, diciembre: 12, dec: 12, december: 12
                };

                const ymSerial = (y, m) => (Number(y) * 12) + Number(m);

                const parseMonth = (txt) => {
                    const clean = norm(txt).replace(/\s+/g, ' ');
                    const parts = clean.split(' ');
                    if (parts.length < 2) return null;
                    const mKey = parts[0].toLowerCase().slice(0, 3);
                    const m = monthMap[mKey] || monthMap[parts[0].toLowerCase()];
                    const y = parseInt(parts[1], 10);
                    if (!m || !y) return null;
                    return {year: y, month: m, text: clean};
                };

                const getPicker = () => Array.from(document.querySelectorAll('.md-drppicker'))
                    .filter(visible)
                    .find(el => el.className.toString().includes('shown')) || null;

                const getInput = () => Array.from(document.querySelectorAll('input'))
                    .filter(visible)
                    .find(el => (el.placeholder || '').toLowerCase().includes('hoy')) || null;

                // 1) Abrir datepicker.
                let openerCandidates = Array.from(document.querySelectorAll('button, input'))
                    .filter(visible)
                    .filter(el => {
                        const blob = [
                            el.placeholder || '',
                            el.value || '',
                            el.className || '',
                            el.innerText || '',
                            el.getAttribute('aria-label') || ''
                        ].join(' ').toLowerCase();

                        return blob.includes('hoy')
                            || blob.includes('calendar')
                            || blob.includes('daterangepicker')
                            || blob.includes('ngx-daterangepicker');
                    });

                if (!openerCandidates.length) {
                    return {ok:false, step:'open', reason:'NO_DATE_CONTROL'};
                }

                openerCandidates[0].scrollIntoView({block:'center', inline:'center'});
                openerCandidates[0].click();
                await sleep(900);

                // 2) Click Personalizado.
                let customCandidates = Array.from(document.querySelectorAll('button, a, div, span'))
                    .filter(visible)
                    .filter(el => norm(el.innerText || el.textContent).toLowerCase() === 'personalizado');

                if (!customCandidates.length) {
                    return {ok:false, step:'personalizado', reason:'NO_PERSONALIZADO'};
                }

                customCandidates[customCandidates.length - 1].click();
                await sleep(900);

                let picker = getPicker();
                if (!picker) {
                    return {ok:false, step:'picker', reason:'NO_PICKER_SHOWN'};
                }

                // 3) Navegar hasta que el calendario izquierdo sea el mes/año inicial.
                const targetLeft = ymSerial(fromY, fromM);
                let moves = 0;

                while (moves < 36) {
                    picker = getPicker();
                    const leftMonthEl = picker?.querySelector('.calendar.left th.month');
                    const leftMonth = parseMonth(leftMonthEl?.innerText || leftMonthEl?.textContent || '');

                    if (!leftMonth) {
                        return {ok:false, step:'parse_left_month', reason:'NO_LEFT_MONTH', text:leftMonthEl?.innerText || ''};
                    }

                    const currentLeft = ymSerial(leftMonth.year, leftMonth.month);
                    if (currentLeft === targetLeft) break;

                    if (currentLeft > targetLeft) {
                        const prev = picker.querySelector('.calendar.left th.prev.available, th.prev.available');
                        if (!prev) return {ok:false, step:'navigate_prev', reason:'NO_PREV', current:leftMonth};
                        prev.click();
                    } else {
                        const next = picker.querySelector('.calendar.right th.next.available, th.next.available');
                        if (!next) return {ok:false, step:'navigate_next', reason:'NO_NEXT', current:leftMonth};
                        next.click();
                    }

                    moves += 1;
                    await sleep(250);
                }

                picker = getPicker();
                const finalLeft = parseMonth(picker.querySelector('.calendar.left th.month')?.innerText || '');
                const finalRight = parseMonth(picker.querySelector('.calendar.right th.month')?.innerText || '');

                if (!finalLeft || ymSerial(finalLeft.year, finalLeft.month) !== targetLeft) {
                    return {ok:false, step:'navigate_final', reason:'LEFT_MONTH_NOT_TARGET', finalLeft, finalRight};
                }

                const clickDayInCalendar = async (calendarSelector, day) => {
                    picker = getPicker();
                    const cal = picker.querySelector(calendarSelector);
                    if (!cal) return {ok:false, reason:'NO_CALENDAR', calendarSelector};

                    const cells = Array.from(cal.querySelectorAll('td.available'))
                        .filter(visible)
                        .filter(td => !String(td.className || '').includes('off'))
                        .filter(td => norm(td.innerText || td.textContent) === String(day));

                    if (!cells.length) {
                        return {
                            ok:false,
                            reason:'NO_DAY_CELL',
                            calendarSelector,
                            day,
                            available: Array.from(cal.querySelectorAll('td.available'))
                                .filter(visible)
                                .map(td => ({text:norm(td.innerText || td.textContent), cls:String(td.className || '')}))
                        };
                    }

                    cells[0].click();
                    await sleep(500);
                    return {ok:true, text:norm(cells[0].innerText || cells[0].textContent), cls:String(cells[0].className || '')};
                };

                // 4) Click fecha inicial.
                let startClick = await clickDayInCalendar('.calendar.left', fromD);
                if (!startClick.ok) {
                    return {ok:false, step:'click_start', detail:startClick, finalLeft, finalRight};
                }

                // 5) Click fecha final: mismo mes = izquierda; mes siguiente = derecha; si no, navegar.
                picker = getPicker();
                let rightMonth = parseMonth(picker.querySelector('.calendar.right th.month')?.innerText || '');
                let endCalendar = null;

                if (Number(toY) === Number(finalLeft.year) && Number(toM) === Number(finalLeft.month)) {
                    endCalendar = '.calendar.left';
                } else if (rightMonth && Number(toY) === Number(rightMonth.year) && Number(toM) === Number(rightMonth.month)) {
                    endCalendar = '.calendar.right';
                } else {
                    return {ok:false, step:'end_month_not_visible', finalLeft, rightMonth, toY, toM};
                }

                let endClick = await clickDayInCalendar(endCalendar, toD);
                if (!endClick.ok) {
                    return {ok:false, step:'click_end', detail:endClick, finalLeft, rightMonth};
                }

                await sleep(700);

                const input = getInput();
                const inputValue = input ? input.value : '';

                return {
                    ok: inputValue === expectedText,
                    step: 'done',
                    expectedText,
                    inputValue,
                    finalLeft,
                    finalRight: rightMonth,
                    startClick,
                    endClick,
                    moves
                };
            }
            """,
            {
                "fromY": date_from.year,
                "fromM": date_from.month,
                "fromD": date_from.day,
                "toY": date_to.year,
                "toM": date_to.month,
                "toD": date_to.day,
                "expectedText": date_range_txt,
            },
        )

        print('[DATEPICKER_REAL_RESULT]', result)
        await page.screenshot(path='/app/netpay_datepicker_real_result.png', full_page=True)
        print('[DATEPICKER_REAL_SCREENSHOT] /app/netpay_datepicker_real_result.png')

        if not result.get('ok'):
            raise RuntimeError(f"No se pudo seleccionar rango real en datepicker NetPay: {result}")

        print('[INFO] Rango real seleccionado en NetPay:', result.get('inputValue'))


    async def download_transactions(self, page: Page, date_from: date, date_to: date) -> Path:
        await self.open_report_menu(page)
        await page.evaluate("""() => { const el = document.querySelector('#linkTransactions'); if (!el) throw new Error('No existe #linkTransactions'); el.click(); }""")
        try:
            await page.wait_for_load_state('networkidle', timeout=8000)
        except Exception as e:
            print('[WARN] networkidle no llegó; se continúa con estado visual:', e)
        await page.wait_for_timeout(3000)
        await self.set_custom_date_range(page, date_from, date_to)
        await page.screenshot(path='/tmp/netpay_transacciones_debug.png', full_page=True)
        print('[DEBUG] screenshot guardado en /tmp/netpay_transacciones_debug.png')
        print('[DEBUG] URL actual:', page.url)
        try:
            print('[DEBUG] Título:', await page.title())
        except Exception as e:
            print('[DEBUG] No se pudo leer título:', e)
        try:
            body_text = await page.locator('body').inner_text(timeout=5000)
            print('[DEBUG] Texto visible inicio:')
            print(body_text[:2000])
            print('[DEBUG] Texto visible fin')
        except Exception as e:
            print('[DEBUG] No se pudo leer body:', e)

        try:
            await page.get_by_role('button', name=re.compile('Aplicar filtros', re.I)).click(timeout=20000, force=True)
        except Exception:
            await page.get_by_text(re.compile('Aplicar filtros', re.I)).click(timeout=20000, force=True)
        try:
            await page.wait_for_load_state('networkidle', timeout=8000)
        except Exception as e:
            print('[WARN] networkidle no llegó; se continúa con estado visual:', e)

        await page.wait_for_timeout(8000)

        try:
            await page.screenshot(path='/tmp/netpay_transacciones_post_filtros.png', full_page=True)
            print('[DEBUG_POST_FILTROS] screenshot guardado en /tmp/netpay_transacciones_post_filtros.png')
            body_post = await page.locator('body').inner_text(timeout=5000)
            print('[DEBUG_POST_FILTROS] Texto visible inicio:')
            print(body_post[:4000])
            print('[DEBUG_POST_FILTROS] Texto visible fin')
        except Exception as e:
            print('[DEBUG_POST_FILTROS] No se pudo capturar body/screenshot:', e)

        try:
            body_after_filters = await page.locator('body').inner_text(timeout=5000)
            if (
                'No se encontraron resultados' in body_after_filters
                or '0 - 0 de 0 ítems' in body_after_filters
                or '0 - 0 de 0 items' in body_after_filters
            ):
                from openpyxl import Workbook

                self.download_dir.mkdir(parents=True, exist_ok=True)
                empty_path = self.download_dir / f"{date_from:%Y%m%d}_{date_to:%Y%m%d}_DetalleTransacciones_SIN_DATOS.xlsx"

                wb = Workbook()
                ws = wb.active
                ws.title = 'vacío'
                ws['A1'] = 'SIN_DATOS'
                ws['A2'] = f'{date_from} - {date_to}'
                wb.save(empty_path)

                await self._log(ExecutionStatus.DESCARGADO, f'SIN_DATOS transacciones {date_from} - {date_to}')
                return empty_path
        except Exception as e:
            print('[WARN] No se pudo validar transacciones sin resultados:', e)

        await self._log(ExecutionStatus.DESCARGANDO, 'Exportar reporte completo')
        await page.get_by_role('button', name=re.compile('^Exportar$', re.I)).click(timeout=20000, force=True)
        async with page.expect_download(timeout=120000) as download_info:
            await page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('a, button'));
            const el = items.find(x => (x.innerText || '').trim().toLowerCase().includes('exportar reporte completo'));
            if (!el) throw new Error('No existe opción Exportar reporte completo');
            el.click();
        }""")
        download = await download_info.value
        path = self.download_dir / download.suggested_filename
        await download.save_as(path)
        return path

    async def download_deposits(self, page: Page, date_from: date, date_to: date) -> Path:
        await self.open_report_menu(page)
        await page.get_by_text(re.compile('Dep[oó]sitos y movimientos', re.I)).click(timeout=20000)
        try:
            await page.wait_for_load_state('networkidle', timeout=8000)
        except Exception as e:
            print('[WARN] networkidle no llegó; se continúa con estado visual:', e)
        await page.wait_for_timeout(3000)
        await self.set_custom_date_range(page, date_from, date_to)

        try:
            await page.evaluate("""() => {
                const els = Array.from(document.querySelectorAll('button, a, div'));
                const el = els.find(x => (x.innerText || '').trim().toLowerCase() === 'aplicar filtros');
                if (!el) throw new Error('No existe botón Aplicar filtros');
                el.click();
            }""")
            print('[INFO] Aplicar filtros ejecutado por JS')
        except Exception as e:
            print('[WARN] No se pudo aplicar filtros por JS:', e)
            try:
                await page.get_by_role('button', name=re.compile('Aplicar filtros', re.I)).click(timeout=20000, force=True)
            except Exception:
                pass

        await page.wait_for_timeout(8000)

        # En Depósitos NetPay se fuerza generación del reporte antes de descargar.
        await self._log(ExecutionStatus.GENERANDO_REPORTE, 'Generar reporte')
        try:
            await page.get_by_text(re.compile('Generar reporte', re.I)).nth(1).click(timeout=20000, force=True)
        except Exception as e:
            raise RuntimeError('No se pudo hacer click en Generar reporte de DEPÓSITOS Y CARGOS; se bloquea para evitar descargar reporte viejo.') from e

        await page.wait_for_timeout(1000)

        modal_text = await page.locator('body').inner_text(timeout=10000)
        if '¿Deseas continuar con la generación del reporte?' in modal_text or 'Deseas continuar' in modal_text:
            clicked_confirm = await page.evaluate("""() => {
                const candidates = Array.from(document.querySelectorAll('button, a, label'))
                    .filter(x => {
                        const t = (x.innerText || '').trim().toLowerCase();
                        return t && !t.includes('cancel') && !t.includes('cerrar') &&
                            (t.includes('continuar') || t.includes('aceptar') || t.includes('sí') || t.includes('si') || t.includes('generar'));
                    });
                const el = candidates[candidates.length - 1];
                if (!el) return false;
                el.click();
                return true;
            }""")
            if not clicked_confirm:
                raise RuntimeError('Se detectó modal de confirmación, pero no se encontró botón para continuar/generar.')

        # Esperar a que NetPay termine de generar el reporte y aparezca Descargar reporte.
        for intento in range(1, 31):
            botones_descarga = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a, button, label'))
                    .filter(x => (x.innerText || '').toLowerCase().includes('descargar reporte'))
                    .map(x => (x.innerText || '').trim());
            }""")
            if botones_descarga:
                break
            await page.wait_for_timeout(5000)
        else:
            raise RuntimeError('NetPay no mostró Descargar reporte después de confirmar generación.')

        await self._log(ExecutionStatus.DESCARGANDO, 'Descargar reporte')


        botones = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a, button, label'))
                .filter(x => (x.innerText || '').toLowerCase().includes('descargar reporte'))
                .map((x, i) => ({idx: i, text: (x.innerText || '').trim()}));
        }""")


        if len(botones) < 1:
            raise RuntimeError('No existe botón Descargar reporte después de Generar reporte.')

        await page.evaluate("""() => {
            const els = Array.from(document.querySelectorAll('a, button, label'))
                .filter(x => (x.innerText || '').toLowerCase().includes('descargar reporte'));
            els[els.length - 1].click();
        }""")
        await page.wait_for_timeout(1500)

        async with page.expect_download(timeout=180000) as download_info:
            await page.get_by_role('button', name=re.compile('^Descargar$', re.I)).click(timeout=60000, force=True)
        download = await download_info.value

        path = self.download_dir / download.suggested_filename
        await download.save_as(path)

        return path

    def _move_to_safe_path(self, path: Path, report_type: ReportType, date_from: date, date_to: date) -> Path:
        safe_dir = self.download_dir / report_type.value / f'{date_from.isoformat()}_{date_to.isoformat()}'
        safe_dir.mkdir(parents=True, exist_ok=True)
        safe_name = path.name
        target = safe_dir / safe_name
        if target.exists():
            target = safe_dir / f'{path.stem}_{sha256_file(path)[:8]}{path.suffix}'
        shutil.move(str(path), str(target))
        return target
