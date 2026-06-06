# PENDIENTE ESPECÍFICO: Dry-run Sync Compras

## Alcance exacto

Este pendiente aplica únicamente al proceso:

```http
POST /api/admin/sync/compras?dry_run=true
```

Y a los endpoints de monitoreo:

```http
GET /api/admin/sync/compras/table-counts
GET /api/admin/sync/compras/logs?limit=50
```

---

## ¿Por qué quedó pendiente?

El firewall de EDARSAHUB SQL Server (`4.255.36.175`) no permite conexiones desde la IP de salida del pod de Emergent (`54.39.104.176`).

---

## Acciones requeridas

El usuario debe ejecutar desde su **ambiente de producción** (donde el backend tiene acceso a SQL Server):

```bash
# 1. Obtener token
TOKEN=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@inventario.com","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

# 2. Dry-run sync compras
curl -s -X POST "http://localhost:8001/api/admin/sync/compras?dry_run=true" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool

# 3. Verificar conteos de tablas
curl -s "http://localhost:8001/api/admin/sync/compras/table-counts" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool

# 4. Ver logs de sincronización
curl -s "http://localhost:8001/api/admin/sync/compras/logs?limit=50" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

---

## Resultado esperado del dry-run

```json
{
  "status": "SUCCESS",
  "servers_processed": 9,
  "results": {
    "inventarios": [...],
    "requisiciones": [...]
  },
  "errors": []
}
```

---

## Siguiente paso después del dry-run

Si el dry-run es exitoso, ejecutar el sync real:

```bash
curl -s -X POST "http://localhost:8001/api/admin/sync/compras?dry_run=false" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

---

## Fecha de creación

2026-06-04
