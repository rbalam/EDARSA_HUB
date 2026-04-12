# DIAGNÓSTICO TÉCNICO ARQUITECTURA EDARSA HUB
## Módulo RH / Nómina
**Fecha**: Diciembre 2025  
**Versión**: 1.0  
**Autor**: Arquitecto de Software Senior

---

## 1. ARQUITECTURA ACTUAL DEL PROYECTO

### 1.1 Estructura Frontend
```
/app/frontend/src/
├── pages/
│   ├── RecursosHumanos.js      # 3,414 líneas - Módulo RH principal
│   ├── Nomina.js               # Módulo de nómina
│   ├── Inventario.js           # Módulo de inventario
│   ├── Dashboard.js            # Dashboard principal
│   ├── Usuarios.js             # Gestión de usuarios
│   ├── Servidores.js           # Configuración de servidores BD
│   ├── TableroEjecutivo.js     # KPIs ejecutivos
│   ├── Alertas.js              # Sistema de alertas
│   └── ... (otros módulos)
├── components/
│   └── ui/                     # Componentes Shadcn/UI
└── App.js                      # Router principal
```

### 1.2 Estructura Backend
```
/app/backend/
├── server.py                   # API principal (~13,000 líneas)
├── core/
│   └── db.py                   # Conexiones BD (MongoDB, SQL Server)
├── modules/
│   ├── auth/                   # Autenticación JWT
│   ├── comercial/              # Módulo comercial
│   └── rh/                     # Módulo RH migrado
│       ├── schemas.py          # Modelos Pydantic (~1,000 líneas)
│       ├── repository.py       # Queries SQL (~2,200 líneas)
│       ├── service.py          # Lógica de negocio (~1,400 líneas)
│       └── routes.py           # Endpoints (~1,000 líneas)
└── tests/
    ├── test_catalogos_rrhh.py  # Tests catálogos
    └── test_rh_modular.py      # Tests módulo RH (41 tests)
```

### 1.3 Bases de Datos

| Servidor | Base de Datos | Uso | Estado |
|----------|---------------|-----|--------|
| MongoDB Local | edarsa_hub | Usuarios, config, sesiones | ✅ Activo |
| **HR2020 ESCRITURA** | **HR2020** | **Empleados, Nómina, Catálogos** | ✅ **1,217 tablas** |
| EDARSA HUB | EDARSAHUB | RH migrado (tablas RH_*) | ⚠️ Sin tablas |
| ManagmentPro | CENTRAL2020 | Ventas, inventario | ✅ Activo |
| SoftRestaurant | Múltiples | POS restaurantes | ✅ Activo |

### 1.4 Roles y Permisos Actuales
- Autenticación: JWT con MongoDB
- Roles definidos: admin, gerente, operador
- Permisos por endpoint (middleware `get_current_user`)

---

## 2. INVENTARIO FUNCIONAL MÓDULO RH/NÓMINA

### 2.1 Endpoints Ya Implementados (41 total)

| Bloque | Endpoints | Estado | Observación |
|--------|-----------|--------|-------------|
| Catálogos | 10 | ✅ Completo | Usa tablas RH_Cat_* (EDARSAHUB) |
| Colaboradores | 5 | ✅ Completo | Usa RH_Colaboradores_Expediente |
| Incidencias | 4 | ✅ Completo | Incluye importación Excel |
| Asistencia | 3 | ✅ Completo | Reloj checador |
| Flujo Nómina | 7 | ✅ Completo | Máquina de estados |
| Auditoría | 2 | ✅ Completo | Dashboard + alertas fraude |
| Reclutamiento | 10 | ✅ Completo | Vacantes + candidatos |

### 2.2 Pantallas Frontend Construidas

| Pantalla | Archivo | Funcionalidades |
|----------|---------|-----------------|
| RecursosHumanos.js | 3,414 líneas | Colaboradores, catálogos, incidencias, asistencia |
| Tabs implementados | 8+ | Colaboradores, Puestos, Sucursales, Incidencias, etc. |

### 2.3 Validaciones Existentes
- ✅ Pydantic schemas para todos los endpoints
- ✅ Validación de transiciones de estado (flujo nómina)
- ✅ Validación email, puntuación, fechas
- ✅ Autenticación requerida en todos los endpoints

---

## 3. INVENTARIO TÉCNICO BASE DE DATOS HR2020

### 3.1 Tablas Principales de Empleados (YA EXISTEN)

| Tabla | Descripción | Campos Clave |
|-------|-------------|--------------|
| **Empleado** | Maestro de empleados | Em_Cve_Empleado (PK), Em_Nombre, Em_Apellido_Paterno, Em_R_F_C, Em_CURP, Em_Fecha_Ingreso, Em_Sueldo_Nominal |
| **Empleado_Historia** | Historial de cambios | Relaciona con Empleado |
| **Empleado_Regimen** | Régimen fiscal | Relaciona con Empleado |
| **Empleado_Centro_Costo** | Asignación centros costo | Em_Cve_Empleado (FK) |
| **Control_Empleado** | Control de acceso | Em_Cve_Empleado (FK) |

### 3.2 Tablas de Catálogos (YA EXISTEN)

| Tabla | Descripción | PK |
|-------|-------------|-----|
| **Puesto_Empleado** | Catálogo de puestos | Pe_Cve_Puesto_Empleado |
| **Departamento_Empleado** | Catálogo de departamentos | De_Cve_Departamento_Empleado |
| **Grupo_Empleado** | Grupos de empleados | Gre_Cve_Grupo_Empleado |
| **Horario_Empleado** | Horarios asignados | Relaciona con Empleado |
| **Horario** | Catálogo de horarios | Ho_Cve_Horario |
| **Causa_Baja_Empleado** | Causas de baja | Cb_Cve_Causa_Baja_Empleado |
| **Nomina_Tipo_Contrato** | Tipos de contrato | Ntc_Cve_Nomina_Tipo_Contrato |

### 3.3 Tablas de Nómina (YA EXISTEN - 30+ tablas)

| Tabla | Descripción | Uso |
|-------|-------------|-----|
| **Nomina** | Recibos de nómina | Detalle percepciones/deducciones |
| **Nomina_Percepcion** | Percepciones | Bonos, salarios, extras |
| **Nomina_Deduccion** | Deducciones | IMSS, ISR, INFONAVIT |
| **Nomina_Incapacidad** | Incapacidades | Registro médico |
| **Nomina_Incidencia** | Incidencias nómina | Faltas, retardos |
| **Nomina_Vacacion** | Vacaciones | Control de días |
| **Nomina_Periodo** | Períodos de pago | Quincenas, semanas |
| **Nomina_Concepto** | Catálogo conceptos | Percepciones/deducciones |
| **Nomina_Configuracion** | Config por empresa | Parámetros de cálculo |
| **Nomina_Tabla_IMSS** | Tablas IMSS | Cuotas patronales |
| **Nomina_Tabla_ISR** | Tablas ISR | Cálculo impuestos |
| **Nomina_Caratula** | Resumen nómina | Totales por período |
| **Pre_Nomina** | Pre-nómina | Cálculo previo |

### 3.4 Relaciones Clave (FK)

```
Empleado
├── Sc_Cve_Sucursal → Sucursal
├── Pe_Cve_Puesto_Empleado → Puesto_Empleado
├── De_Cve_Departamento_Empleado → Departamento_Empleado
├── Gre_Cve_Grupo_Empleado → Grupo_Empleado
└── Ntc_Cve_Nomina_Tipo_Contrato → Nomina_Tipo_Contrato

Nomina
├── Em_Cve_Empleado → Empleado
├── Sc_Cve_Sucursal → Sucursal
├── Nc_Cve_Nomina_Concepto → Nomina_Concepto
└── Nmc_Folio → Nomina_Caratula
```

---

## 4. ANÁLISIS GAP

### 4.1 ✅ YA EXISTE Y SE REUTILIZA (HR2020)

| Elemento | Tabla HR2020 | Acción |
|----------|--------------|--------|
| Empleados | Empleado (101 campos) | **REUTILIZAR** |
| Puestos | Puesto_Empleado | **REUTILIZAR** |
| Departamentos | Departamento_Empleado | **REUTILIZAR** |
| Horarios | Horario, Horario_Empleado | **REUTILIZAR** |
| Nómina | Nomina + 30 tablas relacionadas | **REUTILIZAR** |
| Incapacidades | Nomina_Incapacidad | **REUTILIZAR** |
| Vacaciones | Nomina_Vacacion | **REUTILIZAR** |
| Tablas fiscales | Nomina_Tabla_IMSS, Nomina_Tabla_ISR | **REUTILIZAR** |
| Conceptos | Nomina_Concepto | **REUTILIZAR** |
| Tipos contrato | Nomina_Tipo_Contrato | **REUTILIZAR** |

### 4.2 ⚠️ YA EXISTE PERO REQUIERE AMPLIACIÓN

| Elemento | Estado Actual | Ampliación Requerida |
|----------|---------------|----------------------|
| Flujo aprobación nómina | Implementado en EDARSAHUB (RH_Flujo_Nomina_Sucursal) | Conectar con Nomina de HR2020 |
| Asistencia/checador | Implementado (RH_Reloj_Checador) | Integrar con Control_Empleado de HR2020 |
| Reclutamiento | Implementado (RH_Vacantes, RH_Candidatos) | OK - Independiente |
| Dashboard RH | Implementado | Conectar métricas con HR2020 |

### 4.3 ❌ NO EXISTE Y DEBE CREARSE

| Elemento | Prioridad | Observación |
|----------|-----------|-------------|
| API de lectura HR2020 | **ALTA** | Endpoints para leer datos reales de HR2020 |
| Sincronización HR2020 ↔ EDARSAHUB | MEDIA | Si se decide mantener ambas BD |
| Reportes de nómina | MEDIA | Visualización de recibos |
| Dispersión bancaria | BAJA | Integración con bancos |

---

## 5. HALLAZGOS CRÍTICOS

### 5.1 🔴 PROBLEMA PRINCIPAL: Dos bases de datos RH

**Situación actual:**
- `HR2020` (SQL Server): Contiene 1,217 tablas con datos reales de empleados, nómina, catálogos
- `EDARSAHUB` (SQL Server): Tablas RH_* vacías creadas por el módulo migrado

**Riesgo:** Duplicación de datos, inconsistencia, mantenimiento doble.

### 5.2 🟡 Mapeo de Campos Inconsistente

| Módulo RH Actual | HR2020 Real |
|------------------|-------------|
| RH_Colaboradores_Expediente.ColaboradorID | Empleado.Em_Cve_Empleado |
| RH_Cat_Puestos.PuestoID | Puesto_Empleado.Pe_Cve_Puesto_Empleado |
| RH_Cat_Sucursales.SucursalID | Sucursal.Sc_Cve_Sucursal |

### 5.3 🟢 Fortalezas

- Arquitectura modular bien definida (schemas, repository, service, routes)
- 41 tests automatizados pasando
- Validaciones Pydantic robustas
- Autenticación JWT implementada

---

## 6. PROPUESTA DE SIGUIENTE FASE

### Opción A: CONSOLIDAR EN HR2020 (Recomendada)

**Objetivo:** Usar HR2020 como única fuente de verdad para RH/Nómina

**Pasos:**
1. Crear adaptador de lectura para HR2020 (1-2 días)
2. Mapear campos HR2020 → schemas actuales
3. Modificar repository.py para leer de HR2020
4. Mantener RH_Flujo_Nomina_Sucursal en EDARSAHUB solo para flujo de aprobación
5. Deprecar tablas RH_* duplicadas

**Ventajas:**
- Datos reales inmediatamente
- Sin migración de datos
- Consistencia garantizada

### Opción B: MIGRAR HR2020 → EDARSAHUB

**Objetivo:** Centralizar todo en EDARSAHUB

**Desventajas:**
- Requiere migración masiva de datos
- Riesgo de pérdida de integridad
- Tiempo considerable

---

## 7. REGLAS DE DISEÑO OBLIGATORIAS

1. **NO duplicar tablas** ya existentes en HR2020
2. **Usar nombres canónicos** de HR2020 (Em_Cve_Empleado, Sc_Cve_Sucursal, etc.)
3. **Crear adaptadores** en repository.py para leer HR2020
4. **Mantener schemas Pydantic** actuales como interfaz
5. **Documentar mapeos** de campos explícitamente

---

## 8. RIESGOS TÉCNICOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Permisos insuficientes en HR2020 | Media | Alto | Verificar con DBA |
| Inconsistencia de datos | Alta | Medio | Validar mapeos |
| Performance queries HR2020 | Baja | Medio | Índices, paginación |
| Cambios en HR2020 sin notificar | Media | Alto | Monitoreo, versionado |

---

## 9. SIGUIENTE PASO RECOMENDADO

**FASE HR2020-INTEGRACIÓN-A: Adaptador de Lectura**

Crear endpoints de lectura que consulten directamente HR2020:

```python
# Nuevo en repository.py
async def get_empleados_hr2020(server: Dict, filtros: Dict) -> List[Dict]:
    """Lee empleados directamente de HR2020"""
    query = """
        SELECT 
            Em_Cve_Empleado as ColaboradorID,
            Em_Nombre + ' ' + Em_Apellido_Paterno + ' ' + ISNULL(Em_Apellido_Materno, '') as Nombre_Completo,
            Em_R_F_C as RFC,
            Em_CURP as CURP,
            Em_Fecha_Ingreso as Fecha_Ingreso,
            Em_Sueldo_Nominal as Sueldo,
            Pe_Cve_Puesto_Empleado as PuestoID,
            De_Cve_Departamento_Empleado as DepartamentoID,
            Sc_Cve_Sucursal as SucursalID
        FROM Empleado
        WHERE Es_Cve_Estado = 'AC'
    """
    return execute_hr2020_query(server, query)
```

**¿Autoriza proceder con esta fase de integración?**
