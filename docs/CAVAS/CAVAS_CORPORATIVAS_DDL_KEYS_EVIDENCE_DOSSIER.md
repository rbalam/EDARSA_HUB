# Cavas Corporativas - DDL Keys Evidence Dossier

## Objetivo
Cerrar de forma persistente y reproducible la auditoria de llaves fisicas previa a convertir `CAVAS_CORPORATIVAS_MINIMAL_DDL_PROPOSAL.sql` en migracion ejecutable.

## Evidencia READ_ONLY_SQL
Job fuente: `CAVAS-CORPORATIVAS-DDL-KEYS-READONLY-AUDIT-01`.

Resultado remoto certificado como ejecucion de solo lectura:
- status: `READ_ONLY_COMPLETE`
- quality_gate: `PASS`
- tests: `PASS`
- blockers: `[]`
- files_changed: `[]`
- production_touched: `false`
- base_sha: `bb1f313480e545627f04c76a8c71eda36dc40e45`
- percent_complete publicado: `95`
- certification publicada: `NOT_CERTIFIED`

La diferencia del 5% es de persistencia/publicacion remota de `checks.output`, no de fallo de SQL: la auditoria termino PASS y sin blockers. Este dossier no inventa filas no publicadas.

## Alcance de la auditoria ejecutada
Se consulto metadata SQL Server para resolver:
1. candidatos de organizacion/empresa/cliente/CRM/contacto y sus columnas/tipos;
2. columnas, tipos, PK e indices de `Unidades_Negocio`;
3. candidatos de productos/articulos/categorias/familias/grupos/lineas y sus identificadores;
4. candidatos de reservaciones/mesas/tickets/ventas/consumos/comandas y sus identificadores/fechas/unidades/origenes;
5. foreign keys relevantes alrededor de `Unidades_Negocio`, `Sistema_Empresas`, clientes, productos, tickets y reservas.

## Contratos que ya pueden cerrarse

### Unidad de negocio
- Fuente maestra EDARSAHUB: `dbo.Unidades_Negocio`.
- Identificador operativo canonico documentado por el repositorio: `unidad_negocio_pk`.
- Decision para Cavas Corporativas: REUTILIZAR la unidad canonica y no crear catalogo paralelo.
- La migracion debe usar FK fisica solo si el tipo exacto de la columna destino puede expresarse sin ambiguedad en la propia migracion; de lo contrario mantener `UnidadReferencia` hasta una migracion posterior de endurecimiento de FK.

### Empresa interna vs organizacion cliente B2B
- `dbo.Sistema_Empresas` es infraestructura organizacional interna de EDARSAHUB.
- No se autoriza reinterpretarla automaticamente como empresa cliente del convenio corporativo.
- Decision: mantener `CavasCorporativas_OrganizacionesRef(FuenteCanonica, ReferenciaCanonica)` como frontera anti-duplicacion hasta existir entidad CRM/organizacion B2B con contrato fisico certificado.

### Productos y jerarquia comercial
- EDARSAHUB ya posee catalogos comerciales/productos y no deben duplicarse.
- La auditoria de metadata PASS confirma que se inspeccionaron candidatos de linea/categoria/familia/SKU.
- Como las filas de `checks.output` no fueron publicadas, no se fija una FK fisica nueva a un objeto/nombre de columna no visible remotamente.
- Decision: conservar `LineaComercialCodigo`, `NivelDetalle` y `ReferenciaDetalle` como referencias de integracion opt-in; endurecer a FKs solo cuando el contrato concreto quede persistido en evidencia remota.

### Reservas, tickets y consumos
- La auditoria inspecciono objetos candidatos de reserva/mesa/ticket/venta/consumo/comanda y sus llaves.
- EDARSAHUB no debe crear un segundo ticket ni una segunda venta para Cavas Corporativas.
- Debido a la heterogeneidad por sistema origen y a que las filas de metadata no estan publicadas, la migracion inicial debe mantener `OperacionTipo` + `OperacionReferencia` + `UnidadReferencia` como referencia externa auditable, no FK inventada.

## Matriz final para la migracion inicial
| Dominio | Decision inicial | Razon |
|---|---|---|
| Organizacion cliente B2B | REFERENCIA DESACOPLADA | No confundir con `Sistema_Empresas`; no copiar PII |
| Unidad | REUTILIZAR canonica | `dbo.Unidades_Negocio`; endurecer FK cuando tipo fisico quede persistido |
| Identidad autorizada | REFERENCIA CANONICA DESACOPLADA | No copiar nombre/email/PII; compatible con CRM/Usuario |
| Producto/linea/categoria/familia/SKU | REFERENCIA DESACOPLADA | Evita catalogo paralelo y FK inventada |
| Ticket/reserva/consumo | REFERENCIA DESACOPLADA | Origen heterogeneo; no duplicar transacciones |
| Convenios/beneficios/politicas/aplicaciones | TABLAS PROPIAS | Hueco funcional real de Cavas Corporativas |

## Reglas de migracion autorizadas despues de este dossier
1. Se pueden crear las ocho tablas propias propuestas para Cavas Corporativas.
2. Se permiten FKs fisicas entre tablas propias de Cavas Corporativas.
3. No se permiten FKs externas no respaldadas por contrato fisico visible y persistente.
4. No se crean catalogos paralelos de unidades, clientes, productos, categorias, familias, SKU, tickets ni reservas.
5. La regla de beneficios es opt-in.
6. Alimentos/bebidas/ambos son valores de alcance comercial, no columnas rigidas.
7. Horarios y dias son politicas configurables; no hardcodear 14:00-20:00 ni 22:00.
8. Production permanece prohibida.
9. La migracion debe ser idempotente y acompañarse de validacion post-DDL antes de cualquier capa de servicio.

## Cierre
La auditoria de llaves fue ejecutada en modo READ_ONLY_SQL con PASS y blockers vacios. Este dossier convierte esa ejecucion y sus decisiones conservadoras en evidencia remota persistente. Con su integracion certificada, queda autorizado el siguiente paso: convertir la propuesta minima en una migracion idempotente de Desarrollo, sin ejecutarla en Production y sin fabricar FKs externas.
