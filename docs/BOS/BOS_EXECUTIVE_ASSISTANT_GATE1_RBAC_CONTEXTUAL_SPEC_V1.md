# BOS EXECUTIVE_ASSISTANT — GATE 1 RBAC contextual (especificacion, no implementacion)

Estado: DESIGN_ONLY / PENDING_APPROVAL. Rama: Edarsahub_Desarrollo. Sin activacion ni autorizacion de Produccion.

## Evidencia de GATE 0
- R1: BOS-AI-EXECUTIVE-ASSISTANT-GATE0-R1, CERTIFIED_READ_ONLY.
- R2: BOS-AI-EXECUTIVE-ASSISTANT-GATE0-R2-RBAC, CERTIFIED_READ_ONLY.
- Ambas certificaciones son auditorias de contratos, NO pruebas de aislamiento multiempresa.

## Problemas a resolver
1. `backend/modules/rbac_context_sql/context_service.py`: seleccion implicita de primera unidad; filtro `(%s IS NULL OR UnidadNegocioID = %s)` puede mezclar asignaciones cuando el contexto queda nulo; no se verifica expresamente que la unidad solicitada pertenezca al usuario.
2. `backend/modules/rbac_context_sql/routes.py`: autenticacion presente, guard administrativo contextual no visible en operaciones sobre roles de terceros.
3. `backend/modules/rbac_context_sql/context_routes.py`: seleccion de unidad delegada al servicio sin comprobacion adicional visible.
4. `backend/core/rbac_helper_sql.py`: compatibilidad con claims legacy y acceso jerarquico no deben sustituir asignaciones SQL vigentes.

## Contrato de autorizacion propuesto
Entrada: identidad SQL del solicitante, sujeto, empresa_id, unidad_negocio_id, sucursal_id, modulo, accion, clasificacion de datos, intencion y contexto corporativo solicitado.
Salida: decision DENY/ALLOW, scope efectivo exacto, razon codificada, identificador de correlacion y evidencia auditable. Ausencia o ambiguedad de contexto => DENY salvo alcance corporativo/global explicitamente autorizado.
1. Resolver identidad en SQL y comprobar usuario activo.
2. Comprobar autorizacion del solicitante para ver/modificar roles de terceros; no confundir autenticacion con autorizacion.
3. Resolver asignaciones SQL activas y vigentes para el scope exacto; comprobar pertenencia de unidad a empresa y sucursal, cuando aplique.
4. Respetar alcance global explicito y roles de empresa/unidad/sucursal segun semantica canonica, sin interpretar NULL como comodin universal.
5. Calcular permisos efectivos por operacion y scope; denegaciones/restricciones/propietario/aprobacion deben conservar precedencia definida en RBAC canonico.
6. Para consultas corporativas multiunidad, autorizar cada unidad independientemente y agregar solo datos autorizados, sin union de privilegios.
7. No confiar en rol de JWT, jerarquia o cache desactualizada como unica prueba de autorizacion contextual.
8. Registrar actor, sujeto, empresa, unidad, permiso, decision, razon, correlacion, fuente y fecha; sin exponer PII innecesaria.

## Pruebas obligatorias
- Usuario gerente en Cienfuegos y contador en La Estelar: no cruzar permisos ni datos.
- Unidad inexistente/no asignada: DENY; unidad nula/ambigua: DENY.
- Asignacion global explicita: ALLOW solo dentro de su alcance y permisos.
- Asignacion selectiva: DENY fuera de seleccion; sucursal/empresa inconsistente: DENY.
- Asignacion revocada, usuario inactivo, rol inactivo y token stale: DENY.
- Usuario no autorizado intenta GET/POST/PUT roles de terceros: 403, sin efecto SQL.
- Error de SQL, timeout o cache stale: fail closed.
- Restriccion propietario, requiere autorizacion, permisos denegados: precedencia canonica.
- Pruebas de regresion de flujos legacy autorizados.

## Implementacion propuesta (NO aprobada)
REUSE: Usuario_RolesContexto, SQL-first, core RBAC, agent_capability_policy, auditoria existente.
EXTEND: servicio de resolucion de contexto y guards en rutas; pruebas unitarias/integracion con fixtures no productivas.
BLOCK: cambios de Produccion, migraciones SQL, activacion del agente, scheduler de reportes y autonomia hasta aprobacion y pruebas.
No crear otro motor RBAC, ni Mongo, ni writer/worker paralelo.

## Gates
G1A: aprobacion de esta especificacion y mapa de ownership.
G1B: patch minimo en Desarrollo y tests con resultado verificable.
G1C: validacion de regresion RBAC multiempresa y aprobacion de seguridad.
G1D: evaluacion separada de SQL/FinOps/Scheduler antes de activar EXECUTIVE_ASSISTANT.
