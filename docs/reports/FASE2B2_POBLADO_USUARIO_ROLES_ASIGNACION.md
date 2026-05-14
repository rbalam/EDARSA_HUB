# FASE 2-B2: POBLADO DE USUARIO_ROLESASIGNACION

**Fecha:** 14-Dic-2025  
**Estado:** COMPLETADO  
**Autor:** Agente E1 (Régimen de Autorización Controlada)

---

## 1. VALORES ROLE/ROL ENCONTRADOS EN MONGODB

### 1.1 Valores únicos

| Valor role | Cantidad | Ejemplo usuarios |
|------------|----------|------------------|
| SuperAdministrador | 4 | admin@inventario.com, ricardo@edarsa.com.mx, superadmin@test.com, superadmin2@test.com |
| Administrador | 4 | admin@edarsa.com, carlosruz@edarsa.com.mx, carlos@alpuntoycoma.mx, eduardo@alpuntoycoma.mx |
| Supervisor | 2 | noxte@alpyc.com, administracion@cienfuegos.mx |
| Usuario | 6 | auditoria@edarsa.com.mx, almacen@cienfuegos.mx, david.ricardez@cienfuegos.mx, + 3 test |
| DESHABILITADO | 1 | test_propinas@edarsa.com (inactivo, no migrado a SQL) |

### 1.2 Nota sobre campo `rol` vs `role`

El usuario `admin@edarsa.com` tiene un campo legacy `rol="SuperAdministrador"` además de `role="Administrador"`. 
Se usó el campo `role` como fuente principal ya que es el estándar actual del sistema.

---

## 2. MAPEO MONGODB ROL → SQL ROL

### 2.1 Mapeo aplicado

| Role MongoDB | RolID SQL | CodigoRol SQL | NombreRol SQL |
|--------------|-----------|---------------|---------------|
| SuperAdministrador | 6 | SUPERADMIN | SuperAdministrador |
| Administrador | 1 | ADMIN | Administrador |
| Supervisor | 7 | SUPERVISOR | Supervisor |
| Usuario | 8 | USUARIO | Usuario |
| Visor | 9 | VISOR | Visor |

### 2.2 Roles no mapeados

| Role MongoDB | Razón |
|--------------|-------|
| DESHABILITADO | Usuario inactivo, no migrado a SQL |

---

## 3. SCRIPT EJECUTADO

### 3.1 Lógica del script

```python
# FASE 2-B2: Poblar Usuario_RolesAsignacion
# - Leer usuarios SQL con trazabilidad MongoDB
# - Leer rol de MongoDB usando email
# - Mapear a RolID SQL
# - Insertar asignaciones
# - NO tocar Usuario_EmpresasAsignacion
# - NO modificar código de autenticación

MAPEO_ROLES = {
    'SuperAdministrador': 6,  # SUPERADMIN
    'Administrador': 1,       # ADMIN
    'Supervisor': 7,          # SUPERVISOR
    'Usuario': 8,             # USUARIO
    'Visor': 9,               # VISOR
}

# Para cada usuario SQL:
INSERT INTO Usuario_RolesAsignacion (
    UsuarioID, RolID, EsPrincipal, FechaInicio, Activo, CreatedAt, CreatedBy
) VALUES (
    <usuario_id>, <rol_id>, 1, GETUTCDATE(), 1, GETUTCDATE(), 'FASE2B2_MIGRATION'
)
```

### 3.2 Características

| Característica | Implementación |
|----------------|----------------|
| Idempotente | Verifica si usuario ya tiene rol asignado activo |
| EsPrincipal | 1 (rol único principal por usuario) |
| Activo | 1 (asignación vigente) |
| Trazabilidad | CreatedBy = 'FASE2B2_MIGRATION' |

---

## 4. ASIGNACIONES INSERTADAS (11)

| UsuarioID | Email | Role MongoDB | RolID SQL | CodigoRol SQL |
|-----------|-------|--------------|-----------|---------------|
| 1 | admin@edarsa.com | Administrador | 1 | ADMIN |
| 2 | admin@inventario.com | SuperAdministrador | 6 | SUPERADMIN |
| 3 | carlosruz@edarsa.com.mx | Administrador | 1 | ADMIN |
| 4 | noxte@alpyc.com | Supervisor | 7 | SUPERVISOR |
| 5 | auditoria@edarsa.com.mx | Usuario | 8 | USUARIO |
| 6 | almacen@cienfuegos.mx | Usuario | 8 | USUARIO |
| 7 | administracion@cienfuegos.mx | Supervisor | 7 | SUPERVISOR |
| 8 | ricardo@edarsa.com.mx | SuperAdministrador | 6 | SUPERADMIN |
| 9 | david.ricardez@cienfuegos.mx | Usuario | 8 | USUARIO |
| 11 | carlos@alpuntoycoma.mx | Administrador | 1 | ADMIN |
| 12 | eduardo@alpuntoycoma.mx | Administrador | 1 | ADMIN |

---

## 5. USUARIOS OMITIDOS (0)

Ningún usuario SQL fue omitido. Todos los 11 usuarios recibieron asignación de rol.

---

## 6. USUARIOS SIN ROL (0)

Ningún usuario quedó sin rol asignado.

---

## 7. USUARIOS CON ROL NO MAPEABLE (0)

Ningún usuario tenía un rol sin mapeo definido.

---

## 8. VALIDACIÓN SUPERADMINISTRADOR

### 8.1 SuperAdministradores preservados

| UsuarioID | Email | Role MongoDB | RolID SQL |
|-----------|-------|--------------|-----------|
| 2 | admin@inventario.com | SuperAdministrador | 6 (SUPERADMIN) |
| 8 | ricardo@edarsa.com.mx | SuperAdministrador | 6 (SUPERADMIN) |

### 8.2 Confirmación

**✓ 2 SuperAdministradores asignados correctamente**

---

## 9. CONTEOS ANTES/DESPUÉS

### 9.1 Usuario_Catalogo

| Métrica | Antes | Después | Cambio |
|---------|-------|---------|--------|
| Total usuarios | 11 | 11 | Sin cambios |

### 9.2 Usuario_Roles

| Métrica | Antes | Después | Cambio |
|---------|-------|---------|--------|
| Total roles | 9 | 9 | Sin cambios |

### 9.3 Usuario_RolesAsignacion

| Métrica | Antes | Después | Cambio |
|---------|-------|---------|--------|
| Total asignaciones | 0 | 11 | +11 nuevas |
| Asignaciones activas | 0 | 11 | +11 nuevas |

### 9.4 Usuario_EmpresasAsignacion

| Métrica | Antes | Después | Cambio |
|---------|-------|---------|--------|
| Total registros | 0 | 0 | Sin cambios |

### 9.5 Distribución de roles asignados

| CodigoRol | NombreRol | Usuarios |
|-----------|-----------|----------|
| ADMIN | Administrador | 4 |
| SUPERADMIN | SuperAdministrador | 2 |
| SUPERVISOR | Supervisor | 2 |
| USUARIO | Usuario | 3 |
| GERENCIA | Gerencia | 0 |
| COMPRAS | Compras | 0 |
| VENTAS | Ventas | 0 |
| TESORERIA | Tesoreria | 0 |
| VISOR | Visor | 0 |

---

## 10. EVIDENCIA DE NO REGRESIÓN

### 10.1 Archivos de código NO modificados

| Archivo | MD5 | Estado |
|---------|-----|--------|
| core/security.py | 66a841928ccb2d40d8f93a15f86e06be | Idéntico a FASE 2-B1 |
| modules/auth/repository.py | add919775f233265d4fbd6a7cd6c1a6e | Idéntico a FASE 2-B1 |
| modules/auth/service.py | 01693a1c6ca4e4e20edd7c8d6f2402ed | Idéntico a FASE 2-B1 |
| modules/auth/routes.py | 94caa2db6808241165e280b020dd1b26 | Idéntico a FASE 2-B1 |

### 10.2 Verificación de flujo de login

```
✓ MongoDB sigue siendo fuente de login
✓ Usuario admin@inventario.com encontrado en MongoDB
✓ role: SuperAdministrador
```

### 10.3 Endpoints verificados

| Endpoint | Estado |
|----------|--------|
| Health check | ✓ Backend running |
| /api/servers (sin auth) | ✓ 403 (esperado) |

### 10.4 Confirmaciones

- [x] Login/JWT/get_current_user NO modificados
- [x] MongoDB sigue siendo fuente de autenticación
- [x] EDARSAHUB SQL preparado pero NO activo para auth
- [x] Usuario_EmpresasAsignacion sigue vacía

---

## 11. RIESGOS RESIDUALES

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | Usuario admin@edarsa.com tiene rol="Administrador" pero rol legacy="SuperAdministrador" | Baja | Medio | Se usó campo `role` estándar. El usuario tiene ADMIN en SQL. |
| R2 | Roles GERENCIA, COMPRAS, VENTAS, TESORERIA, VISOR no tienen usuarios | Baja | Ninguno | Son roles canónicos, pueden usarse en futuro |

---

## 12. RECOMENDACIÓN PARA FASE 2-B3

### 12.1 Siguiente paso: Poblar Usuario_EmpresasAsignacion

El campo `empresas_permitidas` en MongoDB contiene UUIDs de empresas. Será necesario:

1. Crear tabla de mapeo `Empresas_MigracionMongoMap` si no existe
2. Mapear UUIDs de MongoDB a `EmpresaID` de SQL
3. Insertar asignaciones en `Usuario_EmpresasAsignacion`
4. Marcar empresa principal (`EsPrincipal=1`) usando `empresa_default_id`

### 12.2 Datos de MongoDB relevantes

```json
empresas_permitidas: [
    "uuid-empresa-1",
    "uuid-empresa-2",
    ...
]
empresa_default_id: "uuid-empresa-principal"
```

### 12.3 Decisiones pendientes

- [ ] Confirmar existencia de tabla `Empresas` en SQL
- [ ] Definir estrategia de mapeo UUID → EmpresaID
- [ ] Decidir si crear empresas faltantes en SQL

---

## 13. CRITERIOS DE ACEPTACIÓN CUMPLIDOS

| Criterio | Estado |
|----------|--------|
| 11 usuarios SQL productivos tienen rol asignado | ✓ |
| No hay roles inválidos | ✓ |
| No hay duplicados de asignación vigente | ✓ |
| SuperAdministrador preservado (2 usuarios) | ✓ |
| Usuario_EmpresasAsignacion sigue vacía | ✓ |
| Login/JWT/get_current_user no modificados | ✓ |
| MongoDB sigue siendo fuente de login | ✓ |
| Reporte generado | ✓ |

---

**ESTADO:** FASE 2-B2 COMPLETADA — ESPERANDO AUTORIZACIÓN PARA FASE 2-B3

*Documento generado bajo régimen de Autorización Controlada.*  
*Solo se ejecutó DML (INSERT) en EDARSAHUB. No se modificó código de autenticación.*
