# CENTRO DE CONTROL EDARSA
## Wireframe Funcional Completo

**Versión:** 1.0.0  
**Fecha:** 2026-04-19  
**Autor:** Arquitectura UX/UI EDARSA HUB  
**Tipo:** Documento de Diseño - Wireframe Funcional  
**Estado:** APROBADO PARA IMPLEMENTACIÓN

---

## ÍNDICE

1. [Visión General](#1-visión-general)
2. [Principios de Diseño](#2-principios-de-diseño)
3. [Arquitectura de Navegación](#3-arquitectura-de-navegación)
4. [Sistema de Diseño](#4-sistema-de-diseño)
5. [Pantalla 1: Resumen General](#5-pantalla-1-resumen-general)
6. [Pantalla 2: Salud por Módulo](#6-pantalla-2-salud-por-módulo)
7. [Pantalla 3: Alertas y Regresiones](#7-pantalla-3-alertas-y-regresiones)
8. [Pantalla 4: Conectividad y Fuentes](#8-pantalla-4-conectividad-y-fuentes)
9. [Pantalla 5: Jobs y Automatizaciones](#9-pantalla-5-jobs-y-automatizaciones)
10. [Pantalla 6: Cambios y Despliegues](#10-pantalla-6-cambios-y-despliegues)
11. [Pantalla 7: Bitácora / Historial](#11-pantalla-7-bitácora--historial)
12. [Pantalla 8: Configuración y Reglas de Blindaje](#12-pantalla-8-configuración-y-reglas-de-blindaje)
13. [Componentes UI Reutilizables](#13-componentes-ui-reutilizables)
14. [Estados y Mensajes](#14-estados-y-mensajes)
15. [Flujos de Navegación](#15-flujos-de-navegación)
16. [Especificación de Endpoints](#16-especificación-de-endpoints)
17. [Recomendaciones de Implementación](#17-recomendaciones-de-implementación)

---

## 1. VISIÓN GENERAL

### 1.1 Propósito
El **Centro de Control EDARSA** es el módulo central de monitoreo técnico-directivo del sistema EDARSA HUB. Su función es proporcionar visibilidad inmediata sobre la salud, estabilidad y riesgos del sistema.

### 1.2 Audiencia
| Rol | Uso Principal |
|-----|---------------|
| **Director** | Verificar estado general en <30 segundos |
| **Supervisor** | Monitorear alertas y regresiones |
| **Administrador** | Investigar incidentes, gestionar blindaje |
| **Soporte Técnico** | Diagnóstico profundo, drill-down técnico |

### 1.3 Clasificación
```
┌─────────────────────────────────────────────────────────────────┐
│  TIPO: Control Directivo/Técnico                                │
│  ✗ NO es módulo operativo                                       │
│  ✗ NO es dashboard comercial                                    │
│  ✗ NO es tablero financiero                                     │
│  ✓ ES centro de control ejecutivo-técnico                       │
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 Casos de Uso Clave
1. Entrar y saber en **10 segundos** si todo está bien
2. Ver inmediatamente si el Tablero Ejecutivo cayó o regresó a $0
3. Saber si falló una fuente SQL o una API local
4. Ver si un cambio reciente pudo provocar una regresión
5. Saber si un job crítico dejó de correr
6. Confirmar qué módulos están blindados
7. Bajar a detalle técnico solo cuando haga falta

---

## 2. PRINCIPIOS DE DISEÑO

### 2.1 Principios Fundamentales

| Principio | Descripción | Aplicación |
|-----------|-------------|------------|
| **Claro** | Sin ambigüedad | Estados binarios: OK/ALERTA |
| **Ejecutivo** | Para toma de decisiones | KPIs arriba, detalle abajo |
| **Accionable** | Siempre hay un "qué hacer" | CTAs claros en cada alerta |
| **Limpio** | Sin saturación visual | Máximo 4 KPIs por fila |
| **Rápido** | Lectura en <30 segundos | Semáforos, no gráficas complejas |
| **Drill-down** | Detalle bajo demanda | Expandir solo si hay problema |

### 2.2 Jerarquía Visual

```
┌─────────────────────────────────────────────────────────────────┐
│ NIVEL 1: SEMÁFORO GLOBAL                                        │
│ ══════════════════════════                                      │
│ El indicador más importante. Visible desde cualquier pantalla.  │
│                                                                 │
│ NIVEL 2: KPIs CRÍTICOS                                          │
│ ──────────────────────                                          │
│ 4-6 métricas clave en cards superiores.                         │
│                                                                 │
│ NIVEL 3: RESÚMENES                                              │
│ ──────────────────                                              │
│ Grids y tablas con información agregada.                        │
│                                                                 │
│ NIVEL 4: DETALLE                                                │
│ ─────────────────                                               │
│ Panels laterales, modales, drill-down.                          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Regla de los 30 Segundos
Todo usuario debe poder responder estas preguntas en 30 segundos:
- ¿El sistema está bien? → Semáforo
- ¿Cuántas alertas hay? → KPI Card
- ¿Qué requiere atención? → Top Alertas

---

## 3. ARQUITECTURA DE NAVEGACIÓN

### 3.1 Estructura de Menú

```
Sistema
└── Centro de Control EDARSA ←── Entrada principal
    ├── Resumen General         (Vista por defecto)
    ├── Salud por Módulo
    ├── Alertas y Regresiones
    ├── Conectividad y Fuentes
    ├── Jobs y Automatizaciones
    ├── Cambios y Despliegues
    ├── Bitácora
    └── Configuración / Blindaje
```

### 3.2 Navegación Interna

```
┌─────────────────────────────────────────────────────────────────┐
│ CENTRO DE CONTROL EDARSA                               [⟳] [?] │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────┬─────────┬─────────┬─────────┬─────────┬──────────┐ │
│ │ Resumen │ Salud   │ Alertas │ Fuentes │  Jobs   │ Cambios  │ │
│ │ General │ Módulo  │ Regres. │ Conect. │  Auto.  │ Deploy   │ │
│ └─────────┴─────────┴─────────┴─────────┴─────────┴──────────┘ │
│ ┌─────────┬──────────────────┐                                  │
│ │Bitácora │ Config/Blindaje  │                                  │
│ └─────────┴──────────────────┘                                  │
├─────────────────────────────────────────────────────────────────┤
│                      [ CONTENIDO DE LA PESTAÑA ]                │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Breadcrumbs
```
Centro de Control > Salud por Módulo > Tablero Ejecutivo
```

---

## 4. SISTEMA DE DISEÑO

### 4.1 Paleta de Estados

```css
/* ESTADOS CRÍTICOS */
--status-healthy:     #22C55E;  /* Verde - Estable, OK */
--status-warning:     #F59E0B;  /* Amarillo - Advertencia, Parcial */
--status-critical:    #EF4444;  /* Rojo - Crítico, Falla */
--status-unknown:     #6B7280;  /* Gris - Sin datos, No aplica */

/* SEVERIDADES */
--severity-critical:  #DC2626;  /* Rojo oscuro */
--severity-high:      #EA580C;  /* Naranja */
--severity-medium:    #CA8A04;  /* Amarillo oscuro */
--severity-low:       #2563EB;  /* Azul */

/* FONDOS */
--bg-healthy:         #22C55E15;
--bg-warning:         #F59E0B15;
--bg-critical:        #EF444420;
```

### 4.2 Iconografía de Estados

| Estado | Icono | Color | Uso |
|--------|-------|-------|-----|
| Saludable | ✓ CheckCircle | Verde | Sistema OK |
| Advertencia | ⚠ AlertTriangle | Amarillo | Requiere atención |
| Crítico | ✗ XCircle | Rojo | Acción inmediata |
| Desconocido | ? HelpCircle | Gris | Sin datos |
| Blindado | 🛡 Shield | Azul | Protegido |
| En ejecución | ▶ Play | Verde | Job corriendo |
| Pausado | ⏸ Pause | Amarillo | Job detenido |
| Fallido | ⚡ Zap | Rojo | Error |

### 4.3 Tipografía Funcional

```
TÍTULO PRINCIPAL:     text-2xl font-bold    (24px)
SUBTÍTULO:            text-lg font-medium   (18px)
KPI VALOR:            text-4xl font-bold    (36px)
KPI LABEL:            text-sm text-muted    (14px)
TABLA HEADER:         text-xs font-semibold (12px)
TABLA BODY:           text-sm               (14px)
BADGE:                text-xs font-medium   (12px)
```

### 4.4 Espaciado

```
SECCIÓN A SECCIÓN:    gap-6   (24px)
CARD A CARD:          gap-4   (16px)
ELEMENTO A ELEMENTO:  gap-2   (8px)
PADDING CARD:         p-4     (16px)
PADDING SECCIÓN:      p-6     (24px)
```

---

## 5. PANTALLA 1: RESUMEN GENERAL

### 5.1 Objetivo
Dar una lectura ejecutiva del estado total del sistema en **menos de 10 segundos**.

### 5.2 Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│ A. ENCABEZADO                                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Centro de Control EDARSA                                               │
│  Estado actual del sistema                                              │
│                                                                         │
│  Última validación: 19/04/2026 16:45:32        [⟳ Refrescar] [📊 Tech] │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    SISTEMA ESTABLE                               │   │
│  │                         ✓                                        │   │
│  │                   Semáforo: VERDE                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ B. KPIs PRINCIPALES                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │    ✓     │  │    6     │  │    0     │  │    0     │  │    0     │  │
│  │ ESTABLE  │  │  SANOS   │  │ ALERTAS  │  │ FUENTES  │  │   JOBS   │  │
│  │ Sistema  │  │ Módulos  │  │ Críticas │  │  Caídas  │  │ Fallidos │  │
│  │ General  │  │  6 de 6  │  │          │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ C. SEMÁFORO POR CATEGORÍA                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Sistema     Datos      Conexiones     Jobs      Blindaje       │   │
│  │    [●]        [●]          [●]         [●]         [●]          │   │
│  │   VERDE      VERDE        VERDE       VERDE       VERDE         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ D. TOP ALERTAS ACTIVAS                   E. RESUMEN FUENTES            │
├──────────────────────────────────────────┬──────────────────────────────┤
│                                          │                              │
│  ┌────────────────────────────────────┐  │  SQL Clásico        [●] OK  │
│  │  Sin alertas activas               │  │  SQL MPRO           [●] OK  │
│  │                                    │  │  APIs Locales       [●] OK  │
│  │         ✓ Sistema estable          │  │  Scheduler          [●] OK  │
│  │                                    │  │                              │
│  │  [Ver historial de alertas]        │  │  Latencia prom: 45ms        │
│  └────────────────────────────────────┘  │  Última prueba: hace 2 min  │
│                                          │                              │
├──────────────────────────────────────────┴──────────────────────────────┤
│ F. ESTADO DE MÓDULOS                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │ [✓] TABLERO │ │ [✓] COMPRAS │ │ [✓] OPERAC. │ │ [✓] FINANZ. │       │
│  │  Ejecutivo  │ │  Auditoría  │ │  Análisis   │ │             │       │
│  │  0 alertas  │ │  0 alertas  │ │  0 alertas  │ │  0 alertas  │       │
│  │ 🛡 Blindado │ │ 🛡 Blindado │ │ 🛡 Blindado │ │             │       │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                                         │
│  ┌─────────────┐ ┌─────────────┐                                       │
│  │ [✓] COMPRAS │ │  [✓] RH     │                                       │
│  │  Operativo  │ │             │                                       │
│  │  0 alertas  │ │  0 alertas  │                                       │
│  └─────────────┘ └─────────────┘                                       │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ G. EVENTOS RECIENTES                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  16:45  ✓  Health check completado exitosamente                        │
│  16:30  ✓  Regression check: 4/4 módulos OK                            │
│  15:45  ●  Centro de Control inicializado                              │
│  15:30  🛡  Módulo "Tablero Ejecutivo" verificado como blindado        │
│                                                                         │
│                                         [Ver bitácora completa →]      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Especificación de Componentes

#### A. Encabezado
```
┌─────────────────────────────────────────────────────────────────┐
│ COMPONENTE: HeaderCentroControl                                 │
├─────────────────────────────────────────────────────────────────┤
│ Props:                                                          │
│   - titulo: "Centro de Control EDARSA"                          │
│   - subtitulo: "Estado actual del sistema"                      │
│   - ultimaValidacion: datetime                                  │
│   - estadoGeneral: "healthy" | "warning" | "critical"           │
│                                                                 │
│ Acciones:                                                       │
│   - [Refrescar]: onClick → fetchAllData()                       │
│   - [Ver detalle técnico]: onClick → expandTechnicalPanel()     │
│                                                                 │
│ Semáforo Global:                                                │
│   - Ocupa el 100% del ancho bajo el título                      │
│   - Fondo coloreado según estado                                │
│   - Icono grande (48px)                                         │
│   - Texto de estado en mayúsculas                               │
└─────────────────────────────────────────────────────────────────┘
```

#### B. KPIs Principales
```
┌─────────────────────────────────────────────────────────────────┐
│ COMPONENTE: KPICard                                             │
├─────────────────────────────────────────────────────────────────┤
│ Props:                                                          │
│   - icon: ReactNode                                             │
│   - value: string | number                                      │
│   - label: string                                               │
│   - sublabel?: string                                           │
│   - status: "healthy" | "warning" | "critical"                  │
│   - onClick?: () => void                                        │
│                                                                 │
│ Layout:                                                         │
│   - Icono arriba (24px)                                         │
│   - Valor centrado (36px, bold)                                 │
│   - Label debajo (14px, muted)                                  │
│   - Sublabel opcional (12px, muted)                             │
│   - Borde izquierdo coloreado según status                      │
│                                                                 │
│ KPIs Requeridos (5):                                            │
│   1. Estado General del Sistema                                 │
│   2. Módulos Sanos (X de Y)                                     │
│   3. Alertas Críticas Activas                                   │
│   4. Fuentes Caídas                                             │
│   5. Jobs Fallidos Hoy                                          │
└─────────────────────────────────────────────────────────────────┘
```

#### C. Semáforo por Categoría
```
┌─────────────────────────────────────────────────────────────────┐
│ COMPONENTE: SemaforoGrid                                        │
├─────────────────────────────────────────────────────────────────┤
│ Categorías (5):                                                 │
│   1. Sistema General                                            │
│   2. Datos                                                      │
│   3. Conexiones                                                 │
│   4. Jobs                                                       │
│   5. Módulos Blindados                                          │
│                                                                 │
│ Cada categoría muestra:                                         │
│   - Círculo de color (16px)                                     │
│   - Label                                                       │
│   - Texto de estado                                             │
│                                                                 │
│ Layout: Horizontal, centrado, gap-8                             │
└─────────────────────────────────────────────────────────────────┘
```

#### D. Top Alertas Activas
```
┌─────────────────────────────────────────────────────────────────┐
│ COMPONENTE: TopAlertasPanel                                     │
├─────────────────────────────────────────────────────────────────┤
│ Estado Vacío:                                                   │
│   - Icono CheckCircle (48px, verde)                             │
│   - Texto "Sin alertas activas"                                 │
│   - Subtexto "Sistema estable"                                  │
│   - Link "Ver historial de alertas"                             │
│                                                                 │
│ Con Alertas (máximo 5):                                         │
│   - Lista de AlertaRow                                          │
│   - Ordenadas por severidad (crítico primero)                   │
│   - Link "Ver todas las alertas →"                              │
│                                                                 │
│ AlertaRow:                                                      │
│   - Badge severidad (color)                                     │
│   - Módulo afectado                                             │
│   - Descripción corta (max 50 chars)                            │
│   - Tiempo relativo ("hace 5 min")                              │
│   - Botón "Ver" (ghost)                                         │
└─────────────────────────────────────────────────────────────────┘
```

#### E. Resumen de Fuentes
```
┌─────────────────────────────────────────────────────────────────┐
│ COMPONENTE: FuentesResumen                                      │
├─────────────────────────────────────────────────────────────────┤
│ Fuentes Mínimas:                                                │
│   - SQL Clásico (SoftRestaurant)                                │
│   - SQL MPRO (ManagementPro)                                    │
│   - APIs Locales                                                │
│   - Scheduler/Core                                              │
│                                                                 │
│ Por cada fuente:                                                │
│   - Nombre                                                      │
│   - Indicador de estado (punto de color)                        │
│   - Status text (OK / ALERTA / CAÍDA)                           │
│                                                                 │
│ Métricas Globales:                                              │
│   - Latencia promedio                                           │
│   - Última prueba exitosa                                       │
│                                                                 │
│ Link: "Ver todas las fuentes →"                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### F. Estado de Módulos
```
┌─────────────────────────────────────────────────────────────────┐
│ COMPONENTE: ModulosGrid                                         │
├─────────────────────────────────────────────────────────────────┤
│ Módulos (6):                                                    │
│   1. Tablero Ejecutivo (Blindado)                               │
│   2. Auditoría de Compras (Blindado)                            │
│   3. Operaciones / Análisis (Blindado)                          │
│   4. Finanzas                                                   │
│   5. Compras                                                    │
│   6. RH                                                         │
│                                                                 │
│ Por cada módulo (ModuloCard):                                   │
│   - Indicador estado (icono + color)                            │
│   - Nombre del módulo                                           │
│   - Cantidad de alertas activas                                 │
│   - Badge "Blindado" si aplica (con icono 🛡)                   │
│   - onClick → navega a Salud por Módulo                         │
│                                                                 │
│ Layout: Grid 4 columnas (responsivo a 2 en móvil)               │
└─────────────────────────────────────────────────────────────────┘
```

#### G. Eventos Recientes
```
┌─────────────────────────────────────────────────────────────────┐
│ COMPONENTE: EventosRecientes                                    │
├─────────────────────────────────────────────────────────────────┤
│ Muestra últimos 5 eventos                                       │
│                                                                 │
│ Por cada evento (EventoRow):                                    │
│   - Hora (HH:mm)                                                │
│   - Icono según tipo                                            │
│   - Descripción                                                 │
│                                                                 │
│ Tipos de evento:                                                │
│   - health_check → ✓ verde                                      │
│   - regression_check → ✓ verde                                  │
│   - alerta_detectada → ⚠ amarillo                               │
│   - alerta_resuelta → ✓ verde                                   │
│   - fuente_caida → ✗ rojo                                       │
│   - fuente_recuperada → ✓ verde                                 │
│   - job_error → ✗ rojo                                          │
│   - job_ok → ✓ verde                                            │
│   - deploy → 🚀 azul                                            │
│   - blindaje → 🛡 azul                                          │
│                                                                 │
│ Link: "Ver bitácora completa →"                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. PANTALLA 2: SALUD POR MÓDULO

### 6.1 Objetivo
Ver cada módulo con nivel de salud, alertas, KPIs monitoreados y confiabilidad.

### 6.2 Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SALUD POR MÓDULO                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│ FILTROS                                                                 │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐│
│ │ Módulo    ▼  │ │ Estado    ▼  │ │ Severidad ▼  │ │ Fecha: 19/04  📅 ││
│ │   Todos      │ │   Todos      │ │   Todas      │ │                  ││
│ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│ A. GRID DE MÓDULOS                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐ │
│  │ 🛡 TABLERO EJECUTIVO│  │ 🛡 AUDITORÍA COMPRAS│  │ 🛡 OPERACIONES  │ │
│  │                     │  │                     │  │    /ANÁLISIS    │ │
│  │    [✓] SALUDABLE    │  │    [✓] SALUDABLE    │  │ [✓] SALUDABLE   │ │
│  │                     │  │                     │  │                 │ │
│  │  Última: 16:45      │  │  Última: 16:45      │  │  Última: 16:45  │ │
│  │  Alertas: 0         │  │  Alertas: 0         │  │  Alertas: 0     │ │
│  │  Confiab: 100%      │  │  Confiab: 100%      │  │  Confiab: 100%  │ │
│  │                     │  │                     │  │                 │ │
│  │    [Ver detalle]    │  │    [Ver detalle]    │  │  [Ver detalle]  │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘ │
│                                                                         │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐ │
│  │     FINANZAS        │  │     COMPRAS         │  │       RH        │ │
│  │                     │  │    (Operativo)      │  │                 │ │
│  │    [✓] SALUDABLE    │  │    [✓] SALUDABLE    │  │ [✓] SALUDABLE   │ │
│  │                     │  │                     │  │                 │ │
│  │  Última: 16:45      │  │  Última: 16:45      │  │  Última: 16:45  │ │
│  │  Alertas: 0         │  │  Alertas: 0         │  │  Alertas: 0     │ │
│  │  Confiab: 98%       │  │  Confiab: 99%       │  │  Confiab: 97%   │ │
│  │                     │  │                     │  │                 │ │
│  │    [Ver detalle]    │  │    [Ver detalle]    │  │  [Ver detalle]  │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ B. PANEL DE DETALLE (se expande al seleccionar módulo)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ TABLERO EJECUTIVO                                    [✓] BLINDADO │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │                                                                   │ │
│  │ ESTADO ACTUAL              CONFIABILIDAD           CHECKS HOY     │ │
│  │ ┌─────────────┐           ┌─────────────┐         ┌─────────────┐ │ │
│  │ │ SALUDABLE   │           │    100%     │         │   12/12     │ │ │
│  │ │     ✓       │           │   ████████  │         │   EXITOSOS  │ │ │
│  │ └─────────────┘           └─────────────┘         └─────────────┘ │ │
│  │                                                                   │ │
│  │ ─────────────────────────────────────────────────────────────── │ │
│  │                                                                   │ │
│  │ KPIs MONITOREADOS                                                 │ │
│  │ ┌────────────────────────────────────────────────────────────┐   │ │
│  │ │ KPI                   │ Última valor │ Estado │ Check     │   │ │
│  │ ├───────────────────────┼──────────────┼────────┼───────────┤   │ │
│  │ │ Ventas Acumuladas     │ $9.2M        │   ✓    │ 16:45     │   │ │
│  │ │ Servicios KPI         │ Disponible   │   ✓    │ 16:45     │   │ │
│  │ │ Comparativos          │ Disponible   │   ✓    │ 16:45     │   │ │
│  │ │ Connection Resolver   │ Operativo    │   ✓    │ 16:45     │   │ │
│  │ └────────────────────────────────────────────────────────────┘   │ │
│  │                                                                   │ │
│  │ FUENTES ASOCIADAS                                                 │ │
│  │ • SQL SoftRestaurant (Cienfuegos, Estelar, 130 Mid)              │ │
│  │ • SQL MPRO                                                        │ │
│  │ • API Local MPRO                                                  │ │
│  │                                                                   │ │
│  │ REGLA DE BLINDAJE                                                 │ │
│  │ ┌────────────────────────────────────────────────────────────┐   │ │
│  │ │ 🛡 Módulo congelado funcionalmente desde 19/04/2026        │   │ │
│  │ │    Documento: CIERRE_Y_BLINDAJE_TABLERO_EJECUTIVO.md       │   │ │
│  │ │    Cualquier cambio requiere autorización expresa          │   │ │
│  │ └────────────────────────────────────────────────────────────┘   │ │
│  │                                                                   │ │
│  │ ARCHIVOS CRÍTICOS                                                 │ │
│  │ • backend/modules/comercial/service.py                            │ │
│  │ • frontend/src/pages/Comercial.js                                 │ │
│  │ • backend/core/connection_resolver.py                             │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ C. TABLA DE CHECKS DEL MÓDULO                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │ Check               │ Tipo      │ Result │ Fecha    │ Dur. │ Sev. ││
│  ├─────────────────────┼───────────┼────────┼──────────┼──────┼──────┤│
│  │ ventas_acumuladas   │ Regresión │   ✓    │ 16:45:32 │ 12ms │ Low  ││
│  │ servicios_kpi       │ Regresión │   ✓    │ 16:45:32 │  8ms │ Low  ││
│  │ comparativos        │ Regresión │   ✓    │ 16:45:32 │  5ms │ Low  ││
│  │ connection_resolver │ Sistema   │   ✓    │ 16:45:32 │  2ms │ Low  ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Estados del Módulo Card

```
┌─────────────────────────────────────────────────────────────────┐
│ ESTADOS VISUALES DE ModuloCard                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SALUDABLE (healthy):                                            │
│ ┌─────────────────────┐                                         │
│ │ ▌ fondo verde claro │  Borde izquierdo: verde                 │
│ │ ▌ [✓] SALUDABLE     │  Icono: CheckCircle verde               │
│ │ ▌ texto normal      │  Texto: "SALUDABLE"                     │
│ └─────────────────────┘                                         │
│                                                                 │
│ ADVERTENCIA (warning):                                          │
│ ┌─────────────────────┐                                         │
│ │ ▌ fondo amarillo    │  Borde izquierdo: amarillo              │
│ │ ▌ [⚠] ADVERTENCIA   │  Icono: AlertTriangle amarillo          │
│ │ ▌ texto destacado   │  Texto: "ADVERTENCIA"                   │
│ └─────────────────────┘                                         │
│                                                                 │
│ CRÍTICO (critical):                                             │
│ ┌─────────────────────┐                                         │
│ │ ▌ fondo rojo claro  │  Borde izquierdo: rojo                  │
│ │ ▌ [✗] CRÍTICO       │  Icono: XCircle rojo                    │
│ │ ▌ texto BOLD        │  Texto: "CRÍTICO" + pulse animation     │
│ └─────────────────────┘                                         │
│                                                                 │
│ SIN DATOS (unknown):                                            │
│ ┌─────────────────────┐                                         │
│ │ ▌ fondo gris        │  Borde izquierdo: gris                  │
│ │ ▌ [?] SIN DATOS     │  Icono: HelpCircle gris                 │
│ │ ▌ texto muted       │  Texto: "SIN DATOS"                     │
│ └─────────────────────┘                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. PANTALLA 3: ALERTAS Y REGRESIONES

### 7.1 Objetivo
Consola central de incidentes y regresiones. Gestión completa de alertas.

### 7.2 Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ALERTAS Y REGRESIONES                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ FILTROS                                                                 │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
│ │Severidad▼│ │ Módulo ▼ │ │ Estado ▼ │ │  Tipo  ▼ │ │ 📅 Fecha rango │ │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│ A. KPIs SUPERIORES                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │    0     │  │    0     │  │    0     │  │    0     │  │    0     │  │
│  │ CRÍTICAS │  │  ALTAS   │  │  MEDIAS  │  │RESUELTAS │  │REGRESION │  │
│  │  activas │  │  activas │  │  activas │  │   hoy    │  │   hoy    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ B. BANNER DE ALERTA CRÍTICA (solo si hay críticas activas)              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ ⚠ ATENCIÓN: 2 alertas críticas requieren acción inmediata        │ │
│  │                                                    [Ver alertas →]│ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ C. TABLA PRINCIPAL DE ALERTAS                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │ Fecha/Hora   │ Módulo    │ Tipo          │ Sev. │ Status │ Acción ││
│  ├──────────────┼───────────┼───────────────┼──────┼────────┼────────┤│
│  │              │           │               │      │        │        ││
│  │  (Sin alertas activas - Sistema estable)                          ││
│  │                                                                    ││
│  │         ✓ No hay alertas que requieran atención                   ││
│  │                                                                    ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ D. PANEL DE DETALLE DE ALERTA (aparece al seleccionar una alerta)       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ ALERTA: Ventas acumuladas en $0                    [CRÍTICA] 🔴   │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │                                                                   │ │
│  │ DESCRIPCIÓN                                                       │ │
│  │ El Tablero Ejecutivo muestra ventas acumuladas en $0 con         │ │
│  │ 3 unidades de negocio reportando como online.                     │ │
│  │                                                                   │ │
│  │ ─────────────────────────────────────────────────────────────── │ │
│  │                                                                   │ │
│  │ IMPACTO                                                           │ │
│  │ • Dirección no puede ver ventas reales                            │ │
│  │ • Posible contaminación de caché                                  │ │
│  │ • Datos comerciales incorrectos                                   │ │
│  │                                                                   │ │
│  │ ─────────────────────────────────────────────────────────────── │ │
│  │                                                                   │ │
│  │ EVIDENCIA TÉCNICA                                                 │ │
│  │ ┌─────────────────────────────────────────────────────────────┐  │ │
│  │ │ Esperado: ventas > $0                                       │  │ │
│  │ │ Obtenido: ventas = $0                                       │  │ │
│  │ │ Fuente: SQL Cienfuegos - timeout 30s                        │  │ │
│  │ │ Unidades online: 3                                          │  │ │
│  │ └─────────────────────────────────────────────────────────────┘  │ │
│  │                                                                   │ │
│  │ RECOMENDACIÓN                                                     │ │
│  │ 1. Verificar conectividad a servidores SQL locales                │ │
│  │ 2. Revisar logs del connection_resolver                           │ │
│  │ 3. Confirmar que no se está usando fallback silencioso            │ │
│  │                                                                   │ │
│  │ ─────────────────────────────────────────────────────────────── │ │
│  │                                                                   │ │
│  │ LÍNEA DE TIEMPO                                                   │ │
│  │ ○───●───○───○                                                     │ │
│  │ │   │   │   │                                                     │ │
│  │ │   │   │   └─ Resuelto (pendiente)                               │ │
│  │ │   │   └───── Mitigado (pendiente)                               │ │
│  │ │   └───────── Confirmado: 16:30                                  │ │
│  │ └───────────── Detectado: 16:28                                   │ │
│  │                                                                   │ │
│  │                      [Reconocer] [Marcar resuelto] [Escalar]      │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Tipos de Alerta

| Tipo | Icono | Color | Descripción |
|------|-------|-------|-------------|
| `regresion_funcional` | ⚡ | Rojo | Algo que funcionaba dejó de funcionar |
| `caida_fuente` | 🔌 | Rojo | Fuente de datos no responde |
| `incoherencia_datos` | ⚠ | Amarillo | Datos no cuadran entre fuentes |
| `job_fallido` | ⏱ | Naranja | Job/automatización falló |
| `cambio_no_documentado` | 📝 | Amarillo | Cambio sin documentación |
| `error_conectividad` | 🌐 | Rojo | Error de red/conexión |
| `diferencia_consolidado` | 📊 | Amarillo | Consolidado vs detalle no cuadra |

---

## 8. PANTALLA 4: CONECTIVIDAD Y FUENTES

### 8.1 Objetivo
Monitorear salud de conexiones y fuentes oficiales de datos.

### 8.2 Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│ CONECTIVIDAD Y FUENTES                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│ FILTROS                                                                 │
│ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐               │
│ │ Tipo fuente ▼  │ │ Sistema     ▼  │ │ Estado      ▼  │               │
│ └────────────────┘ └────────────────┘ └────────────────┘               │
├─────────────────────────────────────────────────────────────────────────┤
│ A. KPIs DE CONECTIVIDAD                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │    4     │  │    0     │  │    0     │  │   45ms   │  │  16:45   │  │
│  │ ACTIVAS  │  │ WARNING  │  │  CAÍDAS  │  │ LATENCIA │  │ ÚLTIMA   │  │
│  │ fuentes  │  │          │  │          │  │ promedio │  │ PRUEBA   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ B. GRID DE FUENTES                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ FUENTES SQL CLÁSICO (SoftRestaurant)                              │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │                                                                   │ │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐         │ │
│  │  │ CIENFUEGOS    │  │ LA ESTELAR    │  │   130 MID     │         │ │
│  │  │     [●]       │  │     [●]       │  │     [●]       │         │ │
│  │  │    ONLINE     │  │    ONLINE     │  │    ONLINE     │         │ │
│  │  │   42ms resp   │  │   38ms resp   │  │   45ms resp   │         │ │
│  │  │  [Ver detalle]│  │  [Ver detalle]│  │  [Ver detalle]│         │ │
│  │  └───────────────┘  └───────────────┘  └───────────────┘         │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ FUENTES MPRO (ManagementPro)                                      │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │                                                                   │ │
│  │  ┌───────────────┐  ┌───────────────┐                            │ │
│  │  │  SQL MPRO     │  │  API LOCAL    │                            │ │
│  │  │     [●]       │  │     [●]       │                            │ │
│  │  │    ONLINE     │  │    ONLINE     │                            │ │
│  │  │   55ms resp   │  │   120ms resp  │                            │ │
│  │  │  [Ver detalle]│  │  [Ver detalle]│                            │ │
│  │  └───────────────┘  └───────────────┘                            │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ SERVICIOS INTERNOS                                                │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │                                                                   │ │
│  │  ┌───────────────┐  ┌───────────────┐                            │ │
│  │  │   MONGODB     │  │  SCHEDULER    │                            │ │
│  │  │     [●]       │  │     [●]       │                            │ │
│  │  │    ONLINE     │  │   RUNNING     │                            │ │
│  │  │   12ms resp   │  │    N/A        │                            │ │
│  │  │  [Ver detalle]│  │  [Ver detalle]│                            │ │
│  │  └───────────────┘  └───────────────┘                            │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ C. MATRIZ FUENTE ↔ MÓDULO                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │ Fuente          │ Módulos Afectados  │ KPIs Dependientes │ Riesgo ││
│  ├─────────────────┼────────────────────┼───────────────────┼────────┤│
│  │ SQL Cienfuegos  │ Tablero, Compras   │ Ventas, Cheques   │ ALTO   ││
│  │ SQL Estelar     │ Tablero, Compras   │ Ventas, Cheques   │ ALTO   ││
│  │ SQL MPRO        │ Tablero, Finanzas  │ Acumulados MPRO   │ ALTO   ││
│  │ API Local MPRO  │ Tablero            │ Ventas día MPRO   │ MEDIO  ││
│  │ MongoDB         │ TODOS              │ Config, Auth      │ CRÍTICO││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ D. PANEL DETALLE FUENTE (aparece al seleccionar)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ CIENFUEGOS SQL                                        [●] ONLINE  │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │                                                                   │ │
│  │ INFORMACIÓN GENERAL                                               │ │
│  │ • Origen: Menú Servidores SQL                                     │ │
│  │ • Tipo: SQL Server (SoftRestaurant)                               │ │
│  │ • IP: serverestelar.ddns.net (interno: 192.168.1.x)              │ │
│  │ • Puerto: 1433                                                    │ │
│  │                                                                   │ │
│  │ MÓDULOS QUE LA CONSUMEN                                           │ │
│  │ • Tablero Ejecutivo (ventas acumuladas)                           │ │
│  │ • Auditoría de Compras (históricos)                               │ │
│  │                                                                   │ │
│  │ KPIs DEPENDIENTES                                                 │ │
│  │ • Ventas del día                                                  │ │
│  │ • Cheques                                                         │ │
│  │ • PAX                                                             │ │
│  │                                                                   │ │
│  │ HEALTH CHECK HISTORY (últimas 24h)                                │ │
│  │ ┌─────────────────────────────────────────────────────────────┐  │ │
│  │ │ ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓  (24/24 exitosos)                 │  │ │
│  │ │ Latencia promedio: 42ms | Máxima: 85ms | Mínima: 28ms      │  │ │
│  │ └─────────────────────────────────────────────────────────────┘  │ │
│  │                                                                   │ │
│  │ ÚLTIMOS ERRORES                                                   │ │
│  │ (Sin errores en las últimas 24 horas)                             │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. PANTALLA 5: JOBS Y AUTOMATIZACIONES

### 9.1 Objetivo
Ver estado de scheduler, jobs, integraciones y procesos automáticos.

### 9.2 Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│ JOBS Y AUTOMATIZACIONES                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ A. KPIs                                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │    5     │  │    0     │  │  16:30   │  │    0     │  │    0     │  │
│  │  JOBS    │  │  ERRORS  │  │ ÚLTIMO   │  │REINTENTOS│  │ PAUSADOS │  │
│  │ activos  │  │   hoy    │  │  ÉXITO   │  │   hoy    │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ B. ESTADO DEL SCHEDULER                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ SCHEDULER EDARSA HUB                               [▶] RUNNING    │ │
│  │ ─────────────────────────────────────────────────────────────── │ │
│  │ Inicio: 19/04/2026 08:00 | Uptime: 8h 45m | Próximo: 17:00      │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ C. TABLA DE JOBS                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │ Job                    │ Frecuencia │ Último Run │ Status │ Acción││
│  ├────────────────────────┼────────────┼────────────┼────────┼───────┤│
│  │ health_check_sistema   │ c/5 min    │ 16:45      │   ✓    │ [👁]  ││
│  │ regression_checks      │ c/15 min   │ 16:30      │   ✓    │ [👁]  ││
│  │ cache_cleanup          │ c/1 hora   │ 16:00      │   ✓    │ [👁]  ││
│  │ metrics_aggregator     │ c/30 min   │ 16:30      │   ✓    │ [👁]  ││
│  │ notifications_dispatch │ c/1 min    │ 16:45      │   ✓    │ [👁]  ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ D. PANEL DETALLE JOB                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ JOB: regression_checks                               [✓] ACTIVO   │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │                                                                   │ │
│  │ PROPÓSITO                                                         │ │
│  │ Ejecuta automáticamente los checks de regresión sobre módulos    │ │
│  │ críticos para detectar anomalías antes de que afecten la         │ │
│  │ operación.                                                        │ │
│  │                                                                   │ │
│  │ CONFIGURACIÓN                                                     │ │
│  │ • Frecuencia: Cada 15 minutos                                     │ │
│  │ • Timeout: 60 segundos                                            │ │
│  │ • Reintentos: 3                                                   │ │
│  │                                                                   │ │
│  │ DEPENDENCIAS                                                      │ │
│  │ • MongoDB (configuración)                                         │ │
│  │ • Connection Resolver                                             │ │
│  │ • Servicios de módulos                                            │ │
│  │                                                                   │ │
│  │ HISTORIAL RECIENTE                                                │ │
│  │ ┌─────────────────────────────────────────────────────────────┐  │ │
│  │ │ 16:45 ✓ OK (12ms) | 16:30 ✓ OK (15ms) | 16:15 ✓ OK (11ms)  │  │ │
│  │ │ 16:00 ✓ OK (14ms) | 15:45 ✓ OK (12ms) | 15:30 ✓ OK (13ms)  │  │ │
│  │ └─────────────────────────────────────────────────────────────┘  │ │
│  │                                                                   │ │
│  │ IMPACTO SI FALLA                                                  │ │
│  │ • No se detectarán regresiones automáticamente                    │ │
│  │ • Alertas manuales requeridas                                     │ │
│  │ • Severidad: ALTA                                                 │ │
│  │                                                                   │ │
│  │                     [Ejecutar ahora] [Pausar] [Ver logs]          │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. PANTALLA 6: CAMBIOS Y DESPLIEGUES

### 10.1 Objetivo
Trazabilidad de cambios recientes y su posible impacto.

### 10.2 Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│ CAMBIOS Y DESPLIEGUES                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ A. KPIs                                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │    3     │  │    8     │  │    1     │  │    0     │  │    5     │  │
│  │ CAMBIOS  │  │ CAMBIOS  │  │ DEPLOYS  │  │  RIESGO  │  │ MÓDULOS  │  │
│  │   hoy    │  │  7 días  │  │ reciente │  │  ALTO    │  │ TOCADOS  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ B. TABLA DE CAMBIOS                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │ Fecha    │ Cambio              │ Tipo   │ Módulo  │Riesgo│ Status ││
│  ├──────────┼─────────────────────┼────────┼─────────┼──────┼────────┤│
│  │ 19/04    │ Centro Control v2   │ deploy │ Sistema │ BAJO │   ✓    ││
│  │ 19/04    │ Health checker init │ config │ Core    │ BAJO │   ✓    ││
│  │ 19/04    │ Blindaje Tablero    │ docs   │ Tablero │ N/A  │   ✓    ││
│  │ 18/04    │ ConnectionResolver  │ código │ Core    │ MEDIO│   ✓    ││
│  │ 18/04    │ Fix cache $0        │ hotfix │ Tablero │ ALTO │   ✓    ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ C. PANEL DE DETALLE DE CAMBIO                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ CAMBIO: Fix cache ventas $0                       [HOTFIX] 🩹     │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │                                                                   │ │
│  │ QUÉ SE PIDIÓ                                                      │ │
│  │ Corregir bug donde ventas acumuladas mostraban $0 cuando la      │ │
│  │ conexión SQL fallaba, contaminando la caché.                      │ │
│  │                                                                   │ │
│  │ QUÉ SE TOCÓ                                                       │ │
│  │ • backend/modules/comercial/service.py (líneas 120-180)           │ │
│  │ • backend/core/connection_resolver.py (líneas 45-60)              │ │
│  │                                                                   │ │
│  │ ARCHIVOS MODIFICADOS                                              │ │
│  │ ┌─────────────────────────────────────────────────────────────┐  │ │
│  │ │ modules/comercial/service.py      (+15, -8)                 │  │ │
│  │ │ core/connection_resolver.py       (+42, -0)                 │  │ │
│  │ └─────────────────────────────────────────────────────────────┘  │ │
│  │                                                                   │ │
│  │ CHECKLIST DE CUMPLIMIENTO                                         │ │
│  │ [✓] Snapshot realizado                                            │ │
│  │ [✓] Pruebas ejecutadas                                            │ │
│  │ [✓] Documentación actualizada                                     │ │
│  │ [✓] Validación de no regresión                                    │ │
│  │ [✓] Autorización obtenida                                         │ │
│  │                                                                   │ │
│  │ RESULTADO POST-CAMBIO                                             │ │
│  │ • Sin alertas generadas                                           │ │
│  │ • Tablero Ejecutivo verificado OK                                 │ │
│  │ • No se detectaron regresiones                                    │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ D. CHECKLIST DE CAMBIO CONTROLADO                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Antes de cualquier cambio en módulo blindado:                         │
│                                                                         │
│  □ 1. Crear snapshot del estado actual                                 │
│  □ 2. Documentar el cambio solicitado                                  │
│  □ 3. Implementar en aislamiento                                       │
│  □ 4. Ejecutar pruebas de regresión                                    │
│  □ 5. Validar con datos reales                                         │
│  □ 6. Obtener autorización                                             │
│  □ 7. Aplicar cambio                                                   │
│  □ 8. Monitorear 24h                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. PANTALLA 7: BITÁCORA / HISTORIAL

### 11.1 Objetivo
Historial navegable de eventos del sistema.

### 11.2 Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│ BITÁCORA DEL SISTEMA                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ FILTROS                                                                 │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │
│ │ 📅 Fecha     │ │ Módulo    ▼  │ │ Tipo      ▼  │ │ Severidad   ▼  │  │
│ │ Últimas 24h  │ │   Todos      │ │   Todos      │ │   Todas        │  │
│ └──────────────┘ └──────────────┘ └──────────────┘ └────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│ TIMELINE DE EVENTOS                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  19 de Abril, 2026                                                      │
│  ───────────────                                                        │
│                                                                         │
│  16:45  [●] health_check                                                │
│         Health check completado exitosamente                            │
│         Sistema | Info                                                  │
│                                                                         │
│  16:45  [●] regression_check                                            │
│         Regression check: 4/4 módulos OK                                │
│         Sistema | Info                                                  │
│                                                                         │
│  16:30  [🚀] deploy                                                     │
│         Centro de Control EDARSA v2.0 implementado                      │
│         Sistema | Info                                                  │
│                                                                         │
│  15:45  [🛡] blindaje                                                   │
│         Módulo "Tablero Ejecutivo" cerrado y blindado                   │
│         Tablero | Info                                                  │
│                                                                         │
│  15:30  [🛡] blindaje                                                   │
│         Módulo "Auditoría de Compras" cerrado y blindado                │
│         Compras | Info                                                  │
│                                                                         │
│  15:15  [🛡] blindaje                                                   │
│         Módulo "Operaciones/Análisis" cerrado y blindado                │
│         Operaciones | Info                                              │
│                                                                         │
│  14:30  [✓] fuente_recuperada                                           │
│         Conexión SQL Cienfuegos restaurada                              │
│         Fuentes | Info                                                  │
│                                                                         │
│  14:25  [✗] fuente_caida                                                │
│         Timeout en conexión SQL Cienfuegos                              │
│         Fuentes | Warning                                               │
│                                                                         │
│  ───────────────────────────────────────────────────────────────────── │
│                                                                         │
│  18 de Abril, 2026                                                      │
│  ───────────────                                                        │
│                                                                         │
│  23:45  [●] health_check                                                │
│         Health check completado exitosamente                            │
│         Sistema | Info                                                  │
│                                                                         │
│  ...                                                                    │
│                                                                         │
│                          [Cargar más eventos]                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.3 Tipos de Evento

| Tipo | Icono | Descripción |
|------|-------|-------------|
| `health_check` | ● | Check de salud ejecutado |
| `regression_check` | ● | Check de regresión ejecutado |
| `alerta_detectada` | ⚠ | Nueva alerta generada |
| `alerta_resuelta` | ✓ | Alerta marcada como resuelta |
| `fuente_caida` | ✗ | Fuente de datos no responde |
| `fuente_recuperada` | ✓ | Fuente de datos recuperada |
| `job_error` | ✗ | Job falló |
| `job_ok` | ✓ | Job completado exitosamente |
| `deploy` | 🚀 | Despliegue realizado |
| `blindaje` | 🛡 | Módulo blindado/documentado |
| `cambio_codigo` | 📝 | Cambio de código |
| `config` | ⚙ | Cambio de configuración |
| `incidente` | 🔥 | Incidente registrado |
| `hotfix` | 🩹 | Hotfix aplicado |

---

## 12. PANTALLA 8: CONFIGURACIÓN Y REGLAS DE BLINDAJE

### 12.1 Objetivo
Mostrar qué módulos están blindados, qué reglas aplican y qué protocolo se exige.

### 12.2 Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│ CONFIGURACIÓN Y REGLAS DE BLINDAJE                                      │
├─────────────────────────────────────────────────────────────────────────┤
│ A. MÓDULOS BLINDADOS                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 🛡 TABLERO EJECUTIVO                                              │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ Status: BLINDADO desde 19/04/2026                                 │ │
│  │ Documento: CIERRE_Y_BLINDAJE_TABLERO_EJECUTIVO.md                 │ │
│  │                                                                   │ │
│  │ Archivos críticos:                                                │ │
│  │ • backend/modules/comercial/service.py                            │ │
│  │ • frontend/src/pages/Comercial.js                                 │ │
│  │ • backend/core/connection_resolver.py                             │ │
│  │                                                                   │ │
│  │ Cambio permitido: SOLO CON AUTORIZACIÓN EXPRESA                   │ │
│  │                                            [Ver documento completo]│ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 🛡 AUDITORÍA DE COMPRAS                                           │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ Status: BLINDADO desde 19/04/2026                                 │ │
│  │ Documento: CIERRE_Y_BLINDAJE_AUDITORIA_COMPRAS.md                 │ │
│  │                                            [Ver documento completo]│ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 🛡 OPERACIONES / ANÁLISIS                                         │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ Status: BLINDADO desde 19/04/2026                                 │ │
│  │ Documento: CIERRE_Y_BLINDAJE_OPERACIONES_ANALISIS.md              │ │
│  │                                            [Ver documento completo]│ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ B. PROTOCOLO GLOBAL DE CAMBIOS                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ PROTOCOLO GLOBAL DE CAMBIOS EDARSA HUB                            │ │
│  │ Documento: PROTOCOLO_GLOBAL_CAMBIOS_EDARSA.md                     │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │                                                                   │ │
│  │ CHECKLIST OBLIGATORIO                                             │ │
│  │                                                                   │ │
│  │ □ 1. SNAPSHOT                                                     │ │
│  │      Crear respaldo del estado actual antes de cualquier cambio   │ │
│  │                                                                   │ │
│  │ □ 2. DOCUMENTACIÓN                                                │ │
│  │      Registrar qué se va a cambiar y por qué                      │ │
│  │                                                                   │ │
│  │ □ 3. AISLAMIENTO                                                  │ │
│  │      Implementar cambios en entorno aislado                       │ │
│  │                                                                   │ │
│  │ □ 4. PRUEBAS                                                      │ │
│  │      Ejecutar pruebas de regresión obligatorias                   │ │
│  │                                                                   │ │
│  │ □ 5. VALIDACIÓN                                                   │ │
│  │      Verificar con datos reales de producción                     │ │
│  │                                                                   │ │
│  │ □ 6. AUTORIZACIÓN                                                 │ │
│  │      Obtener aprobación explícita antes de aplicar                │ │
│  │                                                                   │ │
│  │ □ 7. MONITOREO                                                    │ │
│  │      Vigilar sistema 24h después del cambio                       │ │
│  │                                                                   │ │
│  │                                           [Ver protocolo completo]│ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ C. MATRIZ DE RIESGO                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │ Tipo de Cambio          │ Riesgo  │ Requisito Obligatorio         ││
│  ├─────────────────────────┼─────────┼───────────────────────────────┤│
│  │ Módulo blindado         │ CRÍTICO │ Protocolo completo + autor.   ││
│  │ Connection Resolver     │ ALTO    │ Snapshot + pruebas + docs     ││
│  │ Servicios comerciales   │ ALTO    │ Snapshot + pruebas            ││
│  │ Frontend visual         │ MEDIO   │ Pruebas                       ││
│  │ Documentación           │ BAJO    │ Review                        ││
│  │ Configuración           │ MEDIO   │ Snapshot + pruebas            ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ D. ARCHIVOS CRÍTICOS DEL SISTEMA                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │ Módulo       │ Archivo                          │ Criticidad      ││
│  ├──────────────┼──────────────────────────────────┼─────────────────┤│
│  │ Tablero      │ modules/comercial/service.py     │ 🔴 CRÍTICO      ││
│  │ Tablero      │ pages/Comercial.js               │ 🔴 CRÍTICO      ││
│  │ Core         │ core/connection_resolver.py      │ 🔴 CRÍTICO      ││
│  │ Core         │ core/providers.py                │ 🟡 ALTO         ││
│  │ Compras      │ modules/compras/service.py       │ 🟡 ALTO         ││
│  │ Core         │ core/security.py                 │ 🔴 CRÍTICO      ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ E. DOCUMENTOS VINCULADOS                                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📄 CIERRE_Y_BLINDAJE_TABLERO_EJECUTIVO.md                              │
│  📄 CIERRE_Y_BLINDAJE_AUDITORIA_COMPRAS.md                              │
│  📄 CIERRE_Y_BLINDAJE_OPERACIONES_ANALISIS.md                           │
│  📄 PROTOCOLO_GLOBAL_CAMBIOS_EDARSA.md                                  │
│  📄 ARQUITECTURA_CONEXIONES_RESOLVER.md                                 │
│  📄 MATRIZ_FUENTES_TABLERO_EJECUTIVO.md                                 │
│  📄 CENTRO_CONTROL_EDARSA.md                                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 13. COMPONENTES UI REUTILIZABLES

### 13.1 Catálogo de Componentes

| Componente | Uso | Props Principales |
|------------|-----|-------------------|
| `SemaforoGlobal` | Indicador principal de estado | status, size |
| `KPICard` | Métricas numéricas | value, label, icon, status |
| `StatusBadge` | Indicador inline de estado | status, size |
| `AlertaRow` | Fila de alerta en lista | alerta, onAcknowledge |
| `ModuloCard` | Card de estado de módulo | modulo, onClick |
| `FuenteCard` | Card de estado de fuente | fuente, onClick |
| `JobRow` | Fila de job en tabla | job, onExecute |
| `EventoRow` | Fila de evento en timeline | evento |
| `CambioRow` | Fila de cambio en tabla | cambio, onClick |
| `ChecklistItem` | Item de checklist | label, checked, required |
| `MatrizRow` | Fila de matriz relación | data |
| `TimelineEvent` | Evento en línea de tiempo | evento |
| `PanelDetalle` | Panel lateral de detalle | title, children, onClose |
| `BannerAlerta` | Banner de alerta crítica | mensaje, count, onClick |
| `FilterBar` | Barra de filtros | filters, onChange |
| `TabsNavigation` | Navegación por tabs | tabs, activeTab, onChange |

### 13.2 Especificación StatusBadge

```
┌─────────────────────────────────────────────────────────────────┐
│ COMPONENTE: StatusBadge                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Variantes:                                                      │
│                                                                 │
│ [✓ SALUDABLE]     bg-green-500/20 text-green-400 border-green   │
│ [⚠ ADVERTENCIA]   bg-yellow-500/20 text-yellow-400 border-yellow│
│ [✗ CRÍTICO]       bg-red-500/20 text-red-400 border-red         │
│ [? DESCONOCIDO]   bg-gray-500/20 text-gray-400 border-gray      │
│ [🛡 BLINDADO]     bg-blue-500/20 text-blue-400 border-blue      │
│ [▶ RUNNING]       bg-green-500/20 text-green-400 border-green   │
│ [⏸ PAUSADO]       bg-yellow-500/20 text-yellow-400 border-yellow│
│ [⏹ DETENIDO]      bg-gray-500/20 text-gray-400 border-gray      │
│                                                                 │
│ Tamaños:                                                        │
│ sm: text-xs px-2 py-0.5                                         │
│ md: text-sm px-2.5 py-1                                         │
│ lg: text-base px-3 py-1.5                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 14. ESTADOS Y MENSAJES

### 14.1 Estados Vacíos

```
┌─────────────────────────────────────────────────────────────────┐
│ ESTADO VACÍO: Sin Alertas                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                      ┌─────────────┐                            │
│                      │     ✓       │                            │
│                      │   (48px)    │                            │
│                      └─────────────┘                            │
│                                                                 │
│              Sin alertas activas                                │
│                                                                 │
│        El sistema está funcionando correctamente                │
│                                                                 │
│              [Ver historial de alertas]                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ESTADO VACÍO: Sin Jobs                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                      ┌─────────────┐                            │
│                      │     📅      │                            │
│                      │   (48px)    │                            │
│                      └─────────────┘                            │
│                                                                 │
│               No hay jobs registrados                           │
│                                                                 │
│      Configure automatizaciones en el scheduler                 │
│                                                                 │
│                 [Ir a configuración]                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 14.2 Estados de Error

```
┌─────────────────────────────────────────────────────────────────┐
│ ESTADO ERROR: Falla de Conexión                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ ⚠ No se pudo conectar al Centro de Control                │ │
│  │                                                           │ │
│  │   Error: Connection timeout after 30s                     │ │
│  │                                                           │ │
│  │   [Reintentar]  [Ver logs técnicos]                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ESTADO ERROR: Sin Permisos                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 🔒 Acceso restringido                                     │ │
│  │                                                           │ │
│  │   No tiene permisos para acceder al Centro de Control.    │ │
│  │   Contacte al administrador del sistema.                  │ │
│  │                                                           │ │
│  │   Roles requeridos: Administrador, Supervisor, Director   │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 14.3 Mensajes de Confirmación

```
┌─────────────────────────────────────────────────────────────────┐
│ CONFIRMACIÓN: Reconocer Alerta                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ ¿Reconocer esta alerta?                                   │ │
│  │                                                           │ │
│  │ Al reconocer la alerta, confirma que ha sido revisada.    │ │
│  │ La alerta permanecerá en el historial.                    │ │
│  │                                                           │ │
│  │ Comentario (opcional):                                    │ │
│  │ ┌───────────────────────────────────────────────────┐    │ │
│  │ │                                                   │    │ │
│  │ └───────────────────────────────────────────────────┘    │ │
│  │                                                           │ │
│  │                      [Cancelar]  [Reconocer]              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 15. FLUJOS DE NAVEGACIÓN

### 15.1 Flujo: Detectar y Resolver Alerta

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO: Detectar y Resolver Alerta Crítica                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐   │
│  │ Resumen │ ──► │  Banner │ ──► │ Alertas │ ──► │ Detalle │   │
│  │ General │     │ Crítico │     │  Lista  │     │ Alerta  │   │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘   │
│       │                                               │         │
│       │                                               ▼         │
│       │                                         ┌─────────┐     │
│       │                                         │Reconocer│     │
│       │                                         │ Alerta  │     │
│       │                                         └─────────┘     │
│       │                                               │         │
│       │         ┌─────────┐     ┌─────────┐          │         │
│       └────────►│ Fuentes │ ◄─► │ Detalle │ ◄────────┘         │
│                 │  Lista  │     │ Fuente  │                     │
│                 └─────────┘     └─────────┘                     │
│                                                                 │
│ Acciones del usuario:                                           │
│ 1. Ve semáforo rojo en Resumen General                          │
│ 2. Ve banner "X alertas críticas"                               │
│ 3. Click en "Ver alertas"                                       │
│ 4. Selecciona alerta de la lista                                │
│ 5. Ve detalle y evidencia técnica                               │
│ 6. Navega a fuentes relacionadas si necesita                    │
│ 7. Reconoce alerta cuando está siendo atendida                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 15.2 Flujo: Verificar Impacto de Cambio

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO: Verificar Impacto de Cambio Reciente                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐   │
│  │ Cambios │ ──► │ Detalle │ ──► │ Módulos │ ──► │ Alertas │   │
│  │  Lista  │     │ Cambio  │     │Afectados│     │  Lista  │   │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘   │
│                       │                                         │
│                       ▼                                         │
│                 ┌─────────┐                                     │
│                 │ Archivos│                                     │
│                 │Críticos │                                     │
│                 └─────────┘                                     │
│                                                                 │
│ Pregunta a responder:                                           │
│ "¿El cambio de ayer causó el problema de hoy?"                  │
│                                                                 │
│ Acciones:                                                       │
│ 1. Ir a Cambios y Despliegues                                   │
│ 2. Filtrar por fecha del problema                               │
│ 3. Ver qué cambios se hicieron                                  │
│ 4. Ver qué módulos fueron afectados                             │
│ 5. Verificar si hay alertas en esos módulos                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 16. ESPECIFICACIÓN DE ENDPOINTS

### 16.1 Endpoints Requeridos

| Endpoint | Método | Descripción | Pantalla |
|----------|--------|-------------|----------|
| `/api/centro-control/estado` | GET | Estado general consolidado | Resumen |
| `/api/centro-control/salud` | GET | Reporte completo de salud | Salud |
| `/api/centro-control/salud/resumen` | GET | KPIs ejecutivos | Resumen |
| `/api/centro-control/modulos` | GET | Lista de módulos con estado | Salud |
| `/api/centro-control/modulos/{id}` | GET | Detalle de módulo | Salud |
| `/api/centro-control/modulos/{id}/checks` | GET | Checks del módulo | Salud |
| `/api/centro-control/alertas` | GET | Lista de alertas | Alertas |
| `/api/centro-control/alertas/{id}` | GET | Detalle de alerta | Alertas |
| `/api/centro-control/alertas/acknowledge` | POST | Reconocer alerta | Alertas |
| `/api/centro-control/regresiones` | POST | Ejecutar checks | Alertas |
| `/api/centro-control/fuentes` | GET | Lista de fuentes | Conectividad |
| `/api/centro-control/fuentes/{id}` | GET | Detalle de fuente | Conectividad |
| `/api/centro-control/fuentes/matriz` | GET | Matriz fuente-módulo | Conectividad |
| `/api/centro-control/jobs` | GET | Lista de jobs | Jobs |
| `/api/centro-control/jobs/{id}` | GET | Detalle de job | Jobs |
| `/api/centro-control/jobs/{id}/execute` | POST | Ejecutar job | Jobs |
| `/api/centro-control/cambios` | GET | Lista de cambios | Cambios |
| `/api/centro-control/cambios/{id}` | GET | Detalle de cambio | Cambios |
| `/api/centro-control/bitacora` | GET | Eventos del sistema | Bitácora |
| `/api/centro-control/bitacora` | POST | Registrar evento | Bitácora |
| `/api/centro-control/blindaje` | GET | Módulos blindados | Config |
| `/api/centro-control/blindaje/protocolo` | GET | Protocolo global | Config |
| `/api/centro-control/blindaje/matriz-riesgo` | GET | Matriz de riesgo | Config |
| `/api/centro-control/metricas` | GET | Métricas de estabilidad | Resumen |
| `/api/centro-control/historial` | GET | Historial de eventos | Bitácora |

### 16.2 Estructura de Response Tipo

```json
{
  "estado_general": {
    "status": "healthy",
    "emoji": "✓",
    "timestamp": "2026-04-19T16:45:32Z"
  },
  "kpis": {
    "modulos_sanos": { "valor": 6, "total": 6, "pct": 100 },
    "alertas_criticas": 0,
    "fuentes_caidas": 0,
    "jobs_fallidos": 0,
    "regresiones_24h": 0
  },
  "semaforos": {
    "sistema": "healthy",
    "datos": "healthy",
    "conexiones": "healthy",
    "jobs": "healthy",
    "blindaje": "healthy"
  },
  "modulos": [
    {
      "id": "tablero_ejecutivo",
      "nombre": "Tablero Ejecutivo",
      "status": "healthy",
      "alertas": 0,
      "blindado": true,
      "confiabilidad": 100
    }
  ],
  "alertas_top": [],
  "eventos_recientes": []
}
```

---

## 17. RECOMENDACIONES DE IMPLEMENTACIÓN

### 17.1 Arquitectura Frontend

```
/src/pages/CentroControl/
├── index.jsx                    # Entry point, tabs navigation
├── components/
│   ├── HeaderCentroControl.jsx  # Encabezado + semáforo global
│   ├── KPIGrid.jsx              # Grid de KPIs superiores
│   ├── SemaforoCategoria.jsx    # Semáforos por categoría
│   ├── TopAlertas.jsx           # Panel top alertas
│   ├── FuentesResumen.jsx       # Mini panel fuentes
│   ├── ModulosGrid.jsx          # Grid de módulos
│   ├── EventosRecientes.jsx     # Lista eventos
│   └── ...
├── tabs/
│   ├── ResumenGeneral.jsx
│   ├── SaludModulo.jsx
│   ├── AlertasRegresiones.jsx
│   ├── ConectividadFuentes.jsx
│   ├── JobsAutomatizaciones.jsx
│   ├── CambiosDespliegues.jsx
│   ├── Bitacora.jsx
│   └── ConfigBlindaje.jsx
├── hooks/
│   ├── useCentroControl.js      # Hook principal de datos
│   ├── useAlertas.js
│   ├── useFuentes.js
│   └── ...
└── services/
    └── centroControlService.js  # API calls
```

### 17.2 Prioridad de Implementación

| Fase | Componentes | Prioridad |
|------|-------------|-----------|
| **Fase 1** | Resumen General completo | P0 |
| **Fase 2** | Alertas y Regresiones | P0 |
| **Fase 3** | Salud por Módulo | P1 |
| **Fase 4** | Conectividad y Fuentes | P1 |
| **Fase 5** | Jobs y Automatizaciones | P2 |
| **Fase 6** | Cambios y Despliegues | P2 |
| **Fase 7** | Bitácora | P2 |
| **Fase 8** | Config y Blindaje | P2 |

### 17.3 Consideraciones Técnicas

1. **Polling vs WebSockets**
   - Para alertas críticas: considerar WebSocket
   - Para resto: polling cada 30-60 segundos

2. **Caching**
   - Cachear estado general por 30 segundos
   - Invalidar al recibir nueva alerta

3. **Responsive**
   - Mobile: tabs colapsables
   - Tablet: 2 columnas
   - Desktop: layout completo

4. **Accesibilidad**
   - Colores con suficiente contraste
   - Iconos siempre con texto
   - Navegación por teclado

---

## CRITERIO DE ACEPTACIÓN

Este wireframe se considera completo si:

- [ ] Cubre las 8 pantallas definidas
- [ ] Cada pantalla tiene layout wireframe detallado
- [ ] Se definen todos los componentes UI reutilizables
- [ ] Se especifican estados vacíos y de error
- [ ] Se documentan flujos de navegación
- [ ] Se listan endpoints necesarios
- [ ] Se incluyen recomendaciones de implementación
- [ ] Es claro para Dirección
- [ ] Es útil para Soporte Técnico
- [ ] Está listo para implementación

---

**Documento creado:** 19 de Abril, 2026  
**Última actualización:** 19 de Abril, 2026  
**Autor:** Arquitectura UX/UI EDARSA HUB  
**Revisado por:** [Pendiente]  
**Aprobado por:** [Pendiente]
