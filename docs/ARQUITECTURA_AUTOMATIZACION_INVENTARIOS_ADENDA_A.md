# ADENDA TÉCNICA: Definiciones Críticas de Automatización
## EDARSA HUB - CAB-003 - Adenda A

**Versión**: 1.1  
**Fecha**: Diciembre 2025  
**Estado**: DEFINICIONES TÉCNICAS FINALES  
**Requisito**: Aprobación obligatoria antes de implementación

---

## ÍNDICE DE DEFINICIONES CRÍTICAS

1. [Core Service de Análisis de Inventarios](#1-core-service-de-análisis-de-inventarios)
2. [Clave Única del Proceso (Idempotencia)](#2-clave-única-del-proceso-idempotencia)
3. [Resolución de Destinatarios](#3-resolución-de-destinatarios)
4. [Control de Concurrencia](#4-control-de-concurrencia)
5. [Desacoplamiento Total del Frontend](#5-desacoplamiento-total-del-frontend)
6. [Plan de Fases Ajustado](#6-plan-de-fases-ajustado)

---

## 1. CORE SERVICE DE ANÁLISIS DE INVENTARIOS

### 1.1 Problema a Resolver

La lógica del análisis de inventarios actualmente vive en:
- `server.py:2363` - Endpoint `POST /reports/inventory-analysis`
- Líneas 2363-3200 aproximadamente (800+ líneas de lógica compleja)

**PROHIBIDO**: Duplicar esta lógica en el módulo de automatización.  
**OBLIGATORIO**: Extraer a un servicio reutilizable.

### 1.2 Arquitectura de Core Service

```
ANTES (actual):
┌─────────────────────────────────────────────────┐
│  server.py                                      │
│  ┌───────────────────────────────────────────┐  │
│  │ @api_router.post("/reports/inventory...")  │  │
│  │                                           │  │
│  │   [800+ líneas de lógica de análisis]     │  │
│  │   - Query MPRO                            │  │
│  │   - Query SoftRestaurant                  │  │
│  │   - Cálculo de diferencias                │  │
│  │   - Formateo de respuesta                 │  │
│  │                                           │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘

DESPUÉS (refactor controlado):
┌─────────────────────────────────────────────────┐
│  core/                                          │
│  ┌───────────────────────────────────────────┐  │
│  │ inventory_analysis_core.py                │  │
│  │                                           │  │
│  │ class InventoryAnalysisCore:              │  │
│  │   async def generar_analisis()            │  │
│  │   async def _query_mpro()                 │  │
│  │   async def _query_softrestaurant()       │  │
│  │   async def _calcular_diferencias()       │  │
│  │   async def _formatear_resultado()        │  │
│  │                                           │  │
│  └───────────────────────────────────────────┘  │
│           ▲                    ▲                │
│           │                    │                │
│  ┌────────┴────────┐  ┌───────┴────────┐       │
│  │ server.py       │  │ automatizacion/│       │
│  │ (endpoint API)  │  │ generator.py   │       │
│  │                 │  │                │       │
│  │ Llama al core   │  │ Llama al core  │       │
│  └─────────────────┘  └────────────────┘       │
└─────────────────────────────────────────────────┘
```

### 1.3 Especificación del Core Service

**Archivo**: `/app/backend/core/inventory_analysis_core.py`

```python
"""
EDARSA HUB - Core Service de Análisis de Inventarios
=====================================================
REGLA CRÍTICA: Esta es la ÚNICA fuente de lógica de análisis.
- El endpoint existente (/reports/inventory-analysis) DEBE usar este core.
- El módulo de automatización DEBE usar este core.
- NO SE PERMITE duplicar lógica fuera de este archivo.

MIGRACIÓN:
- Fase 1: Extraer lógica de server.py a este archivo
- Fase 2: Modificar endpoint para usar este core
- Fase 3: Módulo automatización usa el mismo core

GARANTÍA DE NO REGRESIÓN:
- El endpoint existente sigue funcionando exactamente igual
- Solo cambia la ubicación del código, no el comportamiento
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AnalisisInventarioInput:
    """Parámetros de entrada para generar análisis."""
    server_id: str
    sucursal: str
    almacen: str
    fecha_ini: str
    fecha_fin: str
    folio_inicial: str
    folio_final: str
    # Opcionales
    almacenes: Optional[List[str]] = None
    folios_iniciales: Optional[List[str]] = None
    folios_finales: Optional[List[str]] = None
    categorias: Optional[List[str]] = None
    familias: Optional[List[str]] = None
    subfamilias: Optional[List[str]] = None
    agrupar_insumos: bool = False

@dataclass
class AnalisisInventarioOutput:
    """Resultado del análisis de inventario."""
    data: List[Dict[str, Any]]  # Lista de productos con diferencias
    count: int                   # Total de productos
    errores_captura: List[Dict]  # Errores detectados (MPRO)
    metadata: Dict[str, Any]     # Info adicional (fechas, totales)

class InventoryAnalysisCore:
    """
    Core Service para generación de análisis de inventarios.
    
    USO OBLIGATORIO:
    - Desde endpoint API: InventoryAnalysisCore(db).generar_analisis(input)
    - Desde automatización: InventoryAnalysisCore(db).generar_analisis(input)
    
    MISMA INSTANCIA, MISMO RESULTADO.
    """
    
    def __init__(self, db):
        """
        Inicializa el core con conexión a MongoDB.
        
        Args:
            db: Conexión a MongoDB (para obtener config de servidores)
        """
        self.db = db
    
    async def generar_analisis(
        self, 
        input: AnalisisInventarioInput
    ) -> AnalisisInventarioOutput:
        """
        Genera análisis de inventario completo.
        
        Esta función contiene TODA la lógica de análisis.
        Es invocada tanto por el endpoint como por la automatización.
        
        Args:
            input: Parámetros del análisis
            
        Returns:
            AnalisisInventarioOutput con datos, conteo y errores
            
        Raises:
            HTTPException: Si servidor no existe o hay error de conexión
        """
        # AQUÍ VA LA LÓGICA EXTRAÍDA DE server.py:2363-3200
        # Sin cambios funcionales, solo reorganización
        pass
    
    async def _obtener_servidor(self, server_id: str) -> Dict:
        """Obtiene configuración del servidor."""
        pass
    
    async def _generar_analisis_mpro(
        self, 
        server: Dict, 
        input: AnalisisInventarioInput
    ) -> AnalisisInventarioOutput:
        """Lógica específica para MPRO."""
        pass
    
    async def _generar_analisis_softrestaurant(
        self, 
        server: Dict, 
        input: AnalisisInventarioInput
    ) -> AnalisisInventarioOutput:
        """Lógica específica para SoftRestaurant."""
        pass
    
    async def _calcular_diferencias(
        self, 
        inv_inicial: List, 
        movimientos: List, 
        ventas: List, 
        inv_final: List
    ) -> List[Dict]:
        """Calcula diferencias entre inventarios."""
        pass
```

### 1.4 Plan de Migración del Core

| Paso | Acción | Riesgo | Validación |
|------|--------|--------|------------|
| 1 | Crear archivo `inventory_analysis_core.py` vacío | NULO | - |
| 2 | Copiar lógica de server.py al core (sin modificar) | BAJO | Tests unitarios |
| 3 | Modificar endpoint para importar y usar el core | BAJO | Test E2E: mismo output |
| 4 | Validar que UI sigue funcionando igual | BAJO | Test manual |
| 5 | Automatización usa el mismo core | NULO | Ya validado |

### 1.5 Garantía de Identicidad

```python
# TEST OBLIGATORIO antes de deployment

async def test_core_identico_a_endpoint_original():
    """
    Verifica que el core produce exactamente el mismo resultado
    que el endpoint original.
    """
    input_test = AnalisisInventarioInput(
        server_id="LA_ESTELAR",
        sucursal="ESTELAR",
        almacen="COCINA",
        fecha_ini="2025-12-01",
        fecha_fin="2025-12-15",
        folio_inicial="1000",
        folio_final="1050"
    )
    
    # Resultado del core
    core = InventoryAnalysisCore(db)
    resultado_core = await core.generar_analisis(input_test)
    
    # Resultado del endpoint (llamada HTTP real)
    resultado_endpoint = await client.post("/reports/inventory-analysis", json={...})
    
    # DEBEN SER IDÉNTICOS
    assert resultado_core.data == resultado_endpoint.json()['data']
    assert resultado_core.count == resultado_endpoint.json()['count']
```

---

## 2. CLAVE ÚNICA DEL PROCESO (IDEMPOTENCIA)

### 2.1 Definición de Clave Compuesta

La clave única NO es solo un hash. Es una **clave compuesta estructurada** con hash de verificación.

```
CLAVE ÚNICA DE PROCESO:
┌─────────────────────────────────────────────────────────────────────┐
│  Componentes (todos obligatorios):                                  │
│                                                                     │
│  1. server_id        VARCHAR(50)   Ej: "LA_ESTELAR"                │
│  2. sucursal_id      VARCHAR(50)   Ej: "01" o NULL para SOFT       │
│  3. almacen_id       VARCHAR(50)   Ej: "COCINA"                    │
│  4. folio_inventario VARCHAR(50)   Ej: "12345"                     │
│  5. fecha_inventario DATE          Ej: "2025-12-15"                │
│                                                                     │
│  Hash de verificación (derivado):                                   │
│  hash_verificacion = SHA256(                                        │
│      server_id + "|" +                                              │
│      COALESCE(sucursal_id, "NULL") + "|" +                         │
│      almacen_id + "|" +                                            │
│      folio_inventario + "|" +                                      │
│      fecha_inventario                                               │
│  )                                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Tabla de Control de Idempotencia

```sql
CREATE TABLE automatizacion_inventarios_folios_procesados (
    -- Clave primaria técnica
    procesado_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    
    -- CLAVE ÚNICA COMPUESTA (índice único)
    server_id VARCHAR(50) NOT NULL,
    sucursal_id VARCHAR(50) NULL,  -- NULL para SoftRestaurant
    almacen_id VARCHAR(50) NOT NULL,
    folio_inventario VARCHAR(50) NOT NULL,
    fecha_inventario DATE NOT NULL,
    
    -- Hash de verificación (redundancia para validación)
    hash_verificacion VARCHAR(64) NOT NULL,
    
    -- Metadata de procesamiento
    fecha_procesado DATETIME2 NOT NULL DEFAULT GETDATE(),
    fecha_inicio_proceso DATETIME2 NULL,  -- Para control de concurrencia
    fecha_fin_proceso DATETIME2 NULL,
    duracion_ms INT NULL,
    
    -- Estado del proceso
    estado VARCHAR(20) NOT NULL CHECK (estado IN (
        'EN_PROCESO',   -- Siendo procesado ahora
        'EXITOSO',      -- Completado sin errores
        'ERROR',        -- Falló completamente
        'PARCIAL',      -- Generó pero falló envío
        'REPROCESADO'   -- Marcado para reproceso
    )),
    
    -- Detalle de errores
    error_codigo VARCHAR(50) NULL,
    error_mensaje NVARCHAR(500) NULL,
    error_stack NVARCHAR(MAX) NULL,
    
    -- Trazabilidad
    ejecutado_por VARCHAR(100) NULL,  -- 'AUTOMATICO' o email de usuario
    motivo_reproceso NVARCHAR(500) NULL,
    
    -- CONSTRAINT: Clave única compuesta
    CONSTRAINT UQ_folio_unico UNIQUE (
        server_id, 
        sucursal_id, 
        almacen_id, 
        folio_inventario, 
        fecha_inventario
    ),
    
    -- CONSTRAINT: Hash único (validación redundante)
    CONSTRAINT UQ_hash_verificacion UNIQUE (hash_verificacion)
);

-- Índices para consultas frecuentes
CREATE INDEX IX_folios_server_fecha 
    ON automatizacion_inventarios_folios_procesados(server_id, fecha_inventario);
    
CREATE INDEX IX_folios_estado 
    ON automatizacion_inventarios_folios_procesados(estado, fecha_procesado);
```

### 2.3 Algoritmo de Verificación de Duplicados

```python
async def verificar_y_reservar_folio(
    server_id: str,
    sucursal_id: Optional[str],
    almacen_id: str,
    folio_inventario: str,
    fecha_inventario: str
) -> tuple[bool, Optional[str]]:
    """
    Verifica si un folio ya fue procesado y lo reserva si no.
    
    Returns:
        (puede_procesar, procesado_id)
        - (True, "uuid") si se reservó exitosamente
        - (False, None) si ya existe
        - (False, None) si hay conflicto de concurrencia
    """
    
    # 1. Calcular hash de verificación
    hash_input = f"{server_id}|{sucursal_id or 'NULL'}|{almacen_id}|{folio_inventario}|{fecha_inventario}"
    hash_verificacion = hashlib.sha256(hash_input.encode()).hexdigest()
    
    # 2. Intentar insertar con estado EN_PROCESO (operación atómica)
    try:
        procesado_id = str(uuid.uuid4())
        
        # INSERT que falla si ya existe (CONSTRAINT UNIQUE)
        await execute_sql("""
            INSERT INTO automatizacion_inventarios_folios_procesados (
                procesado_id,
                server_id,
                sucursal_id,
                almacen_id,
                folio_inventario,
                fecha_inventario,
                hash_verificacion,
                fecha_inicio_proceso,
                estado,
                ejecutado_por
            ) VALUES (
                @procesado_id,
                @server_id,
                @sucursal_id,
                @almacen_id,
                @folio_inventario,
                @fecha_inventario,
                @hash_verificacion,
                GETDATE(),
                'EN_PROCESO',
                'AUTOMATICO'
            )
        """, {
            'procesado_id': procesado_id,
            'server_id': server_id,
            'sucursal_id': sucursal_id,
            'almacen_id': almacen_id,
            'folio_inventario': folio_inventario,
            'fecha_inventario': fecha_inventario,
            'hash_verificacion': hash_verificacion
        })
        
        return (True, procesado_id)
        
    except UniqueConstraintViolation:
        # Ya existe - verificar estado
        existente = await execute_sql("""
            SELECT estado, fecha_inicio_proceso 
            FROM automatizacion_inventarios_folios_procesados
            WHERE hash_verificacion = @hash
        """, {'hash': hash_verificacion})
        
        if existente and existente[0]['estado'] == 'EN_PROCESO':
            # Está siendo procesado por otra instancia
            logging.warning(f"Folio {folio_inventario} en proceso por otra instancia")
        else:
            # Ya fue procesado anteriormente
            logging.info(f"Folio {folio_inventario} ya procesado anteriormente")
        
        return (False, None)
```

### 2.4 Diagrama de Estados

```
                    ┌─────────────────┐
                    │   (Detectado)   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
        ┌──────────│   EN_PROCESO    │──────────┐
        │          └────────┬────────┘          │
        │                   │                   │
        │ (Timeout/         │ (Éxito)           │ (Error)
        │  Crash)           │                   │
        │                   ▼                   ▼
        │          ┌─────────────────┐  ┌─────────────────┐
        │          │    EXITOSO      │  │     ERROR       │
        │          └─────────────────┘  └────────┬────────┘
        │                                        │
        │                                        │ (Retry manual)
        │                                        ▼
        │                              ┌─────────────────┐
        └─────────────────────────────▶│  REPROCESADO    │
                                       └────────┬────────┘
                                                │
                                                │ (Reinicia flujo)
                                                ▼
                                       ┌─────────────────┐
                                       │   EN_PROCESO    │
                                       └─────────────────┘
```

---

## 3. RESOLUCIÓN DE DESTINATARIOS

### 3.1 Regla Definida: ACUMULACIÓN con DEDUPLICACIÓN

```
REGLA OFICIAL: ACUMULACIÓN JERÁRQUICA CON DEDUPLICACIÓN

Los destinatarios se ACUMULAN desde el nivel más alto (servidor) 
hasta el más específico (almacén), DEDUPLICANDO por email/teléfono.

NO es override (el nivel específico no reemplaza al general).
NO es híbrido complejo.
ES acumulación simple con deduplicación.
```

### 3.2 Algoritmo de Resolución

```python
from typing import List, Dict, Set
from dataclasses import dataclass

@dataclass
class Destinatario:
    destinatario_id: str
    nombre: str
    email: Optional[str]
    telefono_whatsapp: Optional[str]
    tipo_envio_email: str  # TO, CC, BCC
    enviar_email: bool
    enviar_whatsapp: bool
    nivel_origen: str  # 'SERVIDOR', 'SUCURSAL', 'ALMACEN'

def resolver_destinatarios(
    server_id: str,
    sucursal_id: Optional[str],
    almacen_id: str,
    connection
) -> List[Destinatario]:
    """
    Resuelve destinatarios usando ACUMULACIÓN con DEDUPLICACIÓN.
    
    Proceso:
    1. Obtener destinatarios nivel SERVIDOR (sucursal_id IS NULL, almacen_id IS NULL)
    2. Obtener destinatarios nivel SUCURSAL (almacen_id IS NULL)
    3. Obtener destinatarios nivel ALMACÉN (match exacto)
    4. Acumular todos
    5. Deduplicar por email (mantener nivel más específico)
    6. Deduplicar por teléfono WhatsApp (mantener nivel más específico)
    
    Returns:
        Lista de destinatarios únicos, ordenados por nivel (servidor → almacén)
    """
    
    # Query que obtiene los 3 niveles en una sola consulta
    query = """
    SELECT 
        d.destinatario_id,
        d.nombre_destinatario as nombre,
        d.email,
        d.telefono_whatsapp,
        d.tipo_envio_email,
        d.enviar_email,
        d.enviar_whatsapp,
        CASE 
            WHEN d.almacen_id IS NOT NULL THEN 'ALMACEN'
            WHEN d.sucursal_id IS NOT NULL THEN 'SUCURSAL'
            ELSE 'SERVIDOR'
        END as nivel_origen,
        CASE 
            WHEN d.almacen_id IS NOT NULL THEN 3
            WHEN d.sucursal_id IS NOT NULL THEN 2
            ELSE 1
        END as nivel_orden
    FROM automatizacion_inventarios_destinatarios d
    WHERE d.server_id = @server_id
      AND d.activo = 1
      AND (
          -- Nivel SERVIDOR: aplica a todo
          (d.sucursal_id IS NULL AND d.almacen_id IS NULL)
          OR
          -- Nivel SUCURSAL: aplica a esa sucursal
          (d.sucursal_id = @sucursal_id AND d.almacen_id IS NULL)
          OR
          -- Nivel ALMACÉN: aplica solo a ese almacén
          (d.sucursal_id = @sucursal_id AND d.almacen_id = @almacen_id)
      )
    ORDER BY nivel_orden ASC, d.nombre_destinatario ASC
    """
    
    rows = execute_sql(query, {
        'server_id': server_id,
        'sucursal_id': sucursal_id,
        'almacen_id': almacen_id
    })
    
    # Paso 1: Convertir a objetos
    todos = [Destinatario(**row) for row in rows]
    
    # Paso 2: Deduplicar por EMAIL (mantener nivel más específico)
    emails_vistos: Dict[str, Destinatario] = {}
    for dest in todos:
        if dest.email and dest.enviar_email:
            email_lower = dest.email.lower()
            if email_lower not in emails_vistos:
                # Primera vez que vemos este email
                emails_vistos[email_lower] = dest
            else:
                # Ya existe - ¿el nuevo es más específico?
                existente = emails_vistos[email_lower]
                nivel_existente = {'SERVIDOR': 1, 'SUCURSAL': 2, 'ALMACEN': 3}[existente.nivel_origen]
                nivel_nuevo = {'SERVIDOR': 1, 'SUCURSAL': 2, 'ALMACEN': 3}[dest.nivel_origen]
                
                if nivel_nuevo > nivel_existente:
                    # El nuevo es más específico, reemplazar
                    emails_vistos[email_lower] = dest
    
    # Paso 3: Deduplicar por TELÉFONO (mismo criterio)
    telefonos_vistos: Dict[str, Destinatario] = {}
    for dest in todos:
        if dest.telefono_whatsapp and dest.enviar_whatsapp:
            tel_normalizado = normalizar_telefono(dest.telefono_whatsapp)
            if tel_normalizado not in telefonos_vistos:
                telefonos_vistos[tel_normalizado] = dest
            else:
                existente = telefonos_vistos[tel_normalizado]
                nivel_existente = {'SERVIDOR': 1, 'SUCURSAL': 2, 'ALMACEN': 3}[existente.nivel_origen]
                nivel_nuevo = {'SERVIDOR': 1, 'SUCURSAL': 2, 'ALMACEN': 3}[dest.nivel_origen]
                
                if nivel_nuevo > nivel_existente:
                    telefonos_vistos[tel_normalizado] = dest
    
    # Paso 4: Unir resultados únicos
    resultado_ids: Set[str] = set()
    resultado: List[Destinatario] = []
    
    for dest in emails_vistos.values():
        if dest.destinatario_id not in resultado_ids:
            resultado_ids.add(dest.destinatario_id)
            resultado.append(dest)
    
    for dest in telefonos_vistos.values():
        if dest.destinatario_id not in resultado_ids:
            resultado_ids.add(dest.destinatario_id)
            resultado.append(dest)
    
    return resultado
```

### 3.3 Ejemplo Concreto de Resolución

**Configuración en BD:**

| ID | Server | Sucursal | Almacén | Nombre | Email | Tipo | WA |
|----|--------|----------|---------|--------|-------|------|-----|
| D1 | LA_ESTELAR | NULL | NULL | Gerencia | gerencia@edarsa.com | TO | No |
| D2 | LA_ESTELAR | NULL | NULL | Auditoría | auditoria@edarsa.com | CC | No |
| D3 | LA_ESTELAR | NULL | NULL | Director | director@edarsa.com | BCC | Sí |
| D4 | LA_ESTELAR | 01 | NULL | Jefe Estelar | jefe.estelar@edarsa.com | TO | Sí |
| D5 | LA_ESTELAR | 01 | NULL | Contabilidad | auditoria@edarsa.com | TO | No |
| D6 | LA_ESTELAR | 01 | COCINA | Chef Estelar | chef.estelar@edarsa.com | TO | Sí |
| D7 | LA_ESTELAR | 01 | COCINA | Gerencia Local | gerencia@edarsa.com | CC | No |
| D8 | LA_ESTELAR | 01 | BAR | Barman | barman@edarsa.com | TO | No |

**Caso: Análisis de LA_ESTELAR > Sucursal 01 > COCINA**

```
Paso 1: Obtener todos los candidatos
─────────────────────────────────────
Nivel SERVIDOR (sucursal=NULL, almacen=NULL):
  - D1: gerencia@edarsa.com (TO)
  - D2: auditoria@edarsa.com (CC)
  - D3: director@edarsa.com (BCC) + WhatsApp

Nivel SUCURSAL (sucursal=01, almacen=NULL):
  - D4: jefe.estelar@edarsa.com (TO) + WhatsApp
  - D5: auditoria@edarsa.com (TO)  ← DUPLICADO de D2

Nivel ALMACÉN (sucursal=01, almacen=COCINA):
  - D6: chef.estelar@edarsa.com (TO) + WhatsApp
  - D7: gerencia@edarsa.com (CC)  ← DUPLICADO de D1

Paso 2: Deduplicar por EMAIL
─────────────────────────────
gerencia@edarsa.com:
  - D1 (SERVIDOR, TO) vs D7 (ALMACEN, CC)
  - Ganador: D7 (nivel más específico) → gerencia@edarsa.com como CC

auditoria@edarsa.com:
  - D2 (SERVIDOR, CC) vs D5 (SUCURSAL, TO)
  - Ganador: D5 (nivel más específico) → auditoria@edarsa.com como TO

Paso 3: Resultado Final
─────────────────────────
EMAIL - TO:
  ✓ auditoria@edarsa.com (de D5, nivel SUCURSAL)
  ✓ jefe.estelar@edarsa.com (de D4, nivel SUCURSAL)
  ✓ chef.estelar@edarsa.com (de D6, nivel ALMACEN)

EMAIL - CC:
  ✓ gerencia@edarsa.com (de D7, nivel ALMACEN)

EMAIL - BCC:
  ✓ director@edarsa.com (de D3, nivel SERVIDOR)

WHATSAPP:
  ✓ director@edarsa.com (de D3)
  ✓ jefe.estelar@edarsa.com (de D4)
  ✓ chef.estelar@edarsa.com (de D6)
```

### 3.4 Caso Especial: Sin Destinatarios

```python
if not destinatarios:
    # Registrar warning en bitácora
    await registrar_ejecucion(
        estado='PARCIAL',
        error_codigo='SIN_DESTINATARIOS',
        error_mensaje=f'No hay destinatarios activos para {server_id}/{sucursal_id}/{almacen_id}'
    )
    
    # NO es error fatal - el análisis se generó correctamente
    # Solo no se envió a nadie
    
    # Opcionalmente: notificar a admin del sistema
    await notificar_admin(
        asunto='Análisis sin destinatarios',
        cuerpo=f'El análisis para {almacen_id} se generó pero no hay destinatarios configurados.'
    )
```

---

## 4. CONTROL DE CONCURRENCIA

### 4.1 Problema a Resolver

```
Escenario de riesgo:
┌─────────────┐     ┌─────────────┐
│ Instancia A │     │ Instancia B │
└──────┬──────┘     └──────┬──────┘
       │                   │
       │ Detecta folio     │ Detecta mismo folio
       │ 12345             │ 12345
       │                   │
       ▼                   ▼
  ┌─────────┐         ┌─────────┐
  │ Procesa │         │ Procesa │  ← DUPLICADO!
  └─────────┘         └─────────┘
```

### 4.2 Solución: Bloqueo Pesimista con Timeout

```sql
-- La tabla de control incluye campos para concurrencia:
ALTER TABLE automatizacion_inventarios_folios_procesados ADD (
    lock_instance_id VARCHAR(100) NULL,  -- ID de la instancia que tiene el lock
    lock_timestamp DATETIME2 NULL,        -- Cuando se tomó el lock
    lock_timeout_seconds INT DEFAULT 300  -- 5 minutos por defecto
);

-- Índice para buscar locks expirados
CREATE INDEX IX_folios_lock 
    ON automatizacion_inventarios_folios_procesados(lock_timestamp, estado)
    WHERE estado = 'EN_PROCESO';
```

### 4.3 Algoritmo de Adquisición de Lock

```python
import uuid
from datetime import datetime, timedelta

# ID único de esta instancia del worker
INSTANCE_ID = str(uuid.uuid4())[:8]

async def adquirir_lock_folio(
    server_id: str,
    sucursal_id: Optional[str],
    almacen_id: str,
    folio_inventario: str,
    fecha_inventario: str,
    timeout_seconds: int = 300
) -> tuple[bool, Optional[str]]:
    """
    Intenta adquirir lock exclusivo sobre un folio.
    
    Usa INSERT con UNIQUE constraint para garantizar atomicidad.
    
    Returns:
        (lock_adquirido, procesado_id)
    """
    
    hash_verificacion = calcular_hash(server_id, sucursal_id, almacen_id, folio_inventario, fecha_inventario)
    procesado_id = str(uuid.uuid4())
    
    try:
        # Intento 1: INSERT nuevo registro
        result = await execute_sql("""
            INSERT INTO automatizacion_inventarios_folios_procesados (
                procesado_id,
                server_id,
                sucursal_id,
                almacen_id,
                folio_inventario,
                fecha_inventario,
                hash_verificacion,
                estado,
                lock_instance_id,
                lock_timestamp,
                lock_timeout_seconds,
                fecha_inicio_proceso
            ) VALUES (
                @procesado_id,
                @server_id,
                @sucursal_id,
                @almacen_id,
                @folio_inventario,
                @fecha_inventario,
                @hash_verificacion,
                'EN_PROCESO',
                @instance_id,
                GETDATE(),
                @timeout,
                GETDATE()
            )
        """, {
            'procesado_id': procesado_id,
            'server_id': server_id,
            'sucursal_id': sucursal_id,
            'almacen_id': almacen_id,
            'folio_inventario': folio_inventario,
            'fecha_inventario': fecha_inventario,
            'hash_verificacion': hash_verificacion,
            'instance_id': INSTANCE_ID,
            'timeout': timeout_seconds
        })
        
        logging.info(f"Lock adquirido para folio {folio_inventario} por instancia {INSTANCE_ID}")
        return (True, procesado_id)
        
    except UniqueConstraintViolation:
        # Ya existe un registro - verificar si podemos robarlo
        return await _intentar_robar_lock(hash_verificacion)


async def _intentar_robar_lock(hash_verificacion: str) -> tuple[bool, Optional[str]]:
    """
    Si el lock existente expiró, lo robamos.
    """
    
    # Verificar estado actual
    existente = await execute_sql("""
        SELECT 
            procesado_id,
            estado,
            lock_instance_id,
            lock_timestamp,
            lock_timeout_seconds
        FROM automatizacion_inventarios_folios_procesados
        WHERE hash_verificacion = @hash
    """, {'hash': hash_verificacion})
    
    if not existente:
        return (False, None)
    
    registro = existente[0]
    
    # Caso 1: Ya procesado exitosamente
    if registro['estado'] in ('EXITOSO', 'PARCIAL'):
        logging.info(f"Folio ya procesado anteriormente con estado {registro['estado']}")
        return (False, None)
    
    # Caso 2: En proceso pero lock expirado
    if registro['estado'] == 'EN_PROCESO':
        lock_time = registro['lock_timestamp']
        timeout = registro['lock_timeout_seconds'] or 300
        
        if lock_time and (datetime.utcnow() - lock_time).total_seconds() > timeout:
            # Lock expirado - robarlo
            logging.warning(f"Lock expirado de instancia {registro['lock_instance_id']}, robando...")
            
            result = await execute_sql("""
                UPDATE automatizacion_inventarios_folios_procesados
                SET 
                    lock_instance_id = @new_instance,
                    lock_timestamp = GETDATE(),
                    estado = 'EN_PROCESO'
                WHERE hash_verificacion = @hash
                  AND lock_instance_id = @old_instance  -- Garantizar que no cambió
            """, {
                'hash': hash_verificacion,
                'new_instance': INSTANCE_ID,
                'old_instance': registro['lock_instance_id']
            })
            
            if result.rowcount > 0:
                logging.info(f"Lock robado exitosamente por instancia {INSTANCE_ID}")
                return (True, registro['procesado_id'])
            else:
                logging.warning("Otra instancia robó el lock primero")
                return (False, None)
        else:
            # Lock vigente de otra instancia
            logging.info(f"Folio en proceso por instancia {registro['lock_instance_id']}")
            return (False, None)
    
    # Caso 3: Estado ERROR - permitir reproceso
    if registro['estado'] == 'ERROR':
        # Actualizar a EN_PROCESO para reprocesar
        result = await execute_sql("""
            UPDATE automatizacion_inventarios_folios_procesados
            SET 
                estado = 'EN_PROCESO',
                lock_instance_id = @instance,
                lock_timestamp = GETDATE(),
                fecha_inicio_proceso = GETDATE()
            WHERE hash_verificacion = @hash
              AND estado = 'ERROR'
        """, {
            'hash': hash_verificacion,
            'instance': INSTANCE_ID
        })
        
        if result.rowcount > 0:
            return (True, registro['procesado_id'])
    
    return (False, None)


async def liberar_lock_folio(
    procesado_id: str,
    estado_final: str,
    error_mensaje: Optional[str] = None
):
    """
    Libera el lock y actualiza el estado final.
    """
    await execute_sql("""
        UPDATE automatizacion_inventarios_folios_procesados
        SET 
            estado = @estado,
            fecha_fin_proceso = GETDATE(),
            duracion_ms = DATEDIFF(MILLISECOND, fecha_inicio_proceso, GETDATE()),
            error_mensaje = @error,
            lock_instance_id = NULL,
            lock_timestamp = NULL
        WHERE procesado_id = @id
    """, {
        'id': procesado_id,
        'estado': estado_final,
        'error': error_mensaje
    })
```

### 4.4 Diagrama de Concurrencia

```
Instancia A                    Instancia B                    Base de Datos
    │                              │                              │
    │ INSERT folio=123             │                              │
    │────────────────────────────────────────────────────────────▶│
    │                              │                              │
    │◀───────────────────────────────────────────────────────────│
    │ OK, lock adquirido           │                              │
    │                              │                              │
    │ Procesando...                │ INSERT folio=123             │
    │                              │────────────────────────────▶│
    │                              │                              │
    │                              │◀────────────────────────────│
    │                              │ ERROR: Unique constraint     │
    │                              │                              │
    │                              │ SELECT estado, lock_time     │
    │                              │────────────────────────────▶│
    │                              │                              │
    │                              │◀────────────────────────────│
    │                              │ estado=EN_PROCESO, no expiró │
    │                              │                              │
    │                              │ Skip (otro lo procesa)       │
    │                              │                              │
    │ Termina OK                   │                              │
    │────────────────────────────────────────────────────────────▶│
    │ UPDATE estado=EXITOSO        │                              │
    │                              │                              │
```

---

## 5. DESACOPLAMIENTO TOTAL DEL FRONTEND

### 5.1 Declaración Formal

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   EL MÓDULO DE AUTOMATIZACIÓN ES 100% BACKEND.                           ║
║   NO TIENE COMPONENTES DE FRONTEND.                                       ║
║   NO MODIFICA NINGÚN ARCHIVO EN /app/frontend/.                          ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### 5.2 Arquitectura de Desacoplamiento

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                       │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Reportes.js   │  │   Finanzas.js   │  │   Dashboard.js  │             │
│  │                 │  │                 │  │                 │             │
│  │ (NO CAMBIA)     │  │ (NO CAMBIA)     │  │ (NO CAMBIA)     │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  NINGÚN ARCHIVO DE FRONTEND SE MODIFICA PARA ESTA AUTOMATIZACIÓN           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    MÓDULO AUTOMATIZACIÓN (NUEVO)                    │   │
│  │                                                                     │   │
│  │   /app/backend/modules/automatizacion/                              │   │
│  │   ├── __init__.py                                                   │   │
│  │   ├── scheduler.py    ← APScheduler job (no necesita UI)           │   │
│  │   ├── detector.py     ← Detecta folios (backend puro)              │   │
│  │   ├── generator.py    ← Genera análisis (usa core)                 │   │
│  │   ├── notifier.py     ← Envía emails (backend puro)                │   │
│  │   └── routes.py       ← Endpoints SOLO para admin/monitoreo        │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    COMPONENTES EXISTENTES (SIN CAMBIOS)             │   │
│  │                                                                     │   │
│  │   /app/backend/server.py          ← NO CAMBIA (solo import core)   │   │
│  │   /app/backend/modules/compras/   ← NO CAMBIA                      │   │
│  │   /app/backend/modules/finanzas/  ← NO CAMBIA                      │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Endpoints de Administración (Backend API)

```
ESTOS ENDPOINTS SON PARA ADMINISTRACIÓN VÍA API.
NO REQUIEREN UI EN ESTA FASE.
SE PUEDEN CONSUMIR VÍA CURL, POSTMAN, O FUTURO PANEL ADMIN.

Endpoints del módulo:

GET  /api/automatizacion/status
     → Estado general de la automatización (activa/inactiva, último ciclo)

GET  /api/automatizacion/bitacora
     → Lista de ejecuciones recientes (paginada)

GET  /api/automatizacion/config/{server_id}
     → Configuración de un servidor

POST /api/automatizacion/config
     → Crear/actualizar configuración

POST /api/automatizacion/reprocesar
     → Forzar reproceso de un folio específico

POST /api/automatizacion/toggle/{server_id}
     → Activar/desactivar para un servidor

TODOS PROTEGIDOS POR RBAC:
- Requieren autenticación JWT
- Requieren permisos específicos (automatizacion.view, automatizacion.config, etc.)
```

### 5.4 Operación Autónoma

```python
# El scheduler corre como background task en el servidor FastAPI
# No depende de que un usuario tenga el frontend abierto

# /app/backend/modules/automatizacion/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()

def iniciar_scheduler():
    """
    Inicia el scheduler de automatización.
    Se llama desde server.py al iniciar la aplicación.
    """
    scheduler.add_job(
        ejecutar_ciclo_automatizacion,
        trigger=IntervalTrigger(minutes=15),  # Configurable
        id='automatizacion_inventarios',
        name='Ciclo de automatización de inventarios',
        replace_existing=True
    )
    scheduler.start()
    logging.info("Scheduler de automatización iniciado")

async def ejecutar_ciclo_automatizacion():
    """
    Ejecuta un ciclo completo de detección y procesamiento.
    Se ejecuta automáticamente cada X minutos.
    NO REQUIERE INTERACCIÓN DEL USUARIO.
    """
    logging.info("Iniciando ciclo de automatización...")
    
    # 1. Obtener servidores con automatización activa
    servidores = await obtener_servidores_activos()
    
    for servidor in servidores:
        # 2. Detectar nuevos folios
        nuevos = await detectar_nuevos_folios(servidor)
        
        for folio in nuevos:
            # 3. Procesar cada folio
            await procesar_folio(servidor, folio)
    
    logging.info("Ciclo de automatización completado")
```

### 5.5 Garantía de No Impacto en Frontend

```
ARCHIVOS DE FRONTEND QUE NO SE TOCAN:

✗ /app/frontend/src/pages/Reportes.js        → NO MODIFICAR
✗ /app/frontend/src/pages/Finanzas.js        → NO MODIFICAR
✗ /app/frontend/src/pages/Dashboard.js       → NO MODIFICAR
✗ /app/frontend/src/components/*             → NO MODIFICAR
✗ /app/frontend/src/lib/*                    → NO MODIFICAR
✗ /app/frontend/package.json                 → NO MODIFICAR

La automatización funciona completamente en background.
El usuario sigue usando el sistema exactamente igual que antes.
La única diferencia es que ahora recibe emails automáticos.
```

---

## 6. PLAN DE FASES AJUSTADO

### 6.1 Nueva Estructura de Fases

```
FASE 1: EMAIL ÚNICAMENTE
FASE 2: WHATSAPP (POSTERIOR, SEPARADA)
```

### 6.2 Fase 0: Preparación (1-2 días)

| Tarea | Detalle | Validación |
|-------|---------|------------|
| Crear tablas SQL | 6 tablas en EDARSA HUB | Script DDL ejecutable |
| Crear estructura de módulo | `/modules/automatizacion/` | Imports funcionan |
| Configurar APScheduler | Job básico que loguea | Ver logs cada 15 min |

**Entregable**: Infraestructura lista, sin funcionalidad.

### 6.3 Fase 1A: Core Service (2-3 días)

| Tarea | Detalle | Validación |
|-------|---------|------------|
| Crear `inventory_analysis_core.py` | Extraer lógica de server.py | Archivo creado |
| Migrar lógica MPRO | Sin cambios funcionales | Test unitario |
| Migrar lógica SoftRestaurant | Sin cambios funcionales | Test unitario |
| Modificar endpoint existente | Usar core | Test E2E: mismo output |

**Entregable**: Core service funcionando, endpoint existente sin cambios visibles.

**Test obligatorio**:
```bash
# Generar análisis vía endpoint
curl -X POST /api/reports/inventory-analysis -d '{...}' > resultado_endpoint.json

# Generar análisis vía core directamente (test interno)
python -c "from core.inventory_analysis_core import ..."  > resultado_core.json

# Comparar
diff resultado_endpoint.json resultado_core.json
# DEBE SER IDÉNTICO
```

### 6.4 Fase 1B: Detección y Procesamiento (3-4 días)

| Tarea | Detalle | Validación |
|-------|---------|------------|
| Implementar `detector.py` | Query de nuevos folios | Detecta folios de prueba |
| Implementar `resolver.py` | Inventario inicial + destinatarios | Resuelve correctamente |
| Implementar `generator.py` | Usa core service | Genera análisis idéntico |
| Implementar control de duplicados | Tabla de folios procesados | No procesa dos veces |
| Implementar control de concurrencia | Locks con timeout | Test de 2 instancias |

**Entregable**: Motor de procesamiento completo.

### 6.5 Fase 1C: Exportación y Email (3-4 días)

| Tarea | Detalle | Validación |
|-------|---------|------------|
| Implementar `exporter.py` | Reutiliza lógica Excel existente | Excel idéntico al manual |
| Configurar SMTP | Variables de entorno | Envía email de prueba |
| Implementar `notifier.py` | Solo email (TO/CC/BCC) | Email llega correctamente |
| Implementar plantilla email | HTML responsive | Se ve bien en clientes |
| Registrar envíos en bitácora | Tabla de envíos | Trazabilidad completa |

**Entregable**: Automatización funcional con email.

### 6.6 Fase 1D: Scheduler y Monitoreo (2-3 días)

| Tarea | Detalle | Validación |
|-------|---------|------------|
| Implementar `scheduler.py` | APScheduler integrado | Corre cada X minutos |
| Implementar endpoints admin | GET status, bitácora | API responde |
| Implementar toggle on/off | Por servidor | Se activa/desactiva |
| Logging completo | Todos los pasos | Logs útiles para debug |

**Entregable**: Sistema completo Fase 1.

### 6.7 Fase 1E: Piloto Controlado (1 semana)

| Día | Actividad |
|-----|-----------|
| 1 | Activar en 1 servidor de prueba (ej: ambiente QA) |
| 2-3 | Monitorear, ajustar intervalos |
| 4-5 | Validar con auditor real: ¿análisis idéntico? |
| 6-7 | Documentar ajustes, preparar rollout |

**Entregable**: Validación en ambiente real.

### 6.8 Fase 1F: Rollout Gradual (2 semanas)

| Semana | Actividad |
|--------|-----------|
| 1 | Activar 2-3 servidores más, monitorear |
| 2 | Activar resto de servidores, soporte |

**Entregable**: Producción completa (solo email).

### 6.9 Fase 2: WhatsApp (Posterior, Separada)

```
FASE 2 NO INICIA HASTA QUE FASE 1 ESTÉ ESTABLE EN PRODUCCIÓN.

Estimación: 1-2 semanas adicionales después de estabilizar Fase 1.

Tareas Fase 2:
- Integrar proveedor WhatsApp (Twilio o Meta)
- Agregar lógica a notifier.py
- Agregar campo telefono_whatsapp a UI de configuración (única modificación frontend)
- Piloto WhatsApp
- Rollout WhatsApp
```

### 6.10 Cronograma Visual

```
Semana 1        Semana 2        Semana 3        Semana 4        Semana 5-6
────────────────────────────────────────────────────────────────────────────
│ Fase 0 │ Fase 1A │  Fase 1B   │    Fase 1C    │  Fase 1D  │  Fase 1E  │
│Prepara │  Core   │ Detección  │ Excel + Email │ Scheduler │  Piloto   │
│ción    │ Service │ Procesam.  │               │ Monitoreo │ Controlado│
────────────────────────────────────────────────────────────────────────────

Semana 7-8
────────────────
│   Fase 1F    │
│   Rollout    │
│   Gradual    │
────────────────

[PAUSA ESTABILIZACIÓN - 2+ SEMANAS]

Semana 11+
────────────────
│   Fase 2     │
│  WhatsApp    │
│ (Opcional)   │
────────────────
```

---

## RESUMEN DE DEFINICIONES CRÍTICAS

| # | Punto | Definición |
|---|-------|------------|
| 1 | Core Service | Extraer lógica a `inventory_analysis_core.py`, endpoint y automatización usan el mismo core |
| 2 | Clave Única | Compuesta (server+sucursal+almacen+folio+fecha) + hash SHA256 de verificación |
| 3 | Destinatarios | ACUMULACIÓN jerárquica con DEDUPLICACIÓN (nivel más específico gana) |
| 4 | Concurrencia | Bloqueo pesimista con INSERT atómico + timeout de 5 min + robo de lock expirado |
| 5 | Desacoplamiento | 100% backend, cero cambios en frontend, scheduler autónomo |
| 6 | Fases | Fase 1 = solo email, WhatsApp en Fase 2 posterior |

---

## SIGUIENTE PASO

**Estos 6 puntos quedan formalmente definidos.**

Se requiere confirmación explícita antes de iniciar implementación:

1. ¿La estrategia de Core Service es aceptable?
2. ¿La clave compuesta cubre todos los casos?
3. ¿La regla de acumulación con deduplicación es correcta?
4. ¿El control de concurrencia es suficiente?
5. ¿El desacoplamiento del frontend es claro?
6. ¿El plan de fases (email primero) es correcto?

---

*Adenda CAB-003-A - Diciembre 2025*
