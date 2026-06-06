# DOCUMENTO DE PROTECCIÓN
# Tab Actual de Cuadre de Corte Z

**Versión:** 1.0  
**Fecha:** 15 de Abril de 2026  
**Autor:** Arquitecto de Software Senior - EDARSA HUB  
**Clasificación:** COMPONENTE PROTEGIDO DE PRODUCCIÓN  
**Estado:** DOCUMENTO OFICIAL DE NO REGRESIÓN

---

## DECLARACIÓN DE PROTECCIÓN

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║   EL TAB DE CUADRE DE CORTE Z ES UN ACTIVO FUNCIONAL               ║
║   EN PRODUCCIÓN QUE NO DEBE SER MODIFICADO, ALTERADO,              ║
║   DEGRADADO NI REEMPLAZADO SIN VALIDACIÓN FORMAL.                  ║
║                                                                    ║
║   TODO LO NUEVO DEBE DISEÑARSE ALREDEDOR DE LO QUE YA FUNCIONA.   ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

---

# 1. INVENTARIO FUNCIONAL DEL TAB ACTUAL

## 1.1 Identificación del Componente

| Atributo | Valor |
|----------|-------|
| **Archivo Frontend** | `/app/frontend/src/components/TesoreriaCorteZ.jsx` |
| **Líneas de código** | 771 líneas |
| **Montaje** | `/app/frontend/src/pages/Finanzas.js` línea 2227 |
| **Tab ID** | `tesoreria` |
| **data-testid** | `tesoreria-corte-z` |

## 1.2 Qué Muestra Actualmente

### 1.2.1 Dashboard de Resumen (4 KPIs)

| KPI | Color | Campo Mostrado | Fuente |
|-----|-------|----------------|--------|
| **Pendientes** | Amarillo | `resumen.PENDIENTE.count` + `total_esperado` | MongoDB |
| **En Proceso** | Azul | `resumen.EN_PROCESO.count` + `total_esperado` | MongoDB |
| **Cuadrados** | Verde | `resumen.CUADRADO.count` + `total_depositado` | MongoDB |
| **Descuadre** | Rojo | `resumen.DESCUADRE.count` + `total_diferencia` | MongoDB |

### 1.2.2 Lista de Cortes Z Pendientes de Cuadrar

Para cada corte muestra:

| Campo | Fuente | Línea JSX |
|-------|--------|-----------|
| Sucursal (nombre + icono) | `corte.sucursal_nombre` | 375-376 |
| Folio | `corte.folio_corte` | 377 |
| Fecha Corte | `corte.fecha_corte` | 380 |
| Efectivo Ventas | `corte.efectivo_ventas` | 384 |
| Propinas Pagadas | `corte.propinas_pagadas` | 388 |
| **Monto a Depositar** | `corte.monto_a_depositar` | 392 |
| Fecha Depósito Esperada | `corte.fecha_deposito_esperada` | 396 |
| Botón "Cuadrar" | Acción | 399-404 |

### 1.2.3 Lista de Cuadres Registrados

Para cada cuadre muestra:

| Campo | Fuente | Descripción |
|-------|--------|-------------|
| Sucursal | `cuadre.corte_z.sucursal_nombre` | Nombre de la sucursal |
| Folio + Fecha | `cuadre.corte_z.folio_corte` | Identificador del corte |
| Monto Esperado | `cuadre.monto_esperado` | Del sistema origen |
| Monto Depositado | `cuadre.monto_depositado` | Registrado manualmente |
| Diferencia | `cuadre.diferencia` | Calculado |
| Estado | `cuadre.estado` | Badge de color |
| Validación Fecha | `cuadre.validacion_fecha` | Icono ✓ o ⚠️ |

### 1.2.4 Modal de Cuadre (Formulario)

| Sección | Campos |
|---------|--------|
| **Datos del Corte Z** | Fecha, Efectivo Ventas, Propinas Pagadas, Monto a Depositar, Fecha Esperada |
| **Conteo de Efectivo** | Billetes ($1000, $500, $200, $100, $50, $20), Monedas ($20, $10, $5, $2, $1, $0.50), Total Contado |
| **Ficha de Depósito** | Fecha, Banco, Referencia, Cuenta, Importe |
| **Comparativa** | Esperado vs Contado vs Depositado vs Diferencia |

## 1.3 Cálculos que Realiza

### 1.3.1 Cálculo de Total Contado (Frontend)

```javascript
// Líneas 27-41 y 486-493
const calcularTotal = () => {
  return (
    (billetes.b1000 || 0) * 1000 +
    (billetes.b500 || 0) * 500 +
    (billetes.b200 || 0) * 200 +
    (billetes.b100 || 0) * 100 +
    (billetes.b50 || 0) * 50 +
    (billetes.b20 || 0) * 20 +
    (monedas.m20 || 0) * 20 +
    (monedas.m10 || 0) * 10 +
    (monedas.m5 || 0) * 5 +
    (monedas.m2 || 0) * 2 +
    (monedas.m1 || 0) * 1 +
    (monedas.m050 || 0) * 0.50
  );
};
```

### 1.3.2 Cálculo de Diferencia (Frontend)

```javascript
// Línea 638-640
(fichaDeposito.importe || 0) - selectedCorte.monto_a_depositar
```

### 1.3.3 Cálculos en Backend

| Cálculo | Ubicación | Fórmula |
|---------|-----------|---------|
| `monto_a_depositar` | `tesoreria_models.py:102-104` | `efectivo_ventas - propinas_pagadas` |
| `diferencia` | `repository_cuadres_z.py:109` | `monto_depositado - monto_esperado` |
| `fecha_deposito_esperada` | `repository_cuadres_z.py:26-53` | Día hábil siguiente (L-J→+1, V→+3, S→+2, D→+1) |
| Estado automático | `repository_cuadres_z.py:112-119` | Si diferencia ≤ $1 → CUADRADO, sino → DESCUADRE |

## 1.4 Filtros que Usa

| Filtro | Tipo | Valores | Línea JSX |
|--------|------|---------|-----------|
| `fechaInicio` | Date | Fecha inicio | 696-700 |
| `fechaFin` | Date | Fecha fin | 701-705 |
| `sucursal` | Select | CIENFUEGOS, LA_ESTELAR, 130_MERIDA, MPRO_ORIGEN, MPRO_QUERETARO | 706-720 |
| `estado` | (Interno) | PENDIENTE, EN_PROCESO, CUADRADO, DESCUADRE | (usado en loadCuadres) |

## 1.5 Acciones que Permite

| Acción | Método | Endpoint | Efecto |
|--------|--------|----------|--------|
| **Cargar Cortes Z** | `loadCortesZ()` | `GET /api/finanzas/tesoreria/cortes-z` | Lista cortes pendientes |
| **Cargar Cuadres** | `loadCuadres()` | `GET /api/finanzas/tesoreria/cuadres` | Lista cuadres registrados |
| **Cargar Resumen** | `loadResumen()` | `GET /api/finanzas/tesoreria/cuadres/resumen` | KPIs del dashboard |
| **Iniciar Cuadre** | `handleIniciarCuadre()` | (Frontend) | Abre modal |
| **Guardar Cuadre** | `handleGuardarCuadre()` | `POST /api/finanzas/tesoreria/cuadres` | Crea registro en MongoDB |
| **Actualizar** | Botón | Recarga todos | Refresh manual |

## 1.6 Endpoints que Consume

| Endpoint | Método | Archivo Backend | Línea |
|----------|--------|-----------------|-------|
| `/api/finanzas/tesoreria/cortes-z` | GET | `tesoreria.py` | 23-174 |
| `/api/finanzas/tesoreria/cuadres` | GET | `tesoreria.py` | 212-242 |
| `/api/finanzas/tesoreria/cuadres/resumen` | GET | `tesoreria.py` | 245-262 |
| `/api/finanzas/tesoreria/cuadres` | POST | `tesoreria.py` | 286-321 |
| `/api/finanzas/tesoreria/cuadres/{id}` | PUT | `tesoreria.py` | 324-346 |
| `/api/finanzas/tesoreria/cuadres/{id}` | GET | `tesoreria.py` | 265-283 |

## 1.7 Colecciones MongoDB que Usa

| Colección | Archivo | Operaciones |
|-----------|---------|-------------|
| `tesoreria_cuadres_z` | `repository_cuadres_z.py:66` | CRUD completo |

## 1.8 Dependencias del Componente

### Frontend

| Dependencia | Tipo | Uso |
|-------------|------|-----|
| `react` | Core | Hooks (useState, useEffect, useCallback) |
| `lucide-react` | Iconos | 18 iconos diferentes |
| `../components/ui/card` | UI | Card, CardContent, CardHeader, CardTitle |
| `../components/ui/button` | UI | Button |
| `../components/ui/input` | UI | Input |
| `localStorage.token` | Auth | Token JWT |
| `REACT_APP_BACKEND_URL` | Config | URL del API |

### Backend

| Dependencia | Tipo | Uso |
|-------------|------|-----|
| `pymongo` | DB | Conexión a MongoDB |
| `bson.ObjectId` | DB | Manejo de IDs |
| `core.security.get_current_user` | Auth | Validación de usuario |
| `repository_cortes_z.py` | Lectura | Datos de cortes Z de SQL |

---

# 2. PARTES QUE NO SE DEBEN TOCAR

## 2.1 Componentes Visuales PROTEGIDOS

```
╔════════════════════════════════════════════════════════════════════╗
║  COMPONENTES QUE DEBEN CONSERVARSE SIN MODIFICACIÓN                ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  ✗ NO TOCAR: TesoreriaCorteZ.jsx (771 líneas)                     ║
║  ✗ NO TOCAR: ConteoEfectivo (subcomponente, líneas 23-141)        ║
║  ✗ NO TOCAR: renderResumen() (líneas 295-349)                     ║
║  ✗ NO TOCAR: renderCortesPendientes() (líneas 352-410)            ║
║  ✗ NO TOCAR: renderCuadresRegistrados() (líneas 414-479)          ║
║  ✗ NO TOCAR: renderModal() (líneas 482-666)                       ║
║  ✗ NO TOCAR: Tabs de vista (líneas 729-747)                       ║
║  ✗ NO TOCAR: Filtros (líneas 687-725)                             ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

## 2.2 Lógica que DEBE Conservarse

| Lógica | Ubicación | Razón |
|--------|-----------|-------|
| Cálculo de Total Contado | Frontend | Fórmula validada en producción |
| Cálculo de Diferencia | Frontend | Lógica de negocio aprobada |
| Cálculo de Fecha Depósito | Backend | Regla de días hábiles |
| Determinación de Estado | Backend | PENDIENTE, EN_PROCESO, CUADRADO, DESCUADRE |
| Validación de Fecha | Backend | Día hábil siguiente |
| Tolerancia de $1 | Backend línea 115 | Umbral de cuadre aprobado |

## 2.3 Filtros que DEBEN Conservarse

| Filtro | Estado | Razón |
|--------|--------|-------|
| `fechaInicio` | PROTEGIDO | Funciona correctamente |
| `fechaFin` | PROTEGIDO | Funciona correctamente |
| `sucursal` | PROTEGIDO | Lista completa de sucursales |
| Vista "Pendientes/Cuadrados" | PROTEGIDO | UX validada |

## 2.4 Endpoints que NO DEBEN Alterarse

```
╔════════════════════════════════════════════════════════════════════╗
║  ENDPOINTS PROTEGIDOS - NO MODIFICAR FIRMA NI COMPORTAMIENTO       ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  GET  /api/finanzas/tesoreria/cortes-z                            ║
║       → Parámetros: fecha_inicio, fecha_fin, sucursal             ║
║       → Respuesta: { cortes: [...], total: N, fuente: "..." }     ║
║                                                                    ║
║  GET  /api/finanzas/tesoreria/cuadres                             ║
║       → Parámetros: estado, sucursal_id, fecha_inicio, fecha_fin  ║
║       → Respuesta: { cuadres: [...], total: N }                   ║
║                                                                    ║
║  GET  /api/finanzas/tesoreria/cuadres/resumen                     ║
║       → Respuesta: { resumen: { PENDIENTE, EN_PROCESO, ... } }    ║
║                                                                    ║
║  POST /api/finanzas/tesoreria/cuadres                             ║
║       → Body: { corte_z, conteo_efectivo, ficha_deposito }        ║
║       → Respuesta: { message, cuadre }                            ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

## 2.5 Colección MongoDB que NO DEBE Tocarse

| Colección | Acción Prohibida |
|-----------|------------------|
| `tesoreria_cuadres_z` | NO eliminar, NO renombrar, NO cambiar estructura |

## 2.6 Reglas de Negocio que NO DEBEN Alterarse

| Regla | Valor | Ubicación |
|-------|-------|-----------|
| Tolerancia de cuadre | $1.00 MXN | `repository_cuadres_z.py:115` |
| Tolerancia de validación ficha | $5.00 MXN | `tesoreria.py:447` |
| Fórmula monto_a_depositar | efectivo_ventas - propinas_pagadas | `tesoreria_models.py:102-104` |
| Día hábil siguiente | L-J→+1, V→+3, S→+2, D→+1 | `repository_cuadres_z.py:26-53` |

---

# 3. RIESGOS DE AFECTACIÓN

## 3.1 Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Causa Potencial |
|--------|--------------|---------|-----------------|
| **RT-01**: Endpoint deja de responder | Media | CRÍTICO | Migración prematura de datos |
| **RT-02**: Cambio en estructura de respuesta | Alta | CRÍTICO | Modificar modelos Pydantic |
| **RT-03**: Timeout por consultas SQL nuevas | Media | ALTO | Agregar JOINs pesados |
| **RT-04**: Error de autenticación | Baja | MEDIO | Cambiar middleware de auth |
| **RT-05**: Incompatibilidad de versiones | Baja | MEDIO | Actualizar dependencias |

## 3.2 Riesgos Funcionales

| Riesgo | Probabilidad | Impacto | Causa Potencial |
|--------|--------------|---------|-----------------|
| **RF-01**: KPIs muestran datos incorrectos | Alta | CRÍTICO | Cambiar agregaciones |
| **RF-02**: Lista de cortes incompleta | Media | CRÍTICO | Alterar filtros base |
| **RF-03**: Cálculo de diferencia erróneo | Media | CRÍTICO | Modificar fórmulas |
| **RF-04**: Estado de cuadre incorrecto | Media | ALTO | Cambiar lógica de estados |
| **RF-05**: Fecha de depósito mal calculada | Baja | ALTO | Modificar días hábiles |

## 3.3 Riesgos de Regresión

| Riesgo | Probabilidad | Impacto | Escenario |
|--------|--------------|---------|-----------|
| **RR-01**: Tab deja de cargar | Media | CRÍTICO | Error en import de módulo nuevo |
| **RR-02**: Modal no abre | Baja | ALTO | Cambio en props del componente |
| **RR-03**: Filtros no funcionan | Media | ALTO | Modificar parámetros de endpoint |
| **RR-04**: Botón "Cuadrar" no responde | Baja | CRÍTICO | Cambiar handler de evento |
| **RR-05**: Datos de demo interfieren | Media | MEDIO | Mezclar fuentes de datos |

## 3.4 Riesgos de Rendimiento

| Riesgo | Probabilidad | Impacto | Causa Potencial |
|--------|--------------|---------|-----------------|
| **RP-01**: Carga lenta de lista | Media | MEDIO | Agregar JOINs sin índices |
| **RP-02**: Dashboard tarda >3s | Baja | MEDIO | Agregaciones complejas en SQL |
| **RP-03**: Modal lag al abrir | Baja | BAJO | Exceso de re-renders |

## 3.5 Riesgos de Inconsistencia

| Riesgo | Probabilidad | Impacto | Escenario |
|--------|--------------|---------|-----------|
| **RI-01**: Datos Mongo vs SQL difieren | Alta | CRÍTICO | Dual write sin sincronización |
| **RI-02**: Propinas no coinciden con corte | Media | ALTO | FK rota entre módulos |
| **RI-03**: Historial incompleto | Media | MEDIO | Migración parcial |

---

# 4. COMPATIBILIDAD HACIA ATRÁS

## 4.1 Garantía de Funcionamiento del Tab Actual

```
╔════════════════════════════════════════════════════════════════════╗
║  GARANTÍAS DE COMPATIBILIDAD HACIA ATRÁS                           ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  1. El tab actual seguirá funcionando IGUAL                       ║
║     → Mismos endpoints                                             ║
║     → Mismas respuestas                                            ║
║     → Misma colección MongoDB                                      ║
║                                                                    ║
║  2. Sus resultados NO cambiarán                                   ║
║     → Mismos KPIs                                                  ║
║     → Mismos cálculos                                              ║
║     → Mismas listas                                                ║
║                                                                    ║
║  3. Sus filtros NO se alterarán                                   ║
║     → Mismos parámetros                                            ║
║     → Mismo comportamiento                                         ║
║                                                                    ║
║  4. Su experiencia de usuario NO se degradará                     ║
║     → Mismo tiempo de carga                                        ║
║     → Misma interacción                                            ║
║     → Mismos mensajes                                              ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

## 4.2 Mecanismos de Protección

| Mecanismo | Descripción | Implementación |
|-----------|-------------|----------------|
| **Endpoints Intocables** | Los 6 endpoints actuales no se modifican | Crear nuevos endpoints separados |
| **Colección Preservada** | `tesoreria_cuadres_z` no se toca | Crear colecciones/tablas nuevas |
| **Componente Aislado** | `TesoreriaCorteZ.jsx` no se edita | Crear componentes paralelos |
| **Feature Flag** | Nuevas funciones desactivadas por defecto | Activación controlada |

## 4.3 Reglas de Coexistencia

| Regla | Aplicación |
|-------|------------|
| **R1**: Nuevos endpoints usan prefijo diferente | `/api/finanzas/propinas/*` (ya existe), `/api/finanzas/cortes-z-v2/*` (si fuera necesario) |
| **R2**: Nuevas colecciones usan nombres distintos | `propinas_control`, `propinas_config`, `cortes_z_control_sql` |
| **R3**: Nuevos componentes en archivos separados | `TesoreriaCorteZv2.jsx` o similar |
| **R4**: Tab actual no cambia de ID | `tesoreria` sigue siendo `tesoreria` |

---

# 5. ESTRATEGIA DE CONVIVENCIA

## 5.1 Modelo de Convivencia

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MODELO DE CONVIVENCIA                            │
│            Tab Actual + Nuevos Módulos Financieros                  │
└─────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                     │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Tab "Tesorería" (ACTUAL - PROTEGIDO)                              │
│  └── TesoreriaCorteZ.jsx                                           │
│      └── Endpoints: /api/finanzas/tesoreria/*                      │
│      └── Colección: tesoreria_cuadres_z (MongoDB)                  │
│                                                                     │
│  Tab "Propinas TPV" (NUEVO - SEPARADO)                             │
│  └── PropinasTPV.jsx (por crear)                                   │
│      └── Endpoints: /api/finanzas/propinas/*                       │
│      └── Tabla: propinas_tpv_control (SQL Server)                  │
│                                                                     │
│  Tab "Control Financiero" (FUTURO - SEPARADO)                      │
│  └── ControlFinancieroUnificado.jsx (por crear)                    │
│      └── Endpoints: /api/finanzas/control/*                        │
│      └── Tablas SQL unificadas                                     │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                        BACKEND                                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Router /api/finanzas/tesoreria/* (PROTEGIDO)                      │
│  └── tesoreria.py (sin cambios)                                    │
│  └── repository_cuadres_z.py (sin cambios)                         │
│                                                                     │
│  Router /api/finanzas/propinas/* (NUEVO)                           │
│  └── propinas_tpv/routes.py                                        │
│  └── propinas_tpv/sql_repository.py (por crear)                    │
│                                                                     │
│  Router /api/finanzas/control/* (FUTURO)                           │
│  └── control_financiero/routes.py (por crear)                      │
│  └── sql_repository.py unificado (por crear)                       │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                     ALMACENAMIENTO                                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  MongoDB (ACTUAL - PROTEGIDO)                                      │
│  └── tesoreria_cuadres_z     ← Tab actual sigue leyendo de aquí   │
│                                                                     │
│  SQL Server EDARSA HUB (NUEVO - PARALELO)                          │
│  └── propinas_tpv_control    ← Nuevo módulo propinas              │
│  └── propinas_tpv_config                                           │
│  └── cortes_z_control        ← Futuro: migración controlada       │
│  └── cortes_z_historial                                            │
│                                                                     │
│  MongoDB Cache (NUEVO)                                              │
│  └── propinas_cache_*        ← Cache para nuevos módulos          │
│  └── cortes_z_cache_*                                              │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

## 5.2 Relación Tab Actual vs Propinas TPV

| Aspecto | Tab Actual (Cuadre Z) | Módulo Nuevo (Propinas TPV) | Interferencia |
|---------|----------------------|----------------------------|---------------|
| Endpoint base | `/api/finanzas/tesoreria/*` | `/api/finanzas/propinas/*` | NINGUNA |
| Colección/Tabla | `tesoreria_cuadres_z` (Mongo) | `propinas_tpv_control` (SQL) | NINGUNA |
| Campo propinas | `corte_z.propinas_pagadas` (lectura) | `propinas_totales_corte` (escritura) | NINGUNA - diferentes fuentes |
| KPIs | Pendientes, En Proceso, Cuadrado, Descuadre | Sincronizados, Por Pagar, Pagados | SEPARADOS |

## 5.3 Relación Tab Actual vs Arquitectura Unificada Futura

```
FASE ACTUAL (PROTECCIÓN):
┌──────────────────────────────────────────────────────────────────┐
│  Tab Tesorería (Cuadre Z)                                        │
│  └── Lee de: MongoDB tesoreria_cuadres_z                        │
│  └── Escribe en: MongoDB tesoreria_cuadres_z                    │
│                                                                  │
│  Status: INTOCABLE                                               │
└──────────────────────────────────────────────────────────────────┘

FASE FUTURA (POST-VALIDACIÓN):
┌──────────────────────────────────────────────────────────────────┐
│  Nuevo Tab Control Financiero Unificado                          │
│  └── Lee de: SQL Server (tablas nuevas)                         │
│  └── Escribe en: SQL Server                                     │
│  └── Cache en: MongoDB                                          │
│                                                                  │
│  Status: POR CONSTRUIR - PARALELO AL ACTUAL                     │
└──────────────────────────────────────────────────────────────────┘

FASE TRANSICIÓN (CONTROLADA):
┌──────────────────────────────────────────────────────────────────┐
│  Opción A: Mantener ambos tabs indefinidamente                   │
│  Opción B: Migrar usuarios gradualmente con feature flag         │
│  Opción C: Reemplazar solo después de validación completa        │
│                                                                  │
│  DECISIÓN: La toma el usuario, NO el sistema                    │
└──────────────────────────────────────────────────────────────────┘
```

## 5.4 Principios de No Interferencia

| Principio | Descripción |
|-----------|-------------|
| **P1: Aislamiento de Endpoints** | Cada módulo tiene su propio prefijo de URL |
| **P2: Aislamiento de Datos** | Cada módulo tiene sus propias tablas/colecciones |
| **P3: Aislamiento de Componentes** | Cada módulo tiene sus propios archivos JSX |
| **P4: Sin Dependencias Cruzadas** | El tab actual NO importa nada del módulo nuevo |
| **P5: Feature Flags** | Lo nuevo está desactivado hasta validación |

---

# 6. PLAN DE VALIDACIÓN

## 6.1 Validación Pre-Cambio

Antes de cualquier modificación relacionada con finanzas:

### Checklist de Estado Actual

```
[ ] Captura de pantalla del tab completo
[ ] Captura de pantalla de cada KPI
[ ] Captura de pantalla de lista de pendientes
[ ] Captura de pantalla de lista de cuadres
[ ] Captura de pantalla del modal de cuadre
[ ] Exportar respuesta de GET /api/finanzas/tesoreria/cortes-z
[ ] Exportar respuesta de GET /api/finanzas/tesoreria/cuadres
[ ] Exportar respuesta de GET /api/finanzas/tesoreria/cuadres/resumen
[ ] Exportar contenido de colección tesoreria_cuadres_z
[ ] Medir tiempo de carga del tab (baseline)
```

## 6.2 Casos de Prueba Obligatorios

### CP-01: Carga Inicial del Tab

| Paso | Acción | Resultado Esperado |
|------|--------|-------------------|
| 1 | Navegar a Finanzas → Tesorería | Tab carga sin errores |
| 2 | Verificar KPIs | 4 tarjetas visibles con datos |
| 3 | Verificar lista | Cortes pendientes o mensaje vacío |
| 4 | Tiempo de carga | < 3 segundos |

### CP-02: Filtros

| Paso | Acción | Resultado Esperado |
|------|--------|-------------------|
| 1 | Seleccionar fecha inicio | Lista se filtra |
| 2 | Seleccionar fecha fin | Lista se filtra |
| 3 | Seleccionar sucursal | Lista muestra solo esa sucursal |
| 4 | Limpiar filtros | Lista completa |

### CP-03: Flujo de Cuadre Completo

| Paso | Acción | Resultado Esperado |
|------|--------|-------------------|
| 1 | Click en "Cuadrar" en un corte | Modal abre |
| 2 | Ingresar conteo de billetes | Total se calcula automáticamente |
| 3 | Ingresar datos de ficha | Campos se llenan |
| 4 | Verificar comparativa | Esperado vs Depositado vs Diferencia |
| 5 | Click "Guardar Cuadre" | Modal cierra, cuadre aparece en lista |
| 6 | Verificar estado | CUADRADO si diferencia ≤ $1, DESCUADRE si > $1 |

### CP-04: KPIs

| Paso | Acción | Resultado Esperado |
|------|--------|-------------------|
| 1 | Crear cuadre PENDIENTE | KPI Pendientes +1 |
| 2 | Completar cuadre | KPI Cuadrados +1, Pendientes -1 |
| 3 | Verificar totales | Sumas correctas |

## 6.3 Comparativos Antes/Después

| Métrica | Antes | Después | Tolerancia |
|---------|-------|---------|------------|
| Tiempo de carga | X ms | Y ms | ≤ 20% más lento |
| Número de cortes | N | N | Exacto |
| Número de cuadres | M | M | Exacto |
| Total Pendientes | $X | $X | Exacto |
| Total Cuadrados | $Y | $Y | Exacto |

## 6.4 Evidencia Requerida

| Evidencia | Formato | Ubicación |
|-----------|---------|-----------|
| Screenshots antes/después | PNG | `/app/docs/evidencias/cuadre_z/` |
| Respuestas API antes/después | JSON | `/app/docs/evidencias/cuadre_z/api_responses/` |
| Logs de consola | TXT | `/app/docs/evidencias/cuadre_z/logs/` |
| Video de flujo completo | MP4 (opcional) | `/app/docs/evidencias/cuadre_z/` |

---

# 7. PLAN DE ROLLBACK

## 7.1 Escenarios de Rollback

| Escenario | Trigger | Acción |
|-----------|---------|--------|
| **R1: Tab no carga** | Error 500 o pantalla blanca | Revertir último commit, reiniciar servicios |
| **R2: KPIs incorrectos** | Diferencia > 5% vs baseline | Restaurar endpoint original |
| **R3: Cuadre no guarda** | Error al POST | Restaurar repository original |
| **R4: Rendimiento degradado** | Tiempo > 5 segundos | Revertir cambios de backend |
| **R5: Datos inconsistentes** | Mongo vs SQL difieren | Desactivar feature flag |

## 7.2 Elementos que Deben Poder Desactivarse

| Elemento | Mecanismo de Desactivación |
|----------|---------------------------|
| Nuevos endpoints | Feature flag en backend |
| Nuevas tablas SQL | Exclusión de migraciones |
| Nuevo tab frontend | Feature flag en frontend |
| Escritura dual | Flag en repository |

## 7.3 Procedimiento de Rollback

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROCEDIMIENTO DE ROLLBACK                        │
└─────────────────────────────────────────────────────────────────────┘

PASO 1: Detectar problema
   └── Monitoreo detecta error o usuario reporta

PASO 2: Evaluar severidad
   └── CRÍTICO: Tab no funciona → Rollback inmediato
   └── ALTO: Datos incorrectos → Rollback en < 1 hora
   └── MEDIO: Rendimiento → Evaluar corrección vs rollback

PASO 3: Ejecutar rollback
   └── Si es feature flag: Desactivar flag
   └── Si es código: git revert + redeploy
   └── Si es datos: Restaurar backup de colección

PASO 4: Verificar recuperación
   └── Ejecutar casos de prueba CP-01 a CP-04
   └── Comparar con baseline

PASO 5: Documentar incidente
   └── Causa raíz
   └── Tiempo de afectación
   └── Acciones correctivas
```

## 7.4 Backup Requerido Antes de Cambios

| Elemento | Comando/Acción |
|----------|----------------|
| Colección MongoDB | `mongoexport --db edarsahub --collection tesoreria_cuadres_z --out backup_cuadres.json` |
| Código frontend | Git commit/tag antes de cambios |
| Código backend | Git commit/tag antes de cambios |
| Configuración | Exportar .env files |

---

# 8. RECOMENDACIÓN DE IMPLEMENTACIÓN

## 8.1 Opciones Evaluadas

| Opción | Descripción | Riesgo | Recomendación |
|--------|-------------|--------|---------------|
| **A: Modificar tab actual** | Cambiar TesoreriaCorteZ.jsx | ALTO | ❌ NO RECOMENDADO |
| **B: Crear módulo paralelo** | Nuevo tab con nueva arquitectura | BAJO | ✅ RECOMENDADO |
| **C: Feature flag** | Mismo tab con toggle de fuente | MEDIO | ⚠️ CONDICIONAL |
| **D: Endpoints nuevos desacoplados** | Backend paralelo, frontend decide | BAJO | ✅ RECOMENDADO |
| **E: Convivencia por fases** | Gradual con validación | BAJO | ✅ RECOMENDADO |

## 8.2 Recomendación: OPCIÓN B + D + E

### Implementación Recomendada

```
╔════════════════════════════════════════════════════════════════════╗
║  ESTRATEGIA RECOMENDADA: MÓDULO PARALELO CON CONVIVENCIA          ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  1. NO TOCAR el tab actual de Tesorería (Cuadre Z)                ║
║                                                                    ║
║  2. CREAR nuevo tab "Propinas TPV" completamente separado          ║
║     - Endpoints: /api/finanzas/propinas/*                         ║
║     - Tablas: propinas_tpv_* en SQL Server                        ║
║     - Componente: PropinasTPV.jsx                                 ║
║                                                                    ║
║  3. CREAR (futuro) nuevo tab "Control Financiero Unificado"       ║
║     - Solo después de validar Propinas TPV en producción          ║
║     - Migración controlada de datos                                ║
║     - Feature flag para usuarios piloto                           ║
║                                                                    ║
║  4. MANTENER tab actual indefinidamente hasta decisión formal     ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

## 8.3 Fases de Implementación

| Fase | Acción | Tab Actual | Impacto |
|------|--------|------------|---------|
| **F1** | Implementar Propinas TPV | SIN CAMBIOS | CERO |
| **F2** | Validar Propinas TPV en VPN | SIN CAMBIOS | CERO |
| **F3** | Desplegar Propinas TPV | SIN CAMBIOS | CERO |
| **F4** | Crear Control Financiero v2 (paralelo) | SIN CAMBIOS | CERO |
| **F5** | Migrar datos (con flag) | COEXISTE | CONTROLADO |
| **F6** | Decisión de deprecación | USUARIO DECIDE | PLANIFICADO |

---

# 9. DECISIÓN ARQUITECTÓNICA REQUERIDA

## 9.1 ¿Se Debe Tocar el Tab Actual?

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║                      DECISIÓN FORMAL                               ║
║                                                                    ║
║      ████████╗ ██████╗      NO TOCAR                              ║
║      ╚══██╔══╝██╔═══██╗                                           ║
║         ██║   ██║   ██║     EL TAB ACTUAL                         ║
║         ██║   ██║   ██║                                           ║
║         ██║   ╚██████╔╝     DE CUADRE DE CORTE Z                  ║
║         ╚═╝    ╚═════╝                                            ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

## 9.2 ¿Qué SÍ Se Puede Construir Alrededor?

| Elemento | Permitido | Condición |
|----------|-----------|-----------|
| Nuevo tab Propinas TPV | ✅ SÍ | Completamente separado |
| Nuevos endpoints `/api/finanzas/propinas/*` | ✅ SÍ | Sin modificar tesoreria |
| Nuevas tablas SQL | ✅ SÍ | Sin tocar MongoDB actual |
| Nuevo componente PropinasTPV.jsx | ✅ SÍ | Sin importar en TesoreriaCorteZ |
| Cache MongoDB para nuevos módulos | ✅ SÍ | Colecciones con prefijo diferente |
| Futuro tab Control Financiero v2 | ✅ SÍ | Como módulo paralelo |

## 9.3 ¿Qué DEBE Quedarse Intacto?

| Elemento | Estado | Razón |
|----------|--------|-------|
| `TesoreriaCorteZ.jsx` | INTOCABLE | Funciona en producción |
| `tesoreria.py` | INTOCABLE | Endpoints validados |
| `repository_cuadres_z.py` | INTOCABLE | Lógica de negocio aprobada |
| `tesoreria_models.py` | INTOCABLE | Estructuras de datos estables |
| Colección `tesoreria_cuadres_z` | INTOCABLE | Datos de producción |
| Endpoints `/api/finanzas/tesoreria/*` | INTOCABLE | Contratos de API |
| Tab ID `tesoreria` | INTOCABLE | Navegación existente |

---

# 10. CONCLUSIÓN EJECUTIVA

## 10.1 Protección del Tab Actual

```
╔════════════════════════════════════════════════════════════════════╗
║                     CONCLUSIÓN EJECUTIVA                           ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  CÓMO SE PROTEGERÁ EL TAB ACTUAL:                                 ║
║                                                                    ║
║  ✓ No se modificará ningún archivo del módulo actual              ║
║  ✓ No se alterarán los endpoints de tesorería                     ║
║  ✓ No se tocará la colección MongoDB existente                    ║
║  ✓ Los nuevos módulos serán 100% paralelos                        ║
║  ✓ Feature flags controlarán cualquier cambio futuro              ║
║  ✓ Validación obligatoria antes de cualquier transición           ║
║                                                                    ║
║  QUÉ NO SE VA A TOCAR:                                            ║
║                                                                    ║
║  ✗ TesoreriaCorteZ.jsx (771 líneas)                               ║
║  ✗ tesoreria.py (endpoints)                                       ║
║  ✗ repository_cuadres_z.py (lógica)                               ║
║  ✗ tesoreria_models.py (modelos)                                  ║
║  ✗ Colección tesoreria_cuadres_z                                  ║
║  ✗ KPIs, filtros, cálculos, estados actuales                      ║
║                                                                    ║
║  CONDICIONES PARA INTEGRACIÓN FUTURA:                             ║
║                                                                    ║
║  1. Módulo de Propinas TPV validado en producción (mínimo 30 días)║
║  2. Evidencia de cero regresión documentada                       ║
║  3. Aprobación explícita del usuario para migración               ║
║  4. Plan de rollback probado y funcional                          ║
║  5. Comparativo antes/después con desviación < 1%                 ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

## 10.2 Resumen de Arquitectura de Protección

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA DE PROTECCIÓN                       │
└─────────────────────────────────────────────────────────────────────┘

ZONA PROTEGIDA (NO TOCAR):
├── Frontend: TesoreriaCorteZ.jsx
├── Backend: tesoreria.py, repository_cuadres_z.py
├── Datos: tesoreria_cuadres_z (MongoDB)
└── Endpoints: /api/finanzas/tesoreria/*

ZONA DE DESARROLLO (PARALELA):
├── Frontend: PropinasTPV.jsx (nuevo)
├── Backend: propinas_tpv/* (existente), sql_repository.py (nuevo)
├── Datos: propinas_tpv_* (SQL Server), propinas_cache_* (MongoDB)
└── Endpoints: /api/finanzas/propinas/*

ZONA FUTURA (PLANIFICADA):
├── Frontend: ControlFinancieroV2.jsx
├── Backend: control_financiero/*
├── Datos: Tablas SQL unificadas + Cache MongoDB
└── Endpoints: /api/finanzas/control/*

PRINCIPIO: Todo lo nuevo se construye ALREDEDOR de lo que funciona.
           Nunca SOBRE lo que funciona.
```

---

**FIN DEL DOCUMENTO DE PROTECCIÓN**

*Este documento es de cumplimiento obligatorio antes de cualquier cambio relacionado con el módulo de Tesorería o finanzas.*

*Versión: 1.0 | Fecha: 15 de Abril de 2026 | Clasificación: COMPONENTE PROTEGIDO*
