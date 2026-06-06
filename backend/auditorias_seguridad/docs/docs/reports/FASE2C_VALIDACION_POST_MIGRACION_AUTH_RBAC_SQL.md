# FASE 2-C: VALIDACIÓN POST-MIGRACIÓN AUTH/RBAC SQL

**Fecha:** 14-Dic-2025  
**Estado:** COMPLETADO  
**Autor:** Agente E1 (Régimen de Autorización Controlada)

---

## 1. RESUMEN EJECUTIVO

La migración base Auth/RBAC de MongoDB hacia EDARSAHUB SQL ha sido validada integralmente. Los datos son consistentes, no hay duplicados críticos, y los mapeos son correctos.

| Aspecto | Estado |
|---------|--------|
| Usuarios migrados | 11 de 14 activos productivos |
| Roles asignados | 11 de 11 (100%) |
| Empresas asignadas | 27 asignaciones para 7 usuarios |
| Integridad de hashes | ✓ 100% bcrypt válidos |
| Integridad de UUIDs | ✓ 100% presentes |
| Código de auth | Sin modificar |
| MongoDB como fuente | Sigue activo |

**Usuarios omitidos de migración:** 3 activos @test.com + 3 inactivos = 6 total  
**Usuarios sin empresas en SQL:** 4 (ninguno tenía empresas en MongoDB)

---

## 2. CONTEOS MONGODB VS SQL

### 2.1 Usuarios

| Métrica | MongoDB | SQL | Diferencia |
|---------|---------|-----|------------|
| Total | 17 | 11 | -6 (omitidos) |
| Activos | 14 | 11 | -3 (@test.com) |
| Inactivos | 3 | 0 | -3 (no migrados) |

### 2.2 Roles

| Rol MongoDB | Cantidad | Rol SQL | Cantidad |
|-------------|----------|---------|----------|
| SuperAdministrador | 4 | SUPERADMIN | 2 |
| Administrador | 4 | ADMIN | 4 |
| Supervisor | 2 | SUPERVISOR | 2 |
| Usuario | 6 | USUARIO | 3 |
| DESHABILITADO | 1 | (excluido) | 0 |

**Nota:** 2 SuperAdministradores MongoDB son @test.com y no fueron migrados.

### 2.3 Empresas

| Métrica | MongoDB | SQL | Estado |
|---------|---------|-----|--------|
| Empresas definidas | 5 | 5 | ✓ 1:1 |
| Mapeos creados | - | 5 | ✓ Completo |
| Usuarios con empresas | 7 | 7 | ✓ Coincide |

---

## 3. MATRIZ USUARIO POR USUARIO

| UID | Email | SQL | Mongo | UUID | Hash | Rol SQL | Rol Mongo | Empresas |
|-----|-------|-----|-------|------|------|---------|-----------|----------|
| 1 | admin@edarsa.com | ✓ | ✓ | ✓ | ✓ | ADMIN | Administrador | 5 |
| 2 | admin@inventario.com | ✓ | ✓ | ✓ | ✓ | SUPERADMIN | SuperAdministrador | 5 |
| 3 | carlosruz@edarsa.com.mx | ✓ | ✓ | ✓ | ✓ | ADMIN | Administrador | 5 |
| 4 | noxte@alpyc.com | ✓ | ✓ | ✓ | ✓ | SUPERVISOR | Supervisor | 5 |
| 5 | auditoria@edarsa.com.mx | ✓ | ✓ | ✓ | ✓ | USUARIO | Usuario | 5 |
| 6 | almacen@cienfuegos.mx | ✓ | ✓ | ✓ | ✓ | USUARIO | Usuario | 1 |
| 7 | administracion@cienfuegos.mx | ✓ | ✓ | ✓ | ✓ | SUPERVISOR | Supervisor | 1 |
| 8 | ricardo@edarsa.com.mx | ✓ | ✓ | ✓ | ✓ | SUPERADMIN | SuperAdministrador | **0** |
| 9 | david.ricardez@cienfuegos.mx | ✓ | ✓ | ✓ | ✓ | USUARIO | Usuario | **0** |
| 11 | carlos@alpuntoycoma.mx | ✓ | ✓ | ✓ | ✓ | ADMIN | Administrador | **0** |
| 12 | eduardo@alpuntoycoma.mx | ✓ | ✓ | ✓ | ✓ | ADMIN | Administrador | **0** |

---

## 4. MATRIZ ROL MONGODB → ROL SQL

| Rol MongoDB | RolID SQL | Código SQL | Usuarios Migrados | Validación |
|-------------|-----------|------------|-------------------|------------|
| SuperAdministrador | 6 | SUPERADMIN | 2 de 4 | ✓ (2 @test.com omitidos) |
| Administrador | 1 | ADMIN | 4 de 4 | ✓ |
| Supervisor | 7 | SUPERVISOR | 2 de 2 | ✓ |
| Usuario | 8 | USUARIO | 3 de 6 | ✓ (3 test/inactivos omitidos) |
| DESHABILITADO | - | (excluido) | 0 de 1 | ✓ (inactivo) |

---

## 5. MATRIZ EMPRESAS MONGODB → SQL

| UUID MongoDB | Código | EmpresaID SQL | Asignaciones | Validación |
|--------------|--------|---------------|--------------|------------|
| 31784356-6d0b-47ce-8fe8-c8a442e45a07 | ORIGEN | 1 | 5 | ✓ |
| 1118f83c-fd45-4681-8006-5e92dd6d01c1 | 130QRO | 2 | 5 | ✓ |
| 1d91f076-a28e-49a5-b445-84aa767737b6 | CIENFUEGOS | 3 | 7 | ✓ |
| e302e16f-2d97-4119-9ad9-bb5b00b71367 | ESTELAR | 4 | 5 | ✓ |
| a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff | 130MID | 5 | 5 | ✓ |

**Total asignaciones:** 27  
**Empresas no mapeadas:** 0

---

## 6. USUARIOS CON INCONSISTENCIAS

### 6.1 Inconsistencias críticas
**Ninguna detectada.**

### 6.2 Inconsistencias menores

| Usuario | Inconsistencia | Impacto | Estado |
|---------|----------------|---------|--------|
| admin@edarsa.com | Tiene campo legacy `rol="SuperAdministrador"` además de `role="Administrador"` | Bajo | Se usó `role` como estándar |

---

## 7. USUARIOS OMITIDOS Y DECISIÓN PENDIENTE

### 7.1 Usuarios @test.com activos (NO migrados)

| Email | Rol Mongo | UUID | Razón | Decisión |
|-------|-----------|------|-------|----------|
| superadmin@test.com | SuperAdministrador | NO | Sin UUID | Excluir o crear manualmente |
| superadmin2@test.com | SuperAdministrador | SI | @test.com | Excluir o migrar con decisión explícita |
| usuario_test_portal@test.com | Usuario | SI | @test.com | Excluir |

### 7.2 Usuarios SQL sin empresas asignadas

| UID | Email | Rol SQL | Empresas Mongo | Riesgo SQL-first | Recomendación |
|-----|-------|---------|----------------|------------------|---------------|
| 8 | ricardo@edarsa.com.mx | SUPERADMIN | 0 | MEDIO | Definir regla SUPERADMIN |
| 9 | david.ricardez@cienfuegos.mx | USUARIO | 0 | BAJO | Evaluar si necesita empresas |
| 11 | carlos@alpuntoycoma.mx | ADMIN | 0 | BAJO | Evaluar si necesita empresas |
| 12 | eduardo@alpuntoycoma.mx | ADMIN | 0 | BAJO | Evaluar si necesita empresas |

**Análisis:** Ninguno de estos 4 usuarios tenía `empresas_permitidas` en MongoDB, por lo que su situación actual en SQL es **consistente** con MongoDB.

---

## 8. RIESGOS ANTES DE FASE 2-D

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | ricardo@edarsa.com.mx (SUPERADMIN) sin empresas podría perder acceso | Media | Alto | Definir regla SUPERADMIN antes de SQL-first |
| R2 | Usuarios @test.com intentan login y fallan | Baja | Bajo | Documentar que no están migrados |
| R3 | Campo `user['id']` en JWT cambia de UUID string a int | Baja | Medio | Usar PublicUUID en Auth repository SQL |

---

## 9. RECOMENDACIÓN SOBRE REGLA SUPERADMIN

### 9.1 Opciones evaluadas

| Opción | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| **A** | SUPERADMIN requiere asignaciones explícitas | Consistente con modelo RBAC | ricardo@ pierde acceso |
| **B** | SUPERADMIN tiene acceso global implícito | No requiere cambios | Menos control granular |
| **C** | Flag PermiteAccesoGlobal en Usuario_Catalogo | Flexible | Requiere DDL adicional |

### 9.2 Recomendación

**OPCIÓN B: SUPERADMIN tiene acceso global implícito.**

**Justificación:**
1. En el código actual de MongoDB, `get_user_empresas_permitidas()` ya verifica:
   ```python
   if user.get('role') == 'SuperAdministrador':
       # Retorna todas las empresas
   ```
2. Este comportamiento debe preservarse en SQL-first para evitar regresión.
3. ricardo@edarsa.com.mx ya opera así en producción.

### 9.3 Implementación sugerida para FASE 2-D

```python
def get_user_empresas_sql(user_id: int, rol_codigo: str) -> List[int]:
    if rol_codigo == 'SUPERADMIN':
        # Acceso global implícito
        return get_all_empresa_ids()
    else:
        # Consultar Usuario_EmpresasAsignacion
        return query_empresas_asignadas(user_id)
```

---

## 10. CHECKLIST PARA AUTORIZAR FASE 2-D

### 10.1 Validaciones completadas

- [x] Usuarios migrados con integridad de datos
- [x] Hashes bcrypt válidos (11/11)
- [x] UUIDs presentes (11/11)
- [x] MongoLegacyID presentes (11/11)
- [x] Roles asignados correctamente (11/11)
- [x] Empresas mapeadas (5/5)
- [x] Asignaciones de empresas (27/27)
- [x] Sin duplicados críticos
- [x] Sin emails inválidos
- [x] SuperAdministradores preservados (2/2 productivos)

### 10.2 Decisiones tomadas

- [x] Usuarios @test.com excluidos (documentado)
- [x] Usuarios inactivos excluidos (documentado)
- [x] 4 usuarios sin empresas documentados (consistente con MongoDB)

### 10.3 Decisiones pendientes

- [ ] Confirmar regla SUPERADMIN (recomendación: Opción B)
- [ ] Decidir si migrar superadmin2@test.com (tiene UUID válido)

### 10.4 Pre-requisitos para FASE 2-D

1. ✓ Migración base completada y validada
2. ✓ Sin inconsistencias críticas
3. ⚠ Definir regla SUPERADMIN
4. ✓ MongoDB sigue como fuente (no regresión)

---

## 11. EVIDENCIA DE NO REGRESIÓN

### 11.1 Código sin modificar

| Archivo | MD5 | Estado |
|---------|-----|--------|
| core/security.py | 66a841928ccb2d40d8f93a15f86e06be | Sin cambios |
| modules/auth/repository.py | add919775f233265d4fbd6a7cd6c1a6e | Sin cambios |
| modules/auth/service.py | 01693a1c6ca4e4e20edd7c8d6f2402ed | Sin cambios |
| modules/auth/routes.py | 94caa2db6808241165e280b020dd1b26 | Sin cambios |

### 11.2 Tablas sin modificar en esta fase

| Tabla | Registros | Estado |
|-------|-----------|--------|
| Usuario_Catalogo | 11 | Sin cambios |
| Usuario_RolesAsignacion | 11 | Sin cambios |
| Usuario_EmpresasAsignacion | 27 | Sin cambios |
| Sistema_EmpresasMongoMap | 5 | Sin cambios |

### 11.3 Endpoints verificados

| Endpoint | Estado |
|----------|--------|
| Health check | ✓ Backend running |
| /api/servers (sin auth) | ✓ 403 (esperado) |

### 11.4 Confirmaciones

- [x] Login sigue funcionando (MongoDB)
- [x] MongoDB sigue siendo fuente de autenticación
- [x] No se activó SQL-first
- [x] No se modificó frontend

---

## 12. CONCLUSIÓN

La migración base Auth/RBAC hacia EDARSAHUB SQL está **completa y validada**. 

Los datos son consistentes, no hay duplicados críticos, y todos los mapeos son correctos. Los 4 usuarios sin empresas en SQL reflejan su estado original en MongoDB.

**Recomendación:** Proceder con FASE 2-D (Auth repository SQL paralelo) una vez definida la regla SUPERADMIN.

---

**ESTADO:** FASE 2-C COMPLETADA — MIGRACIÓN BASE VALIDADA

*Documento generado bajo régimen de Autorización Controlada.*  
*No se modificó ningún dato ni código. Solo validación y documentación.*
