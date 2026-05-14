# FASE 2-B2.1: MAPEO EMPRESAS MONGODB → SQL

**Fecha:** 14-Dic-2025  
**Estado:** COMPLETADO  
**Autor:** Agente E1 (Régimen de Autorización Controlada)

---

## 1. EMPRESAS MONGODB ENCONTRADAS

### 1.1 Colección `empresas` (5 documentos)

| UUID | Código | Nombre | Razón Social | Activa |
|------|--------|--------|--------------|--------|
| 31784356-6d0b-47ce-8fe8-c8a442e45a07 | ORIGEN | ORIGEN | Restaurante Origen S.A. de C.V. | ✓ |
| 1118f83c-fd45-4681-8006-5e92dd6d01c1 | 130QRO | 130 QRO | 130 Grados Querétaro S.A. de C.V. | ✓ |
| 1d91f076-a28e-49a5-b445-84aa767737b6 | CIENFUEGOS | CIENFUEGOS | Restaurante Cienfuegos S.A. de C.V. | ✓ |
| e302e16f-2d97-4119-9ad9-bb5b00b71367 | ESTELAR | LA ESTELAR | La Estelar S.A. de C.V. | ✓ |
| a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff | 130MID | 130 MID | 130 Grados Mérida S.A. de C.V. | ✓ |

### 1.2 UUIDs usados en `db.users.empresas_permitidas`

Los mismos 5 UUIDs de la colección `empresas`:
- 31784356-6d0b-47ce-8fe8-c8a442e45a07 (ORIGEN)
- 1118f83c-fd45-4681-8006-5e92dd6d01c1 (130QRO)
- 1d91f076-a28e-49a5-b445-84aa767737b6 (CIENFUEGOS)
- e302e16f-2d97-4119-9ad9-bb5b00b71367 (ESTELAR)
- a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff (130MID)

---

## 2. EMPRESAS SQL ENCONTRADAS

### 2.1 Tabla `Sistema_Empresas` (5 registros)

| EmpresaID | Código | Nombre | Nombre Comercial | Activo |
|-----------|--------|--------|------------------|--------|
| 1 | ORIGEN | ORIGEN | Restaurante Origen S.A. de C.V. | ✓ |
| 2 | 130QRO | 130 QRO | 130 Grados Querétaro S.A. de C.V. | ✓ |
| 3 | CIENFUEGOS | CIENFUEGOS | Restaurante Cienfuegos S.A. de C.V. | ✓ |
| 4 | ESTELAR | LA ESTELAR | La Estelar S.A. de C.V. | ✓ |
| 5 | 130MID | 130 MID | 130 Grados Mérida S.A. de C.V. | ✓ |

---

## 3. CAMPOS USADOS PARA MAPEAR

| Campo MongoDB | Campo SQL | Método |
|---------------|-----------|--------|
| `codigo` | `CodigoEmpresa` | CODIGO_EXACTO |

**Justificación:** Los códigos son idénticos en ambas bases de datos (ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID), lo que permite un mapeo 1:1 sin ambigüedad.

---

## 4. TABLA DE EQUIVALENCIAS MONGODB → SQL

### 4.1 Mapeos creados en `Sistema_EmpresasMongoMap`

| MapID | UUID MongoDB | ObjectID MongoDB | EmpresaID SQL | Código | Nombre | Método |
|-------|--------------|------------------|---------------|--------|--------|--------|
| 1 | 31784356-6d0b-47ce-8fe8-c8a442e45a07 | 69e4531f2bb150c941d48981 | 1 | ORIGEN | ORIGEN | CODIGO_EXACTO |
| 2 | 1118f83c-fd45-4681-8006-5e92dd6d01c1 | 69e4531f2bb150c941d48982 | 2 | 130QRO | 130 QRO | CODIGO_EXACTO |
| 3 | 1d91f076-a28e-49a5-b445-84aa767737b6 | 69e4531f2bb150c941d48983 | 3 | CIENFUEGOS | CIENFUEGOS | CODIGO_EXACTO |
| 4 | e302e16f-2d97-4119-9ad9-bb5b00b71367 | 69e4531f2bb150c941d48984 | 4 | ESTELAR | LA ESTELAR | CODIGO_EXACTO |
| 5 | a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff | 69e4531f2bb150c941d48985 | 5 | 130MID | 130 MID | CODIGO_EXACTO |

---

## 5. EMPRESAS SIN MAPEO

**Ninguna.** Todas las 5 empresas de MongoDB tienen equivalencia en SQL.

---

## 6. EMPRESAS AMBIGUAS

**Ninguna.** Cada código de MongoDB tiene exactamente una correspondencia en SQL.

---

## 7. USUARIOS AFECTADOS POR CADA EMPRESA

### 7.1 Usuarios con empresas_permitidas (7 usuarios)

| Usuario | Empresas | Empresa Default |
|---------|----------|-----------------|
| admin@edarsa.com | ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID (5) | ORIGEN |
| admin@inventario.com | ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID (5) | ORIGEN |
| carlosruz@edarsa.com.mx | ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID (5) | ORIGEN |
| noxte@alpyc.com | ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID (5) | ORIGEN |
| auditoria@edarsa.com.mx | ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID (5) | ORIGEN |
| almacen@cienfuegos.mx | CIENFUEGOS (1) | CIENFUEGOS |
| administracion@cienfuegos.mx | CIENFUEGOS (1) | CIENFUEGOS |

### 7.2 Usuarios SIN empresas_permitidas (4 usuarios SQL)

| Usuario | Razón |
|---------|-------|
| ricardo@edarsa.com.mx | SuperAdmin sin restricción de empresas |
| david.ricardez@cienfuegos.mx | Usuario sin empresas asignadas en MongoDB |
| carlos@alpuntoycoma.mx | Usuario nuevo sin empresas asignadas |
| eduardo@alpuntoycoma.mx | Usuario nuevo sin empresas asignadas |

**Nota:** Los usuarios sin `empresas_permitidas` en MongoDB podrían tener acceso global o requerir asignación manual.

---

## 8. SCRIPT DDL - TABLA DE MAPEO

```sql
-- FASE 2-B2.1: Crear tabla Sistema_EmpresasMongoMap
-- Ejecutado: 14-Dic-2025

CREATE TABLE dbo.Sistema_EmpresasMongoMap (
    MapID INT IDENTITY(1,1) PRIMARY KEY,
    EmpresaMongoUUID VARCHAR(50) NOT NULL,
    EmpresaMongoLegacyID VARCHAR(50) NULL,
    EmpresaID_SQL INT NOT NULL,
    CodigoEmpresa VARCHAR(20) NOT NULL,
    NombreEmpresa NVARCHAR(100) NOT NULL,
    MetodoMapeo VARCHAR(50) NOT NULL DEFAULT 'CODIGO_EXACTO',
    Activo BIT NOT NULL DEFAULT 1,
    FechaCreacion DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaActualizacion DATETIME2 NULL,
    Observaciones NVARCHAR(500) NULL,
    CreatedBy VARCHAR(100) NOT NULL DEFAULT 'FASE2B21_MIGRATION',
    
    CONSTRAINT UQ_EmpresaMongoUUID UNIQUE (EmpresaMongoUUID),
    CONSTRAINT FK_EmpresaID_SQL FOREIGN KEY (EmpresaID_SQL) 
        REFERENCES Sistema_Empresas(EmpresaID)
);
```

---

## 9. SCRIPT DE POBLADO DEL MAPEO

```sql
-- FASE 2-B2.1: Poblar mapeos
-- Ejecutado: 14-Dic-2025

INSERT INTO Sistema_EmpresasMongoMap (
    EmpresaMongoUUID, EmpresaMongoLegacyID, EmpresaID_SQL, 
    CodigoEmpresa, NombreEmpresa, MetodoMapeo, Activo, 
    Observaciones, CreatedBy
) VALUES 
('31784356-6d0b-47ce-8fe8-c8a442e45a07', '69e4531f2bb150c941d48981', 1, 'ORIGEN', 'ORIGEN', 'CODIGO_EXACTO', 1, 'Mapeo automático por código exacto', 'FASE2B21_MIGRATION'),
('1118f83c-fd45-4681-8006-5e92dd6d01c1', '69e4531f2bb150c941d48982', 2, '130QRO', '130 QRO', 'CODIGO_EXACTO', 1, 'Mapeo automático por código exacto', 'FASE2B21_MIGRATION'),
('1d91f076-a28e-49a5-b445-84aa767737b6', '69e4531f2bb150c941d48983', 3, 'CIENFUEGOS', 'CIENFUEGOS', 'CODIGO_EXACTO', 1, 'Mapeo automático por código exacto', 'FASE2B21_MIGRATION'),
('e302e16f-2d97-4119-9ad9-bb5b00b71367', '69e4531f2bb150c941d48984', 4, 'ESTELAR', 'LA ESTELAR', 'CODIGO_EXACTO', 1, 'Mapeo automático por código exacto', 'FASE2B21_MIGRATION'),
('a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff', '69e4531f2bb150c941d48985', 5, '130MID', '130 MID', 'CODIGO_EXACTO', 1, 'Mapeo automático por código exacto', 'FASE2B21_MIGRATION');
```

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
```

### 10.3 Endpoints verificados

| Endpoint | Estado |
|----------|--------|
| Health check | ✓ Backend running |
| /api/servers (sin auth) | ✓ 403 (esperado) |

### 10.4 Confirmaciones

- [x] Login/JWT/get_current_user NO modificados
- [x] MongoDB sigue siendo fuente de autenticación
- [x] Usuario_EmpresasAsignacion sigue vacía (0 registros)
- [x] No se crearon empresas nuevas en SQL
- [x] No se modificaron usuarios ni roles

---

## 11. RIESGOS RESIDUALES

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | 4 usuarios SQL sin empresas_permitidas | Media | Medio | Decidir si asignar todas las empresas o dejarlos sin restricción |
| R2 | Usuarios con empresa_default_id que no existe en sus empresas_permitidas | Baja | Bajo | Validar en FASE 2-B3 |

---

## 12. RECOMENDACIÓN PARA AUTORIZAR FASE 2-B3

### 12.1 Pre-requisitos cumplidos

- [x] Tabla `Sistema_EmpresasMongoMap` creada
- [x] 5 mapeos creados (todas las empresas operativas)
- [x] Sin ambigüedades ni conflictos
- [x] Sin empresas sin mapeo

### 12.2 Acciones para FASE 2-B3

1. Para cada usuario SQL con `empresas_permitidas` en MongoDB:
   - Leer UUIDs de empresas desde MongoDB
   - Convertir a EmpresaID_SQL usando `Sistema_EmpresasMongoMap`
   - Insertar en `Usuario_EmpresasAsignacion`
   - Marcar `EsPrincipal=1` para `empresa_default_id`

2. Decisión requerida para usuarios sin empresas_permitidas:
   - **Opción A:** Asignar todas las 5 empresas (acceso global)
   - **Opción B:** No asignar empresas (el sistema usa otra lógica)
   - **Opción C:** Asignar según rol (SuperAdmin = todas, otros = ninguna)

### 12.3 Usuarios a procesar en FASE 2-B3

| Usuario | Acción |
|---------|--------|
| admin@edarsa.com | 5 asignaciones (default: ORIGEN) |
| admin@inventario.com | 5 asignaciones (default: ORIGEN) |
| carlosruz@edarsa.com.mx | 5 asignaciones (default: ORIGEN) |
| noxte@alpyc.com | 5 asignaciones (default: ORIGEN) |
| auditoria@edarsa.com.mx | 5 asignaciones (default: ORIGEN) |
| almacen@cienfuegos.mx | 1 asignación (default: CIENFUEGOS) |
| administracion@cienfuegos.mx | 1 asignación (default: CIENFUEGOS) |
| ricardo@edarsa.com.mx | Decisión pendiente |
| david.ricardez@cienfuegos.mx | Decisión pendiente |
| carlos@alpuntoycoma.mx | Decisión pendiente |
| eduardo@alpuntoycoma.mx | Decisión pendiente |

---

## 13. CRITERIOS DE ACEPTACIÓN CUMPLIDOS

| Criterio | Estado |
|----------|--------|
| Mapeo validado MongoDB → SQL | ✓ |
| 5 empresas operativas con equivalencia SQL clara | ✓ |
| Sin mapeos ambiguos | ✓ |
| Usuario_EmpresasAsignacion sigue vacía | ✓ |
| Login/JWT/get_current_user no modificados | ✓ |
| Frontend no modificado | ✓ |
| Login y módulos funcionando | ✓ |
| Reporte generado | ✓ |

---

**ESTADO:** FASE 2-B2.1 COMPLETADA — ESPERANDO AUTORIZACIÓN PARA FASE 2-B3

*Documento generado bajo régimen de Autorización Controlada.*  
*Solo se ejecutó DDL (CREATE TABLE) y DML (INSERT) para tabla de mapeo. No se modificó código de autenticación.*
