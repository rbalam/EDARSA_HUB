# Tickets de venta: contrato canónico, 2026-10-07

Alcance: ventas abiertas/del día y ventas cerradas de SoftRestaurant y ManagementPro; Tablero Comercial y Tablero Ejecutivo. Rama base `Edarsahub_Desarrollo`, SHA `b44dcbf41e1d1d6d48d64d439fbd6cb4f34d2068`.

## Persistencia y presentación

Se amplía el destino existente `dbo.Comercial_Inteligencia_VentasDetalleProducto`; las ventas del día conservan el mismo contrato en `dbo.Comercial_Ventas_Dia_Abiertas_v2.detalle_abiertas_json`. No se crea otro maestro de clientes ni otra fuente de KPIs. Los comentarios originales se conservan; la descripción del catálogo de descuentos tiene prioridad únicamente para presentación.

Las partidas mantienen `cheqdet.movimiento` (SoftRestaurant), `Comanda_Detalle.Cd_Id` (ManagementPro abierto) o `Venta.Vn_Folio + Vn_ID` (cerrado). `Cd_Key` se conserva por separado. La unión Venta–Comanda_Detalle utiliza documento e ID de partida; no se infiere por producto. La inserción canónica usa una transacción y rollback ante error; la lectura del ticket no usa NOLOCK. Nombre/RFC/dirección, comentario de partida y comentario de descuento de cuenta salen de esa persistencia. Las direcciones de entrega se conservan separadas de la dirección principal. Los campos sin equivalencia en un motor se guardan NULL.

Los dos tableros importan `KpiDrilldownDialog`, con el mismo `IAContextualLauncher` y `view_id=comercial_detalle_ventas`. `TicketVentaModal` es compartido. Las rutas conservan su validación RBAC y no consultan POS en LIVE.

## Mapeo exacto de metadata nueva

Alias `h`: cheques/tempcheques o Comanda; `d`: cheqdet/tempcheqdet o Comanda_Detalle; `cl`: clientes o Cliente; `td`: tipodescuento o Tipo_Descuento. En ventas cerradas de MPRO, la identidad de partida corresponde a Venta, enlazada al documento original.

| Campo canónico | Tipo SQL | SoftRestaurant | ManagementPro |
|---|---|---|---|
| partida_origen_id | nvarchar(100) | `CONVERT(nvarchar(100), d.movimiento)` | `CONVERT(nvarchar(100), d.Cd_Id)` |
| partida_key | nvarchar(100) | `NULL` | `d.Cd_Key` |
| cliente_id | nvarchar(100) | `h.idcliente` | `h.Cl_Cve_Cliente` |
| cliente_nombre | nvarchar(max) | `cl.nombre` | `COALESCE(NULLIF(cl.Cl_Razon_Social,''),NULLIF(cl.Cl_Descripcion,''))` |
| cliente_razon_social | nvarchar(max) | `NULL` | `cl.Cl_Razon_Social` |
| cliente_descripcion | nvarchar(max) | `NULL` | `cl.Cl_Descripcion` |
| cliente_maestro_id | nvarchar(100) | `NULL` | `cl.Cl_Cve_Maestro` |
| cliente_sucursal_origen | nvarchar(50) | `NULL` | `cl.Sc_Cve_Sucursal` |
| cliente_contacto | nvarchar(max) | `cl.contacto` | `cl.Cl_Contacto_1` |
| cliente_rfc | nvarchar(50) | `cl.rfc` | `cl.Cl_R_F_C` |
| cliente_direccion_1 | nvarchar(max) | `cl.direccion` | `cl.Cl_Direccion_1` |
| cliente_direccion_2 | nvarchar(max) | `NULL` | `cl.Cl_Direccion_2` |
| cliente_direccion_3 | nvarchar(max) | `NULL` | `cl.Cl_Direccion_3` |
| cliente_calle | nvarchar(max) | `NULL` | `cl.Cl_Calle` |
| cliente_numero_exterior | nvarchar(max) | `NULL` | `cl.Cl_Numero_Exterior` |
| cliente_numero_interior | nvarchar(max) | `NULL` | `cl.Cl_Numero_Interior` |
| cliente_colonia | nvarchar(max) | `NULL` | `cl.Cl_Colonia` |
| cliente_ciudad | nvarchar(max) | `cl.poblacion` | `cl.Cl_Ciudad` |
| cliente_municipio | nvarchar(max) | `NULL` | `cl.Cl_Municipio` |
| cliente_estado | nvarchar(max) | `cl.estado` | `cl.Cl_Estado` |
| cliente_pais | nvarchar(max) | `cl.pais` | `cl.Cl_Pais` |
| cliente_codigo_postal | nvarchar(max) | `cl.codigopostal` | `cl.Cl_Codigo_Postal` |
| ticket_fecha | datetime2 | `h.fecha` | `h.Co_Fecha` |
| ticket_fecha_cierre | datetime2 | `h.cierre` | `NULL` |
| ticket_pagado | bit | `h.pagado` | `NULL` |
| ticket_impreso | bit | `h.impreso` | `NULL` |
| ticket_impresiones | int | `h.impresiones` | `NULL` |
| ticket_comentario | nvarchar(max) | `NULL` | `h.Co_Comentario` |
| ticket_comentario_descuento | nvarchar(max) | `h.comentariodescuento` | `NULL` |
| ticket_fecha_alta | datetime2 | `NULL` | `h.Fecha_Alta` |
| ticket_oper_ult_modif | nvarchar(100) | `NULL` | `h.Oper_Ult_Modif` |
| ticket_oper_baja | nvarchar(100) | `NULL` | `h.Oper_Baja` |
| ticket_fecha_baja | datetime2 | `h.fechacancelado` | `h.Fecha_Baja` |
| partida_comentario | nvarchar(max) | `d.comentario` | `d.Cd_Comentario` |
| partida_comentario_descuento | nvarchar(max) | `d.comentariodescuento` | `NULL` |
| partida_comentario_cancelacion | nvarchar(max) | `NULL` | `d.Cd_Comentario_Cancelacion` |
| partida_oper_baja | nvarchar(100) | `NULL` | `d.Oper_Baja` |
| partida_fecha_baja | datetime2 | `NULL` | `d.Fecha_Baja` |
| tipo_descuento_id | nvarchar(100) | `d.idtipodescuento` | `d.Cd_Tipo_Descuento` |
| tipo_descuento_descripcion | nvarchar(max) | `td.desc_tipodescuento` | `td.Td_Descripcion` |
| tipo_descuento_valor | decimal(18,6) | `td.descuento` | `td.Td_Porcentaje` |
| cliente_cruzamiento_1 | nvarchar(max) | `NULL` | `cl.Cl_Cruzamiento_1` |
| cliente_cruzamiento_2 | nvarchar(max) | `NULL` | `cl.Cl_Cruzamiento_2` |
| cliente_entrega_direccion_1 | nvarchar(max) | `NULL` | `cl.Cl_Direccion_Entrega_1` |
| cliente_entrega_direccion_2 | nvarchar(max) | `NULL` | `cl.Cl_Direccion_Entrega_2` |
| cliente_entrega_direccion_3 | nvarchar(max) | `NULL` | `cl.Cl_Direccion_Entrega_3` |
| cliente_entrega_ciudad | nvarchar(max) | `NULL` | `cl.Cl_Ciudad_Entrega` |
| cliente_entrega_estado | nvarchar(max) | `NULL` | `cl.Cl_Estado_Entrega` |
| cliente_entrega_pais | nvarchar(max) | `NULL` | `cl.Cl_Pais_Entrega` |
| cliente_entrega_codigo_postal | nvarchar(max) | `NULL` | `cl.Cl_Codigo_Postal_Entrega` |
| cliente_colonia_origen_id | nvarchar(max) | `NULL` | `cl.Cl_Cve_Colonia` |
| cliente_ciudad_origen_id | nvarchar(max) | `NULL` | `cl.Cl_Cve_Ciudad` |
| cliente_municipio_origen_id | nvarchar(max) | `NULL` | `cl.Cl_Cve_Municipio` |
| cliente_estado_origen_id | nvarchar(max) | `NULL` | `cl.Cl_Cve_Estado` |
| cliente_pais_origen_id | nvarchar(max) | `NULL` | `cl.Cl_Cve_Pais` |
| cliente_codigo_postal_origen_id | nvarchar(max) | `NULL` | `cl.Cl_Cve_Codigo_Postal` |
| cliente_latitud | nvarchar(max) | `NULL` | `cl.Cl_Latitud` |
| cliente_longitud | nvarchar(max) | `NULL` | `cl.Cl_Longitud` |

Los campos ya existentes preservan folio visible, folio original, sucursal, vendedor, mesa/referencia, PAX/personas, cancelación y estado. El nombre solicitado `impreciones` corresponde al campo real `impresiones`. La tabla de clientes MPRO se llama `Cliente`, en singular.

## Verificación y orden de activación

1. Worker R1–R3 y R5: auditorías de esquemas y claves, certificadas read-only.
2. Worker `EDARSAHUB-TICKETS-VENTA-SOURCE-SQL-COMPILE-R8-CARLOS-20261007`: PASS de proyecciones completas mediante SELECT TOP(0), SR CIENFUEGOS/130MID/ESTELAR y MPRO CENTRAL2020. Esto valida estructura y SQL; no prueba APIs MPRO LOCAL ni contenido histórico.
3. Pruebas locales: 65 PASS de identidad, descuentos, snapshots, insert/rollback, paridad y Asistente IA. Compilación Python y sintaxis JSX PASS.
4. Integrar primero la migración `20261007_003_ticket_cliente_comentarios_atomicos.sql` mediante Worker; ejecutarla con SQL_MIGRATION_DEVELOPMENT y SHA-256 exacto; auditar todas las columnas y el índice después.
5. Integrar ETL, servicios y frontend mediante Worker, ejecutar build y el canario opt-in `backend/tests/live_canary_requests/ticket_sources_readonly_r9.py` contra ORIGEN LOCAL y 130° QRO LOCAL.
6. Ejecutar sincronizaciones oficiales abiertas y por rango; comprobar persistencia, totales y tickets de ambos tableros. Las filas anteriores a la migración necesitan resincronización para obtener metadata: no se inventan nombres, RFC o comentarios ausentes.

## Estado pendiente verificable

La integración R6 fue detenida por `GIT_WORKTREE_NOT_CLEAN` en el runtime del Worker. No se eliminaron ni sobrescribieron cambios locales ajenos. La ruta de recuperación respondió HTTP 503 (`worker runtime git executable unavailable`). La migración no se ejecutó y el código no se activó en Desarrollo ni Producción. Las validaciones locales y SQL read-only no equivalen a certificación operativa. El siguiente paso es recuperar un runtime limpio, integrar la migración y continuar la secuencia de activación sin pedir otra autorización.
