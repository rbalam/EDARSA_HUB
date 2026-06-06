# ARQUITECTURA: Automatización de Análisis de Inventarios
## EDARSA HUB - Documento de Diseño Técnico

**Versión**: 1.0  
**Fecha**: Diciembre 2025  
**Estado**: DISEÑO - PENDIENTE APROBACIÓN  
**Autor**: Arquitecto de Software Senior  
**Clasificación**: CAB-003 (Change Advisory Board)

---

## ÍNDICE

1. [Objetivo del Proceso](#1-objetivo-del-proceso)
2. [Restricciones Operativas](#2-restricciones-operativas)
3. [Flujo Extremo a Extremo](#3-flujo-extremo-a-extremo)
4. [Componentes Existentes Reutilizables](#4-componentes-existentes-reutilizables)
5. [Componentes Intocables](#5-componentes-intocables)
6. [Componentes Nuevos Desacoplados](#6-componentes-nuevos-desacoplados)
7. [Arquitectura Propuesta](#7-arquitectura-propuesta)
8. [Detección de Nuevos Folios](#8-detección-de-nuevos-folios)
9. [Resolución de Inventario Inicial](#9-resolución-de-inventario-inicial)
10. [Generación de Análisis 1:1](#10-generación-de-análisis-11)
11. [Diseño de Destinatarios](#11-diseño-de-destinatarios)
12. [Resolución de Destinatarios](#12-resolución-de-destinatarios)
13. [Estrategia Anti-Duplicados](#13-estrategia-anti-duplicados)
14. [Bitácora](#14-bitácora)
15. [Exportación Excel/PDF](#15-exportación-excelpdf)
16. [Envío de Correo](#16-envío-de-correo)
17. [Envío de WhatsApp](#17-envío-de-whatsapp)
18. [Auditoría y Reprocesos](#18-auditoría-y-reprocesos)
19. [Estrategia de No Regresión](#19-estrategia-de-no-regresión)
20. [Plan por Fases](#20-plan-por-fases)
21. [Riesgos y Mitigaciones](#21-riesgos-y-mitigaciones)
22. [Integración con RBAC](#22-integración-con-rbac)
23. [Anexos](#23-anexos)

---

## 1. OBJETIVO DEL PROCESO

### 1.1 Objetivo Principal
Automatizar la detección de nuevos inventarios físicos finales capturados por almacén y, al detectarlos, generar y enviar automáticamente un análisis de inventario por almacén.

### 1.2 Beneficios Esperados
| Aspecto | Estado Actual | Estado Objetivo |
|---------|---------------|-----------------|
| Tiempo auditor | 15-30 min por análisis | 0 min (automático) |
| Errores humanos | Variables | Eliminados |
| Trazabilidad | Manual | Completa y automática |
| Cobertura | Dependiente de disponibilidad | 100% de inventarios |
| Tiempo de envío | Horas | Minutos tras captura |

### 1.3 Alcance
- **IN SCOPE**: SoftRestaurant, MPRO
- **OUT OF SCOPE (Fase 1)**: Otros sistemas origen

---

## 2. RESTRICCIONES OPERATIVAS

### 2.1 Restricciones de Arquitectura (CRÍTICAS)

| ID | Restricción | Severidad |
|----|-------------|-----------|
| R-001 | No crear tablas en SoftRestaurant ni MPRO | BLOQUEANTE |
| R-002 | Solo SELECT a sistemas origen | BLOQUEANTE |
| R-003 | Tablas nuevas SOLO en EDARSA HUB SQL Server | BLOQUEANTE |
| R-004 | MongoDB solo para cache temporal | ALTA |
| R-005 | No romper funcionalidad existente | BLOQUEANTE |

### 2.2 Restricciones de Negocio

| ID | Restricción | Severidad |
|----|-------------|-----------|
| R-006 | 1 análisis por almacén (no multi-almacén) | ALTA |
| R-007 | Análisis IDÉNTICO al menú actual | ALTA |
| R-008 | Respetar filtros y permisos RBAC | ALTA |
| R-009 | Evitar duplicados de envío | ALTA |
| R-010 | Trazabilidad completa obligatoria | ALTA |

### 2.3 Restricciones de Rendimiento

| ID | Restricción | Valor |
|----|-------------|-------|
| R-011 | Timeout máximo query SQL | 120 segundos |
| R-012 | Intervalo mínimo de polling | 5 minutos |
| R-013 | Tamaño máximo archivo Excel | 10 MB |
| R-014 | Tamaño máximo adjunto email | 25 MB |

---

## 3. FLUJO EXTREMO A EXTREMO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUJO DE AUTOMATIZACIÓN                           │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  SCHEDULER       │ (Cada X minutos configurable)
    │  (Backend Job)   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ 1. DETECCIÓN     │ Query a SOFT/MPRO
    │    NUEVOS FOLIOS │ Comparar vs último conocido
    └────────┬─────────┘
             │
             │ ¿Nuevo folio detectado?
             │
    ┌────────┴────────┐
    │ NO              │ SI
    │ (Esperar        │
    │  próximo ciclo) │
    └─────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ 2. VALIDACIÓN    │ ¿Ya procesado? (anti-duplicado)
    │    DUPLICADOS    │ Verificar en control EDARSA HUB
    └────────┬─────────┘
             │
             │ ¿Ya procesado?
             │
    ┌────────┴────────┐
    │ SI              │ NO
    │ (Log y saltar)  │
    └─────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ 3. IDENTIFICAR   │ - server_id
    │    CONTEXTO      │ - sucursal_id
    │                  │ - almacen_id
    │                  │ - fecha_folio_nuevo
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ 4. CALCULAR      │ SOFT: primer inventario del mes
    │    INV. INICIAL  │ MPRO: último inventario mes anterior
    └────────┬─────────┘
             │
             │ ¿Existe inv inicial válido?
             │
    ┌────────┴────────┐
    │ NO              │ SI
    │ (Log error,     │
    │  alerta admin)  │
    └─────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ 5. GENERAR       │ Reutilizar EXACTAMENTE
    │    ANÁLISIS      │ lógica de /reports/inventory-analysis
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ 6. EXPORTAR      │ Excel (formato actual)
    │    ARCHIVOS      │ PDF (opcional)
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ 7. RESOLVER      │ Buscar en configuración:
    │    DESTINATARIOS │ servidor → sucursal → almacén
    │                  │ Acumular sin duplicar
    └────────┬─────────┘
             │
             │ ¿Hay destinatarios activos?
             │
    ┌────────┴────────┐
    │ NO              │ SI
    │ (Log warning,   │
    │  no enviar)     │
    └─────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ 8. ENVIAR        │ - Email (To/CC/BCC)
    │    NOTIFICACIÓN  │ - WhatsApp (opcional)
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ 9. REGISTRAR     │ Guardar en EDARSA HUB:
    │    BITÁCORA      │ - Timestamp
    │                  │ - Folio procesado
    │                  │ - Destinatarios
    │                  │ - Resultado
    │                  │ - Archivos generados
    └──────────────────┘
```

---

## 4. COMPONENTES EXISTENTES REUTILIZABLES

### 4.1 Lógica de Análisis de Inventarios

| Componente | Ubicación | Reutilización |
|------------|-----------|---------------|
| Query inventarios MPRO | `modules/compras/repository.py:71` | ✅ REUTILIZAR |
| Query inventarios SoftRestaurant | `modules/compras/repository.py:100` | ✅ REUTILIZAR |
| Análisis completo | `server.py:2363` `/reports/inventory-analysis` | ✅ REUTILIZAR LÓGICA INTERNA |
| Exportación Excel | `server.py:3984` `/reports/export/excel` | ✅ REUTILIZAR |
| Exportación PDF | `server.py:4006` `/reports/export/pdf` | ✅ REUTILIZAR |

### 4.2 Infraestructura de Datos

| Componente | Ubicación | Reutilización |
|------------|-----------|---------------|
| `execute_sql_query()` | `core/db.py` | ✅ REUTILIZAR |
| Conexión SQL resiliente | `core/resilient_sql.py` | ✅ REUTILIZAR |
| Pool de conexiones | `core/pool.py` | ✅ REUTILIZAR |

### 4.3 Seguridad y Permisos

| Componente | Ubicación | Reutilización |
|------------|-----------|---------------|
| `filter_servers_by_permissions()` | `core/security.py:210` | ✅ REUTILIZAR |
| `filter_sucursales_by_permissions()` | `core/security.py:238` | ✅ REUTILIZAR |
| `user_has_server_access()` | `core/security.py:193` | ✅ REUTILIZAR |

### 4.4 Auditoría

| Componente | Ubicación | Reutilización |
|------------|-----------|---------------|
| `registrar_auditoria()` | `core/auditoria.py` | ✅ REUTILIZAR |
| `auditoria_helpers` | `core/auditoria_helpers.py` | ✅ EXTENDER |

---

## 5. COMPONENTES INTOCABLES

### 5.1 Módulo Análisis de Inventarios UI (PROTEGIDO)

| Archivo | Razón de Protección |
|---------|---------------------|
| `Reportes.js` | UI de producción activa |
| Tab "Análisis de Inventarios" | Flujo manual debe seguir funcionando |
| Filtros existentes | No alterar lógica de selección |

**REGLA**: El módulo manual NO se modifica. La automatización corre EN PARALELO.

### 5.2 Módulo Tesorería (PROTEGIDO)

| Archivo | Razón de Protección |
|---------|---------------------|
| `TesoreriaCorteZ.jsx` | Componente crítico de producción |
| `tesoreria.py` | Backend en uso |
| Endpoints `/api/finanzas/tesoreria/*` | Operación real |

**REGLA**: No existe relación funcional. No tocar.

### 5.3 Endpoints de Reportes Existentes

| Endpoint | Razón de Protección |
|----------|---------------------|
| `POST /reports/inventory-analysis` | Usar lógica INTERNA, no modificar endpoint |
| `POST /reports/export/excel` | Reutilizar, no modificar |
| `GET /compras/inventarios-fisicos/{server_id}` | Solo lectura |

---

## 6. COMPONENTES NUEVOS DESACOPLADOS

### 6.1 Tablas SQL Server (EDARSA HUB)

#### 6.1.1 `automatizacion_inventarios_config`
```
Propósito: Configuración general de la automatización por servidor/sucursal/almacén

Campos:
- config_id (PK, UNIQUEIDENTIFIER)
- server_id (VARCHAR(50), NOT NULL)
- sucursal_id (VARCHAR(50), NULL)  -- NULL = aplica a todo el servidor
- almacen_id (VARCHAR(50), NULL)   -- NULL = aplica a toda la sucursal
- activo (BIT, DEFAULT 1)
- intervalo_polling_minutos (INT, DEFAULT 15)
- hora_inicio_operacion (TIME, DEFAULT '00:00')  -- Horario de operación
- hora_fin_operacion (TIME, DEFAULT '23:59')
- generar_excel (BIT, DEFAULT 1)
- generar_pdf (BIT, DEFAULT 0)
- created_at (DATETIME2)
- created_by (VARCHAR(100))
- updated_at (DATETIME2)
- updated_by (VARCHAR(100))

Índices:
- IX_config_server_suc_alm (server_id, sucursal_id, almacen_id) UNIQUE
```

#### 6.1.2 `automatizacion_inventarios_destinatarios`
```
Propósito: Destinatarios por nivel jerárquico

Campos:
- destinatario_id (PK, UNIQUEIDENTIFIER)
- server_id (VARCHAR(50), NOT NULL)
- sucursal_id (VARCHAR(50), NULL)  -- NULL = nivel servidor
- almacen_id (VARCHAR(50), NULL)   -- NULL = nivel sucursal
- usuario_id (VARCHAR(100), NULL)  -- FK a users.email o NULL si externo
- nombre_destinatario (VARCHAR(200), NOT NULL)
- email (VARCHAR(200), NULL)
- telefono_whatsapp (VARCHAR(20), NULL)
- tipo_envio_email (VARCHAR(10), CHECK IN ('TO', 'CC', 'BCC'))
- enviar_email (BIT, DEFAULT 1)
- enviar_whatsapp (BIT, DEFAULT 0)
- activo (BIT, DEFAULT 1)
- created_at (DATETIME2)
- created_by (VARCHAR(100))

Índices:
- IX_dest_server_suc_alm (server_id, sucursal_id, almacen_id)
- IX_dest_email (email)
```

#### 6.1.3 `automatizacion_inventarios_folios_procesados`
```
Propósito: Control anti-duplicados (idempotencia)

Campos:
- procesado_id (PK, UNIQUEIDENTIFIER)
- server_id (VARCHAR(50), NOT NULL)
- sucursal_id (VARCHAR(50))
- almacen_id (VARCHAR(50), NOT NULL)
- folio_inventario (VARCHAR(50), NOT NULL)
- fecha_inventario (DATE, NOT NULL)
- hash_identificador (VARCHAR(64), NOT NULL)  -- SHA256(server+suc+alm+folio)
- fecha_procesado (DATETIME2, NOT NULL)
- resultado (VARCHAR(20), CHECK IN ('EXITOSO', 'ERROR', 'PARCIAL'))
- detalle_error (NVARCHAR(MAX), NULL)

Índices:
- IX_folios_hash (hash_identificador) UNIQUE
- IX_folios_server_fecha (server_id, fecha_inventario)
```

#### 6.1.4 `automatizacion_inventarios_ejecuciones`
```
Propósito: Bitácora detallada de cada ejecución

Campos:
- ejecucion_id (PK, UNIQUEIDENTIFIER)
- procesado_id (FK → folios_procesados)
- server_id (VARCHAR(50), NOT NULL)
- sucursal_nombre (VARCHAR(200))
- almacen_nombre (VARCHAR(200))
- folio_inicial (VARCHAR(50))
- fecha_folio_inicial (DATE)
- folio_final (VARCHAR(50))
- fecha_folio_final (DATE)
- total_productos (INT)
- productos_con_diferencia (INT)
- valor_total_diferencias (DECIMAL(18,2))
- archivo_excel_path (VARCHAR(500), NULL)
- archivo_pdf_path (VARCHAR(500), NULL)
- archivo_excel_size_kb (INT, NULL)
- inicio_ejecucion (DATETIME2)
- fin_ejecucion (DATETIME2)
- duracion_segundos (INT)
- estado (VARCHAR(20), CHECK IN ('EN_PROCESO', 'COMPLETADO', 'ERROR'))
- error_mensaje (NVARCHAR(MAX), NULL)
- error_stack (NVARCHAR(MAX), NULL)

Índices:
- IX_ejec_procesado (procesado_id)
- IX_ejec_fecha (inicio_ejecucion)
```

#### 6.1.5 `automatizacion_inventarios_envios`
```
Propósito: Registro de cada envío individual

Campos:
- envio_id (PK, UNIQUEIDENTIFIER)
- ejecucion_id (FK → ejecuciones)
- destinatario_id (FK → destinatarios)
- canal (VARCHAR(20), CHECK IN ('EMAIL', 'WHATSAPP'))
- email_destino (VARCHAR(200), NULL)
- telefono_destino (VARCHAR(20), NULL)
- tipo_envio_email (VARCHAR(10), NULL)
- fecha_envio (DATETIME2)
- estado (VARCHAR(20), CHECK IN ('PENDIENTE', 'ENVIADO', 'ERROR', 'REBOTADO'))
- mensaje_id_externo (VARCHAR(200), NULL)  -- ID del proveedor email/whatsapp
- error_mensaje (NVARCHAR(MAX), NULL)
- intentos (INT, DEFAULT 0)
- ultimo_intento (DATETIME2, NULL)

Índices:
- IX_envios_ejecucion (ejecucion_id)
- IX_envios_estado (estado, fecha_envio)
```

#### 6.1.6 `automatizacion_inventarios_ultimo_folio_conocido`
```
Propósito: Estado de polling por almacén (checkpoint)

Campos:
- checkpoint_id (PK, UNIQUEIDENTIFIER)
- server_id (VARCHAR(50), NOT NULL)
- sucursal_id (VARCHAR(50))
- almacen_id (VARCHAR(50), NOT NULL)
- ultimo_folio_visto (VARCHAR(50))
- fecha_ultimo_folio (DATE)
- ultimo_check (DATETIME2)
- proxima_verificacion (DATETIME2)

Índices:
- IX_checkpoint_server_alm (server_id, almacen_id) UNIQUE
```

### 6.2 Archivos Backend Nuevos

```
/app/backend/
├── modules/
│   └── automatizacion/
│       ├── __init__.py
│       ├── schemas.py           # Pydantic models
│       ├── repository.py        # Acceso a tablas EDARSA HUB
│       ├── detector.py          # Lógica de detección de nuevos folios
│       ├── resolver.py          # Resolución de inv inicial y destinatarios
│       ├── generator.py         # Genera análisis (reutiliza lógica existente)
│       ├── exporter.py          # Genera Excel/PDF (reutiliza existente)
│       ├── notifier.py          # Envía email y WhatsApp
│       ├── service.py           # Orquestador principal
│       ├── scheduler.py         # Job programado (APScheduler)
│       └── routes.py            # Endpoints de administración/monitoreo
```

### 6.3 Colecciones MongoDB (CACHE TEMPORAL)

```
automatizacion_cache_config
- Propósito: Cache de configuración para evitar queries repetidos
- TTL: 5 minutos
- Estructura: Copia de config SQL con timestamp

automatizacion_cache_folios_recientes
- Propósito: Cache de últimos folios detectados para comparación rápida
- TTL: 1 hora
- Estructura: {server_id, almacen_id, folios: [...]}
```

---

## 7. ARQUITECTURA PROPUESTA

### 7.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EDARSA HUB BACKEND                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   APScheduler   │───▶│  AutomationSvc  │───▶│    Detector     │         │
│  │   (Cron Job)    │    │  (Orquestador)  │    │  (Nuevos Folios)│         │
│  └─────────────────┘    └────────┬────────┘    └────────┬────────┘         │
│                                  │                       │                  │
│                                  │                       ▼                  │
│                                  │             ┌─────────────────┐          │
│                                  │             │    Resolver     │          │
│                                  │             │ (Inv Inicial +  │          │
│                                  │             │  Destinatarios) │          │
│                                  │             └────────┬────────┘          │
│                                  │                       │                  │
│                                  ▼                       ▼                  │
│                         ┌─────────────────┐    ┌─────────────────┐          │
│                         │    Generator    │◀───│   Exporter      │          │
│                         │ (Usa lógica     │    │ (Excel/PDF)     │          │
│                         │  existente)     │    └─────────────────┘          │
│                         └────────┬────────┘                                 │
│                                  │                                          │
│                                  ▼                                          │
│                         ┌─────────────────┐    ┌─────────────────┐          │
│                         │    Notifier     │───▶│   Repository    │          │
│                         │ (Email/WA)      │    │ (Bitácora SQL)  │          │
│                         └─────────────────┘    └─────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                                      │
                    ▼                                      ▼
    ┌───────────────────────────┐          ┌───────────────────────────┐
    │   SISTEMAS ORIGEN         │          │     EDARSA HUB SQL        │
    │   (SOLO LECTURA)          │          │     (PERSISTENCIA)        │
    ├───────────────────────────┤          ├───────────────────────────┤
    │ • SoftRestaurant          │          │ • automatizacion_*        │
    │   - folioconteo           │          │ • auditoria_financiera    │
    │   - detalleconteo         │          │                           │
    │ • MPRO                    │          │                           │
    │   - Inventario_Fisico     │          │                           │
    │   - Inventario_Fisico_Det │          │                           │
    └───────────────────────────┘          └───────────────────────────┘
```

### 7.2 Principios Arquitectónicos

| Principio | Implementación |
|-----------|----------------|
| Single Responsibility | Cada módulo tiene una responsabilidad única |
| Open/Closed | Extensible sin modificar componentes existentes |
| Dependency Injection | Repositorios inyectados para testabilidad |
| Idempotencia | Hash de identificación previene duplicados |
| Fail-Safe | Errores no detienen el ciclo completo |
| Audit Trail | Todo movimiento queda registrado |

---

## 8. DETECCIÓN DE NUEVOS FOLIOS

### 8.1 Query SoftRestaurant
```sql
-- Detectar nuevos folios de inventario por almacén
SELECT 
    CAST(fc.idfolioconteo AS VARCHAR) as folio,
    fc.fecha,
    fc.idalmacen as almacen_id,
    a.descripcion as almacen_nombre,
    (SELECT COUNT(*) FROM detalleconteo dc WHERE dc.idfolioconteo = fc.idfolioconteo) as total_items
FROM folioconteo fc
INNER JOIN almacen a ON a.idalmacen = fc.idalmacen
WHERE fc.idalmacen = @almacen_id
  AND fc.fecha >= @fecha_desde
  AND CAST(fc.idfolioconteo AS VARCHAR) > @ultimo_folio_conocido
ORDER BY fc.idfolioconteo ASC
```

### 8.2 Query MPRO
```sql
-- Detectar nuevos folios de inventario por almacén y sucursal
SELECT 
    IF.If_Folio as folio,
    IF.If_Fecha as fecha,
    IF.Al_Cve_Almacen as almacen_id,
    A.Al_Nombre as almacen_nombre,
    IF.Sc_Cve_Sucursal as sucursal_id,
    (SELECT COUNT(*) FROM Inventario_Fisico_Detalle IFD WHERE IFD.If_Folio = IF.If_Folio) as total_items
FROM Inventario_Fisico IF
INNER JOIN Almacen A ON A.Al_Cve_Almacen = IF.Al_Cve_Almacen 
    AND A.Sc_Cve_Sucursal = IF.Sc_Cve_Sucursal
WHERE IF.Al_Cve_Almacen = @almacen_id
  AND IF.Sc_Cve_Sucursal = @sucursal_id
  AND IF.If_Fecha >= @fecha_desde
  AND IF.If_Folio > @ultimo_folio_conocido
ORDER BY IF.If_Folio ASC
```

### 8.3 Lógica de Detección

```
FUNCIÓN: detectar_nuevos_folios(server_id, sucursal_id, almacen_id)

1. Obtener último folio conocido de `ultimo_folio_conocido`
   - Si no existe → usar fecha inicio de mes actual
   
2. Ejecutar query según system_type (SOFT/MPRO)

3. Por cada folio encontrado:
   a. Calcular hash = SHA256(server_id + sucursal_id + almacen_id + folio)
   b. Verificar en `folios_procesados` si hash existe
   c. Si NO existe → agregar a lista de nuevos
   
4. Retornar lista de folios nuevos con metadata
```

---

## 9. RESOLUCIÓN DE INVENTARIO INICIAL

### 9.1 Reglas por Sistema

| Sistema | Regla Inventario Inicial |
|---------|-------------------------|
| SoftRestaurant | Primer inventario del MES ACTUAL del almacén |
| MPRO | Último inventario del MES ANTERIOR del almacén |

### 9.2 Query SoftRestaurant - Inventario Inicial
```sql
-- Primer inventario del mes actual para el almacén
SELECT TOP 1
    CAST(fc.idfolioconteo AS VARCHAR) as folio,
    fc.fecha
FROM folioconteo fc
WHERE fc.idalmacen = @almacen_id
  AND MONTH(fc.fecha) = MONTH(@fecha_folio_nuevo)
  AND YEAR(fc.fecha) = YEAR(@fecha_folio_nuevo)
ORDER BY fc.idfolioconteo ASC
```

### 9.3 Query MPRO - Inventario Inicial
```sql
-- Último inventario del mes anterior para el almacén
DECLARE @fecha_ref DATE = @fecha_folio_nuevo
DECLARE @primer_dia_mes DATE = DATEFROMPARTS(YEAR(@fecha_ref), MONTH(@fecha_ref), 1)
DECLARE @ultimo_dia_mes_ant DATE = DATEADD(DAY, -1, @primer_dia_mes)

SELECT TOP 1
    IF.If_Folio as folio,
    IF.If_Fecha as fecha
FROM Inventario_Fisico IF
WHERE IF.Al_Cve_Almacen = @almacen_id
  AND IF.Sc_Cve_Sucursal = @sucursal_id
  AND IF.If_Fecha <= @ultimo_dia_mes_ant
ORDER BY IF.If_Fecha DESC, IF.If_Folio DESC
```

### 9.4 Manejo de Errores

| Escenario | Acción |
|-----------|--------|
| No existe inventario inicial | Registrar error, notificar admin, NO enviar análisis |
| Inventario inicial = final | Validar que no sea el mismo, log warning |
| Fecha inicial > fecha final | Error de datos, notificar admin |

---

## 10. GENERACIÓN DE ANÁLISIS 1:1

### 10.1 Principio de Reutilización

```
El análisis generado automáticamente debe ser IDÉNTICO al generado 
manualmente desde el menú de Inventarios > Análisis.

IMPLEMENTACIÓN:
- Extraer la lógica INTERNA del endpoint /reports/inventory-analysis
- Crear función reutilizable: generar_analisis_inventario()
- La función recibe los mismos parámetros que el endpoint
- Retorna el mismo formato de datos
```

### 10.2 Función de Generación

```python
# Pseudocódigo - La lógica real está en server.py:2363

async def generar_analisis_inventario(
    server: dict,
    sucursal: str,
    almacen: str,
    folio_inicial: str,
    folio_final: str,
    fecha_ini: str,
    fecha_fin: str
) -> AnalisisResult:
    """
    Genera análisis de inventario.
    REUTILIZA la misma lógica de /reports/inventory-analysis
    
    Returns:
        AnalisisResult con:
        - data: Lista de productos con diferencias
        - count: Total de productos
        - resumen: Estadísticas agregadas
    """
    # La implementación invoca la lógica existente
    # SIN duplicar código
```

### 10.3 Garantía de Identicidad

| Aspecto | Verificación |
|---------|--------------|
| Cálculo de diferencias | Mismo algoritmo |
| Formato de números | Mismo locale (es-MX) |
| Columnas de Excel | Mismo orden y nombres |
| Fórmulas de costos | Misma lógica |

---

## 11. DISEÑO DE DESTINATARIOS

### 11.1 Modelo Jerárquico

```
NIVEL 1: SERVIDOR
├── Destinatarios que reciben TODOS los análisis del servidor
│
├── NIVEL 2: SUCURSAL
│   ├── Destinatarios que reciben análisis de ESA sucursal
│   │
│   └── NIVEL 3: ALMACÉN
│       └── Destinatarios que reciben análisis de ESE almacén
```

### 11.2 Ejemplo de Configuración

```
Servidor: LA_ESTELAR (SoftRestaurant)
├── gerencia@edarsa.com (TO) - Recibe TODO
├── auditoria@edarsa.com (CC) - Recibe TODO
│
├── Sucursal: ESTELAR
│   ├── jefe.estelar@edarsa.com (TO) - Solo Estelar
│   │
│   ├── Almacén: COCINA
│   │   └── chef.estelar@edarsa.com (TO) - Solo Cocina
│   │
│   └── Almacén: BAR
│       └── barman.estelar@edarsa.com (TO) - Solo Bar
```

### 11.3 Canales de Envío

| Canal | Configuración | Campos |
|-------|---------------|--------|
| Email | To/CC/BCC | `email`, `tipo_envio_email` |
| WhatsApp | Directo | `telefono_whatsapp` |

### 11.4 Estados de Destinatario

| Estado | Significado |
|--------|-------------|
| `activo = 1` | Recibe notificaciones |
| `activo = 0` | Pausado temporalmente |
| `enviar_email = 1` | Recibe por email |
| `enviar_whatsapp = 1` | Recibe por WhatsApp |

---

## 12. RESOLUCIÓN DE DESTINATARIOS

### 12.1 Algoritmo de Acumulación

```
FUNCIÓN: resolver_destinatarios(server_id, sucursal_id, almacen_id)

destinatarios = {}  # Diccionario para evitar duplicados

1. Buscar destinatarios NIVEL SERVIDOR (sucursal_id IS NULL)
   → Agregar todos a `destinatarios`

2. Buscar destinatarios NIVEL SUCURSAL (almacen_id IS NULL)
   → Agregar todos (si email no existe ya)

3. Buscar destinatarios NIVEL ALMACÉN (match exacto)
   → Agregar todos (si email no existe ya)

4. Filtrar solo `activo = 1`

5. Retornar lista final sin duplicados
```

### 12.2 Ejemplo de Resolución

```
Análisis generado para: LA_ESTELAR > ESTELAR > COCINA

Nivel Servidor:
- gerencia@edarsa.com (TO)
- auditoria@edarsa.com (CC)

Nivel Sucursal:
- jefe.estelar@edarsa.com (TO)

Nivel Almacén:
- chef.estelar@edarsa.com (TO)

RESULTADO FINAL:
- TO: gerencia@edarsa.com, jefe.estelar@edarsa.com, chef.estelar@edarsa.com
- CC: auditoria@edarsa.com
```

### 12.3 Query de Resolución

```sql
SELECT 
    d.destinatario_id,
    d.nombre_destinatario,
    d.email,
    d.telefono_whatsapp,
    d.tipo_envio_email,
    d.enviar_email,
    d.enviar_whatsapp,
    CASE 
        WHEN d.almacen_id IS NOT NULL THEN 3  -- Nivel almacén
        WHEN d.sucursal_id IS NOT NULL THEN 2  -- Nivel sucursal
        ELSE 1  -- Nivel servidor
    END as nivel_jerarquia
FROM automatizacion_inventarios_destinatarios d
WHERE d.server_id = @server_id
  AND d.activo = 1
  AND (
    (d.sucursal_id IS NULL AND d.almacen_id IS NULL)  -- Nivel servidor
    OR (d.sucursal_id = @sucursal_id AND d.almacen_id IS NULL)  -- Nivel sucursal
    OR (d.sucursal_id = @sucursal_id AND d.almacen_id = @almacen_id)  -- Nivel almacén
  )
ORDER BY nivel_jerarquia, d.nombre_destinatario
```

---

## 13. ESTRATEGIA ANTI-DUPLICADOS

### 13.1 Identificador Único de Procesamiento

```
hash_identificador = SHA256(
    server_id + "|" +
    sucursal_id + "|" +
    almacen_id + "|" +
    folio_inventario
)

Ejemplo:
server_id = "LA_ESTELAR"
sucursal_id = "01"
almacen_id = "COCINA"
folio = "12345"

hash = SHA256("LA_ESTELAR|01|COCINA|12345")
     = "a1b2c3d4e5f6..."
```

### 13.2 Verificación Antes de Procesar

```
FUNCIÓN: ya_procesado(server_id, sucursal_id, almacen_id, folio)

1. Calcular hash_identificador

2. SELECT 1 FROM automatizacion_inventarios_folios_procesados
   WHERE hash_identificador = @hash

3. Si existe → Ya procesado (TRUE)
   Si no existe → Nuevo (FALSE)
```

### 13.3 Registro Post-Procesamiento

```sql
INSERT INTO automatizacion_inventarios_folios_procesados (
    procesado_id,
    server_id,
    sucursal_id,
    almacen_id,
    folio_inventario,
    fecha_inventario,
    hash_identificador,
    fecha_procesado,
    resultado
) VALUES (
    NEWID(),
    @server_id,
    @sucursal_id,
    @almacen_id,
    @folio,
    @fecha_inv,
    @hash,
    GETDATE(),
    @resultado  -- 'EXITOSO', 'ERROR', 'PARCIAL'
)
```

---

## 14. BITÁCORA

### 14.1 Niveles de Registro

| Nivel | Tabla | Contenido |
|-------|-------|-----------|
| Ejecución | `automatizacion_inventarios_ejecuciones` | Detalle del análisis generado |
| Envío | `automatizacion_inventarios_envios` | Cada notificación individual |
| Control | `automatizacion_inventarios_folios_procesados` | Estado idempotente |

### 14.2 Campos de Trazabilidad

```
EJECUCIÓN:
- Quién: server_id, sucursal_nombre, almacen_nombre
- Qué: folio_inicial, folio_final, total_productos
- Cuándo: inicio_ejecucion, fin_ejecucion, duracion_segundos
- Resultado: estado, error_mensaje, archivos generados

ENVÍO:
- A quién: destinatario_id, email_destino, telefono_destino
- Cómo: canal (EMAIL/WHATSAPP), tipo_envio_email
- Cuándo: fecha_envio
- Resultado: estado, mensaje_id_externo, intentos
```

### 14.3 Retención de Datos

| Tabla | Retención | Razón |
|-------|-----------|-------|
| Configuración | Indefinido | Parametrización activa |
| Ejecuciones | 2 años | Auditoría fiscal |
| Envíos | 1 año | Trazabilidad operativa |
| Folios procesados | 2 años | Anti-duplicados histórico |

---

## 15. EXPORTACIÓN EXCEL/PDF

### 15.1 Reutilización de Exportadores

```python
# La lógica de exportación ya existe en server.py
# Se reutilizará SIN modificar los endpoints existentes

async def exportar_analisis_excel(data: List[Dict], metadata: Dict) -> bytes:
    """
    Genera Excel con el análisis de inventario.
    REUTILIZA la misma lógica de /reports/export/excel
    
    Args:
        data: Lista de productos del análisis
        metadata: Información del reporte (servidor, sucursal, fechas)
    
    Returns:
        Contenido del archivo Excel como bytes
    """
    # Invoca lógica existente de openpyxl
```

### 15.2 Almacenamiento de Archivos

```
Ruta de almacenamiento:
/app/storage/automatizacion/
├── 2025/
│   └── 12/
│       ├── LA_ESTELAR_COCINA_20251215_123456.xlsx
│       └── LA_ESTELAR_COCINA_20251215_123456.pdf

Nomenclatura:
{server_id}_{almacen_id}_{fecha_YYYYMMDD}_{folio}.{ext}
```

### 15.3 Limpieza de Archivos

```
Política de limpieza:
- Archivos > 30 días → Eliminar
- Mantener registro en BD (path queda como histórico)
- Job de limpieza semanal
```

---

## 16. ENVÍO DE CORREO

### 16.1 Integración con Proveedor SMTP

```
Opciones soportadas:
1. SMTP directo (configurable)
2. SendGrid API (recomendado para volumen)
3. AWS SES

Configuración en EDARSA HUB:
- smtp_host, smtp_port, smtp_user, smtp_password
- O: sendgrid_api_key
```

### 16.2 Plantilla de Email

```html
Asunto: [EDARSA HUB] Análisis de Inventario - {sucursal} - {almacen} - {fecha}

Cuerpo:
----------------------------------
ANÁLISIS DE INVENTARIO AUTOMÁTICO
----------------------------------

Servidor: {servidor_nombre}
Sucursal: {sucursal_nombre}
Almacén: {almacen_nombre}

Período: {fecha_inicial} a {fecha_final}

RESUMEN:
- Total productos analizados: {total_productos}
- Productos con diferencia: {productos_con_diferencia}
- Valor total diferencias: ${valor_diferencias}
- Precisión: {porcentaje_precision}%

Archivo adjunto: {nombre_archivo}

----------------------------------
Este es un mensaje automático de EDARSA HUB.
Generado: {timestamp}
```

### 16.3 Manejo de Errores de Envío

| Escenario | Acción |
|-----------|--------|
| Email rebotado | Registrar, reintentar 2 veces, marcar como fallido |
| Timeout SMTP | Reintentar hasta 3 veces |
| Adjunto muy grande | Enviar link de descarga en lugar de adjunto |
| Sin destinatarios | Log warning, no enviar |

---

## 17. ENVÍO DE WHATSAPP

### 17.1 Integración con Proveedor

```
Opciones soportadas:
1. Twilio WhatsApp Business API
2. Meta WhatsApp Business Platform

Configuración:
- twilio_account_sid, twilio_auth_token, twilio_whatsapp_number
- O: meta_whatsapp_token, meta_phone_number_id
```

### 17.2 Plantilla de Mensaje

```
📊 *ANÁLISIS DE INVENTARIO*
━━━━━━━━━━━━━━━━━━━━━

📍 *{sucursal}* - {almacen}
📅 Período: {fecha_ini} a {fecha_fin}

📈 *Resumen:*
• Productos: {total}
• Con diferencia: {con_dif}
• Valor: ${valor}

📎 Excel enviado por correo

_EDARSA HUB - {timestamp}_
```

### 17.3 Limitaciones WhatsApp

| Limitación | Manejo |
|------------|--------|
| No adjuntos directos | Enviar link de descarga |
| Formato limitado | Usar emojis para estructura |
| Rate limiting | Queue con delay entre mensajes |

---

## 18. AUDITORÍA Y REPROCESOS

### 18.1 Endpoint de Reproceso Manual

```
POST /api/automatizacion/reprocesar

Body:
{
    "server_id": "LA_ESTELAR",
    "sucursal_id": "01",
    "almacen_id": "COCINA",
    "folio_inventario": "12345",
    "motivo": "Corrección de datos origen"
}

Requiere: Permiso AUTHORIZE en módulo automatizacion
```

### 18.2 Lógica de Reproceso

```
1. Validar permisos del usuario
2. Buscar registro original en folios_procesados
3. Marcar como REPROCESADO (no eliminar)
4. Crear nuevo registro con mismo folio
5. Ejecutar flujo completo
6. Registrar auditoría con usuario y motivo
```

### 18.3 Vista de Auditoría

```
GET /api/automatizacion/auditoria

Filtros:
- fecha_desde, fecha_hasta
- server_id, sucursal_id, almacen_id
- estado (EXITOSO, ERROR, PARCIAL, REPROCESADO)
- usuario (para reprocesos)

Retorna:
- Lista paginada de ejecuciones
- Incluye detalle de envíos
- Permite descargar archivos históricos
```

---

## 19. ESTRATEGIA DE NO REGRESIÓN

### 19.1 Principios de Aislamiento

| Principio | Implementación |
|-----------|----------------|
| Módulo desacoplado | Nuevo directorio `/modules/automatizacion/` |
| Sin modificar existente | Reutiliza funciones, no modifica |
| Feature flag | `automatizacion_activa` por servidor |
| Rollback instantáneo | Desactivar = dejar de ejecutar |

### 19.2 Tests de Regresión

```
ANTES de deployment:

1. Test unitario: generar_analisis_inventario()
   - Comparar output con endpoint existente
   - Mismo input → mismo output

2. Test integración: flujo completo
   - Detectar folio conocido
   - Generar análisis
   - Exportar Excel
   - Verificar formato idéntico

3. Test manual:
   - Generar análisis desde UI
   - Generar análisis automático
   - Comparar archivos byte-a-byte
```

### 19.3 Monitoreo Post-Deployment

```
Métricas a vigilar:

1. Tasa de error de detección
2. Tiempo promedio de generación
3. Tasa de éxito de envíos
4. Comparación de análisis (manual vs auto)
```

### 19.4 Plan de Rollback

```
SI se detecta regresión:

1. INMEDIATO: Desactivar automatización (config)
   UPDATE automatizacion_inventarios_config SET activo = 0

2. ANÁLISIS: Revisar bitácora de errores

3. CORRECCIÓN: Fix en módulo aislado

4. REACTIVAR: Solo tras validación
```

---

## 20. PLAN POR FASES

### FASE 0: Preparación (1-2 días)
```
□ Crear tablas en EDARSA HUB SQL Server
□ Crear estructura de módulo en backend
□ Configurar APScheduler básico
□ Tests unitarios de conexión
```

### FASE 1: Motor de Detección (3-5 días)
```
□ Implementar detector de nuevos folios
□ Implementar verificación anti-duplicados
□ Implementar resolución de inventario inicial
□ Tests de detección con datos reales
□ Documentar casos edge
```

### FASE 2: Generación de Análisis (3-5 días)
```
□ Extraer lógica de /reports/inventory-analysis
□ Crear función reutilizable
□ Validar identicidad con análisis manual
□ Implementar exportación Excel/PDF
□ Tests de comparación de archivos
```

### FASE 3: Sistema de Notificaciones (3-5 días)
```
□ Implementar resolución de destinatarios
□ Integrar envío de email
□ Integrar envío de WhatsApp (opcional)
□ Tests de envío con destinatarios reales
□ Manejo de errores y reintentos
```

### FASE 4: Monitoreo y Admin (2-3 días)
```
□ Endpoints de administración
□ Vista de bitácora
□ Endpoint de reproceso
□ Integración con RBAC existente
□ Documentación de operación
```

### FASE 5: Piloto Controlado (1 semana)
```
□ Activar en 1 servidor de prueba
□ Monitorear 7 días
□ Validar con auditor real
□ Ajustes finos
□ Documentar lecciones aprendidas
```

### FASE 6: Rollout Gradual (2-3 semanas)
```
□ Activar servidor por servidor
□ Validar cada activación
□ Capacitar usuarios
□ Ajustar configuración por feedback
□ Cierre formal del proyecto
```

---

## 21. RIESGOS Y MITIGACIONES

### 21.1 Riesgos Técnicos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| RT-01 | Timeout en queries SQL pesadas | ALTA | MEDIO | Queries optimizadas, timeout configurable |
| RT-02 | Fallo de conexión a origen | MEDIA | ALTO | Reintentos, notificación admin |
| RT-03 | Archivos Excel muy grandes | BAJA | BAJO | Límite de filas, paginación |
| RT-04 | Fallo de envío email | MEDIA | MEDIO | Reintentos, cola de pendientes |
| RT-05 | Inconsistencia de datos | BAJA | ALTO | Validación pre-generación |

### 21.2 Riesgos Operativos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| RO-01 | Análisis automático diferente a manual | BAJA | CRÍTICO | Tests de comparación, validación humana |
| RO-02 | Spam de notificaciones | BAJA | MEDIO | Control de frecuencia, límites |
| RO-03 | Destinatarios incorrectos | MEDIA | ALTO | UI de administración, confirmación |
| RO-04 | Falta de inventario inicial | MEDIA | MEDIO | Notificación admin, log claro |

### 21.3 Riesgos de Regresión

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| RR-01 | Afectar módulo manual existente | MUY BAJA | CRÍTICO | Módulo 100% desacoplado |
| RR-02 | Modificar queries existentes | MUY BAJA | ALTO | Reutilizar, no modificar |
| RR-03 | Impacto en rendimiento general | BAJA | MEDIO | Job en background, rate limiting |

---

## 22. INTEGRACIÓN CON RBAC

### 22.1 Permisos Requeridos

| Permiso | Descripción | Roles Sugeridos |
|---------|-------------|-----------------|
| `automatizacion.view` | Ver bitácora y estado | Auditor, Supervisor |
| `automatizacion.config` | Configurar destinos | Admin Finanzas |
| `automatizacion.reprocesar` | Reprocesar análisis | Admin Finanzas |
| `automatizacion.admin` | Activar/desactivar global | SuperAdmin |

### 22.2 Validación de Acceso

```
Endpoints protegidos:

GET  /api/automatizacion/bitacora     → automatizacion.view
GET  /api/automatizacion/config       → automatizacion.config
POST /api/automatizacion/config       → automatizacion.config
POST /api/automatizacion/reprocesar   → automatizacion.reprocesar
POST /api/automatizacion/toggle       → automatizacion.admin
```

### 22.3 Filtrado por Servidor/Sucursal

```
La bitácora y configuración deben respetar:
- allowed_servers del usuario
- allowed_sucursales del usuario

Un usuario solo ve y configura lo que tiene permitido.
```

---

## 23. ANEXOS

### 23.1 Glosario

| Término | Definición |
|---------|------------|
| Folio | Identificador único de un inventario físico |
| Polling | Verificación periódica de nuevos datos |
| Idempotencia | Garantía de que una operación no se duplica |
| Hash identificador | Clave única derivada de datos del inventario |

### 23.2 Referencias

| Documento | Ubicación |
|-----------|-----------|
| PRD EDARSA HUB | `/app/memory/PRD.md` |
| Sistema RBAC | `/app/docs/SISTEMA_RBAC_PROPUESTA.md` |
| Auditoría | `/app/docs/AUDITORIA_FINANCIERA_PROPUESTA.md` |

### 23.3 Historial de Cambios

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | Dic 2025 | Documento inicial |

---

## APROBACIÓN

| Rol | Nombre | Fecha | Firma |
|-----|--------|-------|-------|
| Product Owner | | | |
| Tech Lead | | | |
| QA Lead | | | |
| Auditor | | | |

---

**FIN DEL DOCUMENTO**

*Este documento es propiedad de EDARSA y contiene información confidencial.*
