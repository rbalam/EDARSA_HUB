# ENTREGABLES: Importador de Empleados desde Excel
## EDARSA HUB - Implementación Controlada
**Fecha**: Diciembre 2025  
**Estado**: LISTO PARA REVISIÓN

---

## 1. SCRIPTS DDL DE TABLAS STAGING/BITÁCORA

### 1.1 Tabla `RH_Importacion_Staging`

```sql
-- ============================================================================
-- TABLA: RH_Importacion_Staging
-- Propósito: Almacena registros de importación pendientes de validación/aprobación
-- ============================================================================

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'RH_Importacion_Staging')
BEGIN
    CREATE TABLE RH_Importacion_Staging (
        -- PK
        StagingID INT IDENTITY(1,1) PRIMARY KEY,
        
        -- Datos del empleado (campos principales)
        Nombre_Completo NVARCHAR(200) NOT NULL,
        CURP CHAR(18) NULL,
        RFC VARCHAR(13) NULL,
        CLABE_Bancaria CHAR(18) NULL,
        Numero_Empleado_Externo VARCHAR(50) NULL,
        
        -- Datos de catálogo (texto original + ID resuelto)
        Sucursal_Nombre NVARCHAR(100) NULL,
        SucursalID INT NULL,
        Puesto_Nombre NVARCHAR(100) NULL,
        PuestoID INT NULL,
        Area_Departamento NVARCHAR(100) NULL,
        
        -- Datos adicionales del origen
        Sexo CHAR(1) NULL,
        Edad INT NULL,
        Antiguedad NVARCHAR(50) NULL,
        Sueldo_Diario DECIMAL(10,2) NULL,
        Metodo_Pago NVARCHAR(50) NULL,
        
        -- TRAZABILIDAD OBLIGATORIA
        Fuente VARCHAR(50) NOT NULL,              -- 'Excel_CF', 'MPro_Origen', 'MPro_QRO'
        Archivo_Origen NVARCHAR(255) NULL,
        Linea_Origen INT NULL,
        Fecha_Importacion DATETIME DEFAULT GETDATE(),
        Usuario_Importador NVARCHAR(100) NULL,
        
        -- Estado del procesamiento
        Estado VARCHAR(20) DEFAULT 'Pendiente',   -- Pendiente, Validado, Aprobado, Procesado, Error, Rechazado
        Clasificacion VARCHAR(30) NULL,           -- nuevo, actualizar, duplicado_probable, incompleto, rechazado
        Nivel_Confianza VARCHAR(20) NULL,         -- alta, media, baja, muy_baja, revision
        Accion_Realizada VARCHAR(20) NULL,        -- INSERT, UPDATE, SKIP, ERROR
        
        -- Referencias a registros existentes
        ColaboradorID_Destino INT NULL,
        ColaboradorID_Match INT NULL,
        
        -- Resultado y observaciones
        Mensaje_Error NVARCHAR(500) NULL,
        Observaciones NVARCHAR(MAX) NULL,
        
        -- Auditoría de aprobación
        Usuario_Aprobador NVARCHAR(100) NULL,
        Fecha_Aprobacion DATETIME NULL,
        Fecha_Procesamiento DATETIME NULL,
        
        -- Índices
        INDEX IX_Staging_CURP NONCLUSTERED (CURP),
        INDEX IX_Staging_RFC NONCLUSTERED (RFC),
        INDEX IX_Staging_NumEmpleado NONCLUSTERED (Numero_Empleado_Externo),
        INDEX IX_Staging_Estado NONCLUSTERED (Estado),
        INDEX IX_Staging_Clasificacion NONCLUSTERED (Clasificacion),
        INDEX IX_Staging_Fuente NONCLUSTERED (Fuente),
        INDEX IX_Staging_Fecha NONCLUSTERED (Fecha_Importacion DESC)
    );
END
```

### 1.2 Tabla `RH_Importacion_Bitacora`

```sql
-- ============================================================================
-- TABLA: RH_Importacion_Bitacora
-- Propósito: Historial de importaciones ejecutadas con métricas y trazabilidad
-- ============================================================================

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'RH_Importacion_Bitacora')
BEGIN
    CREATE TABLE RH_Importacion_Bitacora (
        -- PK
        BitacoraID INT IDENTITY(1,1) PRIMARY KEY,
        
        -- Identificación de la importación
        Fecha_Ejecucion DATETIME DEFAULT GETDATE(),
        Fuente VARCHAR(50) NOT NULL,
        Archivo_Origen NVARCHAR(255) NULL,
        
        -- Métricas de resultado
        Total_Registros_Leidos INT DEFAULT 0,
        Total_Insertados INT DEFAULT 0,
        Total_Actualizados INT DEFAULT 0,
        Total_Duplicados_Omitidos INT DEFAULT 0,
        Total_Incompletos INT DEFAULT 0,
        Total_Errores INT DEFAULT 0,
        
        -- Auditoría
        Usuario_Ejecutor NVARCHAR(100) NULL,
        Duracion_Segundos INT NULL,
        Estado VARCHAR(20) DEFAULT 'En Proceso',
        
        -- Detalle adicional
        Detalle_JSON NVARCHAR(MAX) NULL,
        
        -- Índices
        INDEX IX_Bitacora_Fecha NONCLUSTERED (Fecha_Ejecucion DESC),
        INDEX IX_Bitacora_Fuente NONCLUSTERED (Fuente),
        INDEX IX_Bitacora_Estado NONCLUSTERED (Estado)
    );
END
```

---

## 2. DISEÑO DEL IMPORTADOR BACKEND

### 2.1 Arquitectura de Archivos

```
/app/backend/modules/rh/importador/
├── __init__.py       # Exportaciones del módulo
├── schemas.py        # Modelos Pydantic (290 líneas)
├── repository.py     # Acceso a datos SQL (698 líneas)
├── service.py        # Lógica de negocio (691 líneas)
└── routes.py         # Endpoints FastAPI (467 líneas)
```

### 2.2 Flujo de Procesamiento

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FLUJO DE IMPORTACIÓN CONTROLADA                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. UPLOAD             2. PREVIEW            3. STAGING                 │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐                │
│  │  Excel   │ ──────► │ Extraer  │ ──────► │ Cargar   │                │
│  │  Upload  │         │ Validar  │         │ Staging  │                │
│  │          │         │ Clasificar│         │          │                │
│  └──────────┘         └──────────┘         └──────────┘                │
│                              │                    │                     │
│                              ▼                    ▼                     │
│                       ┌──────────────────────────────────┐             │
│                       │         CLASIFICACIÓN            │             │
│                       ├──────────────────────────────────┤             │
│                       │ • nuevos → Listos para INSERT    │             │
│                       │ • actualizar → Listos para UPDATE│             │
│                       │ • duplicado_probable → REVISAR   │             │
│                       │ • incompletos → SIN CURP/RFC     │             │
│                       │ • rechazados → DATOS INVÁLIDOS   │             │
│                       └──────────────────────────────────┘             │
│                                      │                                  │
│  4. REVISIÓN           5. APROBACIÓN          6. CARGA                 │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐                │
│  │ Usuario  │ ──────► │ Aprobar  │ ──────► │ INSERT/  │                │
│  │ Revisa   │         │ Registros│         │ UPDATE   │                │
│  │ Staging  │         │          │         │ Maestro  │                │
│  └──────────┘         └──────────┘         └──────────┘                │
│                                                   │                     │
│                                                   ▼                     │
│                                            ┌──────────┐                │
│                                            │ Bitácora │                │
│                                            │ (Audit)  │                │
│                                            └──────────┘                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. ENDPOINTS API PROPUESTOS

| Método | Endpoint | Descripción | Estado |
|--------|----------|-------------|--------|
| `GET` | `/api/rrhh/importar/tablas/script` | Obtener scripts DDL | ✅ Implementado |
| `POST` | `/api/rrhh/importar/tablas/crear` | Crear tablas (admin) | ✅ Implementado |
| `POST` | `/api/rrhh/importar/excel/preview` | Preview sin insertar | ✅ Implementado |
| `POST` | `/api/rrhh/importar/excel/staging` | Cargar a staging | ✅ Implementado |
| `GET` | `/api/rrhh/importar/staging` | Listar staging | ✅ Implementado |
| `PUT` | `/api/rrhh/importar/staging/{id}` | Actualizar registro | ✅ Implementado |
| `POST` | `/api/rrhh/importar/staging/aprobar` | Aprobar y cargar | ✅ Implementado |
| `GET` | `/api/rrhh/importar/bitacora` | Ver historial | ✅ Implementado |

---

## 4. REGLAS DE VALIDACIÓN

### 4.1 Validación de Campos

| Campo | Regla | Obligatorio |
|-------|-------|-------------|
| `nombre_completo` | Mínimo 3 caracteres, no vacío | ✅ Sí |
| `curp` | 18 caracteres, formato oficial | ⚠️ Recomendado |
| `rfc` | 12-13 caracteres, formato oficial | ⚠️ Recomendado |
| `clabe_bancaria` | 18 dígitos numéricos | ❌ No |
| `sucursal_id` | Debe existir en `RH_Cat_Sucursales` | ✅ Sí |
| `puesto_id` | Debe existir en `RH_Cat_Puestos` | ✅ Sí |

### 4.2 Formato CURP

```regex
^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$
```
- 4 letras (apellidos + nombre)
- 6 dígitos (fecha nacimiento AAMMDD)
- 1 letra (H/M sexo)
- 5 letras (entidad + consonantes)
- 1 alfanumérico (homoclave)
- 1 dígito (verificador)

### 4.3 Formato RFC

```regex
^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$
```
- 3-4 letras (nombre/razón social)
- 6 dígitos (fecha AAMMDD)
- 3 caracteres (homoclave)

---

## 5. REGLAS DE DEDUPLICACIÓN

### 5.1 Orden de Matching (Prioridad)

| Prioridad | Criterio | Nivel Confianza | Acción Automática |
|-----------|----------|-----------------|-------------------|
| 1 | CURP exacto | **ALTA** | ✅ Actualizar |
| 2 | RFC exacto | **MEDIA** | ✅ Actualizar |
| 3 | Número empleado externo | **BAJA** | ⚠️ Revisar |
| 4 | Nombre + Sucursal | **MUY BAJA** | ⚠️ Revisar |
| 5 | Coincidencia parcial nombre | **REVISIÓN** | ❌ Manual |

### 5.2 Algoritmo de Deduplicación

```python
def clasificar_registro(registro, servidor):
    # 1. Buscar por CURP (confianza ALTA)
    if registro.curp:
        matches = buscar_por_curp(registro.curp)
        if matches:
            return Clasificacion.ACTUALIZAR, Confianza.ALTA, matches[0]
    
    # 2. Buscar por RFC (confianza MEDIA)
    if registro.rfc:
        matches = buscar_por_rfc(registro.rfc)
        if matches:
            return Clasificacion.ACTUALIZAR, Confianza.MEDIA, matches[0]
    
    # 3. Buscar por Nombre + Sucursal (confianza MUY BAJA)
    if registro.sucursal_id:
        matches = buscar_por_nombre_sucursal(registro.nombre, registro.sucursal_id)
        if matches:
            return Clasificacion.DUPLICADO_PROBABLE, Confianza.MUY_BAJA, matches[0]
    
    # 4. Buscar coincidencias parciales
    matches = buscar_coincidencias_parciales(registro.nombre)
    if matches:
        return Clasificacion.DUPLICADO_PROBABLE, Confianza.REVISION, matches[0]
    
    # 5. Sin match → Nuevo registro
    if not registro.curp and not registro.rfc:
        return Clasificacion.INCOMPLETO, None, None
    
    return Clasificacion.NUEVO, Confianza.ALTA if registro.curp else Confianza.MEDIA, None
```

---

## 6. EJEMPLO DE PREVIEW CON CLASIFICACIÓN

### 6.1 Respuesta de `/api/rrhh/importar/excel/preview`

```json
{
  "archivo_origen": "NOM-#1426Calculo de Nómina Cienfuegos Sem 14.xlsx",
  "fuente": "Excel_CF",
  "fecha_preview": "2025-12-15T10:30:00",
  "usuario": "ricardo.balam",
  
  "total_registros": 150,
  "total_nuevos": 45,
  "total_actualizar": 80,
  "total_duplicados_probables": 12,
  "total_incompletos": 10,
  "total_rechazados": 3,
  
  "registros_nuevos": [
    {
      "linea_origen": 5,
      "nombre_completo": "PÉREZ GARCÍA JUAN CARLOS",
      "curp": "PEGJ850612HDFRRL09",
      "rfc": "PEGJ8506127K5",
      "clasificacion": "nuevo",
      "nivel_confianza": "alta",
      "razon": "Nuevo colaborador - no existe en base de datos",
      "es_valido_para_carga": true
    }
  ],
  
  "registros_actualizar": [
    {
      "linea_origen": 8,
      "nombre_completo": "AGUILAR ARGAEZ HERBERT JESUS",
      "curp": "AUAH900315HDFGLR02",
      "rfc": "AUAH9003152M8",
      "clasificacion": "actualizar",
      "nivel_confianza": "alta",
      "razon": "Match encontrado por CURP",
      "colaborador_existente_id": 1234,
      "colaborador_existente_nombre": "AGUILAR ARGAEZ HERBERT JESUS",
      "es_valido_para_carga": true
    }
  ],
  
  "registros_duplicados_probables": [
    {
      "linea_origen": 15,
      "nombre_completo": "LOPEZ MARTINEZ MARIA",
      "curp": null,
      "rfc": null,
      "clasificacion": "duplicado_probable",
      "nivel_confianza": "muy_baja",
      "razon": "Posible duplicado - requiere revisión manual",
      "colaborador_existente_id": 2345,
      "colaborador_existente_nombre": "LOPEZ MARTINEZ MARIA FERNANDA",
      "es_valido_para_carga": false
    }
  ],
  
  "registros_incompletos": [
    {
      "linea_origen": 22,
      "nombre_completo": "GONZALEZ HERNANDEZ PEDRO",
      "curp": null,
      "rfc": null,
      "clasificacion": "incompleto",
      "razon": "Sin CURP ni RFC - datos insuficientes para identificación única",
      "es_valido_para_carga": false
    }
  ],
  
  "registros_rechazados": [
    {
      "linea_origen": 30,
      "nombre_completo": "",
      "clasificacion": "rechazado",
      "razon": "Nombre completo es requerido",
      "es_valido_para_carga": false,
      "validaciones": [
        {
          "campo": "nombre_completo",
          "valor_original": "",
          "es_valido": false,
          "mensaje": "El nombre completo es requerido"
        }
      ]
    }
  ],
  
  "advertencias_globales": [
    "10 registros sin CURP/RFC - no se pueden identificar de forma única",
    "12 posibles duplicados requieren revisión manual",
    "Catálogo de puestos vacío - no se resolvieron IDs de puesto"
  ]
}
```

---

## 7. ARCHIVOS CREADOS

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `modules/rh/importador/__init__.py` | 66 | Exportaciones del módulo |
| `modules/rh/importador/schemas.py` | 290 | Modelos Pydantic |
| `modules/rh/importador/repository.py` | 698 | Queries SQL y DDL |
| `modules/rh/importador/service.py` | 691 | Lógica de negocio |
| `modules/rh/importador/routes.py` | 467 | Endpoints FastAPI |
| **Total** | **2,212** | |

---

## 8. PRÓXIMOS PASOS (Pendientes de Autorización)

| # | Tarea | Prioridad | Dependencia |
|---|-------|-----------|-------------|
| 1 | Conectar servidor EDARSA HUB y crear tablas | P0 | Servidor disponible |
| 2 | Probar preview con Excel real | P0 | Tablas creadas |
| 3 | Probar flujo completo staging → aprobación | P0 | Preview exitoso |
| 4 | Implementar UI de importación (mínima) | P1 | Backend probado |
| 5 | Explorar tablas MPro para mapeo | P2 | Autorización explícita |

---

*Documento generado por Arquitecto de Software - EDARSA HUB*
