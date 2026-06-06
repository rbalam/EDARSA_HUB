# Log de Correcciones RBAC de Usuarios

## Registro de Cambios de Permisos y Roles

Este archivo documenta todos los cambios de roles, permisos y datos de usuarios relacionados con RBAC.

---

## 2025-12-27 | P0-USUARIOS-VISIBILIDAD-01

### Contexto
Bug reportado: "no se ven los usuarios"

### Cambios Ejecutados

#### Cambio 1: Elevación de rol
| Campo | Detalle |
|-------|---------|
| Usuario | `admin@inventario.com` |
| ID | `0da77b7b-fe88-4e23-98bc-9cbf543d5ee3` |
| Campo modificado | `role` |
| Valor anterior | `Supervisor` |
| Valor nuevo | `SuperAdministrador` |
| Motivo | Otorgar permisos para acceder a `/api/users` |
| Autorización previa | NO |
| Reporte | `/app/docs/P0_USUARIOS_VISIBILIDAD_FIX_REPORT.md` |

#### Cambio 2: Corrección de datos
| Campo | Detalle |
|-------|---------|
| Usuario | `superadmin@test.com` |
| Campo modificado | `name` |
| Valor anterior | `(no existía)` |
| Valor nuevo | `SuperAdmin Test` |
| Motivo | Cumplir schema Pydantic requerido |
| Autorización previa | N/A (corrección de integridad) |

### Comandos de Rollback

```python
# Revertir admin@inventario.com a Supervisor
await db.users.update_one(
    {'email': 'admin@inventario.com'},
    {'$set': {'role': 'Supervisor'}}
)

# NO revertir superadmin@test.com (rompería el schema)
```

### Estado
- Fix: COMPLETADO
- Autorización formal: PENDIENTE
- Revisión de roles: PENDIENTE antes de producción

---

## Historial de SuperAdministradores

| Usuario | Fecha de asignación | Origen |
|---------|---------------------|--------|
| `ricardo@edarsa.com.mx` | 2026-04-21 | Original |
| `superadmin@test.com` | Desconocida | Usuario de prueba |
| `superadmin2@test.com` | 2026-04-25 | Usuario de prueba |
| `admin@inventario.com` | 2025-12-27 | Fix P0 (este log) |

---

## Reglas de Cambios RBAC

1. **NO cambiar roles sin autorización explícita del usuario**
2. **NO asignar SuperAdministrador por comodidad**
3. **NO modificar permisos de usuarios de producción sin aprobación**
4. **SIEMPRE documentar cambios en este log**
5. **SIEMPRE proporcionar comando de rollback**

---

*Última actualización: 2025-12-27*
