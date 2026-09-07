# Cavas Corporativas - GATE 2 Evidence Dossier

## Estado y procedencia

Este dossier persiste la evidencia verificable del GATE 2 antes de cualquier DDL.

### Evidencia Worker READ_ONLY_SQL

Job fuente: `CAVAS-CORPORATIVAS-GATE2-READONLY-SQL-EVIDENCE-01`.

Resultado remoto publicado:
- status: `READ_ONLY_COMPLETE`
- quality_gate: `PASS`
- tests: `PASS`
- blockers: `[]`
- production_touched: `false`
- files_changed: `[]`
- base_sha: `c2f9855f75e001ce7f9a15d016de2c4748f652c3`
- percent_complete publicado por la capa remota: `95`
- certification publicada por la capa remota: `NOT_CERTIFIED`

La ejecucion fue realizada por el Worker universal mediante el modo `READ_ONLY_SQL`. El contrato del runtime obliga `actions=[]`, acepta solo checks `sql_readonly_audit`, usa la conexion canonica de solo lectura y bloquea DML, DDL, EXEC, SELECT INTO y multiples sentencias.

### Consultas ejecutadas

La auditoria consulto metadata de SQL Server para:
1. objetos candidatos TABLE/VIEW relacionados con empresa, organizacion, corporativo, convenio, beneficio, cliente, CRM, contacto, usuario, rol, permiso, unidad, producto, articulo, categoria, familia, grupo, linea, precio, lista, descuento, promocion, reserva, mesa, ticket, venta, consumo, turno, horario, calendario, auditoria, bitacora, excepcion y cava;
2. columnas candidatas y tipos;
3. PK e indices unicos;
4. foreign keys de entrada/salida;
5. objetos canonicos exactos seleccionados para Unidades, Turnos, CavaSocios y fuentes comerciales.

El check SQL paso sin blockers.

## Limitacion de publicacion remota

La rama `worker/results` publica el resultado terminal resumido pero no expone las filas contenidas en `checks.output`. Por lo tanto este dossier NO inventa valores de filas no publicados y solo clasifica como hecho fisico aquello que puede corroborarse adicionalmente con artefactos canonicos versionados del repositorio.

## Matriz canonica de reutilizacion

| Dominio | Objeto/servicio corroborado | Decision | Evidencia util |
|---|---|---|---|
| Empresas internas EDARSAHUB | `dbo.Sistema_Empresas` | REUTILIZAR como catalogo organizacional interno; NO confundir automaticamente con empresa cliente B2B | Existe documentacion y uso backend; `EmpresaID` es la llave usada por modulos existentes |
| Unidades | `dbo.Unidades_Negocio` / `unidad_negocio_pk` | REUTILIZAR | Fuente maestra declarada por AGENTS y servicios canonicos |
| Horarios operativos | `dbo.Sistema_TurnosOperativosUnidad` | REUTILIZAR | El backend ya lee franjas operativas desde esta fuente; no hardcodear horarios |
| Usuarios/RBAC | `Usuario_Catalogo`, `Usuario_Roles`, `Usuario_Modulos`, `Usuario_Acciones` y asignaciones/contextos vigentes | REUTILIZAR/EXTENDER | Arquitectura RBAC SQL documentada; autorizacion debe seguir en backend |
| Cava personal | `backend/modules/cava_socios` y objetos `CavaSocios_*` | REUTILIZAR solo infraestructura transversal | Fuente SQL Server y dominio separado de socios/botellas |
| Productos/jerarquias | Catalogos comerciales canonicos existentes | REUTILIZAR | No crear catalogos paralelos de productos/categorias/familias/SKU |
| Ventas/tickets/KPIs | Fuentes comerciales canonicas SQL sincronizadas | REUTILIZAR | Analitica debe usar fuentes NO-LIVE y no duplicar venta por aplicar beneficio |
| Identidad cliente/contacto | CRM/cliente canonico existente | REUTILIZAR/EXTENDER | CavaSocios ya referencia identidad CRM; no copiar PII |

## Distincion critica: Empresa interna vs Empresa cliente corporativa

`Sistema_Empresas` representa la estructura empresarial interna usada por EDARSAHUB. Cavas Corporativas necesita representar tambien la ORGANIZACION CLIENTE B2B que firma o usa un convenio. GATE 2 no autoriza reutilizar `Sistema_Empresas` para ese proposito sin evidencia semantica explicita. Para evitar corrupcion conceptual, el DDL minimo posterior debe modelar una referencia B2B propia o enlazar una entidad CRM/organizacion canonica si existe una equivalente comprobada.

## Huecos funcionales confirmados para modelado de Cavas Corporativas

Los siguientes agregados no deben resolverse copiando CavaSocios ni catalogos maestros:
- convenio corporativo y su vigencia/estatus;
- vinculacion convenio -> unidad participante;
- usuarios/personas autorizadas del convenio enlazadas a identidad canonica;
- alcance opt-in del beneficio por linea comercial y, opcionalmente, categoria/familia/SKU;
- politicas de dias, horarios, fechas restringidas, acumulacion, topes y excepciones;
- definicion del beneficio comercial;
- registro auditable de beneficio aplicado a una reservacion/ticket/consumo canonico;
- analitica/CRM corporativa derivada, no duplicada.

## Reglas cerradas

1. Cavas Corporativas es un producto B2B separado de Cavas Personales.
2. `alimentos`, `bebidas` y `ambos` son configuraciones de alcance; el modelo debe admitir futuras lineas sin redisenarse.
3. Regla opt-in: lo no incluido expresamente no recibe beneficio.
4. El numero de invitados es ilimitado por defecto; cualquier limite futuro es politica.
5. Horarios sugeridos como 14:00-20:00 y limite antes de 22:00 NO son hardcodes.
6. Antes de implementar el limite de 22:00 negocio debe fijar cual evento manda: reserva, llegada, apertura de ticket, consumo o cierre.
7. Production permanece prohibida.
8. No Mongo y no LIVE para tableros.

## Incertidumbres que el DDL minimo debe respetar

- No crear FK hacia una entidad de organizacion/cliente B2B cuya llave/tipo no este confirmada.
- No asumir que `Sistema_Empresas` es el cliente corporativo.
- No fijar FK a producto/categoria/familia hasta elegir el identificador canonico vigente por dominio comercial.
- No fijar esquema fisico de reservaciones/tickets si el objeto canonico exacto varia por origen; usar referencias de integracion desacopladas hasta contrato posterior.

## Cierre GATE 2

Este dossier cierra la evidencia remota reproducible del GATE 2: existe ejecucion SQL READ_ONLY PASS sin blockers y una matriz persistente que separa REUTILIZAR/EXTENDER/HUECO_REAL sin fabricar filas ausentes. El siguiente paso permitido es GENERAR, pero NO EJECUTAR, un DDL minimo e idempotente para los agregados propios de Cavas Corporativas, respetando las incertidumbres anteriores y dejando Production=false.
