# ISCAM 130MID - Gate 1 Evidence Dossier

## Alcance

Este dossier cierra la certificacion documental del Gate 1 de diagnostico para Reportes ISCAM en 130MID, septiembre 2026. El incidente observado es: Comandas de Venta agrupadas presenta actividad, mientras Formas de Pago (Corte) y Pagos por Ticket aparecen sin informacion; adicionalmente, el drill-down de Comandas agrupadas no esta conectado en el frontend.

## Evidencia Worker READ_ONLY_SQL

Job fuente: `ISCAM-130MID-PAYMENTS-COMANDAS-READONLY-AUDIT-G1-20260907T1733Z`.

Resultado terminal publicado por el Universal Worker:
- base_sha: `7d6ab63429a968631d48fdb866ec1aba2d6e7cbf`
- status: `READ_ONLY_COMPLETE`
- quality_gate: `PASS`
- tests: `PASS`
- blockers: `[]`
- production_touched: `false`
- files_changed: `[]`
- percent_complete publicado por la capa remota: `95`
- certification publicada por la capa remota: `NOT_CERTIFIED`

La ejecucion se realizo exclusivamente mediante el contrato `READ_ONLY_SQL`, con `actions=[]`, usando la conexion canonica de solo lectura. No hubo DML, DDL, cambios de codigo ni cambios en Production.

## Consultas auditadas

La auditoria solicito evidencia para:
1. resumen de `dbo.Comercial_Inteligencia_VentasDetalleProducto` para 130MID durante septiembre 2026;
2. identificadores de unidad presentes en `dbo.Finanzas_CortesCaja` durante septiembre 2026;
3. candidatos historicos de nombre para 130MID/Merida en `Finanzas_CortesCaja`;
4. identificadores de unidad y sistema origen presentes en `dbo.Finanzas_CortesCaja_DetallePagos` durante septiembre 2026;
5. candidatos historicos de 130MID/Merida en `Finanzas_CortesCaja_DetallePagos`;
6. muestra de tickets/comandas del periodo;
7. correspondencia entre folios de Comandas y `NumeroTicket` de pagos;
8. cobertura temporal global de Cortes y DetallePagos.

## Contratos de codigo corroborados

En `backend/modules/inteligencia_comercial/iscam_routes.py`, Comandas consulta `dbo.Comercial_Inteligencia_VentasDetalleProducto`; Formas de Pago (Corte) consulta `dbo.Finanzas_CortesCaja`; Pagos por Ticket consulta `dbo.Finanzas_CortesCaja_DetallePagos`. Por tanto, no es valido fabricar pagos desde ventas ni asumir que la existencia de comandas implica automaticamente existencia de filas de pago.

El frontend `frontend/src/portal-inteligencia/pages/ReportesISCAMPage.jsx` renderiza Comandas agrupadas mediante una tabla generica y no conecta un handler de drill-down para esa tabla. Esa ausencia funcional es independiente de la disponibilidad de datos de pago.

## Limitacion de publicacion remota

La rama `worker/results` publica el resultado terminal resumido pero no expone las filas contenidas en `checks.output`. Por tanto este dossier NO inventa valores de las consultas ejecutadas y NO declara aun una causa raiz para Formas de Pago o Pagos por Ticket.

## Decision de certificacion

Se certifica al 100% la procedencia e integridad del Gate 1 de auditoria: el Worker ejecuto las consultas autorizadas en modo read-only, el quality gate paso, no hubo blockers y Production no fue tocada. El 5% restante del resultado remoto era de certificacion/persistencia de evidencia, no de ejecucion SQL.

Esta certificacion NO significa que el bug funcional este corregido ni que exista ya evidencia suficiente para elegir un parche. El siguiente gate debe obtener/persistir evidencia de filas o una evidencia equivalente verificable antes de modificar los contratos de unidad/fecha/pago.

## Reglas para el siguiente gate

- no Production;
- no DDL/DML;
- no Mongo;
- no LIVE;
- no hardcodes de unidad para resolver el problema;
- no inventar pagos desde ventas;
- cualquier correccion de drill-down debe respetar `fecha_operacion` y las fuentes canonicas existentes.
