# ADENDA TÉCNICA B: Ajustes Finales Obligatorios
## EDARSA HUB - CAB-003 - Adenda B

**Versión**: 1.2  
**Fecha**: Diciembre 2025  
**Estado**: AJUSTES FINALES APROBADOS  
**Referencia**: Correcciones a Adenda A por solicitud del Product Owner

---

## AJUSTES REQUERIDOS

| # | Punto | Estado Anterior | Ajuste Requerido |
|---|-------|-----------------|------------------|
| 1 | Clave Única | Sin `sistema_origen` | Agregar `sistema_origen` como primer componente |
| 2 | Concurrencia | Timeout fijo 5 min | Heartbeat con renovación de lock |

---

## AJUSTE 1: CLAVE ÚNICA CON SISTEMA ORIGEN

### 1.1 Definición Corregida

```
CLAVE ÚNICA DE PROCESO (CORREGIDA):
┌─────────────────────────────────────────────────────────────────────────┐
│  Componentes (todos obligatorios):                                      │
│                                                                         │
│  1. sistema_origen   VARCHAR(20)   'SOFTRESTAURANT' o 'MPRO'           │
│  2. server_id        VARCHAR(50)   Ej: "LA_ESTELAR"                    │
│  3. sucursal_id      VARCHAR(50)   Ej: "01" o NULL para SOFT           │
│  4. almacen_id       VARCHAR(50)   Ej: "COCINA"                        │
│  5. folio_inventario VARCHAR(50)   Ej: "12345"                         │
│  6. fecha_inventario DATE          Ej: "2025-12-15"                    │
│                                                                         │
│  Hash de verificación (derivado):                                       │
│  hash_verificacion = SHA256(                                            │
│      sistema_origen + "|" +                                             │
│      server_id + "|" +                                                  │
│      COALESCE(sucursal_id, "NULL") + "|" +                             │
│      almacen_id + "|" +                                                │
│      folio_inventario + "|" +                                          │
│      fecha_inventario                                                   │
│  )                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Justificación

```
¿Por qué sistema_origen es necesario?

Escenario de riesgo sin sistema_origen:
- Servidor A (SoftRestaurant) tiene folio "12345" en almacén "COCINA"
- Servidor B (MPRO) también tiene folio "12345" en almacén "COCINA"
- Sin sistema_origen, la clave sería ambigua si server_id fuera igual o similar

Aunque en la práctica los server_id son únicos, agregar sistema_origen:
1. Hace explícita la fuente de datos
2. Permite queries filtradas por tipo de sistema
3. Facilita debugging y auditoría
4. Es consistente con el modelo de datos existente en EDARSA HUB
```

### 1.3 Tabla SQL Corregida

```sql
CREATE TABLE automatizacion_inventarios_folios_procesados (
    -- Clave primaria técnica
    procesado_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    
    -- SISTEMA ORIGEN (NUEVO - OBLIGATORIO)
    sistema_origen VARCHAR(20) NOT NULL 
        CHECK (sistema_origen IN ('SOFTRESTAURANT', 'MPRO')),
    
    -- CLAVE ÚNICA COMPUESTA (ahora incluye sistema_origen)
    server_id VARCHAR(50) NOT NULL,
    sucursal_id VARCHAR(50) NULL,
    almacen_id VARCHAR(50) NOT NULL,
    folio_inventario VARCHAR(50) NOT NULL,
    fecha_inventario DATE NOT NULL,
    
    -- Hash de verificación (incluye sistema_origen)
    hash_verificacion VARCHAR(64) NOT NULL,
    
    -- ... resto de campos igual que en Adenda A ...
    
    -- CONSTRAINT CORREGIDO: Incluye sistema_origen
    CONSTRAINT UQ_folio_unico UNIQUE (
        sistema_origen,  -- NUEVO
        server_id, 
        sucursal_id, 
        almacen_id, 
        folio_inventario, 
        fecha_inventario
    ),
    
    CONSTRAINT UQ_hash_verificacion UNIQUE (hash_verificacion)
);

-- Índice corregido
CREATE INDEX IX_folios_sistema_server_fecha 
    ON automatizacion_inventarios_folios_procesados(
        sistema_origen, 
        server_id, 
        fecha_inventario
    );
```

### 1.4 Función de Hash Corregida

```python
def calcular_hash_verificacion(
    sistema_origen: str,  # NUEVO PARÁMETRO
    server_id: str,
    sucursal_id: Optional[str],
    almacen_id: str,
    folio_inventario: str,
    fecha_inventario: str
) -> str:
    """
    Calcula hash único para identificar un folio procesado.
    
    Args:
        sistema_origen: 'SOFTRESTAURANT' o 'MPRO'
        server_id: ID del servidor
        sucursal_id: ID de sucursal (None para SoftRestaurant)
        almacen_id: ID del almacén
        folio_inventario: Folio del inventario
        fecha_inventario: Fecha en formato YYYY-MM-DD
    
    Returns:
        Hash SHA256 de 64 caracteres
    """
    # Normalizar sistema_origen a mayúsculas
    sistema = sistema_origen.upper()
    
    # Construir cadena de entrada
    hash_input = "|".join([
        sistema,
        server_id,
        sucursal_id or "NULL",
        almacen_id,
        folio_inventario,
        fecha_inventario
    ])
    
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
```

### 1.5 Ejemplo de Claves con Sistema Origen

```
Ejemplo 1: SoftRestaurant
─────────────────────────
sistema_origen    = "SOFTRESTAURANT"
server_id         = "LA_ESTELAR"
sucursal_id       = NULL
almacen_id        = "COCINA"
folio_inventario  = "12345"
fecha_inventario  = "2025-12-15"

hash = SHA256("SOFTRESTAURANT|LA_ESTELAR|NULL|COCINA|12345|2025-12-15")
     = "a1b2c3d4..."

Ejemplo 2: MPRO
───────────────
sistema_origen    = "MPRO"
server_id         = "CIENFUEGOS"
sucursal_id       = "01"
almacen_id        = "COCINA"
folio_inventario  = "12345"
fecha_inventario  = "2025-12-15"

hash = SHA256("MPRO|CIENFUEGOS|01|COCINA|12345|2025-12-15")
     = "e5f6g7h8..."

Aunque el folio y almacén son iguales, los hashes son diferentes
porque sistema_origen y server_id son distintos.
```

---

## AJUSTE 2: CONCURRENCIA CON HEARTBEAT

### 2.1 Problema del Timeout Fijo

```
ESCENARIO DE FALLA CON TIMEOUT FIJO:

Tiempo    Instancia A                    Instancia B
──────────────────────────────────────────────────────────────
0:00      Adquiere lock (timeout=5min)   -
0:01      Procesando...                  -
0:02      Procesando...                  -
0:03      Procesando...                  -
0:04      Procesando...                  -
0:05      Procesando (sigue vivo)        Detecta timeout expirado
0:05      ↓                              Roba lock (ERROR!)
0:06      Intenta actualizar BD          Procesando...
0:06      CONFLICTO - Lock robado        ↓
          Proceso A falla                Proceso B continúa
          
RESULTADO: Posible corrupción o análisis duplicado
```

### 2.2 Solución: Heartbeat con Renovación Automática

```
ESTRATEGIA SEGURA: HEARTBEAT + RENOVACIÓN

1. El proceso adquiere lock con timestamp inicial
2. Cada N segundos (heartbeat_interval), el proceso renueva el lock
3. El lock solo expira si NO hay heartbeat en M segundos (heartbeat_timeout)
4. Si el proceso muere, el heartbeat se detiene y el lock expira naturalmente
5. Otro proceso puede robar el lock SOLO si heartbeat_timeout se excede

Parámetros:
- heartbeat_interval = 30 segundos (cada cuánto se renueva)
- heartbeat_timeout = 120 segundos (cuánto esperar sin heartbeat para considerar muerto)
- max_process_time = 30 minutos (tiempo máximo absoluto de un proceso)
```

### 2.3 Campos de Tabla Actualizados

```sql
-- Campos de concurrencia actualizados en folios_procesados
ALTER TABLE automatizacion_inventarios_folios_procesados ADD (
    -- Identificación de instancia
    lock_instance_id VARCHAR(100) NULL,
    lock_instance_hostname VARCHAR(100) NULL,
    
    -- Timestamps de lock
    lock_acquired_at DATETIME2 NULL,
    lock_last_heartbeat DATETIME2 NULL,
    
    -- Configuración de heartbeat
    heartbeat_interval_seconds INT DEFAULT 30,
    heartbeat_timeout_seconds INT DEFAULT 120,
    max_process_time_seconds INT DEFAULT 1800,  -- 30 minutos
    
    -- Contadores de heartbeat
    heartbeat_count INT DEFAULT 0
);

-- Índice para detectar locks muertos
CREATE INDEX IX_folios_heartbeat 
    ON automatizacion_inventarios_folios_procesados(
        lock_last_heartbeat, 
        estado
    )
    WHERE estado = 'EN_PROCESO';
```

### 2.4 Implementación del Heartbeat

```python
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable
import logging

class LockManager:
    """
    Gestor de locks con heartbeat para control de concurrencia.
    
    Garantiza que:
    1. Un proceso mantiene su lock mientras esté vivo
    2. Si el proceso muere, el lock expira tras heartbeat_timeout
    3. Otro proceso puede robar el lock SOLO si está realmente muerto
    """
    
    def __init__(
        self,
        db_connection,
        heartbeat_interval: int = 30,
        heartbeat_timeout: int = 120,
        max_process_time: int = 1800
    ):
        self.db = db_connection
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.max_process_time = max_process_time
        self.instance_id = f"{socket.gethostname()}_{os.getpid()}_{uuid.uuid4().hex[:8]}"
        
        # Estado interno
        self._active_locks: dict[str, asyncio.Task] = {}
        self._shutdown = False
    
    async def adquirir_lock(
        self,
        sistema_origen: str,
        server_id: str,
        sucursal_id: Optional[str],
        almacen_id: str,
        folio_inventario: str,
        fecha_inventario: str
    ) -> tuple[bool, Optional[str]]:
        """
        Intenta adquirir lock con heartbeat automático.
        
        Returns:
            (éxito, procesado_id) - Si éxito=True, el heartbeat ya está corriendo
        """
        hash_verificacion = calcular_hash_verificacion(
            sistema_origen, server_id, sucursal_id, 
            almacen_id, folio_inventario, fecha_inventario
        )
        
        try:
            procesado_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Intentar INSERT atómico
            await self.db.execute("""
                INSERT INTO automatizacion_inventarios_folios_procesados (
                    procesado_id,
                    sistema_origen,
                    server_id,
                    sucursal_id,
                    almacen_id,
                    folio_inventario,
                    fecha_inventario,
                    hash_verificacion,
                    estado,
                    lock_instance_id,
                    lock_instance_hostname,
                    lock_acquired_at,
                    lock_last_heartbeat,
                    heartbeat_interval_seconds,
                    heartbeat_timeout_seconds,
                    max_process_time_seconds,
                    heartbeat_count,
                    fecha_inicio_proceso
                ) VALUES (
                    @procesado_id,
                    @sistema_origen,
                    @server_id,
                    @sucursal_id,
                    @almacen_id,
                    @folio_inventario,
                    @fecha_inventario,
                    @hash,
                    'EN_PROCESO',
                    @instance_id,
                    @hostname,
                    @now,
                    @now,
                    @heartbeat_interval,
                    @heartbeat_timeout,
                    @max_process_time,
                    0,
                    @now
                )
            """, {
                'procesado_id': procesado_id,
                'sistema_origen': sistema_origen,
                'server_id': server_id,
                'sucursal_id': sucursal_id,
                'almacen_id': almacen_id,
                'folio_inventario': folio_inventario,
                'fecha_inventario': fecha_inventario,
                'hash': hash_verificacion,
                'instance_id': self.instance_id,
                'hostname': socket.gethostname(),
                'now': now,
                'heartbeat_interval': self.heartbeat_interval,
                'heartbeat_timeout': self.heartbeat_timeout,
                'max_process_time': self.max_process_time
            })
            
            # Lock adquirido - iniciar heartbeat
            self._iniciar_heartbeat(procesado_id, hash_verificacion)
            
            logging.info(
                f"Lock adquirido: {folio_inventario} por {self.instance_id}"
            )
            return (True, procesado_id)
            
        except UniqueConstraintViolation:
            # Ya existe - intentar robar si está muerto
            return await self._intentar_robar_lock(hash_verificacion)
    
    async def _intentar_robar_lock(
        self, 
        hash_verificacion: str
    ) -> tuple[bool, Optional[str]]:
        """
        Intenta robar un lock SOLO si el proceso original está muerto.
        
        Criterios para considerar muerto:
        1. lock_last_heartbeat > heartbeat_timeout_seconds atrás
        2. O lock_acquired_at > max_process_time_seconds atrás
        """
        existente = await self.db.fetch_one("""
            SELECT 
                procesado_id,
                estado,
                lock_instance_id,
                lock_last_heartbeat,
                lock_acquired_at,
                heartbeat_timeout_seconds,
                max_process_time_seconds
            FROM automatizacion_inventarios_folios_procesados
            WHERE hash_verificacion = @hash
        """, {'hash': hash_verificacion})
        
        if not existente:
            return (False, None)
        
        # Caso 1: Ya procesado exitosamente
        if existente['estado'] in ('EXITOSO', 'PARCIAL'):
            logging.info(f"Folio ya procesado: {existente['estado']}")
            return (False, None)
        
        # Caso 2: En proceso - verificar si está muerto
        if existente['estado'] == 'EN_PROCESO':
            now = datetime.utcnow()
            last_heartbeat = existente['lock_last_heartbeat']
            acquired_at = existente['lock_acquired_at']
            heartbeat_timeout = existente['heartbeat_timeout_seconds'] or 120
            max_time = existente['max_process_time_seconds'] or 1800
            
            # ¿Heartbeat expirado?
            heartbeat_muerto = (
                last_heartbeat and 
                (now - last_heartbeat).total_seconds() > heartbeat_timeout
            )
            
            # ¿Tiempo máximo excedido?
            tiempo_excedido = (
                acquired_at and 
                (now - acquired_at).total_seconds() > max_time
            )
            
            if heartbeat_muerto or tiempo_excedido:
                # Proceso muerto - robar lock
                razon = "heartbeat_expirado" if heartbeat_muerto else "tiempo_maximo_excedido"
                logging.warning(
                    f"Lock muerto detectado ({razon}), "
                    f"instancia anterior: {existente['lock_instance_id']}"
                )
                
                # UPDATE condicional para evitar race condition
                result = await self.db.execute("""
                    UPDATE automatizacion_inventarios_folios_procesados
                    SET 
                        lock_instance_id = @new_instance,
                        lock_instance_hostname = @hostname,
                        lock_acquired_at = @now,
                        lock_last_heartbeat = @now,
                        heartbeat_count = 0,
                        fecha_inicio_proceso = @now
                    WHERE hash_verificacion = @hash
                      AND lock_instance_id = @old_instance
                      AND estado = 'EN_PROCESO'
                """, {
                    'hash': hash_verificacion,
                    'new_instance': self.instance_id,
                    'hostname': socket.gethostname(),
                    'now': now,
                    'old_instance': existente['lock_instance_id']
                })
                
                if result.rowcount > 0:
                    # Lock robado exitosamente
                    self._iniciar_heartbeat(
                        existente['procesado_id'], 
                        hash_verificacion
                    )
                    logging.info(f"Lock robado exitosamente por {self.instance_id}")
                    return (True, existente['procesado_id'])
                else:
                    logging.warning("Otra instancia robó el lock primero")
                    return (False, None)
            else:
                # Proceso vivo - no robar
                segundos_desde_heartbeat = (now - last_heartbeat).total_seconds()
                logging.info(
                    f"Lock activo, último heartbeat hace {segundos_desde_heartbeat:.0f}s "
                    f"(timeout={heartbeat_timeout}s)"
                )
                return (False, None)
        
        # Caso 3: Estado ERROR - permitir reproceso
        if existente['estado'] == 'ERROR':
            result = await self.db.execute("""
                UPDATE automatizacion_inventarios_folios_procesados
                SET 
                    estado = 'EN_PROCESO',
                    lock_instance_id = @instance,
                    lock_instance_hostname = @hostname,
                    lock_acquired_at = @now,
                    lock_last_heartbeat = @now,
                    heartbeat_count = 0,
                    fecha_inicio_proceso = @now
                WHERE hash_verificacion = @hash
                  AND estado = 'ERROR'
            """, {
                'hash': hash_verificacion,
                'instance': self.instance_id,
                'hostname': socket.gethostname(),
                'now': datetime.utcnow()
            })
            
            if result.rowcount > 0:
                self._iniciar_heartbeat(
                    existente['procesado_id'], 
                    hash_verificacion
                )
                return (True, existente['procesado_id'])
        
        return (False, None)
    
    def _iniciar_heartbeat(self, procesado_id: str, hash_verificacion: str):
        """
        Inicia tarea de heartbeat en background.
        """
        async def heartbeat_loop():
            while not self._shutdown:
                try:
                    await asyncio.sleep(self.heartbeat_interval)
                    
                    if self._shutdown:
                        break
                    
                    # Renovar heartbeat
                    result = await self.db.execute("""
                        UPDATE automatizacion_inventarios_folios_procesados
                        SET 
                            lock_last_heartbeat = @now,
                            heartbeat_count = heartbeat_count + 1
                        WHERE procesado_id = @id
                          AND lock_instance_id = @instance
                          AND estado = 'EN_PROCESO'
                    """, {
                        'id': procesado_id,
                        'instance': self.instance_id,
                        'now': datetime.utcnow()
                    })
                    
                    if result.rowcount == 0:
                        # Lock perdido (posiblemente robado)
                        logging.error(
                            f"Heartbeat fallido - lock perdido: {procesado_id}"
                        )
                        break
                    
                    logging.debug(f"Heartbeat renovado: {procesado_id}")
                    
                except Exception as e:
                    logging.error(f"Error en heartbeat: {e}")
                    break
        
        # Crear y registrar tarea
        task = asyncio.create_task(heartbeat_loop())
        self._active_locks[procesado_id] = task
    
    async def liberar_lock(
        self,
        procesado_id: str,
        estado_final: str,
        error_mensaje: Optional[str] = None
    ):
        """
        Libera el lock y detiene el heartbeat.
        """
        # Detener heartbeat
        if procesado_id in self._active_locks:
            self._active_locks[procesado_id].cancel()
            del self._active_locks[procesado_id]
        
        # Actualizar estado final
        await self.db.execute("""
            UPDATE automatizacion_inventarios_folios_procesados
            SET 
                estado = @estado,
                fecha_fin_proceso = @now,
                duracion_ms = DATEDIFF(
                    MILLISECOND, 
                    fecha_inicio_proceso, 
                    @now
                ),
                error_mensaje = @error,
                lock_instance_id = NULL,
                lock_last_heartbeat = NULL
            WHERE procesado_id = @id
        """, {
            'id': procesado_id,
            'estado': estado_final,
            'error': error_mensaje,
            'now': datetime.utcnow()
        })
        
        logging.info(f"Lock liberado: {procesado_id} -> {estado_final}")
    
    async def shutdown(self):
        """
        Detiene todos los heartbeats activos.
        Llamar al apagar la aplicación.
        """
        self._shutdown = True
        for task in self._active_locks.values():
            task.cancel()
        self._active_locks.clear()
```

### 2.5 Diagrama de Heartbeat

```
Tiempo    Instancia A                              Base de Datos
──────────────────────────────────────────────────────────────────────────
0:00      INSERT lock (heartbeat=0:00)             lock_last_heartbeat=0:00
          ↓
0:30      UPDATE heartbeat (heartbeat=0:30)        lock_last_heartbeat=0:30
          ↓
1:00      UPDATE heartbeat (heartbeat=1:00)        lock_last_heartbeat=1:00
          ↓
1:30      UPDATE heartbeat (heartbeat=1:30)        lock_last_heartbeat=1:30
          ↓
2:00      UPDATE heartbeat (heartbeat=2:00)        lock_last_heartbeat=2:00
          ↓
...
5:00      Proceso termina OK                       
          UPDATE estado=EXITOSO                    estado=EXITOSO
          lock_instance_id = NULL


CASO: Proceso A muere inesperadamente
──────────────────────────────────────────────────────────────────────────
Tiempo    Instancia A              Instancia B              BD
──────────────────────────────────────────────────────────────────────────
0:00      Adquiere lock            -                        heartbeat=0:00
0:30      Heartbeat                -                        heartbeat=0:30
1:00      Heartbeat                -                        heartbeat=1:00
1:15      CRASH! (muere)           -                        heartbeat=1:00
          (sin más heartbeats)
1:30      -                        -                        heartbeat=1:00
2:00      -                        -                        heartbeat=1:00
2:30      -                        Detecta folio            heartbeat=1:00
          -                        Verifica: 1:00 + 120s    
          -                        = 3:00 (aún no expira)   
          -                        Espera...                
3:01      -                        Verifica: 1:00 + 120s    
          -                        = 3:00 < 3:01 EXPIRADO!  
          -                        Roba lock                heartbeat=3:01
          -                        Procesa...               
```

### 2.6 Parámetros Configurables

```python
# Configuración recomendada por tipo de entorno

# PRODUCCIÓN (conservador)
HEARTBEAT_INTERVAL = 30      # Heartbeat cada 30 segundos
HEARTBEAT_TIMEOUT = 120      # Considerar muerto si no hay heartbeat en 2 min
MAX_PROCESS_TIME = 1800      # Tiempo máximo absoluto: 30 minutos

# DESARROLLO (más agresivo para testing)
HEARTBEAT_INTERVAL = 10      # Heartbeat cada 10 segundos
HEARTBEAT_TIMEOUT = 45       # Considerar muerto si no hay heartbeat en 45s
MAX_PROCESS_TIME = 300       # Tiempo máximo: 5 minutos

# Los valores se pueden configurar por servidor en la tabla de config
```

### 2.7 Flujo Completo con Heartbeat

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUJO DE PROCESAMIENTO CON HEARTBEAT                     │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │ Detectar folio   │
    │ nuevo            │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ lock_manager.    │
    │ adquirir_lock()  │
    └────────┬─────────┘
             │
             │ ¿Lock adquirido?
             │
    ┌────────┴────────┐
    │ NO              │ SI
    │ (ya procesado   │
    │  o lock activo) │
    └─────────────────┘
             │
             ▼
    ┌──────────────────┐     ┌──────────────────┐
    │ PROCESO MAIN     │     │ HEARTBEAT TASK   │
    │                  │     │ (background)     │
    │ 1. Resolver inv  │     │                  │
    │    inicial       │     │ while not done:  │
    │                  │ ←──▶│   sleep(30s)     │
    │ 2. Generar       │     │   UPDATE         │
    │    análisis      │     │   heartbeat      │
    │                  │     │                  │
    │ 3. Exportar      │     └──────────────────┘
    │    Excel         │
    │                  │
    │ 4. Resolver      │
    │    destinatarios │
    │                  │
    │ 5. Enviar        │
    │    emails        │
    │                  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ lock_manager.    │
    │ liberar_lock(    │
    │   EXITOSO)       │
    │                  │
    │ - Detiene        │
    │   heartbeat      │
    │ - Actualiza      │
    │   estado final   │
    └──────────────────┘
```

### 2.8 Manejo de Errores con Heartbeat

```python
async def procesar_folio_con_heartbeat(
    lock_manager: LockManager,
    sistema_origen: str,
    server_id: str,
    sucursal_id: Optional[str],
    almacen_id: str,
    folio: str,
    fecha: str
):
    """
    Procesa un folio con heartbeat automático.
    Garantiza liberación del lock en cualquier escenario.
    """
    
    # Intentar adquirir lock
    lock_ok, procesado_id = await lock_manager.adquirir_lock(
        sistema_origen, server_id, sucursal_id,
        almacen_id, folio, fecha
    )
    
    if not lock_ok:
        logging.info(f"No se pudo adquirir lock para {folio}")
        return
    
    try:
        # El heartbeat ya está corriendo en background
        
        # Paso 1: Resolver inventario inicial
        inv_inicial = await resolver_inventario_inicial(...)
        
        # Paso 2: Generar análisis
        analisis = await generar_analisis(...)
        
        # Paso 3: Exportar
        archivo = await exportar_excel(...)
        
        # Paso 4: Resolver destinatarios
        destinatarios = await resolver_destinatarios(...)
        
        # Paso 5: Enviar
        await enviar_notificaciones(...)
        
        # Éxito - liberar lock
        await lock_manager.liberar_lock(procesado_id, 'EXITOSO')
        
    except Exception as e:
        # Error - liberar lock con estado ERROR
        logging.error(f"Error procesando {folio}: {e}")
        await lock_manager.liberar_lock(
            procesado_id, 
            'ERROR', 
            str(e)[:500]
        )
        raise
```

---

## RESUMEN DE AJUSTES FINALES

| # | Ajuste | Antes | Después |
|---|--------|-------|---------|
| 1 | Clave única | 5 componentes | **6 componentes** (+ sistema_origen) |
| 2 | Concurrencia | Timeout fijo 5 min | **Heartbeat cada 30s + timeout 120s** |

### Definición Final de Clave Única

```
(sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario, fecha_inventario)
+ hash SHA256 de verificación
```

### Definición Final de Concurrencia

```
- Heartbeat interval: 30 segundos (configurable)
- Heartbeat timeout: 120 segundos (configurable)
- Max process time: 30 minutos (configurable)
- Lock se puede robar SOLO si:
  - No hay heartbeat en 120+ segundos
  - O tiempo total > 30 minutos
```

---

## ESTADO FINAL DE APROBACIONES

| Punto | Estado |
|-------|--------|
| Core Service | ✅ APROBADO |
| Clave Única (con sistema_origen) | ✅ AJUSTADO Y APROBADO |
| Destinatarios (acumulación + dedup) | ✅ APROBADO |
| Concurrencia (heartbeat) | ✅ AJUSTADO Y APROBADO |
| Desacoplamiento frontend | ✅ APROBADO |
| Fases (email primero) | ✅ APROBADO |

---

## SIGUIENTE PASO

**Con estos ajustes formalizados, el diseño técnico está completo.**

¿Se autoriza iniciar implementación de Fase 0 (Preparación)?

---

*Adenda CAB-003-B - Diciembre 2025*
