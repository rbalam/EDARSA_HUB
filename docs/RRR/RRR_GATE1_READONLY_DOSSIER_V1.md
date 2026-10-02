# RRR - GATE 1 - READ_ONLY Dossier V1

## Certificacion base
Fuente: RRR-GATE1-READONLY-EVIDENCE-R2-20260908. Resultado: CERTIFIED_READ_ONLY, PASS, 100%, production_touched=false. Base de certificacion: READ_ONLY_SQL_PASS_PLUS_SANITIZED_EVIDENCE.

## Principio
Esta matriz se deriva de evidencia SQL real de solo lectura. No autoriza todavia DDL. Define que se reutiliza, que puede extenderse, que debe crearse y que no debe tocarse para evitar duplicar fuentes canonicas.

## Matriz canonica

### REUSE
1. Cliente_Catalogo: maestro canonico de cliente. PK ClienteID. Tiene indices/unique sobre CodigoCliente y RFC y relaciones a Cliente_Grupos, Venta_CondicionesPago, Venta_ListasPrecios y otras estructuras. RRR debe referenciar ClienteID y no crear maestro paralelo.
2. Cliente_Contactos: reutilizar para contactos asociados al ClienteID.
3. Cliente_Direcciones: reutilizar para direcciones asociadas al ClienteID.
4. Cliente_UsuariosPortal: reutilizar cuando RRR necesite vincular acceso/portal del cliente; no crear credenciales paralelas.
5. Venta_Encabezado: reutilizar como fuente transaccional canonica cuando aplique; ya referencia Cliente_Catalogo por ClienteID y se relaciona con pagos/detalle/estatus.
6. Venta_Detalle y Venta_Pagos: reutilizar para detalle economico y pagos vinculados a VentaID.
7. Producto_Catalogo y estructuras canonicas de producto: reutilizar; RRR no crea catalogo de productos.
8. Usuario_Catalogo y estructuras actuales de rol/permiso/autorizacion: reutilizar para RBAC y auditoria de acciones administrativas RRR.
9. Operativo_Notificaciones_Log: reutilizar como infraestructura/log de entrega de notificaciones. Tiene NotificacionID, TipoEvento, WorkflowID, TareaID, destinatarios, canal, estado, fechas y MetadatosJSON.
10. CavasCorporativas_* y CavaSocios_*: reutilizar como dominios independientes interoperables; RRR puede consumir elegibilidad/beneficios o relacion de cliente, pero no absorber ni duplicar Cavas.

### EXTEND
1. CRM_PostventaEncuestas: candidato canonico para extender la captura de feedback/resena propietaria porque ya existe y relaciona CuentaID y TicketID. La extension RRR debera preservar su semantica existente y agregar solo lo indispensable para distinguir origen, evento/venta, dimensiones/NPS o metadatos RRR cuando el diseno fisico confirme la brecha.
2. CRM_PostventaTickets: candidato para vincular incidencias/experiencias de postventa a encuestas RRR cuando corresponda; no usarlo como ledger ni score.
3. Infraestructura de notificaciones/comunicaciones existente: extender mediante configuracion/eventos RRR, no mediante un segundo motor de envio, siempre que Gate 2 confirme el contrato tecnico exacto.
4. Cavas: solo extension de interoperabilidad/eligibilidad mediante claves canonicas; no extender su modelo interno para convertirlo en RRR.

### CREATE
La auditoria no encontro un dominio RRR canonico que cubra las siguientes capacidades. Deben modelarse como objetos nuevos en Gate 2, con nombres y columnas definitivos pendientes de diseno fisico minimo:
1. Ledger RRR auditable de movimientos de recompensa, con idempotencia, reversa y trazabilidad. No reutilizar Sync_Token_Ledger: ese ledger pertenece a telemetria/costo de tokens y es semanticamente ajeno.
2. Reglas/versiones de elegibilidad y otorgamiento de recompensas.
3. RRR Score versionado y explicable, separado del saldo redimible.
4. Ranking/tier derivado y versionado, separado de Score y Balance.
5. Catalogo/configuracion de recompensas y beneficios RRR, sin duplicar beneficios de Cavas.
6. Eventos RRR procesados/idempotencia/antifraude cuando no exista contrato equivalente reutilizable.
7. Segmentacion RRR y/o snapshots de segmentos necesarios para marketing, si Gate 2 confirma que no existe estructura funcional equivalente reutilizable.
8. Atribucion/conversion RRR para medir impacto incremental de campanas y beneficios cuando no pueda resolverse exclusivamente con estructuras comerciales existentes.

### DO_NOT_TOUCH
1. Cliente_Catalogo como fuente de verdad: no duplicar, reemplazar ni convertir en tabla RRR.
2. Venta_Encabezado/Venta_Detalle/Venta_Pagos: no alterar su semantica para almacenar score, puntos o ranking. RRR solo referencia claves canonicas.
3. Producto_Catalogo: no incrustar puntos/tiers como hardcodes estructurales.
4. Usuario_Catalogo/RBAC existente: no crear usuarios o roles paralelos para RRR.
5. CavaSocios_* y CavasCorporativas_*: no fusionar con RRR ni reutilizar tablas de botellas/cargos/movimientos como ledger RRR.
6. Sync_Token_Ledger: no reutilizar para recompensas; pertenece a tokens/operacion tecnica.
7. Produccion: no tocar en este gate.

## Evidencia clave observada
- Cliente_Catalogo: PK ClienteID, unique CodigoCliente y RFC; relaciones a Cliente_Contactos, Cliente_Direcciones y Cliente_UsuariosPortal.
- Venta_Encabezado: FK ClienteID -> Cliente_Catalogo.ClienteID; Venta_Detalle y Venta_Pagos se relacionan por VentaID.
- CRM_PostventaEncuestas: relaciona CuentaID con CRM_Cuentas y TicketID con CRM_PostventaTickets.
- CavaSocios_Socios posee ClienteCRMID y sus propios indices; CavaSocios_Botellas/Cargos/Movimientos tienen PK/FK propias.
- Operativo_Notificaciones_Log contiene contrato suficiente para reutilizar el log/canalizacion de notificaciones.
- No aparecio un objeto Reward canonico; el unico objeto con nombre Ledger observado fuera del dominio RRR es Sync_Token_Ledger, semanticamente no reutilizable.

## Decision de arquitectura para Gate 2
Gate 2 debe disenar el DDL minimo de RRR alrededor de referencias a las fuentes canonicas existentes. El nuevo esquema no debe recrear clientes, ventas, productos, usuarios, notificaciones ni Cavas. Debe enfocarse exclusivamente en las brechas CREATE y en extensiones minimas verificadas.

## Cierre Gate 1
GATE 1 queda apto para cierre al 100% como CERTIFIED_READ_ONLY porque la auditoria R2 esta certificada, tiene sql_readonly_evidence saneada, blockers=0, tests=PASS, quality_gate=PASS y production_touched=false. Este dossier no autoriza ejecutar DDL; solo habilita Gate 2 de arquitectura fisica/DDL minimo.
