# EDARSA HUB - Product Requirements Document

## Visión General
Sistema ERP operativo centralizado para EDARSA, actuando como "el cerebro" de operaciones de compras, inventarios, auditorías y flujos de aprobación.

## Estado Actual: FASE 3.1 - Migración RBAC por Módulo (COMPLETADA)

### FIX CRÍTICO: MPRO SQL Nube devuelve $0.00 - RESUELTO
**Fecha**: 2026-04-19

**Problema identificado:**
1. Error `cannot access local variable 'sumar_ventas_api_local_a_sucursal'` - import local redundante causaba conflicto con import global
2. Cuando se seleccionaba un mes futuro (ej: diciembre estando en abril), el rango de fechas era inválido (2026-12-01 a 2026-04-19)
3. El fallback a SQL nube en modo "Ventas del Día" ponía los datos en $0 en lugar de mostrar acumulados

**Solución aplicada:**
- Eliminado import local redundante de `sumar_ventas_api_local_a_sucursal` (ya existe import global línea 29)
- Añadida validación para meses futuros: Si el mes solicitado > mes actual, se ajusta automáticamente al mes actual
- En el fallback SQL nube, se deshabilita `solo_ventas_dia` para permitir mostrar datos acumulados

**Archivos modificados:**
- `/app/backend/modules/comercial/routes.py` (validación de meses futuros)
- `/app/backend/modules/comercial/service.py` (fix import y fallback)

**Resultado:**
- MPRO 130° QUERETARO: $1,602,503.00 ✅
- MPRO ORIGEN: $913,840.71 ✅
- Total tablero: $9,133,083.71 ✅

---

### CAMBIO QUIRÚRGICO: Ventas Históricas vs Ventas del Día
**Fecha**: 2026-04-19

**Comportamiento actual:**
| Tipo de Consulta | Fuente de Datos | Estado |
|------------------|-----------------|--------|
| Ventas históricas / acumulados / KPIs | SQL nube (menú Servidores) | ✅ Funcionando |
| Ventas del día MPRO | API local. Si falla → fallback SQL nube | ✅ Funcionando |
| Ventas del día SoftRestaurant | SQL Server remoto | ✅ Funcionando |

---

### Módulos YA Migrados a RBAC (Fase 3/3.1):
- [x] Tablero Ejecutivo
- [x] Compras
- [x] Comercial
- [x] Operaciones
- [x] Finanzas
- [x] Recursos Humanos

### Backlog P0 - PENDIENTES ESTRUCTURALES:
1. **RH mapeo empresa→sucursal_id SQL**: Agregar campo `rh_sql_sucursal_id` a `sucursales_catalogo` para filtrado granular en HR2020

### Backlog P1:
- Documentar: Inspección local en servidores para revisar por qué no levanta SQL local / API local
- Conectar SQL Server real en Finanzas (actualmente usa fallback demo)

### Backlog P2:
- Deprecación de campos legacy (`role`, `allowed_servers`, `allowed_sucursales`)
- Migración completa del Frontend al selector de contextos RBAC

### Issue Conocido (No Blocker):
- DuplicateKeyError en `rbac_usuarios_roles` al iniciar servidor (no afecta funcionalidad, solo genera logs de warning)

---

## Arquitectura de Datos

### Colecciones MongoDB:
- `users`: Usuarios con `empresa_default_id`, `empresas_permitidas`
- `servers`: Servidores SQL con credenciales
- `sucursales_catalogo`: Mapeo de sucursales por empresa

### Servidores SQL Externos:
- SoftRestaurant (CIENFUEGOS, LA ESTELAR, 130° MERIDA)
- ManagmentPro/MPRO (CENTRAL2020 - ORIGEN, QUERETARO)
- HR2020 (Recursos Humanos)
