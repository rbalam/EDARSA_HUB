# DISEÑO: Proceso de Importación del Catálogo Maestro de Empleados
## EDARSA HUB - Arquitectura de Datos
**Fecha**: Diciembre 2025  
**Versión**: 1.0  
**Estado**: PROPUESTA PARA APROBACIÓN  

---

## PRINCIPIO RECTOR

> **EDARSA HUB (`EDARSAHUB`) es la FUENTE MAESTRA y ÚNICA de la verdad.**
> 
> Todas las fuentes externas (Excel, MPro, HR2020) son únicamente **orígenes de importación/sincronización** hacia EDARSA HUB.

---

## FASE 1: DIAGNÓSTICO DE TABLAS EN EDARSA HUB ✅ COMPLETADO

### 1.1 Tablas RH Existentes (44 tablas confirmadas)

| Categoría | Tabla Principal | Uso |
|-----------|----------------|-----|
| **Colaboradores** | `RH_Colaboradores_Expediente` | Catálogo maestro de empleados |
| **Catálogos** | `RH_Cat_Puestos` | Catálogo de puestos |
| | `RH_Cat_Sucursales` | Catálogo de sucursales |
| | `RH_Cat_SucursalesFiscal` | Info fiscal por sucursal |
| | `RH_Cat_Tipos_Incidencias` | Tipos de incidencias |
| **Operación** | `RH_Incidencias_Nomina` | Incidencias de nómina |
| | `RH_Reloj_Checador` | Registros de asistencia |
| | `RH_Flujo_Nomina_Sucursal` | Estados del flujo de nómina |
| **Reclutamiento** | `RH_Vacantes` | Vacantes abiertas |
| | `RH_Candidatos` | Candidatos a vacantes |
| **Auditoría** | `RH_Auditoria_Fiscal` | Auditoría fiscal |

### 1.2 Estructura de `RH_Colaboradores_Expediente` (Tabla Destino)

```sql
CREATE TABLE RH_Colaboradores_Expediente (
    ColaboradorID INT IDENTITY(1,1) PRIMARY KEY,  -- Auto-generado
    Nombre_Completo NVARCHAR(200) NOT NULL,
    CURP CHAR(18) NULL,                            -- Llave de deduplicación #1
    RFC VARCHAR(13) NULL,                          -- Llave de deduplicación #2
    CLABE_Bancaria CHAR(18) NULL,
    SucursalID INT NOT NULL REFERENCES RH_Cat_Sucursales(SucursalID),
    PuestoID INT NOT NULL REFERENCES RH_Cat_Puestos(PuestoID),
    Colaborador_Activo BIT DEFAULT 1,
    Fecha_Alta DATETIME DEFAULT GETDATE(),
    Estatus_Laboral NVARCHAR(50) DEFAULT 'Activo'
)
```

**Validaciones Pydantic existentes:**
- `CURP`: Exactamente 18 caracteres, formato `[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d`
- `RFC`: 12-13 caracteres, formato `[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}`
- `CLABE_Bancaria`: 18 dígitos numéricos
- `Estatus_Laboral`: ["Activo", "Baja", "Vacaciones", "Incapacidad", "Permiso", "Suspendido"]

---

## FASE 2: MAPEO EXCEL CIENFUEGOS → EDARSA HUB

### 2.1 Análisis del Archivo Fuente

**Archivo**: `NOM-#1426Calculo de Nómina Cienfuegos Sem 14.xlsx`  
**Origen**: Sistema CONTPAQi Nóminas (DESARROLLO AMARILLOS DE LA PENINSULA)  
**Tipo**: Cálculo semanal de nómina (NO es un catálogo de empleados puro)

### 2.2 Hojas Relevantes para Importación

| Hoja | Campos Útiles | Observaciones |
|------|---------------|---------------|
| **RESUMEN DE NÓMINA CIENFUEGOS SEM 14** | NOMBRE, ÁREA, PUESTO, SEXO, EDAD, ANTIGUEDAD, SUELDO DIARIO | Datos demográficos |
| **Lista de Raya (forma tabular)** | Código, Empleado, Sueldo | Solo nombre y código interno |
| **RFC** | (Hoja dedicada a RFC) | Contiene RFCs - **CRÍTICA** |

### 2.3 Mapeo de Campos Excel → RH_Colaboradores_Expediente

| Campo Excel (Hoja RESUMEN) | Campo EDARSA HUB | Transformación | Obligatorio |
|---------------------------|------------------|----------------|-------------|
| `NOMBRE` | `Nombre_Completo` | Trim, normalizar mayúsculas | ✅ |
| *(No disponible)* | `CURP` | Buscar en fuente alterna o dejar NULL | ⚠️ Recomendado |
| *(Hoja RFC)* | `RFC` | Extraer de hoja RFC, normalizar formato | ⚠️ Recomendado |
| *(No disponible)* | `CLABE_Bancaria` | Dejar NULL | ❌ |
| `ÁREA` → Mapear a SucursalID | `SucursalID` | Lookup en `RH_Cat_Sucursales` | ✅ |
| `PUESTO` → Mapear a PuestoID | `PuestoID` | Lookup en `RH_Cat_Puestos` | ✅ |
| *(Calculado)* | `Colaborador_Activo` | Default = 1 (activo) | ✅ |
| *(Fecha importación)* | `Fecha_Alta` | GETDATE() | ✅ |
| *(Calculado)* | `Estatus_Laboral` | Default = 'Activo' | ✅ |

### 2.4 Campos Excel NO Mapeables (Descartados)

| Campo Excel | Razón de Exclusión |
|------------|-------------------|
| `SEXO`, `EDAD`, `ANTIGUEDAD` | No existen columnas en `RH_Colaboradores_Expediente` actual |
| `SUELDO DIARIO`, `SUELDO TOTAL DIARIO` | Corresponde a tabla de sueldos, no al expediente |
| `DÍAS TRABAJADOS`, `JORNADAS`, etc. | Datos de nómina semanal, no de catálogo |
| `ISR`, `IMSS`, `INFONAVIT`, etc. | Deducciones de nómina, no del expediente |

### 2.5 Campos Pendientes de Agregar a EDARSA HUB

> **PROPUESTA**: Extender `RH_Colaboradores_Expediente` para almacenar datos demográficos:

```sql
-- Campos propuestos para ALTER TABLE
ALTER TABLE RH_Colaboradores_Expediente ADD
    Sexo CHAR(1) NULL,                    -- 'M' o 'F'
    Fecha_Nacimiento DATE NULL,           -- Para calcular edad
    Fecha_Ingreso DATE NULL,              -- Para calcular antigüedad
    Sueldo_Diario DECIMAL(10,2) NULL,     -- Sueldo base
    Numero_Empleado_Externo VARCHAR(50) NULL;  -- Código de sistema origen
```

**Decisión requerida**: ¿Aprobar extensión de esquema?

---

## FASE 3: MAPEO MPro (ORIGEN Y QUERÉTARO) → EDARSA HUB

### 3.1 Fuentes MPro Identificadas

| Fuente | Base de Datos | Servidor | Estado |
|--------|---------------|----------|--------|
| **MPro Origen** | CENTRAL2020 | Servidor MPro configurado | ✅ Conectado |
| **MPro Querétaro** | CENTRAL2020 (QRO) | Servidor MPro QRO configurado | ✅ Conectado |

### 3.2 Tablas de Empleados en MPro (Estructura Típica)

> **Nota**: Se requiere explorar las tablas específicas de empleados en MPro.
> Basado en el diagnóstico previo, las tablas relevantes serían:

```sql
-- Tablas probables en CENTRAL2020
SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Empleado%'
```

### 3.3 Mapeo Propuesto MPro → EDARSA HUB

| Campo MPro | Campo EDARSA HUB | Transformación |
|------------|------------------|----------------|
| `Id_Empleado` o similar | *(No mapea a ColaboradorID)* | Guardar como `Numero_Empleado_Externo` |
| `Nombre`, `ApPaterno`, `ApMaterno` | `Nombre_Completo` | Concatenar |
| `RFC` | `RFC` | Normalizar |
| `CURP` | `CURP` | Normalizar |
| `Id_Sucursal` | `SucursalID` | Lookup cruzado |
| `Id_Puesto` | `PuestoID` | Lookup cruzado |

**Acción pendiente**: Ejecutar diagnóstico de tablas en servidores MPro.

---

## FASE 4: REGLAS DE DEDUPLICACIÓN (RFC/CURP)

### 4.1 Estrategia de Identificación Única

**Llaves de deduplicación (en orden de prioridad):**

1. **CURP** (preferida) - Único a nivel nacional
2. **RFC** (secundaria) - Único a nivel fiscal
3. **Nombre_Completo + SucursalID** (fallback) - Para casos sin CURP/RFC

### 4.2 Algoritmo de Deduplicación

```
PARA CADA registro_fuente EN (Excel, MPro_Origen, MPro_QRO):
    
    SI registro_fuente.CURP NO ES NULL:
        existente = BUSCAR EN RH_Colaboradores_Expediente WHERE CURP = registro_fuente.CURP
        
    SINO SI registro_fuente.RFC NO ES NULL:
        existente = BUSCAR EN RH_Colaboradores_Expediente WHERE RFC = registro_fuente.RFC
        
    SINO:
        existente = BUSCAR EN RH_Colaboradores_Expediente 
                    WHERE UPPER(Nombre_Completo) = UPPER(registro_fuente.Nombre)
                    AND SucursalID = registro_fuente.SucursalID
    
    SI existente:
        → ACTUALIZAR con datos más recientes (MERGE)
        → LOG: "Actualizado ColaboradorID={id} desde {fuente}"
    SINO:
        → INSERTAR nuevo registro
        → LOG: "Creado nuevo colaborador desde {fuente}"
```

### 4.3 Reglas de Negocio para Conflictos

| Escenario | Regla |
|-----------|-------|
| Mismo CURP, diferente RFC | Actualizar RFC (el CURP es la verdad) |
| Mismo RFC, diferente CURP | Alerta manual - posible error de captura |
| Mismo nombre, diferente CURP/RFC | Insertar como nuevo (pueden ser homónimos) |
| Datos más recientes en fuente externa | Actualizar si fecha_modificación > fecha_actual |

---

## FASE 5: PROPUESTA DE TABLAS STAGING/BITÁCORA

### 5.1 Análisis de Necesidad

| Opción | Pros | Contras | Recomendación |
|--------|------|---------|---------------|
| **Sin staging** (INSERT directo) | Simple, rápido | Sin rollback, sin auditoría detallada | ❌ No recomendado |
| **Staging temporal** (tabla temp) | Permite validación previa | Se pierde al cerrar sesión | ⚠️ Solo para pruebas |
| **Staging persistente** (nueva tabla) | Auditoría completa, rollback | +1 tabla en esquema | ✅ **RECOMENDADO** |

### 5.2 Tabla Propuesta: `RH_Importacion_Staging`

```sql
CREATE TABLE RH_Importacion_Staging (
    StagingID INT IDENTITY(1,1) PRIMARY KEY,
    -- Datos del registro
    Nombre_Completo NVARCHAR(200),
    CURP CHAR(18),
    RFC VARCHAR(13),
    CLABE_Bancaria CHAR(18),
    SucursalID INT,
    PuestoID INT,
    -- Metadatos de importación
    Fuente VARCHAR(50) NOT NULL,        -- 'Excel_CF', 'MPro_Origen', 'MPro_QRO'
    Archivo_Origen VARCHAR(255),         -- Nombre del archivo/query
    Linea_Origen INT,                    -- Línea en Excel o ID en BD origen
    Fecha_Importacion DATETIME DEFAULT GETDATE(),
    Usuario_Importador VARCHAR(100),
    -- Estado del procesamiento
    Estado VARCHAR(20) DEFAULT 'Pendiente',  -- 'Pendiente', 'Procesado', 'Error', 'Duplicado'
    Accion_Realizada VARCHAR(20),            -- 'INSERT', 'UPDATE', 'SKIP'
    ColaboradorID_Destino INT,               -- FK al registro creado/actualizado
    Mensaje_Error NVARCHAR(500),
    -- Índices para deduplicación rápida
    INDEX IX_Staging_CURP (CURP),
    INDEX IX_Staging_RFC (RFC),
    INDEX IX_Staging_Estado (Estado)
);
```

### 5.3 Tabla Propuesta: `RH_Importacion_Bitacora`

```sql
CREATE TABLE RH_Importacion_Bitacora (
    BitacoraID INT IDENTITY(1,1) PRIMARY KEY,
    Fecha_Ejecucion DATETIME DEFAULT GETDATE(),
    Fuente VARCHAR(50) NOT NULL,
    Archivo_Origen VARCHAR(255),
    Total_Registros_Leidos INT,
    Total_Insertados INT,
    Total_Actualizados INT,
    Total_Duplicados_Omitidos INT,
    Total_Errores INT,
    Usuario_Ejecutor VARCHAR(100),
    Duracion_Segundos INT,
    Estado VARCHAR(20),                     -- 'Completado', 'Parcial', 'Fallido'
    Detalle_JSON NVARCHAR(MAX)              -- JSON con detalles adicionales
);
```

### 5.4 Justificación de las Tablas

**¿Por qué crear estas tablas adicionales?**

1. **Trazabilidad completa**: Saber exactamente de dónde vino cada empleado
2. **Rollback selectivo**: Poder revertir una importación específica
3. **Auditoría regulatoria**: Cumplimiento con requisitos de control interno
4. **Debugging**: Identificar problemas en fuentes específicas
5. **Métricas de calidad**: Medir % de duplicados, errores por fuente

---

## FASE 6: PROPUESTA TÉCNICA EJECUTIVA

### 6.1 Arquitectura del Importador

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        EDARSA HUB - IMPORTADOR RH                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│   │  Excel CF    │    │ MPro Origen  │    │  MPro QRO    │             │
│   │  (Upload)    │    │   (SQL)      │    │   (SQL)      │             │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘             │
│          │                   │                   │                      │
│          ▼                   ▼                   ▼                      │
│   ┌─────────────────────────────────────────────────────────┐          │
│   │              CAPA DE EXTRACCIÓN (Extract)               │          │
│   │  - Lectura Excel (pandas/openpyxl)                      │          │
│   │  - Queries SQL a MPro                                   │          │
│   │  - Normalización de campos                              │          │
│   └─────────────────────────┬───────────────────────────────┘          │
│                             │                                           │
│                             ▼                                           │
│   ┌─────────────────────────────────────────────────────────┐          │
│   │              CAPA DE VALIDACIÓN (Transform)             │          │
│   │  - Validar CURP (formato, longitud)                     │          │
│   │  - Validar RFC (formato, longitud)                      │          │
│   │  - Lookup SucursalID, PuestoID                          │          │
│   │  - Detectar duplicados (CURP/RFC/Nombre)                │          │
│   └─────────────────────────┬───────────────────────────────┘          │
│                             │                                           │
│                             ▼                                           │
│   ┌─────────────────────────────────────────────────────────┐          │
│   │               STAGING (RH_Importacion_Staging)          │          │
│   │  - Almacena registros validados                         │          │
│   │  - Marca estado: Pendiente/Error                        │          │
│   └─────────────────────────┬───────────────────────────────┘          │
│                             │                                           │
│                             ▼                                           │
│   ┌─────────────────────────────────────────────────────────┐          │
│   │              CAPA DE CARGA (Load)                       │          │
│   │  - MERGE a RH_Colaboradores_Expediente                  │          │
│   │  - Actualiza estado en Staging                          │          │
│   │  - Registra en Bitácora                                 │          │
│   └─────────────────────────────────────────────────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Endpoints API Propuestos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/rrhh/importar/excel` | Subir y procesar archivo Excel |
| `POST` | `/api/rrhh/importar/mpro/{servidor_id}` | Sincronizar desde MPro |
| `GET` | `/api/rrhh/importar/staging` | Listar registros en staging |
| `POST` | `/api/rrhh/importar/confirmar/{staging_id}` | Confirmar carga de staging |
| `DELETE` | `/api/rrhh/importar/staging/{staging_id}` | Descartar registro de staging |
| `GET` | `/api/rrhh/importar/bitacora` | Ver historial de importaciones |
| `POST` | `/api/rrhh/importar/rollback/{bitacora_id}` | Revertir una importación |

### 6.3 Plan de Implementación (Fases de Código)

| Fase | Descripción | Archivos a Crear/Modificar | Prioridad |
|------|-------------|---------------------------|-----------|
| **Fase I** | Crear tablas Staging y Bitácora | Script SQL | P0 |
| **Fase II** | Extender `RH_Colaboradores_Expediente` | Script SQL (opcional) | P1 |
| **Fase III** | Importador Excel en backend | `modules/rh/importador.py` | P0 |
| **Fase IV** | Importador MPro | `modules/rh/importador.py` | P1 |
| **Fase V** | Endpoints API | `modules/rh/routes.py` | P0 |
| **Fase VI** | UI de importación en frontend | `pages/RecursosHumanos.js` | P2 |
| **Fase VII** | Tests de integración | `tests/test_importador_rh.py` | P1 |

### 6.4 Estimación de Complejidad

| Componente | Complejidad | Líneas Estimadas |
|------------|-------------|------------------|
| Tablas SQL | Baja | ~50 líneas DDL |
| Extractor Excel | Media | ~200 líneas Python |
| Extractor MPro | Media | ~150 líneas Python |
| Validador/Deduplicador | Alta | ~300 líneas Python |
| Capa de carga | Media | ~200 líneas Python |
| Endpoints API | Media | ~150 líneas Python |
| UI Frontend | Media-Alta | ~400 líneas JSX |
| **TOTAL** | | **~1,450 líneas** |

---

## DECISIONES PENDIENTES DE APROBACIÓN

| # | Decisión | Opciones | Recomendación |
|---|----------|----------|---------------|
| 1 | ¿Crear tablas staging/bitácora? | Sí / No | **Sí** |
| 2 | ¿Extender RH_Colaboradores_Expediente con campos demográficos? | Sí / No / Después | **Después** |
| 3 | ¿Implementar primero Excel o MPro? | Excel primero / MPro primero | **Excel primero** |
| 4 | ¿UI de importación en esta fase? | Sí (completa) / Mínima / Solo API | **Mínima** |
| 5 | ¿Rollback automático en caso de error? | Sí / No | **Sí** |

---

## RIESGOS IDENTIFICADOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Excel sin CURP/RFC | Alta | Medio | Usar nombre+sucursal como fallback |
| Puestos/Sucursales no existentes en catálogos | Media | Alto | Crear lookup previo con INSERT si no existe |
| Duplicados masivos en primera importación | Alta | Bajo | Modo "preview" antes de confirmar |
| Timeout en importación grande | Baja | Medio | Procesamiento en chunks de 100 |
| Datos corruptos en Excel | Baja | Medio | Validación estricta por fila |

---

## SIGUIENTE PASO

**¿Autoriza proceder con la implementación de las Fases I-III-V?**

- Fase I: Crear tablas `RH_Importacion_Staging` y `RH_Importacion_Bitacora`
- Fase III: Implementar importador de Excel
- Fase V: Crear endpoints API de importación

---

*Documento generado por Arquitecto de Software - EDARSA HUB*
