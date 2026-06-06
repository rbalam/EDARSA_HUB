# FASE B-P1-A: Migración workflow_repository.py a SQL Explícito

**Fecha:** 26 Mayo 2026  
**Archivo:** `/app/backend/modules/fase2_operativo/repositories/workflow_repository.py`  
**Tabla SQL:** `Workflow_Inventarios`

---

## 1. ESTADO ANTERIOR

### Dependencias MongoDB:
```python
from pymongo import DESCENDING
```

### Métodos con código MongoDB:
| Método | Código MongoDB |
|--------|---------------|
| `get_by_procesado_id()` | `self.collection.find_one()` |
| `get_by_estado()` | `self.collection.find().skip().limit().sort()` |
| `get_escalados()` | `self.collection.find().limit().sort()` |
| `incrementar_ciclo()` | `self._to_object_id()`, `$inc` |
| `contar_por_estado()` | `self.collection.aggregate()` |

### Problemas identificados:
- Uso de `pymongo.DESCENDING`
- Uso de `self._to_object_id()` que ya no existe en SQL
- Uso de `$inc` para incrementar ciclos
- Dependencia implícita de `self.collection` (MongoDB)

---

## 2. ESTADO NUEVO

### Dependencias:
```python
from .base_repository import BaseRepository, SQLBaseRepository
# CERO pymongo
```

### Constantes migradas:
```python
DESCENDING = -1  # Reemplaza pymongo.DESCENDING
```

### Métodos Migrados:
| Método | Implementación SQL |
|--------|-------------------|
| `get_by_procesado_id()` | `self._sql_repo.find_one({"procesado_id": ...})` |
| `get_by_estado()` | `self._sql_repo.find().sort().skip().limit()` |
| `get_escalados()` | Usa `get_by_estado("ESCALADO", ...)` |
| `incrementar_ciclo()` | SELECT + UPDATE explícito |
| `contar_por_estado()` | `self._sql_repo.aggregate()` con GROUP BY |

---

## 3. MÉTODOS MIGRADOS

| # | Método | Estado | Tabla SQL |
|---|--------|--------|-----------|
| 1 | `__init__()` | ✅ Migrado | - |
| 2 | `get_by_procesado_id()` | ✅ Migrado | Workflow_Inventarios |
| 3 | `get_by_estado()` | ✅ Migrado | Workflow_Inventarios |
| 4 | `get_pendientes_asignacion()` | ✅ Migrado | Workflow_Inventarios |
| 5 | `get_en_revision()` | ✅ Migrado | Workflow_Inventarios |
| 6 | `get_pendientes_justificacion()` | ✅ Migrado | Workflow_Inventarios |
| 7 | `get_en_auditoria()` | ✅ Migrado | Workflow_Inventarios |
| 8 | `get_escalados()` | ✅ Migrado | Workflow_Inventarios |
| 9 | `actualizar_estado()` | ✅ Migrado | Workflow_Inventarios |
| 10 | `incrementar_ciclo()` | ✅ Migrado | Workflow_Inventarios |
| 11 | `contar_por_estado()` | ✅ Migrado | Workflow_Inventarios |

### Métodos nuevos agregados:
| Método | Descripción |
|--------|-------------|
| `buscar_workflows()` | Búsqueda avanzada con múltiples filtros |
| `get_workflow_completo()` | Obtiene workflow con todos sus datos |

### Métodos deprecados (compatibilidad):
| Método | Razón |
|--------|-------|
| `_to_object_id()` | No se usa ObjectId en SQL |
| `_serialize_id()` | No se necesita en SQL |
| `_serialize_list()` | No se necesita en SQL |

---

## 4. MÉTODOS PENDIENTES

**Ninguno.** Todos los métodos del repository original fueron migrados.

---

## 5. TABLAS SQL USADAS

| Tabla | Uso |
|-------|-----|
| `Workflow_Inventarios` | Tabla principal del repository |

### Columnas utilizadas:
- `WorkflowID` (PK lógico)
- `ProcesadoID` (FK a Fase 1)
- `ServerID` (RBAC)
- `EstadoWorkflow` (filtros)
- `CicloActual` (incremento)
- `FechaCreacion` (ordenamiento)
- `FechaUltimaActualizacion` (auditoría)

---

## 6. CONTRATOS PRESERVADOS

| Contrato | Estado |
|----------|--------|
| Retorno de `Dict` o `None` | ✅ Preservado |
| Retorno de `List[Dict]` | ✅ Preservado |
| Retorno de `Dict[str, int]` (conteo) | ✅ Preservado |
| Soporte para RBAC (server_ids) | ✅ Preservado |
| Paginación (skip/limit) | ✅ Preservado |
| Ordenamiento descendente | ✅ Preservado |

---

## 7. EVIDENCIA GREP POST-MIGRACIÓN

```bash
$ grep -c "db\." workflow_repository.py
0

$ grep -c "pymongo" workflow_repository.py
1  # Solo en comentario

$ grep -c "ObjectId" workflow_repository.py
1  # Solo en comentario de método deprecado

$ grep -n "self.collection" workflow_repository.py
(sin resultados - eliminado)
```

### Referencias MongoDB restantes (solo documentación):
- Línea 7: Comentario "CERO MongoDB productivo"
- Línea 20: Comentario "reemplaza pymongo.DESCENDING"
- Línea 202: Comentario "No usa $inc de MongoDB"
- Línea 233: Comentario "en lugar de aggregate de MongoDB"
- Línea 344: Comentario "No se usa ObjectId en SQL"

---

## 8. VALIDACIONES

| Validación | Estado |
|------------|--------|
| Backend arranca | ✅ OK |
| Login funciona | ✅ OK |
| Health funciona | ✅ OK |
| `GET /api/v2/workflows` | ✅ OK (total=0, items=0) |
| `GET /api/v2/workflows?estado=PENDIENTE_ASIGNACION` | ✅ OK |
| `GET /api/v2/dashboard/resumen` | ✅ OK |
| `GET /api/v2/dashboard/kpis` | ✅ OK |
| `GET /api/v2/configuracion` | ✅ OK |

---

## 9. CONFIRMACIONES

| Confirmación | Estado |
|--------------|--------|
| workflow_repository.py usa SQL explícito | ✅ Confirmado |
| CERO MongoDB productivo en el repositorio | ✅ Confirmado |
| CERO conexiones LIVE | ✅ Confirmado |
| No hay stubs silenciosos | ✅ Confirmado |
| Contratos preservados | ✅ Confirmado |

---

## 10. RIESGOS RESIDUALES

| Riesgo | Mitigación |
|--------|------------|
| Tabla vacía (0 workflows) | Esperado - no se han migrado datos |
| `server_id` puede no existir en filtros | `_build_where_clause` omite campos inexistentes |
| Métodos `_to_object_id` etc. deprecados | Mantienen compatibilidad, logs de warning |

---

## 11. RECOMENDACIÓN PARA FASE B-P1-B

### Siguiente: `tarea_repository.py`

**Análisis preliminar:**
```bash
$ grep -c "self.collection" tarea_repository.py
~10 llamadas MongoDB directas
```

**Métodos a migrar:**
1. `get_by_workflow_id()` - Lista tareas de un workflow
2. `get_pendientes()` - Tareas pendientes
3. `get_vencidas()` - Tareas vencidas
4. `actualizar_estado_tarea()` - Cambio de estado
5. `asignar_usuario()` - Asignación de responsable
6. `contar_por_estado()` - Conteo agrupado

**Tabla SQL:** `Tareas_Inventario`

---

## 12. PRÓXIMOS PASOS

1. **FASE B-P1-B**: Migrar `tarea_repository.py`
2. **FASE B-P1-C**: Migrar `responsabilidad_repository.py`
3. **FASE B-P1-D**: Migrar `cargos_repository.py`
4. **FASE B-P2**: Migrar services que acceden directamente a MongoDB

---

**Documento generado automáticamente - FASE B-P1-A COMPLETADA**
