# EDARSAHUB Always-On Guardrails

Esta regla aplica a Antigravity.

## Prioridad

1. Seguridad de base de datos.
2. Seguridad de codigo.
3. Fuente canonica.
4. RBAC.
5. Cambio minimo.

## Rama

Trabajar solo en `Edarsahub_Desarrollo`.

## DB

Solo auditorias `SELECT`.
No DDL/DML.
No imprimir secretos.

## Comercial

- Ventas = `ventas_total` con IVA.
- Unidad de negocio = `unidad_negocio_pk`.
- Fuente = `dbo.Unidades_Negocio`.
- No usar `unidad_negocio_nombre` como llave primaria.
- No usar `ventas_sin_propina` como venta principal.

## Roles

- Auditor: solo evidencia, sin editar.
- Coder: edicion minima.
- Validator: valida y bloquea.

## Prohibido

- MongoDB en modulos criticos.
- Live queries para endpoints/tableros/reportes.
- Mocks.
- Hardcodes.
- Fuentes paralelas.
- Debilitar RBAC.
- Deploy/push sin autorizacion.
