# SERVIDORES 6 — GATE 4A

## CHAPUR Connection Role Classification

**Estado:** CLOSED — EXTERNAL_INTEGRATION_NO_ACTIVE_CONSUMER

## Evidencia

- CHAPUR BACKOFFICE y CHAPUR NORTE son conexiones API_LOCAL.
- Ambas usan system_type ENTERPRISE.
- No tienen Empresa, Sucursal ni Unidad canonica vinculada.
- No existe mapping canonico de sucursal para sus server_id.
- No existe evidencia de ventas sincronizadas con scope corporativo CHAPUR.
- No existe consumidor funcional especifico CHAPUR en el codigo.
- Integrations Center admite conexiones con scope empresarial no explicito.
- CHAPUR 58 solo tiene evidencia historica y no existe como conexion actual.

## Clasificacion

- CHAPUR BACKOFFICE: EXTERNAL_INTEGRATION / NO_ACTIVE_CONSUMER.
- CHAPUR NORTE: EXTERNAL_INTEGRATION / NO_ACTIVE_CONSUMER.
- CHAPUR 58: HISTORICAL_ONLY.

## Decision

No crear Empresa, Sucursal o Unidad para estas conexiones sin evidencia empresarial nueva.

Mantener BACKOFFICE y NORTE fuera de Operaciones.

Servidores / Integraciones conserva estas conexiones como infraestructura tecnica externa.

Cualquier consumidor futuro debe integrarse mediante la infraestructura universal existente de Integraciones y sync, sin arquitectura especifica para CHAPUR.

## Siguiente Gate

Gate 4B — External Integration Health & Consumer Readiness.

Debe verificar estado tecnico y elegibilidad de consumo sin ejecutar sync, sin habilitar Operaciones y sin crear scope corporativo.
