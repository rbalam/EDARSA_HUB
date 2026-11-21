# EDARSAHUB Services - Gate 1 Capability & Ownership Map R1

## 1. Entrada certificada
Gate0A = `CERTIFIED_READ_ONLY`, `PASS`, 100%, `production_touched=false`. Gate0B CERT = `CERTIFIED_READ_ONLY`, `READ_ONLY_REPOSITORY_PASS_PLUS_SANITIZED_EVIDENCE`, 100%, sin blockers ni archivos modificados.

## 2. Principio rector
EDARSAHUB BOS conserva la verdad transversal. Services es una familia de bounded contexts satelite. Cada capacidad se clasifica como `REUSE`, `EXTEND`, `CONSOLIDATE`, `NEW` o `DO_NOT_CREATE`.

## 3. Matriz de ownership transversal
| Capacidad | Clasificacion | Owner canonico | Services |
|---|---|---|---|
| Persona/identidad humana | REUSE | Gobierno | Referencia `Gobierno_Persona` |
| Vinculo persona-cliente-proveedor-usuario | REUSE | Gobierno | Consume `Gobierno_PersonaVinculo` |
| Usuarios/Auth/RBAC | REUSE | Auth/RBAC BOS | Solo registra permisos/rutas del dominio |
| Empresas/unidades/sucursales | REUSE | BOS corporativo | Referencia maestros existentes |
| Cliente/contactos/direcciones | REUSE | Comercial/Clientes | Consume maestros existentes |
| Proveedor | REUSE | Proveedores/Compras | Consume maestro existente |
| CRM leads/oportunidades | REUSE | CRM | No crear CRM paralelo |
| Cotizacion/pedido comercial | REUSE/EXTEND | Comercial | Integrar cuando semantica aplique |
| Documentos/versiones | REUSE | Gobierno documental | Mantener relaciones semanticas |
| Auditoria transversal | REUSE | BOS | Historial de negocio solo donde sea invariancia |
| Notificaciones | REUSE | Communications/Scheduler | Emitir eventos, no segundo dispatcher |
| Inventario/materiales/almacenes | REUSE | Operaciones/Inventarios | Consumir movimientos/maestros canonicos |
| Activos/equipos/mantenimiento | REUSE/EXTEND | ActivoFijo | Integrar recursos y OT compatibles |
| Ordenes de trabajo genericas | CONSOLIDATE | ActivoFijo + Services | Resolver frontera semantica antes de nueva tabla |
| Finanzas/pagos/bancos | REUSE | Finanzas/Banca BOS | Solo hechos y referencias de dominio |
| Comisiones | CONSOLIDATE | COA | Extender reglas/splits/clawback si compatible |
| Expediente/eventos/referencias | REUSE/EXTEND | COA/Gobierno | Reusar patron cuando corresponda |
| Scheduler/SLA | REUSE | Scheduler BOS | Registrar jobs/eventos, no segundo scheduler |

## 4. Universal Services
### 4.1 Provider
Clasificacion: `NEW` como agregado de dominio, pero identidad = `REUSE`.
- Provider puede ser `INDIVIDUAL`, `ORGANIZATION`, `FACILITY`.
- Individual referencia `Gobierno_Persona`.
- Organization/Facility debe enlazarse a entidad canonica existente cuando corresponda; no forzar empresa interna.

### 4.2 Profession / Specialty / Credential / Service
Clasificacion: `NEW` de dominio.
- Profession != Specialty != Credential/Habilitation != Service.
- Prohibido una tabla por oficio/profesion.

### 4.3 Resource
Clasificacion: `NEW` abstraccion de dominio con integracion a maestros existentes.
Tipos minimos: `PERSON`, `TEAM`, `VEHICLE`, `ROOM`, `EQUIPMENT`, `TOOL`, `VENUE`, `RENTAL_ASSET`.

### 4.4 ServiceSubject
Clasificacion: `NEW` abstraccion de referencia.
Tipos: `PERSON`, `VEHICLE`, `PROPERTY`, `EQUIPMENT`, `ASSET`, `COMPANY`, `PROJECT`, `LEGAL_MATTER`, `POLICY`, `PORTFOLIO`, `ANIMAL`, `FACILITY`, `DOCUMENT`.

### 4.5 Engagement motors
Clasificacion: `NEW/EXTEND` segun motor.
Motores canonicos Services: `APPOINTMENT`, `CASE`, `PROJECT`, `WORK_ORDER`, `EVENT`, `RECURRENCE`.
Gate 2 definira si comparten cabecera comun o contratos separados.

## 5. Construction & Design
Ownership Services/Construction para obra, etapas, frentes, partidas, conceptos, avances, generadores, estimaciones, change orders, calidad, seguridad y entrega.
`REUSE`: persona, proveedores, compras, inventario, activos, documentos, pagos, RBAC.
`NEW`: crew/cuadrilla como agregado operativo, avance fisico, presupuesto contractual de obra, estimacion de obra y lineage de revisiones.
Regla: avance fisico != consumo financiero != tiempo transcurrido.
Anticipos y retenciones deben integrarse con Finanzas BOS y no crear tesoreria paralela.

## 6. Fabrication
Ownership Services/Fabrication para configuracion parametrica, BOM, despiece, optimizacion, corte, produccion e instalacion.
`REUSE`: materiales, productos, inventarios, proveedores, costos, activos.
`CONSOLIDATE`: revisar conceptos existentes de Produccion/Tablajeria antes de crear estructuras equivalentes.
Regla: sobrante reutilizable != merma automatica.

## 7. Interiors & Fit-Out
Ownership Services/Interiors para Space, brief, moodboard, layout, seleccion de materiales/mobiliario/equipo, revisiones y aprobacion.
`REUSE`: catalogos comerciales/materiales/proveedores/costos/documentos.
`NEW`: `SPACE` como agregado generico; no crear modulo independiente por cocina/bano/closet.
Regla: Visual Concept != Technical Drawing != Approved Construction Document.

## 8. Real Estate & Land
Ownership Services/Land para genealogia territorial y hechos inmobiliarios.
`NEW`: `LandParcel` jerarquico con parent, type, geometry, surface, legal/cadastral refs, owner/status.
Tipos configurables: `PREDIO`, `MACROLOTE`, `SECTOR`, `ETAPA`, `FRACCIONAMIENTO`, `PRIVADA`, `MANZANA`, `LOTE`, `SUBLOTE`, `CONDOMINIO`, `UNIDAD_PRIVATIVA`, `AREA_COMUN`, `AREA_VERDE`, `PARQUE_PUBLICO`, `VIALIDAD`, `DONACION`, `EQUIPAMIENTO`, `SERVIDUMBRE`, `RESERVA`, `COMERCIAL`.
Eventos territoriales: `SUBDIVISION`, `FUSION`, `SEGREGACION`, `LOTIFICACION`, `RELOTIFICACION`, `AFECTACION`, `DONACION`, `CESION`, `INCORPORACION`, `RECTIFICACION`.
`REUSE`: clientes, documentos, pagos, cobranza, comisiones COA, RBAC.
`NEW`: lineage territorial, conciliacion de superficies, dossier legal por parcela, notario/notaria si no existe maestro compatible, inventario comercial territorial.
Regla: calculo canonico de superficie en m2 preservando unidad capturada/mostrada.

## 9. Commission Engine
Owner propuesto: COA. Clasificacion `CONSOLIDATE/EXTEND`.
Bases candidatas: `PRECIO_VENTA`, `PRECIO_NETO`, `MONTO_COBRADO`, `ENGANCHE`, `UTILIDAD`, `MONTO_ESCRITURADO`, `MONTO_RECONOCIDO`.
Triggers: firma, enganche, cobros proporcionales, escritura, hitos, retencion. Estados: calculada/devengada/autorizada/pagada/pendiente. Reversion = clawback; no borrar historia.

## 10. Fronteras prohibidas
`DO_NOT_CREATE`:
- segundo maestro de personas;
- segundo CRM;
- segundo auth/RBAC;
- segundo inventario;
- segundo motor financiero/bancario;
- segundo scheduler;
- segundo motor generico de comisiones sin agotar COA;
- tablas por profesion;
- Services dentro de `backend/core`;
- Mongo operativo;
- dashboards LIVE.

## 11. Dependencias
Services -> Gobierno Persona/Documentos; Auth/RBAC; Empresas/Unidades; CRM/Clientes; Proveedores/Compras; Inventarios; ActivoFijo; COA; Finanzas; Scheduler/Notifications.
Construction -> Universal Services + Inventarios + Compras + ActivoFijo + Finanzas.
Fabrication -> Universal Services + Inventarios + Produccion/Tablajeria + Costos.
Interiors -> Universal Services + Comercial + Catalogos + Fabrication.
Land -> Universal Services + CRM + Documentos + COA + Finanzas + GIS adapters.

## 12. Gate 2
Siguiente gate: `Domain Data Contract`. Debe definir esquema logico minimo, PK/FK/unique/indexes, ownership, estados/transiciones, idempotencia, auditoria, PII/retencion, migracion y rollback. DDL seguira separado de ejecucion.
