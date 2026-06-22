# Robot NetPay Manager Downloader para EDARSAHUB

Robot base para descargar reportes de NetPay Manager y alimentar el pipeline de conciliaciones de EDARSAHUB SQL.

## Alcance incluido

- Login controlado a `https://manager.netpay.com.mx`.
- Detección de MFA/captcha sin intentar evadirlo.
- Selección/validación de empresa esperada.
- Descarga de reportes:
  - `DETALLE_TRANSACCIONES`: Reportes → Transacciones → Exportar → Exportar reporte completo.
  - `DETALLE_DEPOSITOS_MOVIMIENTOS`: Reportes → Depósitos y movimientos → Depósitos y cargos → Descargar/Generar reporte.
- Particionamiento automático de fechas en bloques máximos de 31 días.
- Guardado de archivo original, hash SHA-256, logs y resumen de ejecución.
- Validación de layouts reales NetPay.
- Stubs para integración SQL Server EDARSAHUB vía `pymssql`.
- Clase base para API futura de NetPay.
- Importación manual/copy-paste preparada como fuente alternativa.

## Lo que NO hace

- No brinca MFA.
- No resuelve captcha.
- No guarda contraseñas en texto plano.
- No hace reportes live desde NetPay.
- No concilia desde el portal; solo descarga y manda a staging.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Variables de entorno

Copia `.env.example` a `.env` y ajusta valores.

```bash
cp .env.example .env
```

Variables mínimas:

```bash
NETPAY_PORTAL_URL=https://manager.netpay.com.mx
NETPAY_USERNAME=usuario_servicio@empresa.com
NETPAY_PASSWORD_CIPHERTEXT=...
NETPAY_EXPECTED_COMPANY="DESARROLLOS AMARILLOS DE LA PENINSULA"
NETPAY_EXPECTED_UNIT="RESTAURANTE CIEN FUEGOS"
EDARSAHUB_SQL_HOST=...
EDARSAHUB_SQL_DATABASE=...
EDARSAHUB_SQL_USER=...
EDARSAHUB_SQL_PASSWORD=...
SERVER_SECRET_KEY=...
```

Para pruebas locales se puede usar `NETPAY_PASSWORD_PLAINTEXT`, pero **no usarlo en producción**.

## Uso CLI

Descargar transacciones de un día:

```bash
python -m netpay_robot.cli run \
  --report-type DETALLE_TRANSACCIONES \
  --date-from 2026-06-16 \
  --date-to 2026-06-16
```

Backfill enero-junio. El robot divide en bloques de máximo 31 días:

```bash
python -m netpay_robot.cli run \
  --report-type DETALLE_DEPOSITOS_MOVIMIENTOS \
  --date-from 2026-01-01 \
  --date-to 2026-06-15
```

Validar un archivo descargado manualmente:

```bash
python -m netpay_robot.cli validate --file /ruta/DetalleDepositos.xlsx
```

## Integración EDARSAHUB

Orden recomendado:

1. Ejecutar `sql/001_conciliaciones_netpay_robot_schema.sql` en ambiente de desarrollo.
2. Configurar credenciales del robot desde backend seguro, no desde frontend plano.
3. Probar `test-login` en modo visible.
4. Descargar un rango de 1 día.
5. Validar layout.
6. Cargar staging.
7. Normalizar a tablas canónicas.
8. Conciliar con Cuadre de Cortes Z, Propinas TPV y Estado de Cuenta Bancario.

## Reglas de conciliación recordadas

- `Cuadre` de Cortes Z es el origen operativo declarado.
- `Propinas TPV` se concilian, pero no alimentan KPI de venta.
- NetPay es una fuente/adquirente dentro de `Finanzas → Conciliaciones`, no el módulo único.
- Estado de cuenta bancario confirma el ingreso real.
