# ISCAM - Baseline certificado de Cuentas y Comandas

Fecha de certificacion: 2026-09-11
Certificado por: Carlos Ruz / Auditoria EDARSA
Commit funcional certificado: `de53545b2f1db2591dc43387828e3db7c0b7a7d6`
Branch de resguardo: `baseline/iscam-cuentas-comandas-r49-20260911`

## Alcance congelado

Los siguientes reportes se consideran correctos y no deben ser alterados por trabajos posteriores destinados a corregir otros reportes ISCAM:

- Resumen de Cuentas
- Comandas de Venta

Las correcciones posteriores de `Formas de Pago (Corte)` y `Pagos por Ticket` deben ser quirurgicas y no cambiar el contrato, consultas, filtros, agregaciones, drill-downs ni presentacion funcional de Cuentas y Comandas.

## Baseline de control - CIENFUEGOS agosto 2026

Exportaciones certificadas por el usuario el 2026-09-11:

- Resumen de Cuentas: 1,027 folios unicos, 2,899 personas, importe $3,959,563.00.
- Comandas de Venta: 11,922 lineas de detalle y 1,027 folios unicos.
- Reporte Ejecutivo/Ventas por Periodo: $3,959,563.00, 1,027 cheques y 2,899 clientes.

## Reportes pendientes de conciliacion

- Pagos por Ticket: pendiente. Export de control $3,958,813.00; diferencia contra venta $750.00.
- Formas de Pago (Corte): pendiente. Export de control $4,407,464.95; diferencia contra venta $447,901.95.

## Regla de cambio

Cualquier trabajo posterior que necesite tocar una region protegida por `test_iscam_cuentas_comandas_locked_r50.py` debe detenerse y requerir una autorizacion explicita que indique que el baseline R49 deja de ser valido. No se debe levantar el lock solo para hacer pasar una correccion de otro reporte.
