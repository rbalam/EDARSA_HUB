# Capa 3 — Diagnóstico auditado y blueprint EXACTO

**Fecha:** 2026-06-07
**Alcance:** SOLO diagnóstico. No se modificó código, no se metió stub, no se migró nada, no se tocó EDARSAHUB SQL.

---

## 0. Conclusión ejecutiva (cambia el panorama)

**Capa 3 NO es una migración Mongo→SQL pendiente.** Los repositorios del módulo
`fase2_operativo` **ya están 100% migrados a SQL** (FASE B-P0 / B-P1). El parámetro
`db` (Mongo) **se ignora** en todos los repos.

El único motivo por el que las 8 rutas v2 truenan con `'NoneType' object is not
subscriptable` es **una sola función rota**:

```
/app/backend/modules/fase2_operativo/db_utils.py
30:        _client = None        # P2-07: MongoDB eliminado
31:        _db = _client[db_name]   # <-- None['test_database'] => CRASH
```

Las rutas llaman `get_db() -> get_database()` para obtener un `db` que pasan a los
services/repos. `get_database()` truena **antes** de que corra el código SQL.

**Implicación:** reparar esa única función (que `get_database()` devuelva `None` en
lugar de hacer `None[db_name]`) haría que las 8 rutas sirvan **DATOS REALES de
EDARSAHUB SQL**. NO es "degradación por stub": los datos vienen de SQL; `db` solo es
un parámetro ignorado.

---

## 1. Cadena de datos real (auditada)

`ruta v2` → `get_db()` (db_utils) → `Service(db)` → `Repository(db)` → **`db` IGNORADO** → `SQLBaseRepository._sql_repo` → `get_sql_connection()` → **EDARSAHUB SQL**

Evidencia:
- `repositories/base_repository.py`: re-exporta `SQLBaseRepository`, `COLLECTION_TO_TABLE_MAP`, `FIELD_MAPPING`. Comentario: *"El parámetro 'db' (MongoDB) se ignora completamente"*.
- `repositories/sql_base_repository.py`: usa `pymssql` + `get_sql_connection()` (EDARSAHUB). Contiene el mapa colección→tabla.
- `workflow_repository.py` (`super().__init__(db, "workflow_inventarios")`), `responsabilidad_repository.py` (`"responsabilidad_economica"`), etc. usan `self._sql_repo`.

---

## 2. Mapa exacto por endpoint v2

| Endpoint v2 | Archivo ruta | Auth | Service / Repo | Colección lógica | Tabla SQL (EDARSAHUB) | Estado tabla |
|---|---|---|---|---|---|---|
| `GET /api/v2/dashboard/resumen` | `dashboard_routes.py` | `get_current_user` | `OperativoService` (workflow+tarea) | workflow_inventarios / tareas_inventario | `Workflow_Inventarios` / `Tareas_Inventario` | ✅ existe (18 / 18 filas) |
| `GET /api/v2/dashboard/alertas` | `dashboard_routes.py` | `get_current_user` | `OperativoService` | tareas_inventario / workflow | `Tareas_Inventario` / `Workflow_Inventarios` | ✅ existe |
| `GET /api/v2/tareas` | `tarea_routes.py` | `get_current_user` | `TareaService` → `TareaRepository` | tareas_inventario | `Tareas_Inventario` | ✅ existe (18 filas) |
| `GET /api/v2/workflows` | `workflow_routes.py` | `get_current_user` | `WorkflowService` → `WorkflowRepository` | workflow_inventarios | `Workflow_Inventarios` | ✅ existe (18 filas) |
| `GET /api/v2/sla/metricas` | `sla_routes.py` | `require_permission("SLA_VER")` | `SLAService` (tareas) | tareas_inventario | `Tareas_Inventario` | ✅ existe (18 filas) |
| `GET /api/v2/responsabilidad/metricas` | `responsabilidad_routes.py` | `require_permission("RESPONSABILIDAD_VER")` | `ResponsabilidadRepository` | responsabilidad_economica | `Operativo_ResponsabilidadEconomica` | ✅ existe (0 filas) |
| `GET /api/v2/responsabilidad/pendientes-aprobacion` | `responsabilidad_routes.py` | `require_permission(...)` | `ResponsabilidadRepository.get_pendientes_revision` | responsabilidad_economica | `Operativo_ResponsabilidadEconomica` | ✅ existe (0 filas) |
| `GET /api/v2/responsabilidad/en-disputa` | `responsabilidad_routes.py` | `require_permission(...)` | `ResponsabilidadRepository` | responsabilidad_economica | `Operativo_ResponsabilidadEconomica` | ✅ existe (0 filas) |

> Nota: `Operativo_ResponsabilidadEconomica` existe pero está vacía (0 filas). Sus
> métodos de métricas ya devuelven ceros por defecto, así que **no truenan** una vez
> reparado `get_database()`; simplemente regresan datos vacíos legítimos.

---

## 3. Punto único de falla

```
/app/backend/modules/fase2_operativo/db_utils.py : línea 31
_db = _client[db_name]   con _client = None  ->  'NoneType' object is not subscriptable
```

Llamado por TODAS las rutas v2 vía `get_db()` (dashboard_routes:30, tarea_routes:37,
workflow_routes:40, responsabilidad_routes:59, etc.).

---

## 4. Fix recomendado (DIFERIDO — pendiente de tu aprobación como bloque Capa 3)

**Tamaño:** ~3 líneas. **Riesgo:** bajo. **Reversible:** sí.

```python
# db_utils.py  (get_database)
# ANTES:
_client = None
_db = _client[db_name]   # CRASH

# DESPUÉS (Mongo eliminado; los repos usan SQL e ignoran db):
_db = None               # get_database() retorna None de forma segura
return _db
```

- NO es stub de datos: los repos siguen leyendo de EDARSAHUB SQL.
- Efecto: las 8 rutas v2 dejan de dar 500 y sirven datos reales (`Workflow_Inventarios`,
  `Tareas_Inventario`, `Operativo_ResponsabilidadEconomica`).
- Validación propuesta (curl): cada endpoint con token → 200 con payload SQL.

**Riesgo residual a revisar antes de aplicar:** confirmar que ningún service/ruta
subscripta `db[...]` o use `db.<coleccion>` directamente (no vía repo). La auditoría
no encontró tal uso en la cadena de las 8 rutas, pero debe verificarse por endpoint
antes de ejecutar el fix.

---

## 5. Lo que NO se hizo (respetando tus reglas)

- ❌ No se aplicó el fix (Capa 3 = bloque separado y auditado, pendiente de tu OK).
- ❌ No se metió stub de datos.
- ❌ No se migró nada nuevo (ya estaba migrado).
- ❌ No se tocó EDARSAHUB SQL (solo lecturas COUNT(*) de verificación).
