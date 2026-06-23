from __future__ import annotations

from datetime import date
from pathlib import Path
from decimal import Decimal

from .settings import Settings
from .crypto import decrypt_secret
from .date_ranges import split_date_range
from .models import ReportType, DownloadResult
from .portal import NetPayPortalRobot
from .layouts import detect_layout
from .importer import parse_netpay_workbook
from .db import EdarsaHubRepository


class NetPayRobotPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.repo = EdarsaHubRepository(settings)
        self.robot = NetPayPortalRobot(settings, logger=self._print_log)

    def _print_log(self, msg: str) -> None:
        print(msg)

    def _get_credentials(self) -> tuple[str, str]:
        creds = self.repo.get_active_netpay_credentials()
        if creds:
            username = creds.get('usuario') or ''
            ciphertext = creds.get('secreto_cifrado') or ''
            if not username or not ciphertext:
                raise RuntimeError('Credencial NetPay canonizada incompleta en SQL.')
            password = decrypt_secret(ciphertext, self.settings.server_secret_key)
            print(f"[CREDENCIALES_OK] NetPay desde SQL canonizado conector_id={creds.get('conector_id')} credencial_id={creds.get('credencial_id')}")
            return username, password

        print('[CREDENCIALES_WARN] No hay credencial NetPay activa en SQL; usando fallback .env temporal.')
        if self.settings.netpay_password_ciphertext:
            return self.settings.netpay_username, decrypt_secret(self.settings.netpay_password_ciphertext, self.settings.server_secret_key)
        allow_plaintext = str(getattr(self.settings, 'netpay_allow_plaintext_fallback', '') or '').lower() in {'1', 'true', 'yes', 'si'}
        if allow_plaintext and self.settings.netpay_password_plaintext:
            return self.settings.netpay_username, self.settings.netpay_password_plaintext
        raise RuntimeError('No existe credencial NetPay activa en SQL ni contraseña cifrada configurada.')

    def _get_password(self) -> str:
        return self._get_credentials()[1]


    def _coerce_excel_date(self, value):
        if value is None or value == "":
            return None

        try:
            if hasattr(value, "date"):
                return value.date()
        except Exception:
            pass

        from datetime import datetime

        s = str(value).strip()
        if not s:
            return None

        # NetPay puede traer fecha con hora: 18/06/2026 02:13
        formats = (
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
            "%d-%m-%Y %H:%M",
            "%d-%m-%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        )

        for fmt in formats:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue

        return None

    def _validate_transaction_dates(self, parsed, date_from, date_to) -> None:
        # En DETALLE_TRANSACCIONES la fecha operativa real es la fecha de transacción/cobro.
        # Si NetPay descarga un día distinto al solicitado, se bloquea antes de insertar SQL.
        fechas_trx = []

        for sheet in parsed:
            if sheet.report_kind != 'DETALLE_TRANSACCIONES':
                continue

            for row in sheet.rows:
                for key in (
                    'Fecha',
                    'Fecha de TRX',
                    'Fecha Trx',
                    'FechaTrx',
                    'Fecha Transacción',
                    'Fecha Transaccion',
                    'Fecha de Transacción',
                    'Fecha de Transaccion',
                ):
                    value = row.get(key)
                    f = self._coerce_excel_date(value)
                    if f:
                        fechas_trx.append(f)
                        break

        if not fechas_trx:
            raise RuntimeError(
                'No se encontraron fechas de transacción válidas dentro del Excel de transacciones. '
                'Se bloquea inserción SQL.'
            )

        fuera = [f for f in fechas_trx if f < date_from or f > date_to]
        if fuera:
            raise RuntimeError(
                f'Excel de transacciones no corresponde al rango solicitado. '
                f'rango_solicitado={date_from}..{date_to}, '
                f'fecha_trx_min_excel={min(fechas_trx)}, '
                f'fecha_trx_max_excel={max(fechas_trx)}, '
                f'fechas_fuera_de_rango={sorted(set(fuera))[:10]}'
            )

    def _validate_deposit_dates(self, parsed, date_from, date_to) -> None:
        # En DETALLE_DEPOSITOS_MOVIMIENTOS la fecha operativa del reporte es la
        # fecha de depósito/liquidación. La Fecha Trx puede ser anterior porque
        # NetPay liquida el 17 operaciones realizadas días antes.
        fechas_liquidacion = []

        for sheet in parsed:
            if sheet.report_kind != 'DETALLE_DEPOSITOS_MOVIMIENTOS':
                continue

            for row in sheet.rows:
                for key in (
                    'Fecha de depósito',
                    'Fecha Deposito',
                    'FechaDeposito',
                    'Fecha de Movimiento',
                    'Fecha Movimiento',
                ):
                    value = row.get(key)
                    if not value:
                        continue

                    try:
                        if hasattr(value, 'date'):
                            fechas_liquidacion.append(value.date())
                        else:
                            from datetime import datetime
                            s = str(value).strip()
                            for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'):
                                try:
                                    fechas_liquidacion.append(datetime.strptime(s, fmt).date())
                                    break
                                except ValueError:
                                    pass
                    except Exception:
                        pass

        if not fechas_liquidacion:
            raise RuntimeError('No se encontraron fechas de depósito/liquidación válidas dentro del Excel de depósitos. Se bloquea inserción SQL.')

        fuera = [f for f in fechas_liquidacion if f < date_from or f > date_to]
        if fuera:
            raise RuntimeError(
                f'Excel de depósitos no corresponde al rango solicitado por fecha de liquidación. '
                f'rango_solicitado={date_from}..{date_to}, '
                f'fecha_liquidacion_min_excel={min(fechas_liquidacion)}, '
                f'fecha_liquidacion_max_excel={max(fechas_liquidacion)}'
            )

    async def run(self, report_type: ReportType, date_from: date, date_to: date) -> list[DownloadResult]:
        username, password = self._get_credentials()
        if username:
            self.settings.netpay_username = username
        blocks = split_date_range(date_from, date_to, max_days=31)
        results: list[DownloadResult] = []
        print(f'Backfill/descarga dividido en {len(blocks)} bloque(s).')
        for block in blocks:
            print(f'Bloque {block.number}/{block.total}: {block.date_from} - {block.date_to}')
            execution_id = self.repo.create_execution(
                report_type=report_type.value,
                date_from=block.date_from.isoformat(),
                date_to=block.date_to.isoformat(),
            )
            try:
                result = await self.robot.run_download(report_type, block.date_from, block.date_to, password)
                self.repo.register_file(execution_id, str(result.file_path), result.sha256, report_type.value)
                validation = detect_layout(result.file_path)
                if not validation.ok:
                    err = '; '.join(validation.errors)

                    if 'No se reconoció layout NetPay' in err and 'vacío' in err:
                        self.repo.log_event(execution_id, 'INFO', 'SIN_DATOS', err)
                        print(f'[SIN_DATOS] {report_type.value} {block.date_from} - {block.date_to}: NetPay no devolvió registros.')
                        results.append(result)
                        continue

                    self.repo.log_event(execution_id, 'ERROR', 'LAYOUT_INVALIDO', err)
                    raise RuntimeError(err)
                parsed = parse_netpay_workbook(result.file_path)
                if report_type.value == 'DETALLE_TRANSACCIONES':
                    self._validate_transaction_dates(parsed, block.date_from, block.date_to)
                elif report_type.value == 'DETALLE_DEPOSITOS_MOVIMIENTOS':
                    self._validate_deposit_dates(parsed, block.date_from, block.date_to)
                for sheet in parsed:
                    self.repo.log_event(
                        execution_id,
                        'INFO',
                        'LAYOUT_OK',
                        f'{sheet.report_kind}/{sheet.sheet_name}: {len(sheet.rows)} registros; totales={sheet.totals}',
                    )
                self.repo.persist_parsed_rows(
                    execution_id=execution_id,
                    report_type=report_type.value,
                    file_path=str(result.file_path),
                    sha256=result.sha256,
                    date_from=block.date_from.isoformat(),
                    date_to=block.date_to.isoformat(),
                    parsed_rows=parsed,
                )
                results.append(result)
            except Exception as exc:
                self.repo.log_event(execution_id, 'ERROR', 'BLOQUE_FALLIDO', str(exc))
                raise
        return results

    def validate_file(self, file_path: str | Path) -> None:
        layout = detect_layout(file_path)
        print(layout)
        if layout.ok:
            parsed = parse_netpay_workbook(file_path)
            for sheet in parsed:
                print(f'{sheet.report_kind}/{sheet.sheet_name}')
                print(f'  registros: {len(sheet.rows)}')
                print(f'  totales: {sheet.totals}')
        else:
            raise SystemExit(2)
