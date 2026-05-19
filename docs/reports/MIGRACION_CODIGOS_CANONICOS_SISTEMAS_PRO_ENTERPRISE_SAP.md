# MIGRACIÓN DE CÓDIGOS CANÓNICOS DE SISTEMAS
## SOFTRESTAURANT_PRO | ENTERPRISE | SAP_BUSINESS_ONE

**Fecha:** 2026-05-19  
**Prioridad:** P0  
**Estado:** EN PROGRESO  
**Autorización:** Controlada - Explícita del usuario

---

## FASE 1: DIAGNÓSTICO COMPLETO

### 1.1 Estado Actual de Sistema_Catalogo

| SistemaID | Codigo (actual) | Descripcion (actual) | Activo |
|-----------|-----------------|----------------------|--------|
| 1 | `MPRO` | ManagementPro (MPRO) | ✅ |
| 2 | `SOFTRESTAURANT` | SoftRestaurant | ✅ |
| 3 | `OTRO` | Otro | ✅ |
| 4 | `SAP_BUSINESS_ONE` | SAP Business One | ✅ |
| 5 | `SOFRESATAURANT_ENTER` | Sofresataurant Enterprise | ✅ |

### 1.2 Estado Actual de Sistema_Tipos (Capacidades)

| SistemaTipoID | CodigoSistema | NombreSistema | Usado por |
|---------------|---------------|---------------|-----------|
| 1 | `SOFTRESTAURANT` | SoftRestaurant | Catálogo SQL, Explorador BD |
| 2 | `MPRO` | ManagementPro | Catálogo SQL, Explorador BD |
| 3 | `API_LOCAL` | API Local | Enterprise (via variante) |
| 4 | `EDARSAHUB_SQL` | EDARSAHUB SQL Server | Interno |

### 1.3 Estado Actual de Sistema_TiposVariantes

| Variante | Se normaliza a | EsCanónico |
|----------|----------------|------------|
| `SOFTRESTAURANT` | SOFTRESTAURANT (ID=1) | ✅ Sí |
| `MPRO` | MPRO (ID=2) | ✅ Sí |
| `API_LOCAL` | API_LOCAL (ID=3) | ✅ Sí |
| `SOFRESATAURANT_ENTER` | API_LOCAL (ID=3) | ❌ No |
| `ENTERPRISE` | API_LOCAL (ID=3) | ❌ No |
| `SOFTRESTAURANT_PRO` | **NO EXISTE** | N/A |

### 1.4 Referencias en Servidores_Conexiones

```
Conexión: 130° MERIDA
  - system_type: SoftRestaurant
  - tipo_conexion: DATA_SOURCE

Conexión: CHAPUR BACKOFFICE
  - system_type: SOFRESATAURANT_ENTER  <-- Código con typo histórico
  - tipo_conexion: API_LOCAL

Conexión: CHAPUR NORTE
  - system_type: SOFRESATAURANT_ENTER  <-- Código con typo histórico
  - tipo_conexion: API_LOCAL

Conexión: CIENFUEGOS
  - system_type: SoftRestaurant
  - tipo_conexion: DATA_SOURCE
```

### 1.5 Referencias en ConsultasSQL_Catalogo

| SistemaTipoID | Codigo | Total Consultas |
|---------------|--------|-----------------|
| 1 | SOFTRESTAURANT | 14 |
| 2 | MPRO | 6 |

**NOTA:** No hay consultas SQL asociadas directamente a `SOFRESATAURANT_ENTER` porque este se usa como `system_type` en servidores, no como `SistemaTipoID` en consultas.

### 1.6 Referencias en Código Backend

| Archivo | Línea | Referencia | Acción requerida |
|---------|-------|------------|------------------|
| `server.py` | 9566 | `SOFRESATAURANT_ENTER` (comentario) | Actualizar comentario |
| `server.py` | 9587 | `SOFRESATAURANT_ENTER` (CASE WHEN) | **MIGRAR a ENTERPRISE** |
| `api/catalogos_sistemas.py` | 205 | `SOFRESATAURANT_ENTER` (comentario) | Actualizar comentario |
| `api/catalogos_sistemas.py` | 216 | `SOFRESATAURANT_ENTER` (CASE WHEN) | **MIGRAR a ENTERPRISE** |
| `scripts/validate_*.py` | varios | `SOFRESATAURANT_ENTER` | Actualizar scripts |
| `system_capability_resolver.py` | 233 | `SOFRESATAURANT_ENTER` (docstring) | Actualizar docstring |
| `system_capability_integration.py` | 47 | `SOFRESATAURANT_ENTER` (docstring) | Actualizar docstring |

### 1.7 Referencias en Código Frontend

| Archivo | Línea | Referencia | Acción requerida |
|---------|-------|------------|------------------|
| `ExploradorBD.js` | 808 | `SOFRESATAURANT_ENTER` (comentario) | Actualizar comentario |
| `useCatalogoConsultasData.js` | 104 | `SOFRESATAURANT_ENTER` (comentario) | Actualizar comentario |
| `CatalogoConsultas.js` | 171 | `SAP_BUSINESS_ONE` | ✅ OK (sin cambios) |
| `Servidores.js` | 2996 | `SAP Business One` (placeholder) | ✅ OK (sin cambios) |

### 1.8 Referencias en core/system_type_utils.py

```python
SYSTEM_TYPE_MAP = {
    # NO tiene ENTERPRISE ni SOFTRESTAURANT_PRO
    # Solo mapea variantes a MANAGEMENTPRO, SOFTRESTAURANT, API
}
```

**Acción:** Este archivo NO necesita cambios directos porque el nuevo flujo usa `Sistema_TiposVariantes` de SQL Server.

---

## FASE 2: MAPEO CANÓNICO FINAL

### 2.1 Tabla de Migración Autorizada

| Código Actual | Código Final | Descripción Final | Notas |
|---------------|--------------|-------------------|-------|
| `SOFTRESTAURANT` | `SOFTRESTAURANT_PRO` | SoftRestaurant Pro | Cambio de código y descripción |
| `SAP_BUSINESS_ONE` | `SAP_BUSINESS_ONE` | SAP Business One | Sin cambio en código |
| `SOFRESATAURANT_ENTER` | `ENTERPRISE` | Enterprise | Corrige typo histórico |

### 2.2 Reglas de Compatibilidad

1. Los códigos antiguos deben seguir funcionando como alias/variantes
2. `SOFTRESTAURANT` → `SOFTRESTAURANT_PRO` (alias temporal)
3. `SOFRESATAURANT_ENTER` → `ENTERPRISE` (alias permanente para datos históricos)
4. `SOFTRESTAURANT_ENTERPRISE` → `ENTERPRISE` (si existe)

---

## FASE 3: PLAN DE MIGRACIÓN SQL

### 3.1 Pre-condiciones

- [ ] Backup de tablas afectadas
- [ ] Validar que no hay FK que bloqueen el UPDATE
- [ ] Script idempotente (puede ejecutarse múltiples veces)

### 3.2 Script SQL Propuesto (Requiere autorización explícita)

```sql
-- ==============================================================
-- MIGRACIÓN CÓDIGOS CANÓNICOS DE SISTEMAS
-- Fecha: 2026-05-19
-- Autorización: Requerida antes de ejecutar
-- ==============================================================

BEGIN TRANSACTION;

-- 1. ACTUALIZAR Sistema_Catalogo
-- ---------------------------------------------------------------

-- 1.1 SOFTRESTAURANT → SOFTRESTAURANT_PRO
UPDATE Sistema_Catalogo
SET Codigo = 'SOFTRESTAURANT_PRO',
    Descripcion = 'SoftRestaurant Pro',
    FechaActualizacion = GETDATE()
WHERE Codigo = 'SOFTRESTAURANT';

-- 1.2 SAP_BUSINESS_ONE: Solo actualizar descripción si difiere
UPDATE Sistema_Catalogo
SET Descripcion = 'SAP Business One',
    FechaActualizacion = GETDATE()
WHERE Codigo = 'SAP_BUSINESS_ONE'
  AND Descripcion != 'SAP Business One';

-- 1.3 SOFRESATAURANT_ENTER → ENTERPRISE
UPDATE Sistema_Catalogo
SET Codigo = 'ENTERPRISE',
    Descripcion = 'Enterprise',
    FechaActualizacion = GETDATE()
WHERE Codigo = 'SOFRESATAURANT_ENTER';

-- 2. ACTUALIZAR Sistema_Tipos (si tiene referencias por Codigo)
-- ---------------------------------------------------------------

-- 2.1 SOFTRESTAURANT → SOFTRESTAURANT_PRO
UPDATE Sistema_Tipos
SET CodigoSistema = 'SOFTRESTAURANT_PRO',
    NombreSistema = 'SoftRestaurant Pro'
WHERE CodigoSistema = 'SOFTRESTAURANT';

-- 2.2 Verificar/Actualizar SAP si existe
UPDATE Sistema_Tipos
SET NombreSistema = 'SAP Business One'
WHERE CodigoSistema = 'SAP_BUSINESS_ONE'
  AND NombreSistema != 'SAP Business One';

-- 3. CREAR/ACTUALIZAR VARIANTES DE COMPATIBILIDAD
-- ---------------------------------------------------------------

-- 3.1 Variante SOFTRESTAURANT → SOFTRESTAURANT_PRO
IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'SOFTRESTAURANT')
BEGIN
    INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico, Activo)
    SELECT SistemaTipoID, 'SOFTRESTAURANT', 0, 1
    FROM Sistema_Tipos WHERE CodigoSistema = 'SOFTRESTAURANT_PRO';
END

-- 3.2 Variante SOFTRESTAURANT_PRO (canónica)
IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'SOFTRESTAURANT_PRO')
BEGIN
    INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico, Activo)
    SELECT SistemaTipoID, 'SOFTRESTAURANT_PRO', 1, 1
    FROM Sistema_Tipos WHERE CodigoSistema = 'SOFTRESTAURANT_PRO';
END

-- 3.3 Variante SOFRESATAURANT_ENTER → ENTERPRISE (alias histórico)
-- Primero crear registro ENTERPRISE en Sistema_Tipos si no existe
IF NOT EXISTS (SELECT 1 FROM Sistema_Tipos WHERE CodigoSistema = 'ENTERPRISE')
BEGIN
    INSERT INTO Sistema_Tipos (CodigoSistema, NombreSistema, Descripcion, Activo)
    VALUES ('ENTERPRISE', 'Enterprise', 'Sofrestaurant Enterprise', 1);
END

-- Variante canónica ENTERPRISE
IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'ENTERPRISE')
BEGIN
    INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico, Activo)
    SELECT SistemaTipoID, 'ENTERPRISE', 1, 1
    FROM Sistema_Tipos WHERE CodigoSistema = 'ENTERPRISE';
END

-- Variante alias SOFRESATAURANT_ENTER → ENTERPRISE
UPDATE Sistema_TiposVariantes
SET SistemaTipoID = (SELECT SistemaTipoID FROM Sistema_Tipos WHERE CodigoSistema = 'ENTERPRISE'),
    EsCanonico = 0
WHERE VarianteNombre = 'SOFRESATAURANT_ENTER';

-- 4. ACTUALIZAR Servidores_Conexiones (system_type)
-- ---------------------------------------------------------------

-- 4.1 Servidores SoftRestaurant estándar → SOFTRESTAURANT_PRO
UPDATE Servidores_Conexiones
SET system_type = 'SOFTRESTAURANT_PRO'
WHERE UPPER(system_type) IN ('SOFTRESTAURANT', 'SOFT_RESTAURANT', 'SR')
  AND tipo_conexion NOT IN ('CORE', 'HUB');

-- 4.2 Servidores Enterprise (Chapur) → ENTERPRISE
UPDATE Servidores_Conexiones
SET system_type = 'ENTERPRISE'
WHERE UPPER(system_type) IN ('SOFRESATAURANT_ENTER', 'SOFTRESTAURANT_ENTER', 'SOFTRESTAURANT_ENTERPRISE');

-- 5. ACTUALIZAR ConsultasSQL_Catalogo (si tiene referencias por código)
-- ---------------------------------------------------------------
-- NOTA: ConsultasSQL_Catalogo usa SistemaTipoID (FK), no Codigo
-- Por lo tanto NO requiere UPDATE directo si Sistema_Tipos mantiene el mismo ID

-- 6. VERIFICACIÓN POST-MIGRACIÓN
-- ---------------------------------------------------------------

-- Verificar Sistema_Catalogo
SELECT SistemaID, Codigo, Descripcion, Activo FROM Sistema_Catalogo ORDER BY SistemaID;

-- Verificar Sistema_Tipos
SELECT SistemaTipoID, CodigoSistema, NombreSistema FROM Sistema_Tipos ORDER BY SistemaTipoID;

-- Verificar Variantes
SELECT sv.VarianteNombre, st.CodigoSistema, sv.EsCanonico, sv.Activo
FROM Sistema_TiposVariantes sv
JOIN Sistema_Tipos st ON sv.SistemaTipoID = st.SistemaTipoID
ORDER BY st.CodigoSistema, sv.VarianteNombre;

-- Verificar Servidores
SELECT id, nombre, system_type, tipo_conexion
FROM Servidores_Conexiones
WHERE activo = 1
ORDER BY nombre;

COMMIT TRANSACTION;
```

---

## FASE 4: CAMBIOS EN CÓDIGO (Post-SQL)

### 4.1 Backend - server.py (líneas 9587-9593)

**Antes:**
```python
CASE 
    WHEN UPPER(sc.system_type) = 'SOFRESATAURANT_ENTER' THEN 'Sofrestaurant Enterprise'
    WHEN UPPER(sc.system_type) = 'SOFTRESTAURANT' THEN 'SoftRestaurant'
```

**Después:**
```python
CASE 
    WHEN UPPER(sc.system_type) = 'ENTERPRISE' THEN 'Enterprise'
    WHEN UPPER(sc.system_type) = 'SOFRESATAURANT_ENTER' THEN 'Enterprise'  -- Alias temporal
    WHEN UPPER(sc.system_type) = 'SOFTRESTAURANT_PRO' THEN 'SoftRestaurant Pro'
    WHEN UPPER(sc.system_type) = 'SOFTRESTAURANT' THEN 'SoftRestaurant Pro'  -- Alias temporal
```

### 4.2 Backend - api/catalogos_sistemas.py (líneas 216-220)

Misma actualización que server.py.

### 4.3 Actualización de comentarios/docstrings

Archivos a actualizar (solo comentarios, sin impacto funcional):
- `server.py` línea 9566
- `api/catalogos_sistemas.py` línea 205
- `scripts/validate_*.py`
- `system_capability_resolver.py` línea 233
- `system_capability_integration.py` línea 47
- `ExploradorBD.js` línea 808
- `useCatalogoConsultasData.js` línea 104

---

## FASE 5: VALIDACIÓN POST-MIGRACIÓN

### 5.1 Validación SQL

```sql
-- Debe mostrar los nuevos códigos
SELECT Codigo, Descripcion FROM Sistema_Catalogo 
WHERE Codigo IN ('SOFTRESTAURANT_PRO', 'ENTERPRISE', 'SAP_BUSINESS_ONE');

-- Debe mostrar los alias funcionando
SELECT sv.VarianteNombre, st.CodigoSistema 
FROM Sistema_TiposVariantes sv
JOIN Sistema_Tipos st ON sv.SistemaTipoID = st.SistemaTipoID
WHERE sv.VarianteNombre IN ('SOFTRESTAURANT', 'SOFRESATAURANT_ENTER');
```

### 5.2 Validación Endpoints (cURL)

```bash
# Diagnóstico de normalización
curl /api/catalogos/sistemas-capacidades/diagnostico/SOFTRESTAURANT
# Debe retornar: codigo_sistema = SOFTRESTAURANT_PRO

curl /api/catalogos/sistemas-capacidades/diagnostico/ENTERPRISE
# Debe retornar: codigo_sistema = ENTERPRISE

curl /api/catalogos/sistemas-capacidades/diagnostico/SOFRESATAURANT_ENTER
# Debe retornar: codigo_sistema = ENTERPRISE (via alias)
```

### 5.3 Validación UI

| Módulo | Validación | Esperado |
|--------|------------|----------|
| Catálogos del Sistema | `/catalogos/sistemas` | SOFTRESTAURANT_PRO, ENTERPRISE, SAP_BUSINESS_ONE |
| Catálogo SQL | Filtro sistema | SoftRestaurant Pro (sin mezclar con Enterprise) |
| Explorador BD | Primer filtro | SoftRestaurant Pro, Enterprise (separados) |
| Servidores | Lista | CHAPUR = ENTERPRISE, 130° = SOFTRESTAURANT_PRO |

---

## FASE 6: BACKOUT PLAN

```sql
-- ROLLBACK si es necesario
BEGIN TRANSACTION;

-- Revertir Sistema_Catalogo
UPDATE Sistema_Catalogo SET Codigo = 'SOFTRESTAURANT', Descripcion = 'SoftRestaurant' 
WHERE Codigo = 'SOFTRESTAURANT_PRO';

UPDATE Sistema_Catalogo SET Codigo = 'SOFRESATAURANT_ENTER', Descripcion = 'Sofresataurant Enterprise' 
WHERE Codigo = 'ENTERPRISE';

-- Revertir Servidores_Conexiones
UPDATE Servidores_Conexiones SET system_type = 'SoftRestaurant' 
WHERE system_type = 'SOFTRESTAURANT_PRO';

UPDATE Servidores_Conexiones SET system_type = 'SOFRESATAURANT_ENTER' 
WHERE system_type = 'ENTERPRISE';

-- Revertir Sistema_Tipos
UPDATE Sistema_Tipos SET CodigoSistema = 'SOFTRESTAURANT', NombreSistema = 'SoftRestaurant' 
WHERE CodigoSistema = 'SOFTRESTAURANT_PRO';

COMMIT TRANSACTION;
```

---

## ESTADO ACTUAL

| Fase | Estado | Notas |
|------|--------|-------|
| 1. Diagnóstico | ✅ COMPLETADO | Todas las referencias documentadas |
| 2. Mapeo Final | ✅ COMPLETADO | Definido según autorización |
| 3. Script SQL | 🟡 LISTO | Pendiente autorización para ejecutar |
| 4. Cambios Código | 🟡 LISTO | Pendiente ejecución SQL primero |
| 5. Validación | ⏳ PENDIENTE | Después de ejecución |
| 6. Backout | ✅ LISTO | Script de rollback preparado |

---

## PRÓXIMOS PASOS

1. **SOLICITO AUTORIZACIÓN** para ejecutar el script SQL de FASE 3
2. Una vez autorizado, ejecutaré el script y documentaré resultados
3. Luego actualizaré el código backend (FASE 4)
4. Finalmente, ejecutaré validaciones completas (FASE 5)

---

*Reporte generado en cumplimiento del régimen de Autorización Controlada.*
