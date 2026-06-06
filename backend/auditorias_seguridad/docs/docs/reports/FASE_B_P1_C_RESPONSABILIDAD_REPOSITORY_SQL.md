# FASE B-P1-C: Migración responsabilidad_repository.py a SQL Explícito

**Fecha:** 26 Mayo 2026  
**Archivo:** `/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py`  
**Tabla SQL:** `Operativo_ResponsabilidadEconomica`

---

## 1. ESTADO ANTERIOR

### Dependencias MongoDB:
```python
# Comentario referenciando MongoDB ObjectId
# Use _id (MongoDB ObjectId) for update, not id (UUID)
```

### Métodos con código MongoDB:
| Método | Código MongoDB | Líneas |
|--------|---------------|--------|
| `get_by_workflow()` | `self.collection.find_one()` | 28 |
| `existe_calculo()` | `self.collection.count_documents()` | 41 |
| `actualizar_calculo()` | `self.collection.find_one_and_update()` | 76-80 |
| `obtener_metricas_globales()` | `self.collection.aggregate()` | 196 |
| `eliminar_por_workflow()` | `self.collection.delete_one()` | 220 |

### Problemas identificados:
- 5 referencias directas a `self.collection` (MongoDB)
- Uso de `find_one_and_update` con `$set` y `return_document`
- Pipeline de agregación con `$group` y `$cond`
- Comentario obsoleto referenciando MongoDB ObjectId

---

## 2. ESTADO NUEVO

### Dependencias:
```python
from .base_repository import BaseRepository, SQLBaseRepository
# CERO pymongo, CERO MongoDB directo
```

### Métodos Migrados:
| Método | Implementación SQL |
|--------|-------------------|
| `get_by_workflow()` | `_sql_repo.find_one()` |
| `existe_calculo()` | `_sql_repo.count_documents()` |
| `actualizar_calculo()` | `_sql_repo.find_one_and_update()` |
| `obtener_metricas_globales()` | `_sql_repo.aggregate()` con GROUP BY |
| `eliminar_por_workflow()` | `_sql_repo.delete_one()` |

---

## 3. MÉTODOS MIGRADOS

| # | Método | Estado | Tabla SQL |
|---|--------|--------|-----------|
| 1 | `__init__()` | ✅ Migrado | - |
| 2 | `get_by_workflow()` | ✅ Migrado | Operativo_ResponsabilidadEconomica |
| 3 | `existe_calculo()` | ✅ Migrado | Operativo_ResponsabilidadEconomica |
| 4 | `crear_calculo()` | ✅ Migrado | Operativo_ResponsabilidadEconomica |
| 5 | `actualizar_calculo()` | ✅ Migrado | Operativo_ResponsabilidadEconomica |
| 6 | `listar_por_sucursal()` | ✅ Migrado | Operativo_ResponsabilidadEconomica |
| 7 | `listar_por_estado()` | ✅ Migrado | Operativo_ResponsabilidadEconomica |
| 8 | `listar_con_filtros()` | ✅ Migrado | Operativo_ResponsabilidadEconomica |
| 9 | `obtener_metricas_globales()` | ✅ Migrado | Operativo_ResponsabilidadEconomica |
| 10 | `eliminar_por_workflow()` | ✅ Migrado | Operativo_ResponsabilidadEconomica |

### Métodos nuevos agregados:
| Método | Descripción |
|--------|-------------|
| `aprobar()` | Aprueba un cálculo de responsabilidad |
| `rechazar()` | Rechaza un cálculo con motivo |
| `get_pendientes_revision()` | Obtiene cálculos pendientes con filtro RBAC |
| `get_by_responsable()` | Obtiene cálculos asignados a un responsable |

### Métodos deprecados (compatibilidad):
| Método | Razón |
|--------|-------|
| `_serialize_id()` | No se necesita serialización de _id en SQL |
| `_serialize_list()` | No se necesita serialización en SQL |

---

## 4. MÉTODOS PENDIENTES

**Ninguno.** Todos los métodos del repository original fueron migrados.

---

## 5. TABLAS SQL USADAS

| Tabla | Uso |
|-------|-----|
| `Operativo_ResponsabilidadEconomica` | Tabla principal del repository |

### Columnas utilizadas:
- `ResponsabilidadID` (PK lógico)
- `WorkflowID` (FK a Workflow_Inventarios)
- `ServerID` (RBAC)
- `SucursalID` (filtros)
- `ResponsableID` (filtros)
- `MontoTotal`, `MontoJustificado`, `MontoNoJustificado` (cálculos)
- `Estado` (filtros)
- `ExcedeMinimo` (filtros)
- `FechaCalculo` (ordenamiento)
- `FechaUltimaActualizacion` (auditoría)
- `FechaAprobacion` (auditoría)
- `AprobadoPorID` (auditoría)

### Mapeo de campos actualizado:
Se agregó mapeo completo de 23 campos en `FIELD_MAPPING` de `sql_base_repository.py`.

---

## 6. CONTRATOS PRESERVADOS

| Contrato | Estado |
|----------|--------|
| Retorno de `Optional[Dict]` | ✅ Preservado |
| Retorno de `List[Dict]` | ✅ Preservado |
| Retorno de `Dict` (métricas) | ✅ Preservado |
| Retorno de `bool` (eliminar) | ✅ Preservado |
| Soporte para filtros múltiples | ✅ Preservado |
| Soporte para RBAC (server_ids) | ✅ Preservado |
| Paginación (skip/limit) | ✅ Preservado |

---

## 7. EVIDENCIA GREP POST-MIGRACIÓN

```bash
$ grep -c "self.collection" responsabilidad_repository.py
0

$ grep -c "ObjectId" responsabilidad_repository.py
0

$ grep "MongoDB" responsabilidad_repository.py
7:- CERO MongoDB productivo  # Solo en comentario de documentación
```

### Referencias MongoDB eliminadas:
- Línea 75 original: `# Use _id (MongoDB ObjectId) for update` → Eliminado
- Línea 196 original: `list(self.collection.aggregate())` → Migrado a `_sql_repo.aggregate()`

---

## 8. VALIDACIONES

| Validación | Estado |
|------------|--------|
| Backend arranca | ✅ OK |
| Login funciona | ✅ OK |
| Health funciona | ✅ OK |
| `GET /api/v2/responsabilidad` | ✅ OK (total=0, items=[]) |
| `GET /api/v2/dashboard/resumen` | ✅ OK |
| `GET /api/v2/configuracion` | ✅ OK (umbral=500) |

---

## 9. CONFIRMACIONES

| Confirmación | Estado |
|--------------|--------|
| responsabilidad_repository.py usa SQL explícito | ✅ Confirmado |
| CERO `self.collection` | ✅ Confirmado |
| CERO MongoDB productivo | ✅ Confirmado |
| CERO conexiones LIVE | ✅ Confirmado |
| No hay stubs silenciosos | ✅ Confirmado |
| Contratos preservados | ✅ Confirmado |

---

## 10. RIESGOS RESIDUALES

| Riesgo | Mitigación |
|--------|------------|
| Tabla vacía (0 cálculos) | Esperado - no se han migrado datos |
| Agregación de métricas simplificada | Pipeline adaptado a capacidades de `aggregate()` SQL |
| Campos de cálculo legacy (monto_propuesto_mxn) | Mapeados a campos nuevos (monto_total) |

---

## 11. RECOMENDACIÓN PARA FASE B-P1-D

### Siguiente: `cargos_repository.py`

**Análisis preliminar:**
- Usa `Operativo_CargosResponsabilidad` (creada en B-P0-B)
- Usa `Operativo_HistorialCargos` para log de acciones
- Gestiona cargos económicos propuestos por diferencias

**Métodos esperados a migrar:**
1. `get_by_workflow_id()` - Obtener cargos por workflow
2. `get_by_responsabilidad_id()` - Cargos por responsabilidad
3. `crear_cargo()` - Crear nuevo cargo
4. `aprobar_cargo()` - Aprobar cargo
5. `rechazar_cargo()` - Rechazar cargo
6. `disputar_cargo()` - Abrir disputa
7. `registrar_historial()` - Log de acciones

**Tablas SQL:**
- `Operativo_CargosResponsabilidad`
- `Operativo_HistorialCargos`

---

## 12. PRÓXIMOS PASOS

1. **FASE B-P1-D**: Migrar `cargos_repository.py`
2. **FASE B-P1-E**: Migrar otros repositories menores
3. **FASE B-P2**: Migrar services con acceso directo a MongoDB
4. **FASE B-P3**: Migrar rutas con acceso directo a MongoDB

---

**Documento generado automáticamente - FASE B-P1-C COMPLETADA**
