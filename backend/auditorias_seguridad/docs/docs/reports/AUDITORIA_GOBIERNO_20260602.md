# REPORTE AUDITORÍA GOBIERNO EDARSAHUB

**Fecha**: 2026-06-02  
**Ejecutado por**: `run_governance_audit.sh`

---

## 1. Resumen Sistema_Gobierno_Tablas

| Módulo | Categoría | Estado | Total |
|--------|-----------|--------|-------|
| AUTH | TRANSICIONAL | DEPRECADA | 3 |
| Comercial | DERIVADA | ACTIVA | 2 |
| Comercial | LEGADO_REVISION | NO_USAR_NUEVO | 3 |
| Comercial | SINCRONIZADA | ACTIVA | 5 |
| COMERCIAL | VISTA | ACTIVA | 2 |
| Finanzas | CANONICA | ACTIVA | 1 |
| Finanzas/PropinasTPV | CANONICA | ACTIVA | 3 |
| Global | CANONICA | ACTIVA | 4 |
| RH | CANONICA | ACTIVA | 1 |
| RH | LOG | ACTIVA | 1 |
| RH | STAGING | ACTIVA | 1 |
| SISTEMA | CORE | ACTIVA | 1 |

**Total tablas gobernadas**: 27

---

## 2. Tablas RBAC en Gobierno

### Transicionales (DEPRECADAS)
| Tabla | Reemplazo |
|-------|-----------|
| `Sistema_RBAC_Permisos` | `Usuario_Acciones + Usuario_PermisosRolModulo` |
| `Sistema_RBAC_Roles` | `Usuario_Roles` |
| `Sistema_RBAC_RolesPermisos` | `Usuario_PermisosRolModulo` |

**Directiva**: NO usar para nuevos desarrollos. Migrar a `Usuario_*`.

---

## 3. Tablas NO_USAR_NUEVO

| Tabla | Módulo | Categoría | Observación |
|-------|--------|-----------|-------------|
| `Config_Horarios` | Comercial | LEGADO_REVISION | Sin reemplazo definido |
| `Fact_Ventas_Consolidadas` | Comercial | LEGADO_REVISION | Sin reemplazo definido |
| `Products` | Comercial | LEGADO_REVISION | Sin reemplazo definido |

**Acción recomendada**: Definir tablas de reemplazo o migrar datos.

---

## 4. Tablas Sin Clasificar

✅ **Ninguna tabla sin clasificar**

---

## 5. Violaciones NO-LIVE Detectadas

El scanner `no_live_dashboard_policy.py` detectó **67 archivos** con patrones de conexión.

### Clasificación:

| Tipo | Cantidad | Acción |
|------|----------|--------|
| PERMITIDO (scripts/tools/tests) | ~40 | Mantener - son herramientas |
| PERMITIDO (sync/jobs/adapters) | ~15 | Mantener - sincronizan datos |
| P0 (endpoints legacy comercial) | ~5 | Marcar legacy, no crecer |
| P1 (módulos con live fuera de job) | ~7 | Migrar gradualmente |

### Módulos Legacy con Conexiones Live (NO alimentan dashboards nuevos):
- `backend/modules/comercial/routes.py`
- `backend/modules/comercial/service.py`
- `backend/modules/comercial/repository.py`

**Directiva**: El dashboard de Inteligencia Comercial usa exclusivamente `/api/comercial/inteligencia/*` que lee de vistas SQL canónicas.

---

## 6. Vista Creada

```sql
CREATE OR ALTER VIEW dbo.Sistema_VW_Gobierno_Tablas_Resumen
AS
SELECT modulo, categoria, estado, COUNT(*) AS total_tablas, ...
FROM dbo.Sistema_Gobierno_Tablas
GROUP BY modulo, categoria, estado;
```

---

## 7. Cumplimiento de Máximas

| Máxima | Estado |
|--------|--------|
| 3. Cero MongoDB para comercial | ✅ Inteligencia Comercial usa SQL |
| 4. NO-LIVE para dashboards | ✅ Endpoints usan vistas canónicas |
| 5. Gobierno de tablas | ✅ 27 tablas registradas |
| 8. Prohibición testing_agent | ✅ Pruebas via bash/SQL Runner |

---

## 8. Archivos Generados en esta Sesión

- `/app/scripts/run_governance_audit.sh`
- `/app/scripts/report_tablas_sin_clasificar.sh` (actualizado)
- `/app/backend/database/migrations/018_crear_vista_gobierno_resumen.sql`
- `/app/backend/database/diagnostics/017_validar_tablas_no_usar_nuevo.sql`
- `/app/docs/reports/AUDITORIA_GOBIERNO_20260602.md`
