# CONFIGURACIÓN OPERATIVA DE UNIDADES - FASE 0 DIAGNÓSTICO

**Fecha**: 2025-12-19  
**Objetivo**: Diagnóstico de tablas existentes antes de implementar turnos operativos

---

## TABLAS EXISTENTES RELACIONADAS

| Tabla | Propósito |
|-------|-----------|
| Unidades_Negocio | Catálogo maestro de unidades |
| Sistema_HorariosServicioUnidad | Horario operativo por día de semana |
| RH_Cat_Turnos | Turnos para RH (entrada/salida empleados) |

---

## ESTRUCTURA DE Sistema_HorariosServicioUnidad

```sql
CREATE TABLE Sistema_HorariosServicioUnidad (
    id                    uniqueidentifier PRIMARY KEY DEFAULT newid(),
    unidad_negocio_id     nvarchar(50) NOT NULL,
    dia_semana            int NOT NULL,  -- 0=Lunes, 6=Domingo
    hora_inicio_operativo time NOT NULL,
    hora_fin_operativo    time NOT NULL,
    cruza_medianoche      bit NOT NULL DEFAULT 0,
    activo                bit NOT NULL DEFAULT 1,
    fecha_creacion        datetime2 DEFAULT sysutcdatetime(),
    fecha_modificacion    datetime2 DEFAULT sysutcdatetime()
);
```

---

## DATOS ACTUALES

### ORIGEN (MPRO)
| Día | Horario | Cruza |
|-----|---------|-------|
| Lun-Dom | 13:00 - 06:00 | ✓ |

**Problema**: NO tiene configuración de desayuno (07:00-13:00)

### 130QRO (MPRO)
| Día | Horario | Cruza |
|-----|---------|-------|
| Lun-Dom | 13:00 - 06:00 | ✓ |

### 130MID (SoftRestaurant)
| Día | Horario | Cruza |
|-----|---------|-------|
| Lun-Dom | 13:00 - 06:00 | ✓ |

### CIENFUEGOS (SoftRestaurant)
| Día | Horario | Cruza |
|-----|---------|-------|
| Lun-Dom | 13:00 - 23:00 | ✗ |

### ESTELAR (SoftRestaurant)
| Día | Horario | Cruza |
|-----|---------|-------|
| Lun-Dom | 13:00 - 23:00 | ✗ |

---

## ANÁLISIS

### Limitaciones de la Tabla Actual

1. **No soporta múltiples turnos por unidad**
   - Una unidad solo puede tener UN horario por día
   - No puede tener desayuno (07:00-13:00) Y comida/cena (13:00-06:00)

2. **No distingue tipo de turno**
   - No hay campo `tipo_turno` o `turno_codigo`
   - No se puede identificar si es desayuno o comida/cena

3. **No tiene flag de "aplica a Ventas del Día"**
   - Todos los horarios aplican igual
   - No se puede excluir un turno del cálculo de FechaOperacion

### RH_Cat_Turnos NO es útil para esto

- Es para control de asistencia de empleados
- No está vinculada a unidades de negocio
- No tiene relación con Ventas del Día

---

## PROPUESTA: Nueva Tabla

### Sistema_TurnosOperativosUnidad

```sql
CREATE TABLE Sistema_TurnosOperativosUnidad (
    id                    uniqueidentifier PRIMARY KEY DEFAULT newid(),
    unidad_negocio_id     nvarchar(50) NOT NULL,
    turno_codigo          nvarchar(20) NOT NULL,  -- 'DESAYUNO', 'COMIDA_CENA'
    turno_nombre          nvarchar(100) NOT NULL,
    hora_inicio           time NOT NULL,
    hora_fin              time NOT NULL,
    cruza_medianoche      bit NOT NULL DEFAULT 0,
    aplica_ventas_dia     bit NOT NULL DEFAULT 1,
    es_turno_principal    bit NOT NULL DEFAULT 0,  -- Para calcular FechaOperacion
    orden                 int NOT NULL DEFAULT 0,
    activo                bit NOT NULL DEFAULT 1,
    fecha_creacion        datetime2 DEFAULT sysutcdatetime(),
    creado_por            nvarchar(100) NULL,
    fecha_modificacion    datetime2 NULL,
    modificado_por        nvarchar(100) NULL,
    
    CONSTRAINT UK_TurnoOperativo_Unidad_Turno 
        UNIQUE (unidad_negocio_id, turno_codigo)
);
```

### Turnos Iniciales (Catálogo)

| turno_codigo | turno_nombre | Descripción |
|--------------|--------------|-------------|
| DESAYUNO | Desayuno | Turno matutino (ej: 07:00-13:00) |
| COMIDA_CENA | Comida/Cena | Turno principal (ej: 13:00-06:00) |

---

## CONFIGURACIÓN PROPUESTA POR UNIDAD

### ORIGEN
| Turno | Horario | Cruza | Activo | Principal |
|-------|---------|-------|--------|-----------|
| DESAYUNO | 07:00 - 13:00 | ✗ | ✓ | ✗ |
| COMIDA_CENA | 13:00 - 06:00 | ✓ | ✓ | ✓ |

**FechaOperacion**: A las 08:00 = día actual (desayuno activo)

### 130QRO
| Turno | Horario | Cruza | Activo | Principal |
|-------|---------|-------|--------|-----------|
| DESAYUNO | 07:00 - 13:00 | ✗ | ✗ | ✗ |
| COMIDA_CENA | 13:00 - 06:00 | ✓ | ✓ | ✓ |

**FechaOperacion**: A las 12:00 = día anterior (desayuno inactivo)

### 130MID, CIENFUEGOS, ESTELAR
- Similar a 130QRO (desayuno inactivo por defecto)
- Puede activarse después sin cambiar código

---

## SIGUIENTE PASO

**Solicitar autorización para:**
1. Crear tabla `Sistema_TurnosOperativosUnidad`
2. Insertar configuración inicial
3. Actualizar `operational_window.py` para usar la nueva tabla
4. Crear endpoints de administración
5. Crear UI en Catálogo de Unidades
