"""Commercial Analytics package.

El paquete no importa routers automáticamente. Esto permite utilizar
componentes puros, como temporal_selection, sin inicializar seguridad,
RBAC o configuración SQL.

El router se registra explícitamente desde backend/server.py.
"""
