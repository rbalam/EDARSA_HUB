# DISEÑO DE HOMOLOGACIÓN DE CATÁLOGOS
## EDARSA HUB - Módulo RH - Abril 2026

---

## A. DIAGNÓSTICO

### Catálogos en EDARSA HUB

| Catálogo | Tabla | Registros | Estado |
|----------|-------|-----------|--------|
| Sucursales | `RH_Cat_Sucursales` | 0 | VACÍA |
| Puestos | `RH_Cat_Puestos` | 0 | VACÍA |
| Departamentos | `RH_Cat_Departamentos` | 0 | VACÍA |
| Áreas | `RH_Cat_Areas` | 0 | VACÍA |

### Valores en Staging (MPro_CENTRAL2020)

| Tipo | Valores Únicos | Empleados |
|------|----------------|-----------|
| Sucursales | 8 | 476 |
| Puestos | 37 | 476 |
| Departamentos | 11 | 476 |

---

## B. ESTRATEGIA DE HOMOLOGACIÓN

### B.1 Dado que los catálogos están vacíos:

1. **Poblar catálogos automáticamente** desde los valores del staging
2. **Crear tabla de equivalencias** para mapear staging → catálogo
3. **Actualizar staging** con los IDs de catálogo
4. **Validar antes de aprobar** que todos los registros tengan IDs válidos

### B.2 Flujo de Homologación

```
STAGING (valores texto)
        ↓
  [Extracción de valores únicos]
        ↓
CATÁLOGOS (poblar con IDs)
        ↓
TABLA DE EQUIVALENCIAS (valor_origen → catálogo_id)
        ↓
STAGING (actualizar SucursalID, PuestoID)
        ↓
VALIDACIÓN (todos con ID = homologado)
        ↓
APROBACIÓN MASIVA (permitida)
```

---

## C. REGLAS DE HOMOLOGACIÓN

### C.1 Coincidencia Exacta
- Comparación case-insensitive
- TRIM de espacios
- Si hay match exacto → asignar ID

### C.2 Coincidencia Normalizada
- Remover acentos
- Remover caracteres especiales (°, /, etc.)
- Comparar normalizados

### C.3 Equivalencias Manuales
- Para casos especiales (ej: "JEFE DECOCINA" → "JEFE DE COCINA")
- Almacenadas en tabla de equivalencias

### C.4 Valores No Homologados
- Marcar como "Pendiente Homologación"
- Impedir aprobación hasta resolver

---

## D. ESTRUCTURA TÉCNICA

### D.1 Nueva Tabla: RH_Homologacion_Equivalencias

```sql
CREATE TABLE RH_Homologacion_Equivalencias (
    EquivalenciaID INT IDENTITY(1,1) PRIMARY KEY,
    Tipo VARCHAR(20) NOT NULL,  -- 'SUCURSAL', 'PUESTO', 'DEPARTAMENTO'
    Valor_Origen NVARCHAR(200) NOT NULL,
    Valor_Normalizado NVARCHAR(200),
    CatalogoID INT,
    Estado VARCHAR(20) DEFAULT 'Pendiente',  -- 'Aprobado', 'Rechazado', 'Pendiente'
    Usuario_Aprobador VARCHAR(100),
    Fecha_Aprobacion DATETIME,
    Observaciones NVARCHAR(500),
    UNIQUE(Tipo, Valor_Origen)
)
```

### D.2 Campos a Actualizar en Staging

- `SucursalID` → ID de RH_Cat_Sucursales
- `PuestoID` → ID de RH_Cat_Puestos
- Añadir campo `Homologado` (BIT) para validación

---

## E. VALORES A HOMOLOGAR

### Sucursales (8)
| Valor Origen | Empleados | Acción |
|--------------|-----------|--------|
| 130° QUERETARO | 208 | Crear en catálogo |
| ORIGEN | 156 | Crear en catálogo |
| 130° TULUM | 40 | Crear en catálogo |
| CIEN FUEGOS | 28 | Crear en catálogo |
| XCANATUN | 16 | Crear en catálogo |
| MECA | 14 | Crear en catálogo |
| GARCIA LAVIN | 11 | Crear en catálogo |
| EDARSA | 3 | Crear en catálogo |

### Puestos (37) - Muestra
| Valor Origen | Empleados | Observación |
|--------------|-----------|-------------|
| MESERO | 92 | OK |
| GARROTERO | 46 | OK |
| JEFE DECOCINA | 4 | ⚠️ Falta espacio → "JEFE DE COCINA" |
| MIXÓLOGO/JEFE DE BARRA | 5 | OK (con caracteres especiales) |

### Departamentos (11)
| Valor Origen | Empleados | Acción |
|--------------|-----------|--------|
| PISO | 214 | Crear |
| COCINA | 123 | Crear |
| OPERACIONES | 66 | Crear |
| ADMINISTRACION | 47 | Crear |
| CAPITAL HUMANO | 8 | Crear |
| CAJAS | 7 | Crear |
| MARKETING | 4 | Crear |
| TESORERIA | 4 | Crear |
| TECNOLOGIAS DE LA INFORMACION | 1 | Crear |
| CONTABILIDAD | 1 | Crear |
| AUDITORIA | 1 | Crear |

---

## F. IMPLEMENTACIÓN

### F.1 Backend
- Endpoint para poblar catálogos desde staging
- Endpoint para ver equivalencias pendientes
- Endpoint para aprobar/rechazar equivalencia
- Endpoint para verificar homologación de staging

### F.2 Frontend
- Vista de equivalencias por tipo
- Acciones de aprobar/rechazar
- Indicador de homologación en staging
- Bloqueo de aprobación masiva si no está homologado

---

*Diseño: Abril 2026*
