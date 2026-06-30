# EDARSAHUB Codex Context

Memoria operativa para Codex en EDARSAHUB / V1.0.

Actualizado desde resumen del Project de ChatGPT el 2026-06-30.

## 1. Proyecto y ramas

- Proyecto: EDARSAHUB / V1.0.
- Repo: `rbalam/EDARSA_HUB`.
- Rama correcta de trabajo: `Edarsahub_Desarrollo`.
- Rama de producción: `Edarsahub_Produccion`.
- Regla principal: todo se valida primero en Desarrollo.
- No trabajar directo en Producción.
- Producción solo recibe cambios ya probados.

Snapshot reportado desde ChatGPT Project:

- `Edarsahub_Desarrollo` local/remoto: `0 0`.
- HEAD Desarrollo: `ec955f48`.
- Producción: `4885da1e`.
- Producción no incluye todavía los últimos cambios RBAC/menú.

Antes de cualquier commit, push o deploy:

```bash
git status --short --branch
git log --oneline --decorate -5
```

Si el workspace está en una rama temporal o hotfix, no asumir que es Desarrollo.

## 2. Máximas de trabajo

- No hacer parches a ciegas.
- Primero auditar el bloque exacto que se va a cambiar.
- Usar scripts cortos en depuración.
- En respuestas de depuración, máximo 3 scripts/comandos sugeridos.
- Validar antes de commit.
- Commit y push van a Desarrollo.
- Producción se toca después de validar Desarrollo.
- No revertir cambios ajenos sin autorización explícita.

## 3. SQL, auditoría y datos productivos

- Usar `HRLectura` para revisar.
- No usar `GPTWRITE`.
- No hacer `UPDATE`, `DELETE` o `INSERT` manual en auditoría/productivo.
- No inventar datos.
- No crear fuentes paralelas si existe flujo canónico.
- IDs internos para relaciones.
- Códigos estables para API/frontend.
- Nombres visibles solo para UI.

## 4. Inventarios y fuentes canónicas

- No usar conexiones LIVE desde endpoints de usuario.
- MPRO y SoftRestaurant deben leerse desde tablas canónicas/sync de EDARSAHUB.
- Reportes canónicos deben operar SQL-first / no-live.
- No agregar fallback live para “resolver rápido” un reporte.
- Para MPRO inventarios, la fecha de inicio de movimientos/ventas debe ser inventario inicial + 1 día.
- Los almacenes pueden tener tensión entre `almacen_id` canónico y nombre visible; conservar ambos y validar contra la tabla sync antes de filtrar de forma estricta.

## 5. RBAC

RBAC se conserva.

No eliminar RBAC, no sustituir RBAC por menú y no usar `sec_roles`, `sec_permisos` o `sec_perfil` como fuente primaria nueva.

El menú no es fuente de permisos. El menú consume permisos efectivos.

Fuentes canónicas para permisos y roles:

- `Usuario_Catalogo`
- `Usuario_Roles`
- `Usuario_RolesAsignacion`
- `Usuario_RolesContexto`
- `Usuario_Modulos`
- `Usuario_Acciones`
- `Usuario_PermisosRolModulo`
- `Sistema_CatalogosPermisos`

Fuentes de alcance operativo:

- `Usuario_EmpresasAsignacion`
- `Usuario_ServidoresAsignacion`
- `Usuario_SucursalesAsignacion`
- `Usuario_AlmacenesAsignacion`

## 6. Cambios RBAC recientes

### 6.1 Endurecimiento de alcance operativo

Endpoint trabajado:

- `PUT /users/{user_id}/permissions`

Debe limitarse a alcance operativo:

- `allowed_servers`
- `allowed_sucursales`
- `allowed_warehouses`

Debe bloquear explícitamente cambios sobre:

- `roles`
- `permissions`
- `menu`
- `modules`
- `actions`
- `sec_roles`
- `sec_permisos`
- `sec_perfil`
- `Usuario_Roles`
- `Usuario_RolesAsignacion`
- `Usuario_PermisosRolModulo`
- `Usuario_Modulos`
- `Usuario_Acciones`
- `Sistema_CatalogosPermisos`

Commit reportado:

- `5213c92c fix(rbac): harden user scope permissions endpoint`

### 6.2 Permisos efectivos

Endpoint nuevo:

- `GET /auth/me/effective-permissions`

Objetivo:

- Resolver permisos efectivos desde RBAC SQL canónico.
- Usar `core.rbac.service.get_user_permissions()`.

Debe devolver:

- `source`
- `roles`
- `permissions`
- `permissions_flat`
- `scope`

### 6.3 Menú derivado de permisos efectivos

Endpoint afectado:

- `GET /auth/me/menu-permissions`

Ya no debe decidir menú con hardcodes por rol como:

- `Administrador`
- `Supervisor`
- `Director`
- `Gerente`
- `Auditor`
- `sec_roles`

Debe derivar de:

- `permissions_flat`
- `tiene_acceso_global`
- `MENU_PERMISSION_MAP`

Commit reportado:

- `ec955f48 feat(rbac): expose effective permissions for menu`

## 7. Validaciones obligatorias

Backend:

```bash
python3 -m py_compile backend/server.py
```

Frontend:

```bash
cd frontend
yarn build
```

Si el entorno local no tiene `yarn` en PATH, usar el runtime disponible de Codex solo para validar, pero mantener `yarn.lock` como lockfile del proyecto. No introducir `package-lock.json` ni cambiar de gestor sin decisión explícita.

Validaciones funcionales pendientes:

- `/api/auth/me/effective-permissions`
- `/api/auth/me/menu-permissions`
- Menú para `SuperAdministrador`.
- Menú para `Administrador`.
- Menú para `Supervisor`.
- Menú para usuario limitado.
- Usuario sin permiso no debe ver acceso o debe verlo bloqueado con lógica futura.

Riesgo activo:

- El menú puede funcionar para administradores por acceso global, pero usuarios normales podrían tener `permissions_flat` vacío si faltan datos en `Usuario_RolesAsignacion`, `Usuario_PermisosRolModulo`, `Usuario_Modulos` o `Usuario_Acciones`.

## 8. UX y producto

Todo menú, módulo o tab nuevo debe tener lógica formal de:

- integración
- ubicación
- agrupación
- jerarquía
- navegación
- permisos

No agregar accesos sueltos sin criterio de UX/navegación.

Jerarquía de menú objetivo:

- Inicio
- Operación
- Comercial
- Compras
- Inventarios
- Finanzas
- RH
- Reportes
- Sistema
- Configuración

## 9. Backlog técnico

### Alta prioridad

1. Validar menú RBAC con usuarios reales.
2. Mantener este archivo como memoria operativa de Codex.

### Media prioridad

3. Ordenar menú con lógica formal de producto.
4. Diseñar solicitudes contextuales de permisos.
5. Diseñar autorización/rechazo/mancomunada con auditoría.
6. Diseñar workspace multiventana / multitransaccional.

## 10. Solicitud contextual de permisos

Máxima:

Si un usuario encuentra un botón, tab, acción o acceso bloqueado, debe poder solicitar permiso desde ese mismo punto.

No debe ir a otro módulo para pedirlo.

Flujo deseado:

1. Usuario intenta una acción bloqueada.
2. UI ofrece `Solicitar permiso`.
3. Se captura módulo, acción, contexto operativo y motivo.
4. Llega al superior/autorizador.
5. Se aprueba o rechaza.
6. Queda auditado.
7. El permiso puede ser temporal, permanente, excepcional por transacción o mancomunado.

Datos a contemplar:

- solicitante
- acción requerida
- módulo
- contexto operativo
- empresa
- servidor
- sucursal
- almacén
- motivo
- autorizador
- aprobación/rechazo
- autorización mancomunada
- vigencia
- auditoría

Tablas futuras candidatas:

- `Usuario_SolicitudesPermiso`
- `Usuario_AutorizacionesPermiso`
- `Usuario_PermisosExcepcion`
- `Usuario_LogPermisos`

## 11. Workspace multiventana / multitransaccional

Problema:

- Las pantallas actuales tienden a operar aisladas.
- Para ir de una pantalla a otra se pierde contexto.

Meta:

Pasar de pantallas aisladas a un workspace operativo conectado.

Ejemplo de navegación deseada:

```text
Venta
-> producto vendido
-> receta
-> insumo
-> inventario
-> requisición
-> compra
-> proveedor
-> factura / recepción
```

Elementos esperados:

- pestañas internas
- paneles persistentes
- breadcrumbs transaccionales
- historial operativo
- deep links internos
- navegación contextual
- conservación de filtros y selección
- apertura de módulos sin cerrar el actual

## 12. Qué no hacer

- No trabajar directo en Producción.
- No eliminar RBAC.
- No convertir menú en fuente de permisos.
- No usar `sec_roles`, `sec_permisos` o `sec_perfil` como fuente primaria nueva.
- No consultar POS/SoftRestaurant/MPRO live desde endpoints de usuario.
- No inventar datos para llenar reportes.
- No hacer escrituras manuales productivas durante auditorías.
- No introducir módulos duplicados para evitar corregir el flujo existente.
- No reorganizar navegación sin mapa de producto.

