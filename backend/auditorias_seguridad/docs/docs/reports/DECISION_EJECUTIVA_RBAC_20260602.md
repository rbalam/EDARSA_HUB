# DECISIÓN EJECUTIVA RBAC - EDARSAHUB

**Fecha**: 2026-06-02  
**Estado**: APROBADO

---

## 1. Arquitectura RBAC Definitiva

### RBAC Canónico: `Usuario_*`

| Tabla | Propósito | Registros |
|-------|-----------|-----------|
| `Usuario_Modulos` | Catálogo de módulos del sistema | 59 |
| `Usuario_Roles` | Catálogo de roles | 16 |
| `Usuario_Acciones` | Catálogo de acciones | 16 |
| `Usuario_PermisosRolModulo` | Matriz de permisos | 150+ |
| `Usuario_Catalogo` | Usuarios del sistema | (Pendiente migración) |

### Sistema_RBAC_*: CONGELADO COMO TRANSICIÓN

| Tabla | Estado | Acción |
|-------|--------|--------|
| `Sistema_RBAC_Permisos` | STAGING_RBAC_TRANSICION / NO_USAR_NUEVO | No usar |
| `Sistema_RBAC_Roles` | STAGING_RBAC_TRANSICION / NO_USAR_NUEVO | No usar |
| `Sistema_RBAC_RolesPermisos` | STAGING_RBAC_TRANSICION / NO_USAR_NUEVO | No usar |

**Observación**: Este esquema fue creado para Inteligencia Comercial pero el canónico existente es `Usuario_*`. No asignar usuarios aquí.

---

## 2. Permisos INTELIGENCIA_COMERCIAL

| Rol | Acciones Permitidas |
|-----|---------------------|
| SUPERADMIN | VER, EXPORTAR, GESTIONAR, CONFIGURAR |
| ADMIN | VER, EXPORTAR, GESTIONAR |
| CRM_ADMIN | VER, EXPORTAR, GESTIONAR |
| DIRECCION | VER, EXPORTAR |
| GERENCIA | VER, EXPORTAR |
| GERENTE_OPS | VER, EXPORTAR |
| CRM_EJEC | VER, EXPORTAR |
| CRM_AUDIT | VER |
| AUDITOR | VER |
| VISOR | VER |

**Total permisos asignados**: 21

---

## 3. Decisiones Pendientes

| Tema | Estado | Próximo Paso |
|------|--------|--------------|
| Migrar usuarios MongoDB → SQL | PENDIENTE | Mapear colección `rbac_*` hacia `Usuario_*` |
| MongoDB RBAC | CONGELADO | No borrar todavía |
| Usuarios | PENDIENTE | No migrar hasta definir mapeo |

---

## 4. Migraciones Ejecutadas

| Script | Descripción |
|--------|-------------|
| `019_clasificacion_masiva_por_familia.sql` | 428 tablas clasificadas |
| `020_marcar_sistema_rbac_transicion.sql` | Sistema_RBAC_* → NO_USAR_NUEVO |
| `021_permisos_inteligencia_comercial.sql` | 21 permisos para IC |

---

## 5. Próximos Pasos

1. **Mapear Mongo → SQL**: Definir equivalencias entre colecciones MongoDB `rbac_*` y tablas `Usuario_*`
2. **Script de migración**: Crear script de migración de usuarios una vez definido el mapeo
3. **Testing**: Validar que endpoints de autenticación funcionen con `Usuario_*`
4. **Deprecación MongoDB**: Solo después de validación completa

---

## 6. Resumen Gobierno de Tablas

| Métrica | Valor |
|---------|-------|
| Total tablas gobernadas | 428 |
| Tablas ACTIVA | 401 |
| Tablas REVISION | 18 |
| Tablas NO_USAR_NUEVO | 9 |
| Tablas SIN_CLASIFICAR | 0 ✅ |

---

*Documento generado automáticamente - E1 Agent*
