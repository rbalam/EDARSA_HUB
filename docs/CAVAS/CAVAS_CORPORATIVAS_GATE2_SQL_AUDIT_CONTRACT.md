# Cavas Corporativas - GATE 2 SQL Audit Contract

## Objetivo
Auditar el esquema SQL canonico real antes de proponer DDL o codigo de Cavas Corporativas. Este contrato es READ-ONLY y no autoriza cambios de datos, esquema ni Production.

## Precondicion
GATE 1 esta CERTIFIED/INTEGRATED al 100% en commit 3c4592797207ae125cab516ed83ab170e4eb2e89.

## Dominios obligatorios de auditoria
1. Empresa/organizacion B2B y contactos.
2. Identidad CRM/cliente/persona y llaves publicas/canonicas vigentes.
3. Usuarios EDARSAHUB y RBAC; mecanismo correcto para autorizados corporativos.
4. dbo.Unidades_Negocio y relaciones canonicas de unidad.
5. Productos, lineas de venta, categorias, familias y SKU.
6. Listas/precios/descuentos/promociones/beneficios/convenios existentes.
7. Reservaciones, mesas, tickets, ventas, consumos y relaciones disponibles.
8. Sistema_TurnosOperativosUnidad y cualquier configuracion de horarios/dias/calendarios.
9. Auditoria, bitacoras, autorizaciones/excepciones.
10. CRM/analitica y fuentes NO-LIVE disponibles.
11. CavaSocios solo para infraestructura transversal reutilizable; no reutilizar agregados personales como modelo corporativo.

## Consultas permitidas
Solo SELECT y metadata. Usar sys.schemas, sys.tables, sys.views, sys.columns, sys.foreign_keys, sys.foreign_key_columns, sys.indexes, sys.index_columns e INFORMATION_SCHEMA cuando ayude. Se permiten SELECT TOP limitados para comprender semantica de catalogos no sensibles. No exponer secretos, passwords, tokens ni credenciales.

## Busqueda inicial de objetos
Buscar nombres y columnas relacionados con: Empresa, Organizacion, Corporativo, Convenio, Beneficio, Cliente, CRM, Contacto, Usuario, Rol, Permiso, Unidad, Producto, Articulo, Categoria, Familia, Grupo, Linea, Precio, Lista, Descuento, Promocion, Reserva, Reservacion, Mesa, Ticket, Venta, Consumo, Turno, Horario, Calendario, Auditoria, Bitacora, Excepcion y Cava.

## Evidencia minima por objeto candidato
- schema y nombre fisico exacto; tipo TABLE/VIEW.
- columnas relevantes con tipo/nullability.
- PK/unique indexes.
- FKs de entrada/salida.
- evidencia de uso en codigo actual cuando exista.
- muestra TOP limitada solo si es necesaria y no sensible.
- clasificacion: REUTILIZAR, EXTENDER, NO_APLICA o HUECO_REAL.

## Reglas de arquitectura
- No duplicar dbo.Unidades_Negocio ni catalogos maestros existentes.
- No copiar PII de clientes/contactos; referenciar identidad canonica.
- No crear catalogo paralelo de productos, categorias, familias o SKU.
- Beneficios son opt-in: lo no incluido expresamente queda fuera.
- Alcance parametrico por convenio -> unidad -> linea comercial -> categoria/familia/SKU si el catalogo real lo permite.
- Alimentos, bebidas y ambos son configuracion, no columnas/hardcodes exclusivos; futuras lineas deben poder agregarse sin redisenar el dominio.
- Horarios y limite antes de 22:00 son politicas configurables; no hardcodear hasta definir evento temporal de aplicacion.
- RBAC y autorizacion siempre backend/canonicos.
- Cavas Corporativas es producto B2B separado de Cavas Personales.
- Analitica usa fuentes SQL canonicas sincronizadas; no Mongo ni LIVE para tableros.

## Entregable esperado de la ejecucion SQL READ-ONLY
Crear un dossier de evidencia con matriz DOMINIO | OBJETO REAL | LLAVE | RELACIONES | REUTILIZAR/EXTENDER/CREAR | EVIDENCIA. Enumerar HUECOS_REALES solamente cuando la ausencia haya sido comprobada en metadata. Proponer DDL minimo posterior, pero NO ejecutarlo.

## Criterios para GATE 2 completo
GATE 2 no se considera funcionalmente cerrado solo por integrar este contrato. El cierre requiere una ejecucion READ_ONLY_SQL autorizada contra SQL canonico, evidencia de objetos reales, matriz reuse/extend/create y blockers vacios. Este archivo evita inventar DDL antes de esa evidencia.

## Production
PROHIBIDA. production_allowed=false.
