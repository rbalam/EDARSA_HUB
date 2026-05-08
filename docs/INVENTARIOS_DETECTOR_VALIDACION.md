# CHECKLIST DE VALIDACIÓN - Job `inventarios_detector`

## Fecha de Implementación: Abril 2026
## Estado: PENDIENTE VALIDACIÓN EN PRODUCCIÓN

---

## PRE-REQUISITOS

- [ ] Deploy a producción completado
- [ ] Conectividad SQL a servidores externos confirmada:
  - [ ] CIENFUEGOS (servercienfuegos.ddns.net)
  - [ ] LA ESTELAR (serverestelar.ddns.net)
  - [ ] 130° MERIDA

---

## 1. SCHEDULER ACTIVO

**Verificar:**
```bash
# Login como SuperAdministrador
curl -X POST "$URL/api/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"ricardo@edarsa.com.mx","password":"[PASSWORD]"}'

# Ver estado del scheduler
curl -X GET "$URL/api/v2/scheduler/status" -H "Authorization: Bearer $TOKEN"
```

**Evidencia esperada:**
- [ ] `running: true`
- [ ] Job `inventarios_detector` en lista de jobs
- [ ] `next_run_time` programado cada 10 minutos

---

## 2. EJECUCIÓN DEL JOB

**Verificar en logs de backend:**
```bash
grep -i "INVENTARIOS_DETECTOR" /var/log/supervisor/backend.err.log | tail -50
```

**Evidencia esperada:**
- [ ] `[INVENTARIOS_DETECTOR] Iniciando ejecución`
- [ ] `[INVENTARIOS_DETECTOR] Escaneando [SERVIDOR]`
- [ ] `[INVENTARIOS_DETECTOR] X inventarios detectados, Y nuevos`
- [ ] `[INVENTARIOS_DETECTOR] Finalizado - Detectados: X, Procesados: Y, Errores: Z`

---

## 3. INVENTARIOS DETECTADOS

**Verificar en MongoDB:**
```javascript
// Total registros
db.inventarios_procesados_auto.countDocuments({})

// Distribución por estado
db.inventarios_procesados_auto.aggregate([
  { $group: { _id: "$estado", count: { $sum: 1 } } }
])

// Últimos detectados
db.inventarios_procesados_auto.find().sort({fecha_deteccion: -1}).limit(5)
```

**Evidencia esperada:**
- [ ] Registros con `estado: "COMPLETADO"`
- [ ] Clave de idempotencia completa (sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
- [ ] `analisis_resultado` con datos

---

## 4. WORKFLOWS NUEVOS CON DATOS COMPLETOS

**Verificar en MongoDB:**
```javascript
// Workflows recientes
db.workflow_inventarios.find().sort({fecha_creacion: -1}).limit(5).pretty()

// Verificar campos críticos
db.workflow_inventarios.find({
  $or: [
    { folio_inventario: null },
    { servidor_id: null },
    { server_id: null }
  ]
}).count()
```

**Evidencia esperada:**
- [ ] `folio_inventario` NO es null
- [ ] `servidor_id` NO es null
- [ ] `server_id` NO es null
- [ ] `server_name` correcto
- [ ] `almacen_nombre` correcto

---

## 5. DETALLE_DIFERENCIAS SIN NULLS

**Verificar en MongoDB:**
```javascript
// Últimos detalles
db.detalle_diferencias.find().sort({fecha_creacion: -1}).limit(10).pretty()

// Verificar campos críticos
db.detalle_diferencias.find({
  $or: [
    { producto_nombre: null },
    { diferencia: null },
    { producto_id: null }
  ],
  fecha_creacion: { $gte: new Date(Date.now() - 24*60*60*1000) } // Últimas 24h
}).count()
```

**Evidencia esperada:**
- [ ] `producto_nombre` NO es null
- [ ] `diferencia` NO es null
- [ ] `producto_id` presente
- [ ] `costo_unitario` presente (si aplica)

---

## 6. ANTI-DUPLICADOS

**Verificar:**
```javascript
// Ejecutar job manualmente dos veces seguidas
// POST /api/v2/scheduler/jobs/inventarios_detector/run

// Luego verificar que no haya duplicados
db.inventarios_procesados_auto.aggregate([
  { $group: {
      _id: {
        sistema: "$clave.sistema_origen",
        server: "$clave.server_id",
        sucursal: "$clave.sucursal_id",
        almacen: "$clave.almacen_id",
        folio: "$clave.folio_inventario"
      },
      count: { $sum: 1 }
  }},
  { $match: { count: { $gt: 1 } } }
])
```

**Evidencia esperada:**
- [ ] Cero duplicados
- [ ] Log muestra "Duplicado: folio=X" para intentos repetidos

---

## 7. SCHEDULER_JOB_LOGS

**Verificar en MongoDB:**
```javascript
db.scheduler_job_logs.find({job_name: "inventarios_detector"}).sort({started_at: -1}).limit(5).pretty()
```

**Evidencia esperada:**
- [ ] Registros con `status: "success"`
- [ ] `processed_count` > 0
- [ ] `duration_ms` razonable
- [ ] `metadata.stats` con estadísticas

---

## 8. NO REGRESIÓN DEL FLUJO MANUAL

**Verificar:**
```bash
# Ejecutar análisis manual
curl -X POST "$URL/api/reports/inventory-analysis" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "[SERVER_ID]",
    "sucursal": "[SUCURSAL]",
    "almacen": "[ALMACEN]",
    "fecha_ini": "2026-04-01",
    "fecha_fin": "2026-04-22",
    "folio_inicial": "[FOLIO_INI]",
    "folio_final": "[FOLIO_FIN]"
  }'
```

**Evidencia esperada:**
- [ ] Respuesta exitosa con resultados
- [ ] Workflow creado con datos completos
- [ ] Frontend sigue funcionando

---

## RESUMEN DE VALIDACIÓN

| Punto | Estado | Notas |
|-------|--------|-------|
| 1. Scheduler activo | ⬜ | |
| 2. Job ejecuta cada 10min | ⬜ | |
| 3. Inventarios detectados | ⬜ | |
| 4. Workflows completos | ⬜ | |
| 5. Detalle sin nulls | ⬜ | |
| 6. Anti-duplicados | ⬜ | |
| 7. Scheduler logs | ⬜ | |
| 8. Flujo manual OK | ⬜ | |

---

## POST-VALIDACIÓN

Una vez confirmado todo ✅, proceder con:
1. Plan de corrección de históricos NULL
2. Limpieza de registros de prueba en Preview

---

## ROLLBACK (SI ES NECESARIO)

```bash
# Deshabilitar job
export SCHEDULER_INVENTARIOS_ENABLED=false
# Reiniciar backend

# O pausar via API
curl -X POST "$URL/api/v2/scheduler/jobs/inventarios_detector/pause" \
  -H "Authorization: Bearer $TOKEN"
```
