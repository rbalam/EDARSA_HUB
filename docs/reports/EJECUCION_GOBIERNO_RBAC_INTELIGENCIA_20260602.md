# REPORTE EJECUCIÓN: Gobierno RBAC e Inteligencia Comercial

**Fecha**: 2026-06-02  
**Ejecutado por**: SQL Runner (`edarsahub_sql_runner.py`)  
**Modo**: migrate  

---

## 1. Módulo INTELIGENCIA_COMERCIAL Registrado

```sql
INSERT INTO Usuario_Modulos (CodigoModulo, NombreModulo, Ruta, ...)
VALUES ('INTELIGENCIA_COMERCIAL', 'Inteligencia Comercial', '/comercial/inteligencia', ...)
```

**Resultado:**
| Campo | Valor |
|-------|-------|
| ModuloID | 59 |
| CodigoModulo | INTELIGENCIA_COMERCIAL |
| NombreModulo | Inteligencia Comercial |
| Ruta | /comercial/inteligencia |
| Activo | Sí |

---

## 2. Tablas Sistema_RBAC_* Marcadas como TRANSICIONAL

Las siguientes tablas del esquema antiguo RBAC fueron marcadas como **TRANSICIONAL/DEPRECADA**:

| Tabla | Reemplazo Canónico | Estado |
|-------|-------------------|--------|
| `Sistema_RBAC_Permisos` | `Usuario_Acciones + Usuario_PermisosRolModulo` | DEPRECADA |
| `Sistema_RBAC_Roles` | `Usuario_Roles` | DEPRECADA |
| `Sistema_RBAC_RolesPermisos` | `Usuario_PermisosRolModulo` | DEPRECADA |

**Directiva:** No usar estas tablas para nuevos desarrollos. Migrar gradualmente a `Usuario_*`.

---

## 3. Vistas y Tablas de Inteligencia Comercial Registradas

### Vistas Canónicas (SQL-first)
| Vista | Categoría | Fuente Verdad |
|-------|-----------|---------------|
| `Comercial_Inteligencia_VW_KPIsEjecutivos` | VISTA | SÍ |
| `Comercial_Inteligencia_VW_SyncStatus` | VISTA | SÍ |

### Tablas de Datos
| Tabla | Categoría | Fuente Verdad |
|-------|-----------|---------------|
| `Comercial_Ventas_Dia_Abiertas_v2` | DERIVADA | EDARSAHUB SQL |
| `Sync_Sales` | SINCRONIZADA | SoftRestaurant/MPRO |
| `Sync_PAX_Detalle` | SINCRONIZADA | SoftRestaurant/MPRO |
| `Unidades_Negocio` | CORE | SÍ |

---

## 4. Estado Final Sistema_Gobierno_Tablas

**Total registros:** 27

### Distribución por Categoría
| Categoría | Cantidad |
|-----------|----------|
| CORE | 3 |
| VISTA | 2 |
| SINCRONIZADA | 2 |
| TRANSICIONAL | 3 |
| DERIVADA | 1 |
| Otras | 16 |

---

## 5. Próximos Pasos

1. **Migración RBAC**: Migrar usuarios de MongoDB a `Usuario_Catalogo` usando las tablas canónicas `Usuario_*`.
2. **Jobs de Sincronización**: Implementar la extracción real hacia `Sync_Sales` y `Sync_PAX_Detalle` (requiere credenciales SoftRestaurant/MPRO).
3. **Frontend**: Conectar el portal de Inteligencia Comercial a los endpoints `/api/comercial/inteligencia/*`.

---

## Archivos Generados

- `/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql`
- `/app/backend/database/diagnostics/014_diagnostico_tablas_rbac_usuario.sql`
- `/app/backend/database/diagnostics/015_diagnostico_completo_rbac_canonico.sql`
- `/app/backend/database/diagnostics/016_verificar_datos_rbac.sql`
- `/app/scripts/classify_no_live_violations.sh`
- `/app/scripts/report_tablas_sin_clasificar.sh`
- `/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md`
- `/app/docs/reports/MATRIZ_NO_LIVE_DASHBOARD_EDARSAHUB.md`

---

## Cumplimiento de Máximas Inquebrantables

✅ **Máxima 3**: Cero dependencias MongoDB para nuevos módulos  
✅ **Máxima 4**: Arquitectura NO-LIVE para dashboards  
✅ **Máxima 5**: Todas las tablas registradas en `Sistema_Gobierno_Tablas`  
✅ **Máxima 8**: Prohibición de `testing_agent_v3_fork` respetada (pruebas via SQL Runner y bash)
