# EDARSA HUB - Product Requirements Document

## Visión General
Sistema ERP operativo centralizado para EDARSA, actuando como "el cerebro" de operaciones de compras, inventarios, auditorías y flujos de aprobación.

## Estado Actual: FASE 3.2 - Migración "Unidad de Negocio" (EN PROGRESO)

---

## FASE 3.2: Migración "Servidor" → "Unidad de Negocio" - COMERCIAL
**Fecha**: 2026-04-19

### Trabajo Completado
- [x] **Módulo Compras**: Completado anteriormente
- [x] **Módulo Comercial**: Completado hoy (2026-04-19)
  - Todos los tabs migrados: Dashboard, Precios Const., Reporte PAX, Ticket Perfecto, Metas, Por Hora/Día, Mesas
  - Labels cambiados de "Servidor" a "Unidad de Negocio"
  - Selectores actualizados a `unidadesNegocio.map()` con auto-selección
  - Placeholders/mensajes de error actualizados
  - Props correctamente propagadas a subcomponentes

### Evidencia Visual Verificada
1. Usuario admin ve dropdown "Seleccionar unidad" con todas las unidades RBAC
2. Usuario restringido (CIENFUEGOS) ve campo fijo con su única unidad pre-seleccionada
3. Sucursal se auto-selecciona correctamente basada en `sucursal_origen_id`
4. Todos los tabs funcionan correctamente con el nuevo modelo

### Próximos Módulos (P1)
- [ ] Operaciones
- [ ] Finanzas
- [ ] Reportes/ExploradorBD

---

## FIX ESTRUCTURAL: MPRO SQL Nube y Política de Fechas
**Fecha**: 2026-04-19

### Problema Original
El tablero ejecutivo devolvía **$0.00** para unidades MPRO aunque existían datos reales en SQL Server CENTRAL2020.

### Causas Raíz Identificadas
1. **Import local conflictivo** - Variable no accesible fuera del bloque `if`
2. **Rango de fechas inválido** - Mes futuro generaba `fecha_ini > fecha_fin`
3. **Fallback incorrecto** - No deshabilitaba modo ventas del día

### Solución Implementada
1. **Helper centralizado de fechas**: `/app/backend/core/utils/date_filters.py`
   - `DateFilterPolicy.to_yyyymmdd_range()` - Conversión segura
   - `DateFilterPolicy.is_valid_range()` - Validación de rangos
   - `DateFilterPolicy.adjust_future_month()` - Ajuste de meses futuros

2. **Gestor de conexiones**: `/app/backend/core/server_connection_manager.py`
   - Fuente única de credenciales desde MongoDB
   - `get_server_config()` - Config completa (backend)
   - `get_safe_server_info()` - Info sin password (frontend/logs)

3. **Fix en service.py**
   - Validación de rango antes de ejecutar queries
   - Fallback correcto deshabilitando `solo_ventas_dia`

### Resultado Verificado
| Unidad | Antes | Después |
|--------|-------|---------|
| 130° QUERETARO | $0.00 | $1,602,503.00 |
| ORIGEN | $0.00 | $913,840.71 |

---

## Arquitectura de Fechas y Conexiones

### Política de Fechas
- **PROHIBIDO**: Construir filtros de fecha manualmente
- **OBLIGATORIO**: Usar `DateFilterPolicy` de `core/utils/date_filters`
- **Validación**: Siempre verificar `is_valid_range()` antes de queries

### Política de Credenciales
- **Fuente única**: MongoDB (colección `servers`)
- **PROHIBIDO**: Hardcodear credenciales en código
- **PROHIBIDO**: Exponer passwords al frontend
- Ver `/app/docs/POLITICA_TRANSVERSAL_FECHAS_Y_CONEXIONES.md`

---

## Módulos Migrados a RBAC (Fase 3/3.1)
- [x] Tablero Ejecutivo
- [x] Compras
- [x] Comercial
- [x] Operaciones
- [x] Finanzas
- [x] Recursos Humanos

---

## Backlog

### P0 - COMPLETADO
- [x] Fix MPRO fallback $0.00
- [x] Helper centralizado de fechas
- [x] Documentación de políticas
- [x] **Corrección servidores duplicados en MongoDB** (2026-04-19)
  - Servidores huérfanos marcados como `deprecated: true`
  - Canónicos: `a5ff...` (LA ESTELAR), `a5547...` (130° MERIDA)
  - Query SQL corregida en `/api/compras/pedidos-vigentes` (MPRO)
  - Documentado en `/app/docs/FIX_SERVIDORES_DUPLICADOS_20260419.md`
- [x] **FASE 3.2: Migración "Servidor" → "Unidad de Negocio" en Compras** (2026-04-19)
  - Nuevo endpoint `/api/unidades-negocio` con RBAC
  - Selector visible cambiado de "Servidor" a "Unidad de Negocio"
  - Auto-selección para usuarios con 1 unidad
  - server_id relegado a dato interno
  - Documentado en `/app/docs/MIGRACION_UNIDAD_NEGOCIO_COMPRAS.md`
- [x] **Manuales Operativos Modelo Cienfuegos** (2026-04-19)
  - Generación automática al cerrar procesos (APROBADO/RECHAZADO/COMPLETADA)
  - Formato Cienfuegos: objetivo, alcance, responsables, procedimiento, políticas, evidencias
  - Endpoints: listar, obtener, exportar texto, generar bajo demanda
  - Trigger integrado en servicio de automatización compras
  - Documentado en `/app/docs/MANUALES_OPERATIVOS_CIENFUEGOS.md`
- [x] **FASE 3.2: Migración "Servidor" → "Unidad de Negocio" en Comercial** (2026-04-19)
  - Todos los tabs migrados (Dashboard, Precios Const., PAX, Ticket Perfecto, Metas, Por Hora/Día, Mesas)
  - Labels, placeholders y mensajes de error actualizados
  - Auto-selección funcional para usuarios restringidos

### P0 - PENDIENTE
- [ ] RH mapeo empresa→sucursal_id SQL (agregar `rh_sql_sucursal_id` a `sucursales_catalogo`)

### P1 - PENDIENTE
- [ ] **Migrar módulo Operaciones a "Unidad de Negocio"**
- [ ] **Migrar módulo Finanzas a "Unidad de Negocio"**
- [ ] **Migrar módulo Reportes/ExploradorBD a "Unidad de Negocio"**
- [ ] Migrar credenciales legacy de `repository_cortes_z.py` a MongoDB
- [ ] Migrar credenciales legacy de `validacion_propinas_tpv.py` a MongoDB
- [ ] Conectar SQL Server real en Finanzas (actualmente usa fallback demo)

### P2 - FUTURO
- [ ] Cifrado de passwords en reposo (MongoDB)
- [ ] Deprecación de campos legacy (`role`, `allowed_servers`)
- [ ] Refactor global para eliminar `fetchServersOperativos` (después de migrar todos los módulos)
- [ ] Documentar inspección de servidores locales

---

## Documentación Técnica

| Documento | Ruta |
|-----------|------|
| Diagnóstico MPRO | `/app/docs/DIAGNOSTICO_MPRO_FALLBACK_FECHAS_Y_CREDENCIALES.md` |
| Política de Fechas | `/app/docs/POLITICA_TRANSVERSAL_FECHAS_Y_CONEXIONES.md` |
| Worklog del Fix | `/app/memory/WORKLOG_FIX_MPRO_CREDENCIALES_FECHAS.md` |
| Fix Servidores Duplicados | `/app/docs/FIX_SERVIDORES_DUPLICADOS_20260419.md` |
| Migración Unidad de Negocio | `/app/docs/MIGRACION_UNIDAD_NEGOCIO_COMPRAS.md` |
| Manuales Operativos Cienfuegos | `/app/docs/MANUALES_OPERATIVOS_CIENFUEGOS.md` |

---

## Issue Conocido (No Blocker)
- DuplicateKeyError en `rbac_usuarios_roles` al iniciar servidor (no afecta funcionalidad)

---

## Arquitectura de Datos

### Colecciones MongoDB
- `users`: Usuarios con `empresa_default_id`, `empresas_permitidas`
- `servers`: Servidores SQL con credenciales (FUENTE ÚNICA)
- `sucursales_catalogo`: Mapeo de sucursales por empresa

### Servidores SQL Externos
- SoftRestaurant (CIENFUEGOS, LA ESTELAR, 130° MERIDA)
- ManagmentPro/MPRO (CENTRAL2020 - ORIGEN, QUERETARO)
- HR2020 (Recursos Humanos)
