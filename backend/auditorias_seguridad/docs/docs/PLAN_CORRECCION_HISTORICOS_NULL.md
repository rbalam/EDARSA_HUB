# PLAN DE CORRECCIÓN DE HISTÓRICOS NULL

## Fecha: Abril 2026
## Estado: PENDIENTE APROBACIÓN

---

## RESUMEN EJECUTIVO

| Categoría | Total | A Reparar | Método |
|-----------|-------|-----------|--------|
| Workflows con NULL | 6 | 6 | REPARABLE DIRECTO |
| detalle_diferencias con NULL | 0 | 0 | N/A |
| scheduler_job_logs | 0 | - | MEJORA DE CÓDIGO |

---

## 1. WORKFLOWS HISTÓRICOS INCOMPLETOS

### 1.1 Inventario de Casos

| # | Workflow ID | Server | Almacén | folio_inventario | servidor_id | Reparable |
|---|-------------|--------|---------|------------------|-------------|-----------|
| 1 | 940ff676-... | LA ESTELAR | 001 BODEGA | ❌ NULL | ❌ NULL | ✅ DIRECTO |
| 2 | 3eb51330-... | CIENFUEGOS | 004 BODEGA | ❌ NULL | ❌ NULL | ✅ DIRECTO |
| 3 | 3471ab20-... | LA ESTELAR | 001 BODEGA | ❌ NULL | ❌ NULL | ✅ DIRECTO |
| 4 | 20c03a2c-... | CIENFUEGOS | 004 BODEGA | ❌ NULL | ❌ NULL | ✅ DIRECTO |
| 5 | 869ed63b-... | ManagmentPro | BODEGA | ❌ NULL | ❌ NULL | ✅ DIRECTO |
| 6 | 1f23be91-... | ManagmentPro | (vacío) | ❌ NULL | ❌ NULL | ✅ DIRECTO |

### 1.2 Datos Disponibles para Reconstrucción

**Todos los 6 workflows tienen:**
- ✅ `folios_finales[]` - Array con folio(s)
- ✅ `folio_final_key` - Folio principal
- ✅ `server_id` - UUID del servidor (correcto)
- ✅ `server_name` - Nombre del servidor

**Lógica de reconstrucción:**
```python
folio_inventario = folios_finales[0] if folios_finales else folio_final_key
servidor_id = server_id  # Ya existe, solo copiar
```

### 1.3 Clasificación

| Clasificación | Cantidad | IDs |
|---------------|----------|-----|
| **REPARABLE DIRECTO** | 6 | Todos |
| REPARABLE CON REANÁLISIS | 0 | - |
| NO REPARABLE | 0 | - |

---

## 2. DETALLE_DIFERENCIAS HISTÓRICOS

### 2.1 Estado Actual

| Campo | Registros con NULL | Registros vacíos | Total OK |
|-------|-------------------|------------------|----------|
| codigo_producto | 0 | 0 | 1397 ✅ |
| nombre_producto | 0 | 0 | 1397 ✅ |
| diferencia_cantidad | 0 | - | 1397 ✅ |
| costo_unitario | 0 | - | 1397 ✅ |
| workflow_id | 0 | - | 1397 ✅ |

### 2.2 Integridad Referencial

- Workflow IDs en detalles: 12
- Workflow IDs existentes: 12
- **Detalles huérfanos: 0** ✅

### 2.3 Clasificación

| Clasificación | Cantidad |
|---------------|----------|
| **NO REQUIERE REPARACIÓN** | 1397 |

**Conclusión:** Los `detalle_diferencias` están **COMPLETOS**. No requieren corrección.

---

## 3. CRITERIO DE REPARACIÓN

### 3.1 REPARABLE DIRECTO (6 workflows)

**Condición:** El workflow tiene `folios_finales[]` y `server_id` disponibles.

**Acción:**
```javascript
db.workflow_inventarios.updateOne(
  { id: "<workflow_id>" },
  { 
    $set: { 
      folio_inventario: <folios_finales[0]>,
      servidor_id: <server_id>  // Copiar de server_id existente
    }
  }
)
```

**Confianza:** 100% - Los datos fuente son exactos.

### 3.2 REPARABLE CON REANÁLISIS

**No aplica** - No hay casos que requieran reanálisis.

### 3.3 NO REPARABLE

**No aplica** - Todos los casos son reparables.

---

## 4. ESTRATEGIA DE EJECUCIÓN

### 4.1 Método: Script Único

Se ejecutará un único script Python que:
1. Lee los 6 workflows con `folio_inventario = NULL`
2. Para cada uno, extrae `folios_finales[0]` y `server_id`
3. Actualiza `folio_inventario` y `servidor_id`
4. Registra cada actualización en log
5. Genera reporte final

### 4.2 Orden de Ejecución

```
1. BACKUP (export de colección workflow_inventarios)
2. VALIDACIÓN PRE (contar registros con NULL)
3. EJECUCIÓN (actualizar 6 registros)
4. VALIDACIÓN POST (confirmar 0 NULLs)
5. REPORTE (generar evidencia)
```

### 4.3 Script de Corrección

```python
# /app/backend/scripts/corregir_workflows_null.py

import os
from pymongo import MongoClient
from datetime import datetime, timezone

def corregir_workflows_null():
    mongo_url = os.environ.get('MONGO_URL')
    client = MongoClient(mongo_url)
    db = client['edarsa_hub']
    
    # 1. Backup previo
    backup_collection = f"workflow_inventarios_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    workflows_all = list(db.workflow_inventarios.find())
    db[backup_collection].insert_many(workflows_all)
    print(f"Backup creado: {backup_collection}")
    
    # 2. Obtener workflows con NULL
    workflows_null = list(db.workflow_inventarios.find({
        '$or': [
            {'folio_inventario': None},
            {'servidor_id': None}
        ]
    }))
    
    print(f"Workflows a corregir: {len(workflows_null)}")
    
    # 3. Corregir cada uno
    resultados = []
    for w in workflows_null:
        wid = w['id']
        
        # Extraer datos de reconstrucción
        folios_finales = w.get('folios_finales', [])
        folio_final_key = w.get('folio_final_key')
        server_id = w.get('server_id')
        
        # Calcular valores
        nuevo_folio = folios_finales[0] if folios_finales else folio_final_key
        nuevo_servidor_id = server_id
        
        # Actualizar
        result = db.workflow_inventarios.update_one(
            {'id': wid},
            {'$set': {
                'folio_inventario': nuevo_folio,
                'servidor_id': nuevo_servidor_id,
                'fecha_correccion_historicos': datetime.now(timezone.utc).isoformat()
            }}
        )
        
        resultados.append({
            'workflow_id': wid,
            'folio_inventario': nuevo_folio,
            'servidor_id': nuevo_servidor_id,
            'modified': result.modified_count
        })
        
        print(f"  Corregido: {wid[:8]}... -> folio={nuevo_folio}, servidor={nuevo_servidor_id}")
    
    # 4. Validación post
    restantes = db.workflow_inventarios.count_documents({
        '$or': [
            {'folio_inventario': None},
            {'servidor_id': None}
        ]
    })
    
    print(f"\nResultado: {len(resultados)} corregidos, {restantes} restantes con NULL")
    
    return {
        'backup_collection': backup_collection,
        'corregidos': len(resultados),
        'restantes_null': restantes,
        'detalle': resultados
    }

if __name__ == '__main__':
    corregir_workflows_null()
```

---

## 5. VALIDACIONES

### 5.1 Validación Pre-Ejecución

```python
# Contar NULLs antes
null_folio_pre = db.workflow_inventarios.count_documents({'folio_inventario': None})
null_servidor_pre = db.workflow_inventarios.count_documents({'servidor_id': None})

assert null_folio_pre == 6, f"Esperados 6, encontrados {null_folio_pre}"
assert null_servidor_pre == 6, f"Esperados 6, encontrados {null_servidor_pre}"
```

### 5.2 Validación Post-Ejecución

```python
# Contar NULLs después
null_folio_post = db.workflow_inventarios.count_documents({'folio_inventario': None})
null_servidor_post = db.workflow_inventarios.count_documents({'servidor_id': None})

assert null_folio_post == 0, f"Esperados 0, encontrados {null_folio_post}"
assert null_servidor_post == 0, f"Esperados 0, encontrados {null_servidor_post}"

# Verificar cada workflow corregido
for wid in workflows_corregidos:
    w = db.workflow_inventarios.find_one({'id': wid})
    assert w['folio_inventario'] is not None
    assert w['servidor_id'] is not None
    assert w['servidor_id'] == w['server_id']  # Consistencia
```

### 5.3 Checklist de Campos Críticos

| Campo | Validación | Criterio |
|-------|------------|----------|
| folio_inventario | NOT NULL | Debe existir |
| servidor_id | NOT NULL | Debe existir |
| servidor_id == server_id | Igualdad | Deben coincidir |
| folios_finales[0] | Origen | Debe ser fuente del folio |

---

## 6. RIESGOS

### 6.1 Riesgo: Sobreescribir Datos Correctos

| Probabilidad | Impacto | Mitigación |
|--------------|---------|------------|
| BAJA | MEDIO | Solo se actualizan workflows con folio_inventario=NULL |

**Control:** El query filtra explícitamente por `folio_inventario: None`.

### 6.2 Riesgo: Reconstruir Mal un Folio

| Probabilidad | Impacto | Mitigación |
|--------------|---------|------------|
| MUY BAJA | ALTO | Se usa `folios_finales[0]` que es dato original |

**Control:** Los datos fuente (`folios_finales`, `server_id`) son los originales, no se inventan.

### 6.3 Riesgo: Duplicar Información

| Probabilidad | Impacto | Mitigación |
|--------------|---------|------------|
| NULA | - | No se crean registros nuevos, solo se actualizan |

**Control:** Se usa `updateOne`, no `insertOne`.

### 6.4 Riesgo: Pérdida de Datos

| Probabilidad | Impacto | Mitigación |
|--------------|---------|------------|
| MUY BAJA | CRÍTICO | Backup automático antes de ejecutar |

**Control:** Se crea colección de backup con timestamp.

---

## 7. SCHEDULER_JOB_LOGS - CORRECCIÓN TÉCNICA

### 7.1 Problema Actual

El job `inventarios_detector` termina con errores individuales por cada inventario que falla, y **nunca llega a llamar `finish_execution()`**, por lo que no se registran logs.

### 7.2 Solución Propuesta

Refactorizar el job para que:
1. Los errores individuales se acumulen pero no detengan el job
2. Al final del job, siempre se llame `finish_execution()`
3. El status sea `success` (éxito parcial) o `error` (fallo total)

### 7.3 Cambios de Código

**Archivo:** `/app/backend/core/scheduler/jobs/inventarios_detector_job.py`

```python
# ANTES (actual):
async def _ejecutar_analisis(self, registro, servidor, inv):
    try:
        # ... análisis ...
    except Exception as e:
        await self._marcar_error(registro, str(e))
        # ❌ No se registra nada si todos fallan

# DESPUÉS (propuesto):
async def run(self, manual=False, server_id_filter=None):
    # ... inicio ...
    try:
        # Procesar servidores (acumular errores, no lanzar)
        for servidor in servidores:
            try:
                await self._escanear_servidor(servidor)
            except Exception as e:
                self.stats["errores_servidor"] += 1
                logger.error(f"Error en servidor {servidor['name']}: {e}")
        
        # SIEMPRE registrar al final
        status = "success" if self.stats["inventarios_procesados"] > 0 else "partial"
        if self.stats["inventarios_error"] > 0 and self.stats["inventarios_procesados"] == 0:
            status = "error"
        
        await self.job_logger.finish_execution(
            log_entry=log_entry,
            status=status,
            processed_count=self.stats["inventarios_procesados"],
            success_count=self.stats["inventarios_procesados"],
            failed_count=self.stats["inventarios_error"],
            skipped_count=self.stats["inventarios_duplicados"],
            message=self._generar_resumen()
        )
        
    except Exception as e:
        # Solo errores CRÍTICOS del job (no individuales)
        await self.job_logger.finish_execution(
            log_entry=log_entry,
            status="error",
            error_detail=str(e)
        )
```

### 7.4 Estados de Log Propuestos

| Status | Condición |
|--------|-----------|
| `success` | Al menos 1 inventario procesado exitosamente |
| `partial` | 0 procesados pero hubo intentos (todo falló) |
| `error` | Error crítico del job (no llegó a procesar) |

---

## 8. ROLLBACK

### 8.1 Rollback de Workflows

```python
# Restaurar desde backup
backup_name = "workflow_inventarios_backup_YYYYMMDD_HHMMSS"

# Opción A: Restaurar toda la colección
db.workflow_inventarios.drop()
db[backup_name].aggregate([{"$out": "workflow_inventarios"}])

# Opción B: Restaurar solo los 6 modificados
for wid in workflows_corregidos:
    original = db[backup_name].find_one({'id': wid})
    db.workflow_inventarios.replace_one({'id': wid}, original)
```

### 8.2 Rollback de scheduler_job_logs

No aplica - los cambios son aditivos (solo se agregan logs, no se modifican existentes).

---

## 9. PLAN DE EJECUCIÓN PROPUESTO

| Paso | Acción | Verificación |
|------|--------|--------------|
| 1 | Aprobar este plan | Confirmación del usuario |
| 2 | Crear script de corrección | Archivo listo |
| 3 | Ejecutar en Preview | Ver resultados |
| 4 | Validar 0 NULLs | Query de verificación |
| 5 | Corregir scheduler_job_logs | Modificar código |
| 6 | Ejecutar job de prueba | Ver logs registrados |
| 7 | Documentar cierre | Actualizar PRD.md |

---

## 10. RESUMEN DE DECISIONES

| Decisión | Valor |
|----------|-------|
| Workflows a corregir | 6 |
| Método | Script único |
| Backup | Automático |
| detalle_diferencias | No requiere corrección |
| scheduler_job_logs | Refactorizar código |
| Riesgo general | BAJO |

---

## APROBACIÓN

- [ ] Plan revisado y aprobado
- [ ] Autorizado ejecutar corrección de workflows
- [ ] Autorizado modificar scheduler_job_logs

---

**Pendiente confirmación del usuario para proceder con implementación.**
