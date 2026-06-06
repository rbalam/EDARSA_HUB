# Sync Propina TPV SoftRestaurant hasta último corte

Fecha: Thu Jun  4 18:14:40 UTC 2026


## Resultado de Intento de Sync

### Corrección aplicada
- Se agregó el parámetro `system_type_filter` a `list_operational_servers()` en `/app/backend/core/server_registry.py`

### Intento de sync CIENFUEGOS
```json
{
  "success": false,
  "errores": [{
    "servidor": "CIENFUEGOS",
    "error": "Esquema no compatible: []",
    "status": "NO_COMPATIBLE"
  }]
}
```

### Causa raíz
- **TimeoutError**: El servidor `servercienfuegos.ddns.net,6669\nationalsoft` no es accesible desde este entorno
- Los servidores SoftRestaurant están detrás de firewalls del cliente
- Esto explica por qué la sincronización se detuvo el 17 de mayo 2026

### Servidores SoftRestaurant identificados
| Servidor | Host | Estado |
|----------|------|--------|
| 130° MERIDA | 130mid.ddns.net | ⚠️ Sin acceso de red |
| CIENFUEGOS | servercienfuegos.ddns.net,6669 | ⚠️ Sin acceso de red |
| LA ESTELAR | serverestelar.ddns.net,6969 | ⚠️ Sin acceso de red |

### Acción requerida (cliente)
1. Verificar reglas de firewall en servidores SoftRestaurant
2. Permitir conexión entrante desde IP del servidor EDARSA HUB
3. Una vez habilitado el acceso de red, ejecutar:
   ```
   POST /api/finanzas/propinas/sincronizar
   {
     "fecha_inicio": "2026-05-18",
     "fecha_fin": "2026-06-04",
     "server_id": "<UUID_SERVIDOR>"
   }
   ```
