# PENDIENTE: Dry-run Sync Compras

## Estado

El dry-run real de:

```http
POST /api/admin/sync/compras?dry_run=true
```

**NO se pudo ejecutar desde el ambiente preview de Emergent** debido a que el firewall de SQL Server (EDARSAHUB `4.255.36.175`) bloquea conexiones desde la IP de salida del pod (`54.39.104.176`).

---

## Acciones pendientes para el usuario

### Opción 1: Ejecutar desde ambiente de producción

```bash
# Obtener token
TOKEN=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@inventario.com","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

# Dry-run
curl -s -X POST "http://localhost:8001/api/admin/sync/compras?dry_run=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Table counts
curl -s "http://localhost:8001/api/admin/sync/compras/table-counts" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Sync logs
curl -s "http://localhost:8001/api/admin/sync/compras/logs?limit=50" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Opción 2: Agregar IP al firewall de Azure

1. Azure Portal → SQL Server → Networking → Firewall rules
2. Agregar regla:
   - Nombre: `Emergent_Preview`
   - Start IP: `54.39.104.176`
   - End IP: `54.39.104.176`
3. Guardar

---

## Endpoints disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/admin/sync/compras?dry_run=true` | POST | Dry-run (lista servidores) |
| `/api/admin/sync/compras?dry_run=false` | POST | Sync real |
| `/api/admin/sync/compras/force-unlock` | POST | Liberar locks atascados |
| `/api/admin/sync/compras/table-counts` | GET | Conteos de tablas |
| `/api/admin/sync/compras/logs` | GET | Logs y checkpoints |

---

## Fecha de creación

$(date)
