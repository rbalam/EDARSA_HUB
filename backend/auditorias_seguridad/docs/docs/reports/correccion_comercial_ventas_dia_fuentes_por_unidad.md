# Corrección Comercial - Ventas del Día por Unidad

## Fecha: 2026-04-29

## Resumen del Problema

El tablero Comercial / Ventas Consolidadas mostraba:
- 130° MERIDA: "Offline" (usando FALLBACK)
- CIENFUEGOS: "Offline" (usando FALLBACK)
- LA ESTELAR: "Offline" (usando FALLBACK)
- ORIGEN: "Offline" y $0
- 130° QUERETARO: "Offline" y $0

## Causa Raíz

El pool de conexiones SQL usaba **pytds** como driver primario, pero pytds tiene:
1. Bug que devuelve datos incorrectos en ciertas configuraciones
2. Incapacidad de conectar a servidores DDNS externos

## Corrección Aplicada

**Archivo:** `/app/backend/core/pool.py`

Cambio de prioridad de drivers:
- **ANTES**: pytds primero → pymssql fallback
- **DESPUÉS**: pymssql primero → pytds fallback

## Fuente por Unidad

| Unidad | system_type | Fuente configurada | Host | Status |
|--------|-------------|-------------------|------|--------|
| 130° MERIDA | SoftRestaurant | softrestaurant10 | 130mid.ddns.net:1433 | ✅ CONNECTED |
| CIENFUEGOS | SoftRestaurant | softrestaurant95pro | servercienfuegos.ddns.net,6669\nationalsoft | ✅ CONNECTED |
| LA ESTELAR | SoftRestaurant | softrestaurant12 | serverestelar.ddns.net,6969 | ✅ CONNECTED |
| 130° QUERETARO | MPRO | CENTRAL2020 (API Local) | <REDACTED_EDARSAHUB_SQL_HOST>:8001 | ✅ CONNECTED |
| ORIGEN | MPRO | CENTRAL2020 (API Local) | <REDACTED_EDARSAHUB_SQL_HOST>:8000 | ✅ CONNECTED |

## Validación EDARSAHUB SQL como Fuente Maestra

Todas las unidades se resuelven desde:
- **Tabla**: `EDARSAHUB.dbo.Unidades_Negocio`
- **Servidores**: `EDARSAHUB.dbo.Servidores_Conexiones`

MongoDB **NO** se usa para resolver:
- ❌ Unidades de negocio
- ❌ Servidores
- ❌ Sucursales
- ❌ Conexiones SQL

## Matriz de Pruebas por Unidad

| Unidad | system_type | connection_type | Fuente esperada | Fuente usada | Estado | Ventas | Error | Resultado |
|--------|-------------|-----------------|-----------------|--------------|--------|--------|-------|-----------|
| 130° MERIDA | SoftRestaurant | SQL_SERVER | tempcheques | tempcheques | online | $4.01M | - | ✅ PASS CON DATOS |
| CIENFUEGOS | SoftRestaurant | SQL_SERVER | tempcheques | tempcheques | online | $3.66M | - | ✅ PASS CON DATOS |
| LA ESTELAR | SoftRestaurant | SQL_SERVER | tempcheques | tempcheques | online | $2.38M | - | ✅ PASS CON DATOS |
| 130° QUERETARO | MPRO | API_LOCAL | API local | API local | online | $3.19M | - | ✅ PASS CON DATOS |
| ORIGEN | MPRO | API_LOCAL | API local | API local | online | $1.74M | - | ✅ PASS CON DATOS |

## Endpoints Modificados

1. `/api/comercial/tablero-ejecutivo` - Manejo de errores mejorado
2. `/api/compras/dashboard/{server_id}` - Query MPRO corregida
3. `/api/unidades-negocio` - Migrado a EDARSAHUB SQL

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/core/pool.py` | pymssql como driver primario |
| `/app/backend/server.py` | Query Compra_Encabezado + endpoint unidades |
| `/app/backend/modules/comercial/service.py` | Manejo de errores específicos |
| `/app/backend/modules/comercial/routes.py` | Procesamiento de errores en tablero |
| `/app/frontend/src/pages/Compras.js` | Usar id para sucursal MPRO |

## Estados de Error Implementados

| Estado | Descripción |
|--------|-------------|
| CONNECTED | Conexión exitosa |
| SERVER_UNREACHABLE | No fue posible conectar con el servidor SQL |
| SERVER_TIMEOUT | Timeout de conexión |
| AUTH_ERROR | Error de autenticación |
| DATABASE_NOT_FOUND | Base de datos no encontrada |
| CONFIG_QUERY_ERROR | Configuración incorrecta |

## No Regresión

Validado que los siguientes módulos siguen funcionando:
- ✅ Compras
- ✅ Comercial / Tablero Ejecutivo
- ✅ Servidores
- ✅ Login

## Conclusión

El problema principal era el driver **pytds** del pool de conexiones que:
1. No podía conectar a servidores DDNS externos
2. Devolvía datos incorrectos para ciertas consultas

Al cambiar a **pymssql** como driver primario, todas las 5 unidades conectan correctamente y muestran ventas en vivo.
