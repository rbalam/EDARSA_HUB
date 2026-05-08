# DISEÑO FUNCIONAL Y TÉCNICO: Aprobación de Colaboradores
## EDARSA HUB - Módulo RH - Abril 2026

---

## A. FLUJO DE APROBACIÓN

### Diagrama de Estados

```
                                    ┌─────────────┐
                                    │   STAGING   │
                                    │  (Cargado)  │
                                    └──────┬──────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        │                  │                  │
                        ▼                  ▼                  ▼
                 ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                 │  PENDIENTE  │    │ INCOMPLETO  │    │  EXCLUIDO   │
                 │ (Revisión)  │    │ (Sin datos) │    │ (Fuente NV) │
                 └──────┬──────┘    └─────────────┘    └─────────────┘
                        │                  │                  │
            ┌───────────┼───────────┐      │                  │
            │           │           │      │                  │
            ▼           ▼           ▼      │                  │
     ┌──────────┐ ┌──────────┐ ┌──────────┐│                  │
     │ APROBADO │ │RECHAZADO │ │OBSERVADO ││                  │
     │          │ │          │ │          ││                  │
     └────┬─────┘ └──────────┘ └──────────┘│                  │
          │                                │                  │
          ▼                                │                  │
   ┌─────────────┐                         │                  │
   │  PROCESADO  │◄────────────────────────┴──────────────────┘
   │ (En Maestro)│        (NO pasan)
   └─────────────┘
```

### Estados del Registro en Staging

| Estado | Descripción | Puede pasar al Maestro |
|--------|-------------|------------------------|
| **Pendiente** | Cargado, esperando revisión | ✅ Si se aprueba |
| **Aprobado** | Validado, listo para procesar | ✅ Sí |
| **Procesado** | Ya insertado/actualizado en maestro | ❌ Ya está |
| **Rechazado** | Descartado por usuario con motivo | ❌ No |
| **Observado** | Requiere corrección o más info | ❌ No hasta corregir |
| **Incompleto** | Sin datos mínimos (CURP/RFC) | ❌ No |
| **Excluido** | Fuente no autorizada (HR2020) | ❌ Nunca |

### Transiciones Permitidas

| De → A | Condición |
|--------|-----------|
| Pendiente → Aprobado | Validaciones OK + Usuario aprueba |
| Pendiente → Rechazado | Usuario rechaza con motivo |
| Pendiente → Observado | Usuario marca para revisión |
| Aprobado → Procesado | INSERT/UPDATE exitoso en maestro |
| Aprobado → Rechazado | Usuario cancela aprobación |
| Observado → Pendiente | Usuario corrige y reenvía |
| Observado → Rechazado | Usuario descarta definitivamente |
| Rechazado → Pendiente | Usuario reactiva (casos excepcionales) |

---

## B. REGLAS DE APROBACIÓN

### B.1 Criterios de Elegibilidad (Pre-filtro)

Un registro es **candidato a aprobación** si cumple TODAS estas condiciones:

```python
ELEGIBLE_PARA_APROBACION = (
    Fuente == 'MPro_CENTRAL2020'           # Fuente autorizada
    AND Estado NOT IN ('Excluido', 'Procesado')  # No excluido ni ya procesado
    AND Clasificacion != 'incompleto'      # Tiene datos mínimos
    AND Nombre_Completo IS NOT NULL        # Nombre obligatorio
    AND (CURP IS NOT NULL OR RFC IS NOT NULL)  # Al menos un identificador
)
```

### B.2 Validaciones Pre-Aprobación

Antes de aprobar, se valida:

| Validación | Acción si falla |
|------------|-----------------|
| Fuente = 'MPro_CENTRAL2020' | Rechazar automático |
| Estado != 'Excluido' | Rechazar automático |
| Nombre no vacío | Marcar incompleto |
| CURP o RFC presente | Marcar incompleto |
| CURP único en maestro | Marcar duplicado probable |
| RFC único en maestro | Marcar duplicado probable |
| Sucursal identificada | Warning (no bloquea) |

### B.3 Regla INSERT vs UPDATE

| Condición | Acción |
|-----------|--------|
| CURP no existe en maestro AND RFC no existe | **INSERT** nuevo colaborador |
| CURP existe en maestro | **UPDATE** colaborador existente |
| RFC existe en maestro (sin CURP match) | Marcar para revisión manual |

---

## C. DISEÑO TÉCNICO

### C.1 Tablas Involucradas

| Tabla | Rol | Operación |
|-------|-----|-----------|
| `RH_Importacion_Staging` | Origen | SELECT, UPDATE estado |
| `RH_Colaboradores_Expediente` | Destino | INSERT, UPDATE |
| `RH_Importacion_Bitacora` | Log | INSERT |
| `RH_Cat_Sucursales` | Catálogo | SELECT (homologación) |
| `RH_Cat_Puestos` | Catálogo | SELECT (homologación) |

### C.2 Mapeo Staging → Maestro

| Campo Staging | Campo Maestro | Transformación |
|---------------|---------------|----------------|
| `Nombre_Completo` | `Nombre_Completo` | Directo, TRIM |
| `CURP` | `CURP` | Directo, UPPER, TRIM |
| `RFC` | `RFC` | Directo, UPPER, TRIM |
| `CLABE_Bancaria` | `CLABE_Bancaria` | Directo |
| `SucursalID` | `SucursalID` | Homologar vs catálogo |
| `PuestoID` | `PuestoID` | Homologar vs catálogo |
| `Numero_Empleado_Externo` | `NumeroEmpleado` | Directo |
| `Sexo` | `Sexo` | Directo |
| (generado) | `Colaborador_Activo` | DEFAULT 1 |
| (generado) | `Fecha_Alta` | GETDATE() |
| (generado) | `Estatus_Laboral` | DEFAULT 'ACTIVO' |
| `Sucursal_Nombre` | `ObservacionesRH` | Concatenar empresa origen |

### C.3 Estructura de Bitácora de Aprobación

Se añadirán campos a `RH_Importacion_Staging` para trazabilidad:

```sql
-- Campos ya existentes (usar):
Estado                    -- 'Aprobado', 'Rechazado', 'Observado', etc.
Usuario_Aprobador         -- Quién aprobó/rechazó
Fecha_Aprobacion          -- Cuándo
ColaboradorID_Destino     -- ID generado en maestro
Accion_Realizada          -- 'INSERT', 'UPDATE', 'SKIP'
Mensaje_Error             -- Si hubo error
Observaciones             -- Motivo rechazo/observación
```

### C.4 Endpoints a Implementar

| Endpoint | Método | Función |
|----------|--------|---------|
| `/api/rrhh/importar/staging/pendientes` | GET | Listar candidatos a aprobación |
| `/api/rrhh/importar/staging/aprobar/{id}` | POST | Aprobar uno |
| `/api/rrhh/importar/staging/rechazar/{id}` | POST | Rechazar uno con motivo |
| `/api/rrhh/importar/staging/observar/{id}` | POST | Marcar para revisión |
| `/api/rrhh/importar/staging/aprobar-lote` | POST | Aprobar múltiples |
| `/api/rrhh/importar/staging/estadisticas` | GET | Resumen por estado/empresa |

---

## D. TRATAMIENTO POR TIPO DE REGISTRO

### D.1 Aprobables (466 candidatos de CENTRAL2020)

```
Criterio: Fuente=MPro_CENTRAL2020 AND Clasificacion='nuevo' AND Estado='Pendiente'

Proceso:
1. Validar unicidad CURP/RFC en maestro
2. Si único → INSERT en RH_Colaboradores_Expediente
3. Actualizar staging: Estado='Procesado', ColaboradorID_Destino=ID_generado
4. Registrar en bitácora
```

### D.2 Incompletos (66 registros)

```
Criterio: Clasificacion='incompleto'

Proceso:
- NO pasan al maestro
- Quedan en staging con Estado='Pendiente' o 'Incompleto'
- Disponibles para corrección manual futura
- Si se completan datos → pueden revalidarse
```

### D.3 Excluidos (39 registros de HR2020)

```
Criterio: Estado='Excluido' OR Fuente='MPro_HR2020'

Proceso:
- NUNCA pasan al maestro
- Se mantienen solo para auditoría
- No aparecen en listados de pendientes
- Filtrados automáticamente en todas las consultas
```

### D.4 Rechazados

```
Proceso:
- NO pasan al maestro
- Guardan: motivo, usuario, fecha
- Pueden reactivarse excepcionalmente
```

### D.5 Observados

```
Proceso:
- NO pasan al maestro (aún)
- Requieren acción correctiva
- Pueden pasar a Pendiente después de corrección
```

---

## E. MANEJO DE ERRORES

| Error | Acción |
|-------|--------|
| CURP duplicado en maestro | Marcar como 'duplicado_probable', no insertar |
| RFC duplicado en maestro | Marcar como 'duplicado_probable', no insertar |
| Error SQL | Registrar en Mensaje_Error, Estado='Error' |
| Timeout | Reintentar 1 vez, luego Error |
| Datos truncados | Truncar con warning, no fallar |

---

## F. RESTRICCIONES OBLIGATORIAS

1. ❌ NO incluir registros de MPro_HR2020
2. ❌ NO aprobar incompletos automáticamente
3. ❌ NO perder trazabilidad
4. ❌ NO mezclar empresas sin control
5. ❌ NO mandar excluidos al maestro
6. ❌ NO aprobar automáticamente sin validación

---

*Diseño: Abril 2026*
*Módulo: RH - Importador - Aprobación*
