# FASE A2 — POBLADO Sistema_Empresas

**Documento:** Registro de Poblado de Catálogo de Empresas  
**Fecha:** 8 de Mayo 2026, 20:06 UTC  
**Estado:** ✅ EJECUTADO EXITOSAMENTE  
**Versión:** 1.0

---

## 1. RESUMEN

Se pobló exitosamente la tabla `Sistema_Empresas` en EDARSAHUB con las 5 empresas provenientes de MongoDB.

| Métrica | Valor |
|---------|-------|
| Empresas en MongoDB | 5 |
| Empresas insertadas en EDARSAHUB | 5 |
| Empresas omitidas (duplicados) | 0 |
| Errores | 0 |

**⚠️ Nota:** La tabla `Sistema_Empresas` NO tiene columna para almacenar el UUID de MongoDB. Se documenta la necesidad para fase futura, pero NO se ejecutó ALTER TABLE.

---

## 2. CONFIRMACIÓN DE AUTORIZACIÓN

| Autorización | Estado |
|--------------|--------|
| Poblar `Sistema_Empresas` | ✅ AUTORIZADO Y EJECUTADO |
| Actualizar `NivelJerarquia` | ❌ NO AUTORIZADO |
| Crear tabla de equivalencias UUID | ❌ NO AUTORIZADO |
| Poblar `Usuario_EmpresasAsignacion` | ❌ NO AUTORIZADO |
| Modificar código | ❌ NO AUTORIZADO |
| Modificar login/JWT | ❌ NO AUTORIZADO |

---

## 3. EMPRESAS ORIGEN EN MONGODB

### Campos disponibles en colección `empresas`:

- `id` (UUID)
- `codigo` (string)
- `nombre` (string)
- `razon_social` (string)
- `rfc` (string, vacío)
- `activa` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)

### Datos completos:

| # | MongoDB_ID | Código | Nombre | Razón Social | Activa |
|---|------------|--------|--------|--------------|--------|
| 1 | `31784356-6d0b-47ce-8fe8-c8a442e45a07` | ORIGEN | ORIGEN | Restaurante Origen S.A. de C.V. | ✅ |
| 2 | `1118f83c-fd45-4681-8006-5e92dd6d01c1` | 130QRO | 130 QRO | 130 Grados Querétaro S.A. de C.V. | ✅ |
| 3 | `1d91f076-a28e-49a5-b445-84aa767737b6` | CIENFUEGOS | CIENFUEGOS | Restaurante Cienfuegos S.A. de C.V. | ✅ |
| 4 | `e302e16f-2d97-4119-9ad9-bb5b00b71367` | ESTELAR | LA ESTELAR | La Estelar S.A. de C.V. | ✅ |
| 5 | `a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff` | 130MID | 130 MID | 130 Grados Mérida S.A. de C.V. | ✅ |

---

## 4. SCRIPT EJECUTADO

```sql
-- Insertado por Python con validación de duplicados
-- Para cada empresa de MongoDB:

INSERT INTO Sistema_Empresas (CodigoEmpresa, NombreEmpresa, NombreComercial, RFC, Activo, CreatedBy)
VALUES 
    ('ORIGEN', 'ORIGEN', 'Restaurante Origen S.A. de C.V.', NULL, 1, 'MIGRACION_FASE_A2'),
    ('130QRO', '130 QRO', '130 Grados Querétaro S.A. de C.V.', NULL, 1, 'MIGRACION_FASE_A2'),
    ('CIENFUEGOS', 'CIENFUEGOS', 'Restaurante Cienfuegos S.A. de C.V.', NULL, 1, 'MIGRACION_FASE_A2'),
    ('ESTELAR', 'LA ESTELAR', 'La Estelar S.A. de C.V.', NULL, 1, 'MIGRACION_FASE_A2'),
    ('130MID', '130 MID', '130 Grados Mérida S.A. de C.V.', NULL, 1, 'MIGRACION_FASE_A2');
```

**Notas:**
- Se usó `NombreComercial` para almacenar `razon_social` de MongoDB
- `RFC` se dejó NULL porque MongoDB tiene valores vacíos
- `CreatedBy` = 'MIGRACION_FASE_A2' para trazabilidad

---

## 5. REGISTROS INSERTADOS EN EDARSAHUB

| EmpresaID | CodigoEmpresa | NombreEmpresa | NombreComercial | RFC | Activo | FechaAlta | CreatedBy |
|-----------|---------------|---------------|-----------------|-----|--------|-----------|-----------|
| 1 | ORIGEN | ORIGEN | Restaurante Origen S.A. de C.V. | NULL | 1 | 2026-05-08 20:06:32 | MIGRACION_FASE_A2 |
| 2 | 130QRO | 130 QRO | 130 Grados Querétaro S.A. de C.V. | NULL | 1 | 2026-05-08 20:06:32 | MIGRACION_FASE_A2 |
| 3 | CIENFUEGOS | CIENFUEGOS | Restaurante Cienfuegos S.A. de C.V. | NULL | 1 | 2026-05-08 20:06:32 | MIGRACION_FASE_A2 |
| 4 | ESTELAR | LA ESTELAR | La Estelar S.A. de C.V. | NULL | 1 | 2026-05-08 20:06:32 | MIGRACION_FASE_A2 |
| 5 | 130MID | 130 MID | 130 Grados Mérida S.A. de C.V. | NULL | 1 | 2026-05-08 20:06:32 | MIGRACION_FASE_A2 |

---

## 6. MATRIZ MongoDB vs EDARSAHUB

| MongoDB_ID | MongoDB_Nombre | MongoDB_Codigo | EDARSAHUB_EmpresaID | EDARSAHUB_NombreEmpresa | EDARSAHUB_Codigo | Coincidencia | Observaciones |
|------------|----------------|----------------|---------------------|-------------------------|------------------|--------------|---------------|
| `31784356-6d0b-47ce-8fe8-c8a442e45a07` | ORIGEN | ORIGEN | 1 | ORIGEN | ORIGEN | ✅ | Insertado correctamente |
| `1118f83c-fd45-4681-8006-5e92dd6d01c1` | 130 QRO | 130QRO | 2 | 130 QRO | 130QRO | ✅ | Insertado correctamente |
| `1d91f076-a28e-49a5-b445-84aa767737b6` | CIENFUEGOS | CIENFUEGOS | 3 | CIENFUEGOS | CIENFUEGOS | ✅ | Insertado correctamente |
| `e302e16f-2d97-4119-9ad9-bb5b00b71367` | LA ESTELAR | ESTELAR | 4 | LA ESTELAR | ESTELAR | ✅ | Insertado correctamente |
| `a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff` | 130 MID | 130MID | 5 | 130 MID | 130MID | ✅ | Insertado correctamente |

### Mapeo de IDs (para referencia futura)

| MongoDB UUID | EDARSAHUB EmpresaID | Código |
|--------------|---------------------|--------|
| `31784356-6d0b-47ce-8fe8-c8a442e45a07` | 1 | ORIGEN |
| `1118f83c-fd45-4681-8006-5e92dd6d01c1` | 2 | 130QRO |
| `1d91f076-a28e-49a5-b445-84aa767737b6` | 3 | CIENFUEGOS |
| `e302e16f-2d97-4119-9ad9-bb5b00b71367` | 4 | ESTELAR |
| `a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff` | 5 | 130MID |

---

## 7. VALIDACIÓN DE DUPLICADOS

| Validación | Resultado |
|------------|-----------|
| Registros antes de inserción | 0 |
| Registros después de inserción | 5 |
| Incremento | 5 |
| Duplicados detectados | 0 |
| Errores de inserción | 0 |

✅ **No hubo duplicados ni errores.**

---

## 8. VALIDACIÓN FINAL DE CONTEOS

| Fuente | Tabla/Colección | Conteo |
|--------|-----------------|--------|
| MongoDB | `empresas` | 5 |
| EDARSAHUB | `Sistema_Empresas` | 5 |

✅ **Paridad perfecta: 5/5 empresas migradas.**

---

## 9. RIESGOS REMANENTES

| Riesgo | Severidad | Estado |
|--------|-----------|--------|
| `Sistema_Empresas` no tiene columna para MongoDB_ID | P2 | **Documentado** - No se hizo ALTER TABLE |
| `Usuario_EmpresasAsignacion` vacía | P1 | Pendiente poblar |
| MongoDB sigue siendo fuente principal | P1 | Correcto por diseño |
| Mapeo UUID→INT solo documentado, no persistido en BD | P2 | Requiere tabla de equivalencias o columna adicional |

### Necesidad Detectada (NO EJECUTADA)

Para trazabilidad completa, sería útil agregar columna `MongoDBUUID` a `Sistema_Empresas`:

```sql
-- NO EJECUTAR SIN AUTORIZACIÓN
ALTER TABLE Sistema_Empresas ADD MongoDBUUID UNIQUEIDENTIFIER NULL;
```

---

## 10. SIGUIENTE FASE RECOMENDADA

### Opción A: FASE A3 — Crear Tabla de Equivalencias

Crear tabla `Sistema_EmpresasEquivalencias` para mapear MongoDB UUID ↔ EDARSAHUB EmpresaID de forma persistente.

### Opción B: FASE A3 — Actualizar NivelJerarquia

Actualizar `Usuario_Roles.NivelJerarquia` con valores de MongoDB `rbac_roles`:

```sql
UPDATE Usuario_Roles SET NivelJerarquia = 100 WHERE CodigoRol = 'ADMIN';
UPDATE Usuario_Roles SET NivelJerarquia = 80 WHERE CodigoRol = 'GERENCIA';
-- etc.
```

### Opción C: FASE A3 — Poblar Usuario_EmpresasAsignacion

Requiere primero:
1. Migrar usuarios a `Usuario_Catalogo`
2. Tener tabla de equivalencias para mapear `empresas_permitidas` (UUIDs) a `EmpresaID` (INT)

---

## 11. AUTORIZACIÓN REQUERIDA

### Checklist de Siguiente Fase

| Paso | Descripción | Estado |
|------|-------------|--------|
| ✅ | Poblar `Sistema_Empresas` | COMPLETADO |
| ⬜ | Crear tabla de equivalencias UUID | **PENDIENTE AUTORIZACIÓN** |
| ⬜ | Agregar columna `MongoDBUUID` a `Sistema_Empresas` | **PENDIENTE AUTORIZACIÓN** |
| ⬜ | Actualizar `NivelJerarquia` en roles | **PENDIENTE AUTORIZACIÓN** |
| ⬜ | Migrar usuarios a `Usuario_Catalogo` | **PENDIENTE AUTORIZACIÓN** |
| ⬜ | Poblar `Usuario_EmpresasAsignacion` | **PENDIENTE AUTORIZACIÓN** |

---

## CONFIRMACIONES EXPLÍCITAS

| Confirmación | Estado |
|--------------|--------|
| ✅ 5 empresas insertadas correctamente | CONFIRMADO |
| ✅ NO se modificó código | CONFIRMADO |
| ✅ NO se migraron usuarios | CONFIRMADO |
| ✅ NO se migraron permisos | CONFIRMADO |
| ✅ NO se modificó login/JWT | CONFIRMADO |
| ✅ MongoDB sigue siendo fuente principal del sistema | CONFIRMADO |
| ✅ NO se ejecutó ALTER TABLE | CONFIRMADO |

---

**FIN DEL DOCUMENTO FASE A2**

*Poblado completado exitosamente. Siguiente fase requiere autorización expresa.*
