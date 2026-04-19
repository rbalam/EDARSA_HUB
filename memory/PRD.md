# EDARSA HUB - Product Requirements Document

## Visión General
Sistema ERP operativo centralizado para EDARSA, actuando como "el cerebro" de operaciones de compras, inventarios, auditorías y flujos de aprobación.

## Estado Actual: FASE 3.1 - Migración RBAC por Módulo (EN PROGRESO)

### COMPLETADO - Fase 3.1: Módulo Operaciones Migrado a RBAC
**Fecha**: 2026-04-19

#### Archivos Modificados:
- `/app/backend/modules/fase2_operativo/routes/dashboard_routes.py` - Todos los endpoints protegidos con `Depends(get_current_user)` y filtrado por `server_ids`
- `/app/backend/modules/fase2_operativo/routes/workflow_routes.py` - RBAC inyectado
- `/app/backend/modules/fase2_operativo/routes/tarea_routes.py` - RBAC inyectado
- `/app/backend/modules/fase2_operativo/routes/justificacion_routes.py` - RBAC inyectado
- `/app/backend/modules/fase2_operativo/routes/auditoria_routes.py` - RBAC inyectado
- `/app/backend/modules/fase2_operativo/routes/configuracion_routes.py` - RBAC inyectado
- `/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py` - RBAC inyectado
- `/app/backend/modules/fase2_operativo/routes/documentos_routes.py` - RBAC inyectado
- `/app/backend/modules/fase2_operativo/services/operativo_service.py` - Soporte filtrado `server_ids`
- `/app/backend/modules/fase2_operativo/services/workflow_service.py` - Soporte filtrado `server_ids`
- `/app/backend/modules/fase2_operativo/services/tarea_service.py` - Soporte filtrado `server_ids`
- `/app/backend/modules/fase2_operativo/repositories/workflow_repository.py` - Filtrado MongoDB por `server_id`
- `/app/backend/modules/fase2_operativo/repositories/tarea_repository.py` - Filtrado MongoDB por `server_id`

#### Validaciones Realizadas:
- ✅ Endpoints sin token devuelven 403 "Not authenticated"
- ✅ Admin (`admin@edarsa.com`) accede a todas las empresas (5)
- ✅ Usuario restringido (`almacen@cienfuegos.mx`) solo ve CIENFUEGOS
- ✅ Frontend carga correctamente para ambos usuarios
- ✅ Menú del usuario restringido está filtrado (menos opciones)

### Módulos YA Migrados a RBAC (Fase 3/3.1):
- [x] Tablero Ejecutivo
- [x] Compras
- [x] Comercial
- [x] **Operaciones** (NUEVO - 2026-04-19)

### Módulos Pendientes de Migrar (P1):
- [ ] Finanzas
- [ ] Recursos Humanos

### Backlog P2:
- Deprecación de campos legacy (`role`, `allowed_servers`, `allowed_sucursales`)
- Migración completa del Frontend al selector de contextos RBAC
    └── components/
        └── TabOperativasCompras.jsx     # UI Operativas
```

## Colecciones MongoDB
- `automatizaciones_operativas_compras`: Registro principal de automatizaciones
- `automatizaciones_bitacora`: Log de eventos y cambios
- `pedidos_procesados_automatizacion`: Control de pedidos ya procesados (índice único)
- `inventarios_fisicos_procesados`: Cache de inventarios físicos
- `scheduler_job_log`: Logs de ejecución de jobs

---
*Última actualización: 19/04/2026 - Trigger automático implementado*
