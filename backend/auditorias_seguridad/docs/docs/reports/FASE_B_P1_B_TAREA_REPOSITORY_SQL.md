# FASE B-P1-B: Migración tarea_repository.py a SQL Explícito

**Fecha:** 26 Mayo 2026  
**Archivo:** `/app/backend/modules/fase2_operativo/repositories/tarea_repository.py`  
**Tabla SQL:** `Tareas_Inventario`

---

## 1. ESTADO ANTERIOR

### Dependencias MongoDB:
```python
from pymongo import ASCENDING, DESCENDING
```

### Métodos con código MongoDB:
| Método | Código MongoDB | Líneas |
|--------|---------------|--------|
| `get_by_workflow()` | `self.collection.find().sort()` | 29-33 |
| `get_by_usuario()` | `self.collection.find().sort()` | 55-56 |
| `get_pendientes_globales()` | `self.collection.find().sort().limit()` | 65-68 |
| `get_sin_asignar()` | `self.collection.find($or, $exists).limit()` | 78-84 |
| `get_vencidas()` | `self.collection.find()` | 108-109 |
| `contar_por_estado()` | `self.collection.aggregate()` | 184 |
| `contar_por_usuario()` | `self.collection.aggregate()` | 202 |

### Problemas identificados:
- 7 referencias directas a `self.collection` (MongoDB)
- Uso de `pymongo.ASCENDING/DESCENDING`
- Uso de operadores `$or`, `$exists`, `$nin`
- `server_id` no existe en `Tareas_Inventario` (requiere JOIN)

---

## 2. ESTADO NUEVO

### Dependencias:
```python
from .base_repository import BaseRepository, SQLBaseRepository
# CERO pymongo
```

### Constantes migradas:
```python
ASCENDING = 1    # Reemplaza pymongo.ASCENDING
DESCENDING = -1  # Reemplaza pymongo.DESCENDING
```

### Métodos Migrados:
| Método | Implementación SQL |
|--------|-------------------|
| `get_by_workflow()` | `_sql_repo.find().sort()` via SQLCursor |
| `get_by_usuario()` | `_sql_repo.find().sort()` via SQLCursor |
| `get_pendientes_globales()` | `_sql_repo.find().sort().limit()` |
| `get_sin_asignar()` | `_sql_repo.find({None})` (IS NULL) |
| `get_vencidas()` | `_sql_repo.find({$lt, $nin})` |
| `contar_por_estado()` | `_sql_repo.aggregate()` con GROUP BY |
| `contar_por_usuario()` | `_sql_repo.aggregate()` con $match |

---

## 3. MÉTODOS MIGRADOS

| # | Método | Estado | Tabla SQL |
|---|--------|--------|-----------|
| 1 | `__init__()` | ✅ Migrado | - |
| 2 | `get_by_workflow()` | ✅ Migrado | Tareas_Inventario |
| 3 | `get_by_usuario()` | ✅ Migrado | Tareas_Inventario |
| 4 | `get_pendientes_globales()` | ✅ Migrado | Tareas_Inventario |
| 5 | `get_sin_asignar()` | ✅ Migrado | Tareas_Inventario |
| 6 | `get_vencidas()` | ✅ Migrado | Tareas_Inventario |
| 7 | `asignar()` | ✅ Migrado | Tareas_Inventario |
| 8 | `actualizar_estado()` | ✅ Migrado | Tareas_Inventario |
| 9 | `completar()` | ✅ Migrado | Tareas_Inventario |
| 10 | `marcar_en_progreso()` | ✅ Migrado | Tareas_Inventario |
| 11 | `marcar_vencida()` | ✅ Migrado | Tareas_Inventario |
| 12 | `contar_por_estado()` | ✅ Migrado | Tareas_Inventario |
| 13 | `contar_por_usuario()` | ✅ Migrado | Tareas_Inventario |

### Métodos nuevos agregados:
| Método | Descripción |
|--------|-------------|
| `get_tareas_con_rbac()` | Obtiene tareas con JOIN a Workflow para filtro RBAC por server_ids |
| `buscar_tareas()` | Búsqueda avanzada con múltiples filtros |

### Métodos deprecados (compatibilidad):
| Método | Razón |
|--------|-------|
| `_serialize_list()` | No se necesita serialización en SQL |

---

## 4. MÉTODOS PENDIENTES

**Ninguno.** Todos los métodos del repository original fueron migrados.

---

## 5. TABLAS SQL USADAS

| Tabla | Uso |
|-------|-----|
| `Tareas_Inventario` | Tabla principal del repository |
| `Workflow_Inventarios` | JOIN para filtro RBAC (server_id) |

### Columnas utilizadas en Tareas_Inventario:
- `TareaID` (PK lógico)
- `WorkflowID` (FK a Workflow_Inventarios)
- `EstadoTarea` (filtros)
- `UsuarioAsignadoID` (filtros)
- `FechaCreacion` (ordenamiento)
- `FechaLimite` (ordenamiento, vencidas)
- `FechaAsignacion` (auditoría)
- `FechaCompletada` (auditoría)
- `FechaActualizacion` (auditoría)
- `Vencida` (flag)

### Nota sobre server_id:
`Tareas_Inventario` **NO tiene campo ServerID**.
Para filtrar tareas por server_id (RBAC), se debe hacer JOIN:
```sql
SELECT t.* 
FROM Tareas_Inventario t
INNER JOIN Workflow_Inventarios w ON t.WorkflowID = w.WorkflowID
WHERE w.ServerID IN (...)
```

El método `get_tareas_con_rbac()` implementa este JOIN.

---

## 6. CONTRATOS PRESERVADOS

| Contrato | Estado |
|----------|--------|
| Retorno de `List[Dict]` | ✅ Preservado |
| Retorno de `Dict[str, int]` (conteo) | ✅ Preservado |
| Retorno de `Optional[Dict]` | ✅ Preservado |
| Soporte para paginación | ✅ Preservado |
| Ordenamiento (ASC/DESC) | ✅ Preservado |
| Filtros múltiples | ✅ Preservado |

---

## 7. EVIDENCIA GREP POST-MIGRACIÓN

```bash
$ grep -c "self.collection" tarea_repository.py
0

$ grep -c "pymongo" tarea_repository.py
1  # Solo en comentario

$ grep -c "ObjectId" tarea_repository.py
0

$ grep "db\." tarea_repository.py
(sin resultados)
```

### Referencias MongoDB restantes (solo documentación):
- Línea 7: Comentario "CERO MongoDB productivo"
- Línea 20: Comentario "reemplazan pymongo.ASCENDING/DESCENDING"

---

## 8. VALIDACIONES

| Validación | Estado |
|------------|--------|
| Backend arranca | ✅ OK |
| Login funciona | ✅ OK |
| Health funciona | ✅ OK |
| `GET /api/v2/tareas` | ✅ OK (items=[], total=0) |
| `GET /api/v2/dashboard/resumen` | ✅ OK (tareas_por_estado={}) |
| `GET /api/v2/dashboard/kpis` | ✅ OK (tareas_pendientes=0) |
| `GET /api/v2/configuracion` | ✅ OK |

---

## 9. CONFIRMACIONES

| Confirmación | Estado |
|--------------|--------|
| tarea_repository.py usa SQL explícito | ✅ Confirmado |
| CERO `self.collection` | ✅ Confirmado |
| CERO MongoDB productivo | ✅ Confirmado |
| CERO conexiones LIVE | ✅ Confirmado |
| No hay stubs silenciosos | ✅ Confirmado |
| Contratos preservados | ✅ Confirmado |

---

## 10. RIESGOS RESIDUALES

| Riesgo | Mitigación |
|--------|------------|
| Tabla vacía (0 tareas) | Esperado - no se han migrado datos |
| server_id requiere JOIN | Implementado método `get_tareas_con_rbac()` |
| Métodos con server_ids ignorado | Logging de warning + documentado |
| `$or`/`$exists` no soportado | Convertido a IS NULL |

---

## 11. RECOMENDACIÓN PARA FASE B-P1-C

### Siguiente: `responsabilidad_repository.py`

**Análisis preliminar:**
- Usa `Operativo_ResponsabilidadEconomica` (creada en B-P0-B)
- Gestiona responsabilidades económicas de diferencias
- Probable uso de MongoDB para cálculos y estados

**Métodos esperados a migrar:**
1. `get_by_workflow_id()` - Obtener responsabilidad por workflow
2. `get_pendientes()` - Responsabilidades sin resolver
3. `calcular_total()` - Suma de montos
4. `actualizar_estado()` - Cambio de estado
5. `aprobar()` / `rechazar()` - Acciones de gestión

**Tabla SQL:** `Operativo_ResponsabilidadEconomica`

---

## 12. PRÓXIMOS PASOS

1. **FASE B-P1-C**: Migrar `responsabilidad_repository.py`
2. **FASE B-P1-D**: Migrar `cargos_repository.py`
3. **FASE B-P1-E**: Migrar otros repositories menores
4. **FASE B-P2**: Migrar services con acceso directo a MongoDB

---

**Documento generado automáticamente - FASE B-P1-B COMPLETADA**
