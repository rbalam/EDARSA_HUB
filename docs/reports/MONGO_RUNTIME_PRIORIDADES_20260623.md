# Prioridades runtime Mongo backend

## P0 - Runtime directo en server.py
- server_status
- inventario_diferencias_detalle
- alerts
- users / alerts counts
- script_logs
- solicitudes_catalogos
- portal_proveedores
- tareas_sistema
- nomina_ciclos
- nomina_movimientos
- nomina_configuracion
- nomina_kpis_puestos
- sec_roles

## P0 - API productiva
- backend/api/sync_receiver.py:
  - sql_servers
  - sync_agent_registry

## P1 - Comunicaciones / notificaciones
- notification_queue
- notification_provider_config
- notification_config
- notification_templates
- notification_log

## P1 - Módulos con db legacy
- comercial_cache
- estructura_service sec_*
- rh/routes.py empresas
- finanzas empresas
- manuales_operativos
- fase2_operativo users/notificaciones

## Regla de ejecución
Migrar por bloques pequeños, un commit por bloque, con:
1. backup previo si se edita archivo grande
2. grep antes/después
3. py_compile
4. actualizar reporte Graphify/auditoría después del cambio
