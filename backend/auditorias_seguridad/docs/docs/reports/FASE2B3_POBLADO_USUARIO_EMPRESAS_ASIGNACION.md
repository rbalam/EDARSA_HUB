# FASE 2-B3: POBLADO USUARIO_EMPRESASASIGNACION

**Fecha:** 14-Dic-2025  
**Estado:** COMPLETADO  
**Autor:** Agente E1 (Régimen de Autorización Controlada)

---

## 1. USUARIOS PROCESADOS (7)

| UsuarioID | Email | Empresas | Empresa Default |
|-----------|-------|----------|-----------------|
| 1 | admin@edarsa.com | 5 | ORIGEN |
| 2 | admin@inventario.com | 5 | ORIGEN |
| 3 | carlosruz@edarsa.com.mx | 5 | ORIGEN |
| 4 | noxte@alpyc.com | 5 | ORIGEN |
| 5 | auditoria@edarsa.com.mx | 5 | ORIGEN |
| 6 | almacen@cienfuegos.mx | 1 | CIENFUEGOS |
| 7 | administracion@cienfuegos.mx | 1 | CIENFUEGOS |

---

## 2. USUARIOS OMITIDOS (4)

| UsuarioID | Email | Motivo |
|-----------|-------|--------|
| 8 | ricardo@edarsa.com.mx | Sin empresas_permitidas en MongoDB |
| 9 | david.ricardez@cienfuegos.mx | Sin empresas_permitidas en MongoDB |
| 11 | carlos@alpuntoycoma.mx | Sin empresas_permitidas en MongoDB |
| 12 | eduardo@alpuntoycoma.mx | Sin empresas_permitidas en MongoDB |

**Nota:** Estos usuarios quedan pendientes de decisión explícita para asignación de empresas.

---

## 3. MOTIVO DE OMISIÓN

| Motivo | Usuarios | Acción |
|--------|----------|--------|
| Sin empresas_permitidas en MongoDB | 4 | No se asignaron empresas según directiva |

---

## 4. EMPRESAS ASIGNADAS POR USUARIO

### 4.1 Usuarios con 5 empresas (acceso global)

| Usuario | ORIGEN | 130QRO | CIENFUEGOS | ESTELAR | 130MID |
|---------|--------|--------|------------|---------|--------|
| admin@edarsa.com | ★ | ✓ | ✓ | ✓ | ✓ |
| admin@inventario.com | ★ | ✓ | ✓ | ✓ | ✓ |
| carlosruz@edarsa.com.mx | ★ | ✓ | ✓ | ✓ | ✓ |
| noxte@alpyc.com | ★ | ✓ | ✓ | ✓ | ✓ |
| auditoria@edarsa.com.mx | ★ | ✓ | ✓ | ✓ | ✓ |

### 4.2 Usuarios con 1 empresa (acceso limitado)

| Usuario | CIENFUEGOS |
|---------|------------|
| almacen@cienfuegos.mx | ★ |
| administracion@cienfuegos.mx | ★ |

**Leyenda:** ★ = Empresa Principal | ✓ = Empresa asignada

---

## 5. EMPRESA PRINCIPAL POR USUARIO

| Usuario | Empresa Principal | UUID MongoDB |
|---------|-------------------|--------------|
| admin@edarsa.com | ORIGEN | 31784356-6d0b-47ce-8fe8-c8a442e45a07 |
| admin@inventario.com | ORIGEN | 31784356-6d0b-47ce-8fe8-c8a442e45a07 |
| carlosruz@edarsa.com.mx | ORIGEN | 31784356-6d0b-47ce-8fe8-c8a442e45a07 |
| noxte@alpyc.com | ORIGEN | 31784356-6d0b-47ce-8fe8-c8a442e45a07 |
| auditoria@edarsa.com.mx | ORIGEN | 31784356-6d0b-47ce-8fe8-c8a442e45a07 |
| almacen@cienfuegos.mx | CIENFUEGOS | 1d91f076-a28e-49a5-b445-84aa767737b6 |
| administracion@cienfuegos.mx | CIENFUEGOS | 1d91f076-a28e-49a5-b445-84aa767737b6 |

---

## 6. ASIGNACIONES INSERTADAS (27)

| # | UsuarioID | Email | EmpresaID | Empresa | Principal |
|---|-----------|-------|-----------|---------|-----------|
| 1 | 1 | admin@edarsa.com | 1 | ORIGEN | ★ |
| 2 | 1 | admin@edarsa.com | 2 | 130QRO | |
| 3 | 1 | admin@edarsa.com | 3 | CIENFUEGOS | |
| 4 | 1 | admin@edarsa.com | 4 | ESTELAR | |
| 5 | 1 | admin@edarsa.com | 5 | 130MID | |
| 6 | 2 | admin@inventario.com | 1 | ORIGEN | ★ |
| 7 | 2 | admin@inventario.com | 2 | 130QRO | |
| 8 | 2 | admin@inventario.com | 3 | CIENFUEGOS | |
| 9 | 2 | admin@inventario.com | 4 | ESTELAR | |
| 10 | 2 | admin@inventario.com | 5 | 130MID | |
| 11 | 3 | carlosruz@edarsa.com.mx | 1 | ORIGEN | ★ |
| 12 | 3 | carlosruz@edarsa.com.mx | 2 | 130QRO | |
| 13 | 3 | carlosruz@edarsa.com.mx | 3 | CIENFUEGOS | |
| 14 | 3 | carlosruz@edarsa.com.mx | 4 | ESTELAR | |
| 15 | 3 | carlosruz@edarsa.com.mx | 5 | 130MID | |
| 16 | 4 | noxte@alpyc.com | 1 | ORIGEN | ★ |
| 17 | 4 | noxte@alpyc.com | 2 | 130QRO | |
| 18 | 4 | noxte@alpyc.com | 3 | CIENFUEGOS | |
| 19 | 4 | noxte@alpyc.com | 4 | ESTELAR | |
| 20 | 4 | noxte@alpyc.com | 5 | 130MID | |
| 21 | 5 | auditoria@edarsa.com.mx | 1 | ORIGEN | ★ |
| 22 | 5 | auditoria@edarsa.com.mx | 2 | 130QRO | |
| 23 | 5 | auditoria@edarsa.com.mx | 3 | CIENFUEGOS | |
| 24 | 5 | auditoria@edarsa.com.mx | 4 | ESTELAR | |
| 25 | 5 | auditoria@edarsa.com.mx | 5 | 130MID | |
| 26 | 6 | almacen@cienfuegos.mx | 3 | CIENFUEGOS | ★ |
| 27 | 7 | administracion@cienfuegos.mx | 3 | CIENFUEGOS | ★ |

---

## 7. VALIDACIÓN CONTRA SISTEMA_EMPRESASMONGOMAP

| UUID MongoDB | EmpresaID SQL | Código | Asignaciones |
|--------------|---------------|--------|--------------|
| 31784356-6d0b-47ce-8fe8-c8a442e45a07 | 1 | ORIGEN | 5 |
| 1118f83c-fd45-4681-8006-5e92dd6d01c1 | 2 | 130QRO | 5 |
| 1d91f076-a28e-49a5-b445-84aa767737b6 | 3 | CIENFUEGOS | 7 |
| e302e16f-2d97-4119-9ad9-bb5b00b71367 | 4 | ESTELAR | 5 |
| a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff | 5 | 130MID | 5 |

**Empresas no mapeadas:** 0 (todas resueltas vía Sistema_EmpresasMongoMap)

---

## 8. VALIDACIÓN DE DUPLICADOS

| Verificación | Resultado |
|--------------|-----------|
| Asignaciones duplicadas (mismo usuario + empresa) | 0 |
| Script idempotente | ✓ Verificado |

---

## 9. VALIDACIÓN DE EMPRESAS PRINCIPALES

| Verificación | Resultado |
|--------------|-----------|
| Usuarios con empresa principal | 7 de 7 |
| Usuarios con más de una empresa principal | 0 |
| Usuarios sin empresa principal | 0 |

---

## 10. EVIDENCIA DE NO REGRESIÓN

### 10.1 Archivos de código NO modificados

| Archivo | MD5 | Estado |
|---------|-----|--------|
| core/security.py | 66a841928ccb2d40d8f93a15f86e06be | Idéntico |
| modules/auth/repository.py | add919775f233265d4fbd6a7cd6c1a6e | Idéntico |
| modules/auth/service.py | 01693a1c6ca4e4e20edd7c8d6f2402ed | Idéntico |
| modules/auth/routes.py | 94caa2db6808241165e280b020dd1b26 | Idéntico |

### 10.2 Verificación de flujo de login

```
✓ MongoDB sigue siendo fuente de login
✓ Usuario admin@inventario.com encontrado
✓ role: SuperAdministrador
✓ empresas_permitidas: 5 empresas
✓ empresa_default_id: 31784356-6d0b-47ce-8...
```

### 10.3 Endpoints verificados

| Endpoint | Estado |
|----------|--------|
| Health check | ✓ Backend running |
| /api/servers (sin auth) | ✓ 403 (esperado) |

### 10.4 Confirmaciones

- [x] Login/JWT/get_current_user NO modificados
- [x] MongoDB sigue siendo fuente de autenticación
- [x] Solo se pobló Usuario_EmpresasAsignacion
- [x] No se modificaron Usuario_Catalogo ni Usuario_RolesAsignacion
- [x] No se crearon empresas nuevas

---

## 11. RIESGOS RESIDUALES

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | 4 usuarios SQL sin empresas asignadas | Media | Medio | Decidir asignación según rol/permisos deseados |
| R2 | ricardo@edarsa.com.mx es SuperAdmin sin empresas | Baja | Bajo | Posiblemente acceso global implícito por rol |

---

## 12. RECOMENDACIÓN PARA FASE 2-C

### 12.1 Estado actual de migración Auth/RBAC

| Tabla | Registros | Estado |
|-------|-----------|--------|
| Usuario_Catalogo | 11 | ✓ Completo |
| Usuario_Roles | 9 | ✓ Completo |
| Usuario_RolesAsignacion | 11 | ✓ Completo |
| Usuario_EmpresasAsignacion | 27 | ✓ Completo (7 usuarios) |
| Sistema_EmpresasMongoMap | 5 | ✓ Completo |
| Usuario_MigracionMongoTrace | 11 | ✓ Completo |

### 12.2 FASE 2-C: Validación post-migración

Próximos pasos sugeridos:
1. **Validación cruzada:** Comparar datos MongoDB vs SQL para cada usuario
2. **Verificación de integridad:** Confirmar que todos los mapeos son correctos
3. **Prueba de consistencia:** Ejecutar queries que simulen el comportamiento de auth

### 12.3 Decisiones pendientes para usuarios sin empresas

| Usuario | Rol SQL | Sugerencia |
|---------|---------|------------|
| ricardo@edarsa.com.mx | SUPERADMIN | Asignar todas las empresas o dejar sin restricción |
| david.ricardez@cienfuegos.mx | USUARIO | Evaluar si necesita empresa específica |
| carlos@alpuntoycoma.mx | ADMIN | Evaluar pertenencia organizacional |
| eduardo@alpuntoycoma.mx | ADMIN | Evaluar pertenencia organizacional |

---

## 13. CRITERIOS DE ACEPTACIÓN CUMPLIDOS

| Criterio | Estado |
|----------|--------|
| Solo se poblaron usuarios con empresas_permitidas | ✓ |
| No se asignaron empresas a usuarios sin empresas_permitidas | ✓ |
| No hay empresas no mapeadas | ✓ |
| No hay duplicados | ✓ |
| No hay más de una empresa principal por usuario | ✓ |
| Login/JWT/get_current_user no modificados | ✓ |
| MongoDB sigue siendo fuente de login | ✓ |
| Endpoints funcionando | ✓ |
| Reporte generado | ✓ |

---

**ESTADO:** FASE 2-B3 COMPLETADA — FASE 2 (MIGRACIÓN BASE AUTH/RBAC) COMPLETADA

*Documento generado bajo régimen de Autorización Controlada.*  
*Solo se ejecutó DML (INSERT) en Usuario_EmpresasAsignacion. No se modificó código de autenticación.*
