# DISEÑO TÉCNICO: EDARSA Sync Agent

**Versión**: 1.0  
**Fecha**: 2026-04-23  
**Estado**: DISEÑO (sin implementación)  
**Autor**: Arquitectura Senior

---

## 1. CONTEXTO Y MOTIVACIÓN

### 1.1 Problema Actual

EDARSA HUB necesita datos de múltiples sucursales que operan sistemas POS (SoftRestaurant, MPRO) en ubicaciones geográficamente dispersas. Actualmente:

```
┌─────────────────┐     ❌ TIMEOUT      ┌─────────────────┐
│  EDARSA HUB     │ ─────────────────── │  Sucursal A     │
│  (Cloud)        │     VPN/Internet    │  (SoftRestaurant)│
└─────────────────┘                     └─────────────────┘
        │
        │ ❌ Sin conectividad directa
        ▼
┌─────────────────┐
│  Sucursal B     │
│  (MPRO)         │
└─────────────────┘
```

**Limitaciones del modelo Pull actual:**
1. Dependencia de conectividad inversa (Cloud → Sucursal)
2. Timeouts frecuentes por redes inestables
3. Firewalls corporativos bloquean conexiones entrantes
4. VPNs costosas y complejas de mantener
5. Imposibilidad de validar paridad numérica desde ambientes sin acceso

### 1.2 Solución Propuesta: Modelo Push

```
┌─────────────────┐                     ┌─────────────────┐
│  EDARSA HUB     │ ◄───────────────────│  SYNC AGENT A   │
│  (Cloud)        │     HTTPS POST      │  (Sucursal A)   │
│                 │     (Push)          │                 │
│  - Recibe datos │                     │  - Extrae SQL   │
│  - UPSERT       │                     │  - Envía a HUB  │
│  - Valida       │                     └─────────────────┘
│  - Almacena     │                              │
└─────────────────┘                     ┌────────┴────────┐
        ▲                               │  SQL Server     │
        │                               │  SoftRestaurant │
        │                               └─────────────────┘
        │
        │     HTTPS POST
┌───────┴─────────┐
│  SYNC AGENT B   │
│  (Sucursal B)   │
│                 │
│  - Extrae SQL   │
│  - Envía a HUB  │
└─────────────────┘
        │
┌───────┴─────────┐
│  SQL Server     │
│  MPRO           │
└─────────────────┘
```

---

## 2. PRINCIPIOS ARQUITECTÓNICOS

### 2.1 EDARSA HUB como Cerebro (Invariante)

| Componente | Responsabilidad | Ubicación |
|------------|-----------------|-----------|
| **EDARSA HUB** | Recibir, validar, almacenar, servir, orquestar | Cloud |
| **Sync Agent** | Extraer, transformar, enviar | Sucursal (local) |

**El agente NO sustituye a HUB**. El agente es un extractor/transportador de datos.

### 2.2 Cero Dependencia de Conectividad Inversa

```
✅ PERMITIDO: Sucursal → Cloud (HTTPS POST a endpoints públicos)
❌ PROHIBIDO: Cloud → Sucursal (requiere VPN, firewall rules, etc.)
```

### 2.3 Idempotencia y Deduplicación

- Cada sync utiliza el patrón UPSERT existente en `kpis_comercial`
- La clave única (`server_id + empresa_id + sucursal_id + fecha`) garantiza no duplicados
- El agente puede reintentar infinitamente sin crear duplicados

### 2.4 Fuentes Configuradas en HUB

El agente NO define qué extraer. EDARSA HUB tiene la configuración maestra en el menú de Servidores:

```javascript
// Colección: sql_servers (ya existe)
{
  "id": "uuid-server-1",
  "name": "Cienfuegos MPRO",
  "system_type": "MPRO",           // SoftRestaurant | MPRO
  "host": "192.168.1.100",
  "port": 1433,
  "database": "CIENFUEGOS_MPRO",
  "username": "...",
  "password": "...",
  "empresa_id": "uuid-empresa",
  "activo": true,
  // NUEVO: Configuración de Sync Agent
  "sync_agent": {
    "habilitado": true,
    "frecuencia_minutos": 15,
    "ultima_sincronizacion": "2026-04-23T10:15:00Z",
    "version_agent_minima": "1.0.0"
  }
}
```

---

## 3. ARQUITECTURA POR COMPONENTES

### 3.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EDARSA HUB (Cloud)                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐    ┌─────────────────────┐                    │
│  │  API Gateway        │    │  Sync Receiver      │                    │
│  │  /api/sync/...      │───▶│  Service            │                    │
│  │                     │    │                     │                    │
│  │  - Autenticación    │    │  - Validación       │                    │
│  │  - Rate limiting    │    │  - Transformación   │                    │
│  │  - Logs acceso      │    │  - UPSERT           │                    │
│  └─────────────────────┘    └──────────┬──────────┘                    │
│                                        │                                │
│                                        ▼                                │
│  ┌─────────────────────┐    ┌─────────────────────┐                    │
│  │  Agent Registry     │    │  kpis_comercial     │                    │
│  │  (MongoDB)          │    │  (MongoDB)          │                    │
│  │                     │    │                     │                    │
│  │  - Agentes activos  │    │  - KPIs diarios     │                    │
│  │  - Heartbeats       │    │  - Histórico        │                    │
│  │  - Versiones        │    │  - Estados          │                    │
│  └─────────────────────┘    └─────────────────────┘                    │
│                                                                         │
│  ┌─────────────────────┐                                               │
│  │  Agent Monitor      │                                               │
│  │  Dashboard          │                                               │
│  │                     │                                               │
│  │  - Estado agentes   │                                               │
│  │  - Alertas offline  │                                               │
│  │  - Logs de sync     │                                               │
│  └─────────────────────┘                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

                               ▲
                               │ HTTPS POST
                               │ (Internet público)
                               │
┌─────────────────────────────────────────────────────────────────────────┐
│                        SYNC AGENT (Por Sucursal)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐    ┌─────────────────────┐                    │
│  │  Config Manager     │    │  Extractor          │                    │
│  │                     │    │                     │                    │
│  │  - Lee config HUB   │    │  - SoftRestaurant   │                    │
│  │  - Credenciales     │    │  - MPRO             │                    │
│  │  - Frecuencia       │    │  - Query Builder    │                    │
│  └─────────────────────┘    └──────────┬──────────┘                    │
│                                        │                                │
│                                        ▼                                │
│  ┌─────────────────────┐    ┌─────────────────────┐                    │
│  │  Cola Local         │    │  Sender             │                    │
│  │  (SQLite/JSON)      │───▶│                     │                    │
│  │                     │    │  - HTTP Client      │                    │
│  │  - Retries          │    │  - Reintentos       │                    │
│  │  - Offline cache    │    │  - Compresión       │                    │
│  └─────────────────────┘    └─────────────────────┘                    │
│                                                                         │
│  ┌─────────────────────┐    ┌─────────────────────┐                    │
│  │  Scheduler          │    │  Logger Local       │                    │
│  │  (cron interno)     │    │  (archivo rotativo) │                    │
│  └─────────────────────┘    └─────────────────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FUENTE LOCAL (SQL Server)                       │
├─────────────────────────────────────────────────────────────────────────┤
│  SoftRestaurant / MPRO                                                  │
│  - localhost:1433 (conexión local, sin latencia)                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Componentes del Agente (Detalle)

| Componente | Responsabilidad | Tecnología |
|------------|-----------------|------------|
| **Config Manager** | Descarga config de HUB, almacena localmente | JSON file |
| **Extractor** | Ejecuta queries al SQL local | pyodbc/pymssql |
| **Queue (Cola Local)** | Buffer de payloads pendientes | SQLite (< 1MB) |
| **Sender** | Envía a HUB con reintentos | requests/httpx |
| **Scheduler** | Ejecuta cada N minutos | schedule lib |
| **Logger** | Logs rotativos locales | logging + rotation |

### 3.3 Decisión: Un Agente Único Multipropósito

**Decisión**: Implementar **UN SOLO agente** con **adaptadores internos** por tipo de fuente.

**Razones:**
1. Reduce complejidad de instalación (un solo binario/script)
2. Comparte lógica de cola, sender, scheduler, logs
3. El `system_type` del servidor define qué adaptador usar
4. Actualización única para todas las sucursales

```python
# Pseudocódigo de selección de adaptador
class SyncAgent:
    def __init__(self, server_config):
        self.extractor = self._get_extractor(server_config['system_type'])
    
    def _get_extractor(self, system_type):
        if system_type == 'SoftRestaurant':
            return SoftRestaurantExtractor()
        elif system_type == 'MPRO':
            return MPROExtractor()
        else:
            raise ValueError(f"Tipo no soportado: {system_type}")
```

---

## 4. FLUJO DE SINCRONIZACIÓN

### 4.1 Flujo Principal (Happy Path)

```
┌────────────┐    ┌──────────────┐    ┌─────────────┐    ┌────────────┐
│ Scheduler  │───▶│ Extractor    │───▶│ Queue       │───▶│ Sender     │
│ (cada 15m) │    │ (SQL local)  │    │ (SQLite)    │    │ (HTTPS)    │
└────────────┘    └──────────────┘    └─────────────┘    └──────┬─────┘
                                                                │
                                                                ▼
                                                        ┌──────────────┐
                                                        │ EDARSA HUB   │
                                                        │ Sync Receiver│
                                                        └──────────────┘
```

**Secuencia detallada:**

```
1. [Agent] Scheduler dispara ejecución (cron cada 15 min)
2. [Agent] Extractor lee configuración local
3. [Agent] Extractor conecta a SQL local (localhost:1433)
4. [Agent] Extractor ejecuta query de KPIs del día
5. [Agent] Extractor transforma resultado a payload JSON
6. [Agent] Queue almacena payload en SQLite
7. [Agent] Sender lee payload de Queue
8. [Agent] Sender hace POST a HUB: /api/sync/kpis
9. [HUB]   Receiver valida token y payload
10.[HUB]   Receiver llama a upsert_kpi_comercial()
11.[HUB]   Receiver responde 200 OK
12.[Agent] Sender marca payload como enviado
13.[Agent] Queue elimina payload de cola
14.[Agent] Logger registra sync exitoso
```

### 4.2 Flujo con Error de Conectividad (Offline)

```
┌────────────┐    ┌──────────────┐    ┌─────────────┐    ┌────────────┐
│ Scheduler  │───▶│ Extractor    │───▶│ Queue       │───▶│ Sender     │
└────────────┘    └──────────────┘    │ (acumula)   │    │ (falla)    │
                                      └──────┬──────┘    └────────────┘
                                             │
                                             │ RETRY (backoff exponencial)
                                             ▼
                                      ┌─────────────┐
                                      │ Sender      │ ──▶ HUB (cuando recupera)
                                      │ (reintenta) │
                                      └─────────────┘
```

**Comportamiento offline:**
1. Extractor sigue funcionando (SQL local OK)
2. Queue acumula payloads (hasta 7 días o 100MB)
3. Sender reintenta con backoff exponencial (1min, 2min, 4min, ..., max 1h)
4. Al recuperar conexión, envía cola completa (FIFO)
5. UPSERT de HUB maneja orden y deduplicación

### 4.3 Flujo con Error de SQL Local

```
┌────────────┐    ┌──────────────┐
│ Scheduler  │───▶│ Extractor    │───▶ ERROR: SQL local caído
└────────────┘    │ (falla)      │
                  └──────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Logger       │ Registra error, NO encola nada
                  │              │ Alerta a HUB (heartbeat con estado)
                  └──────────────┘
```

**Comportamiento con SQL local caído:**
1. Extractor falla, NO encola payload vacío/erróneo
2. Logger registra error con timestamp
3. Heartbeat a HUB indica "SQL_LOCAL_ERROR"
4. HUB muestra alerta en dashboard de monitoreo
5. NO se envían datos hasta que SQL local se recupere

---

## 5. PAYLOADS PROPUESTOS

### 5.1 Payload de Sincronización de KPIs

```json
{
  "version": "1.0",
  "agent_id": "agent-cienfuegos-001",
  "agent_version": "1.2.3",
  "timestamp": "2026-04-23T10:15:00Z",
  "server_id": "6d053c22-523e-48c0-b72b-96081e2d781b",
  "empresa_id": "1d91f076-a28e-49a5-b445-84aa767737b6",
  "system_type": "MPRO",
  
  "payload_type": "KPIS_DIARIOS",
  "records": [
    {
      "sucursal_id": "0021",
      "sucursal_nombre": "CIENFUEGOS PRINCIPAL",
      "fecha": "2026-04-23",
      "kpis": {
        "ventas": 125000.00,
        "pax": 450,
        "cheques": 120,
        "ticket_promedio": 1041.67,
        "propina": 5000.00,
        "descuentos": 2500.00,
        "efectivo": 45000.00,
        "tarjeta": 70000.00
      },
      "source": {
        "type": "LIVE",
        "query_timestamp": "2026-04-23T10:14:58Z",
        "query_duration_ms": 1200,
        "rows_retrieved": 1
      }
    }
  ],
  
  "checksum": "sha256:abc123...",
  "batch_id": "batch-20260423-101500-001"
}
```

### 5.2 Payload de Heartbeat

```json
{
  "version": "1.0",
  "agent_id": "agent-cienfuegos-001",
  "agent_version": "1.2.3",
  "timestamp": "2026-04-23T10:15:00Z",
  "server_id": "6d053c22-523e-48c0-b72b-96081e2d781b",
  
  "status": "OK",                    // OK | SQL_LOCAL_ERROR | CONFIG_ERROR
  "queue_depth": 0,                   // Payloads pendientes
  "last_successful_sync": "2026-04-23T10:00:00Z",
  "last_extraction": "2026-04-23T10:14:58Z",
  "sql_local_status": "CONNECTED",   // CONNECTED | DISCONNECTED | ERROR
  "sql_local_latency_ms": 50,
  "disk_usage_mb": 12,
  "memory_usage_mb": 45,
  "uptime_seconds": 86400
}
```

### 5.3 Respuesta de HUB

```json
{
  "status": "OK",                    // OK | PARTIAL | ERROR
  "received": 1,                      // Records recibidos
  "processed": 1,                     // Records procesados
  "actions": {
    "INSERT": 0,
    "UPDATE": 1,
    "SKIP": 0,
    "REJECTED": 0
  },
  "errors": [],
  "batch_id": "batch-20260423-101500-001",
  "server_time": "2026-04-23T10:15:02Z"
}
```

---

## 6. ESTRATEGIA OFFLINE / RETRY / CACHE LOCAL

### 6.1 Cola Local (SQLite)

```sql
-- Tabla de cola de sincronización
CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT UNIQUE,
    payload_type TEXT,           -- KPIS_DIARIOS, HEARTBEAT, etc.
    payload_json TEXT,           -- Payload comprimido (gzip)
    created_at TEXT,             -- ISO timestamp
    retry_count INTEGER DEFAULT 0,
    last_retry_at TEXT,
    status TEXT DEFAULT 'PENDING' -- PENDING, SENT, FAILED
);

-- Índice para procesar FIFO
CREATE INDEX idx_queue_status ON sync_queue(status, created_at);
```

### 6.2 Política de Reintentos

| Intento | Espera | Acción |
|---------|--------|--------|
| 1 | Inmediato | Envío inicial |
| 2 | 1 minuto | Primer reintento |
| 3 | 2 minutos | Backoff |
| 4 | 4 minutos | Backoff |
| 5 | 8 minutos | Backoff |
| 6 | 16 minutos | Backoff |
| 7+ | 60 minutos | Máximo backoff |
| 100+ | - | Marcar como FAILED, alertar |

### 6.3 Límites de Cola

| Parámetro | Valor | Razón |
|-----------|-------|-------|
| Max registros | 10,000 | ~7 días de data a 15 min |
| Max tamaño | 100 MB | Evitar llenar disco |
| Max edad | 7 días | Data más vieja pierde relevancia |
| Compresión | gzip | Reduce ~70% tamaño |

### 6.4 Manejo de Errores

```python
class SyncErrorHandler:
    def handle_network_error(self, error):
        """Internet caído: encolar y reintentar"""
        self.queue.mark_for_retry(exponential_backoff=True)
        self.logger.warning(f"Network error, will retry: {error}")
    
    def handle_auth_error(self, error):
        """Token inválido: NO reintentar, alertar"""
        self.logger.error(f"Auth error, requires manual intervention: {error}")
        self.send_alert_to_hub("AUTH_ERROR")
    
    def handle_validation_error(self, error):
        """Payload inválido: mover a dead-letter, alertar"""
        self.queue.move_to_dead_letter()
        self.logger.error(f"Validation error: {error}")
    
    def handle_sql_local_error(self, error):
        """SQL local caído: NO encolar datos vacíos"""
        self.logger.error(f"SQL local error: {error}")
        self.send_heartbeat(status="SQL_LOCAL_ERROR")
```

---

## 7. SEGURIDAD

### 7.1 Autenticación del Agente

Cada agente tiene un **token único** generado por HUB:

```python
# En HUB: Generación de token para agente
def generate_agent_token(server_id: str, empresa_id: str) -> str:
    payload = {
        "server_id": server_id,
        "empresa_id": empresa_id,
        "type": "sync_agent",
        "exp": datetime.utcnow() + timedelta(days=365)  # 1 año
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
```

### 7.2 Flujo de Autenticación

```
1. Admin registra agente en HUB (menú Servidores)
2. HUB genera token único para ese servidor
3. Admin instala agente en sucursal con el token
4. Agente incluye token en header: Authorization: Bearer <token>
5. HUB valida token y extrae server_id, empresa_id
6. HUB verifica que payload.server_id == token.server_id
```

### 7.3 Comunicación Segura

| Aspecto | Implementación |
|---------|----------------|
| Protocolo | HTTPS (TLS 1.3) |
| Autenticación | JWT con expiración |
| Validación | server_id en token == payload |
| Rate limiting | 100 req/min por agente |
| IP whitelist | Opcional, configurable en HUB |

### 7.4 Almacenamiento de Credenciales (Local)

```yaml
# config.yaml (en sucursal)
agent:
  id: "agent-cienfuegos-001"
  hub_url: "https://edarsa-hub.com"
  token: "eyJhbGciOiJIUzI1NiIs..."  # Encriptado con DPAPI (Windows) o keyring (Linux)

sql_local:
  host: "localhost"
  port: 1433
  database: "CIENFUEGOS_MPRO"
  username: "sync_user"             # Usuario de solo lectura
  password_encrypted: "..."         # Encriptado localmente
```

---

## 8. MONITOREO Y OBSERVABILIDAD

### 8.1 Dashboard de Agentes en HUB

```
┌─────────────────────────────────────────────────────────────────────────┐
│  EDARSA HUB - Monitor de Sync Agents                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │ CIENFUEGOS  │ │ REFORMA     │ │ POLANCO     │ │ SATELITE    │       │
│  │ ✅ ONLINE   │ │ ✅ ONLINE   │ │ ⚠️ DELAYED  │ │ ❌ OFFLINE  │       │
│  │ v1.2.3      │ │ v1.2.3      │ │ v1.2.1      │ │ v1.2.0      │       │
│  │ Queue: 0    │ │ Queue: 0    │ │ Queue: 45   │ │ Queue: ?    │       │
│  │ Last: 2min  │ │ Last: 1min  │ │ Last: 45min │ │ Last: 2d    │       │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                                         │
│  Alertas Activas:                                                       │
│  ⚠️ POLANCO: Queue > 30 pendientes (hace 45 min)                        │
│  ❌ SATELITE: Sin heartbeat hace 2 días                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Métricas a Capturar

| Métrica | Fuente | Alerta si |
|---------|--------|-----------|
| Último heartbeat | HUB | > 30 min |
| Queue depth | Heartbeat | > 50 payloads |
| Sync latency | HUB | > 5 min promedio |
| Error rate | HUB | > 5% últimos 100 |
| Agent version | Heartbeat | < versión mínima |
| SQL local status | Heartbeat | != CONNECTED |

### 8.3 Logs del Agente (Local)

```
# /var/log/edarsa-sync-agent/sync.log (rotación diaria, 7 días)
2026-04-23 10:15:00 INFO  [SCHEDULER] Starting sync cycle
2026-04-23 10:15:01 INFO  [EXTRACTOR] Connecting to SQL local
2026-04-23 10:15:02 INFO  [EXTRACTOR] Query executed: 1200ms, 1 rows
2026-04-23 10:15:02 INFO  [QUEUE] Payload enqueued: batch-20260423-101500-001
2026-04-23 10:15:03 INFO  [SENDER] POST to HUB: 200 OK
2026-04-23 10:15:03 INFO  [QUEUE] Payload sent successfully
2026-04-23 10:15:03 INFO  [SCHEDULER] Sync cycle completed: 3.1s
```

### 8.4 Colección de Registry en HUB

```javascript
// Colección: sync_agent_registry
{
  "agent_id": "agent-cienfuegos-001",
  "server_id": "6d053c22-...",
  "empresa_id": "1d91f076-...",
  "version": "1.2.3",
  "status": "ONLINE",               // ONLINE | DELAYED | OFFLINE
  "registered_at": "2026-04-01T00:00:00Z",
  "last_heartbeat": "2026-04-23T10:15:00Z",
  "last_successful_sync": "2026-04-23T10:15:02Z",
  "queue_depth": 0,
  "sql_local_status": "CONNECTED",
  "config": {
    "frecuencia_minutos": 15,
    "version_minima": "1.0.0"
  },
  "stats_24h": {
    "syncs_total": 96,
    "syncs_ok": 95,
    "syncs_error": 1,
    "records_sent": 288,
    "avg_latency_ms": 1500
  }
}
```

---

## 9. VERSIONADO Y ACTUALIZACIÓN DEL AGENTE

### 9.1 Estrategia de Versionado

```
Versión: MAJOR.MINOR.PATCH
- MAJOR: Cambios de protocolo incompatibles
- MINOR: Nuevas funcionalidades (compatible)
- PATCH: Bug fixes

Ejemplo: 1.2.3
```

### 9.2 Verificación de Versión Mínima

```python
# En HUB: Sync Receiver
def validate_agent_version(agent_version: str, server_config: dict) -> bool:
    min_version = server_config.get('sync_agent', {}).get('version_agent_minima', '1.0.0')
    return parse_version(agent_version) >= parse_version(min_version)

# Si versión < mínima:
# - Rechazar sync con error 426 (Upgrade Required)
# - Incluir URL de descarga de nueva versión
```

### 9.3 Proceso de Actualización

```
1. Admin sube nueva versión a repositorio interno
2. HUB actualiza `version_agent_minima` para servidores objetivo
3. Agente recibe error 426 en siguiente sync
4. Agente descarga nueva versión (URL en respuesta)
5. Agente se auto-actualiza y reinicia
6. Nuevo sync con versión actualizada
```

### 9.4 Distribución del Agente

| Plataforma | Formato | Ubicación |
|------------|---------|-----------|
| Windows | exe (PyInstaller) | `https://edarsa-hub.com/downloads/agent/windows/` |
| Linux | deb/rpm/tar.gz | `https://edarsa-hub.com/downloads/agent/linux/` |
| Config | YAML template | Generado desde HUB al registrar |

---

## 10. INSTALACIÓN MÍNIMA EN SUCURSAL

### 10.1 Requisitos del Sistema

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 1 core | 2 cores |
| RAM | 256 MB | 512 MB |
| Disco | 500 MB | 1 GB |
| Red | Internet saliente | - |
| OS | Windows 10+ / Ubuntu 20+ | - |
| SQL | Acceso localhost:1433 | Usuario de solo lectura |

### 10.2 Instalación Windows (Ejemplo)

```powershell
# 1. Descargar agente
Invoke-WebRequest -Uri "https://edarsa-hub.com/downloads/agent/edarsa-sync-agent-1.2.3.exe" -OutFile "edarsa-sync-agent.exe"

# 2. Crear carpeta de configuración
New-Item -ItemType Directory -Path "C:\ProgramData\EDARSA\SyncAgent"

# 3. Descargar configuración generada desde HUB
# (Admin genera en HUB: Servidores > [Servidor] > Generar Config Agente)
# Copiar config.yaml a C:\ProgramData\EDARSA\SyncAgent\config.yaml

# 4. Instalar como servicio
.\edarsa-sync-agent.exe --install

# 5. Iniciar servicio
Start-Service EDARSASyncAgent
```

### 10.3 Archivos en Sucursal

```
C:\ProgramData\EDARSA\SyncAgent\
├── config.yaml          # Configuración (token, SQL local, frecuencia)
├── queue.db             # SQLite de cola local
├── logs\
│   ├── sync.log         # Log actual
│   └── sync.log.1       # Rotación
└── cache\
    └── last_config.json # Última config descargada de HUB
```

---

## 11. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Token comprometido | Baja | Alto | Rotación de tokens, alertas de uso anómalo, IP whitelist |
| Queue se llena (offline largo) | Media | Medio | Límites de cola, alertas por umbral, purga automática > 7 días |
| Versión desactualizada | Media | Bajo | Auto-update, rechazo de sync con versión vieja |
| SQL local modificado | Baja | Alto | Queries de solo lectura, usuario con permisos mínimos |
| Agente no inicia | Baja | Medio | Healthcheck local, reinicio automático (Windows Service) |
| Datos duplicados | Muy Baja | Bajo | UPSERT idempotente en HUB ya implementado |
| Diferencia de hora | Media | Medio | Usar UTC en todo, incluir timestamp del agente |

---

## 12. PLAN DE IMPLEMENTACIÓN POR FASES

### Fase 1: Infraestructura HUB (2-3 días)

| Tarea | Archivo | Estado |
|-------|---------|--------|
| Endpoint `/api/sync/kpis` | `/app/backend/api/sync_receiver.py` | Pendiente |
| Endpoint `/api/sync/heartbeat` | `/app/backend/api/sync_receiver.py` | Pendiente |
| Colección `sync_agent_registry` | MongoDB | Pendiente |
| Validación de token JWT para agentes | `/app/backend/core/security.py` | Pendiente |
| Dashboard de monitoreo (Admin) | Frontend | Pendiente |

### Fase 2: Agente Básico (3-4 días)

| Tarea | Componente | Estado |
|-------|------------|--------|
| Estructura base del agente | Python script | Pendiente |
| Config Manager | `config.py` | Pendiente |
| Extractor SoftRestaurant | `extractors/softrestaurant.py` | Pendiente |
| Extractor MPRO | `extractors/mpro.py` | Pendiente |
| Queue local (SQLite) | `queue.py` | Pendiente |
| Sender HTTP | `sender.py` | Pendiente |
| Scheduler | `scheduler.py` | Pendiente |

### Fase 3: Producción Piloto (1-2 días)

| Tarea | Sucursal | Estado |
|-------|----------|--------|
| Instalar agente piloto | 1 sucursal SR | Pendiente |
| Validar sync cada 15 min | - | Pendiente |
| Validar offline/retry | - | Pendiente |
| Validar heartbeat | - | Pendiente |

### Fase 4: Rollout (1 semana)

| Tarea | Descripción | Estado |
|-------|-------------|--------|
| Documentación de instalación | Wiki interna | Pendiente |
| Instalación en todas las sucursales | - | Pendiente |
| Monitoreo activo | Dashboard HUB | Pendiente |
| Desactivar schedulers SYNC-S/SYNC-N | Solo si todos los agentes OK | Pendiente |

---

## 13. DEPENDENCIAS Y PRERREQUISITOS

### 13.1 Prerrequisitos Técnicos

- [x] Colección `kpis_comercial` con UPSERT idempotente (MACROFASE 2)
- [x] Función `upsert_kpi_comercial()` implementada
- [ ] JWT con scope específico para agentes
- [ ] Endpoint de descarga de configuración para agentes

### 13.2 Prerrequisitos Operativos

- [ ] Usuario SQL de solo lectura en cada sucursal
- [ ] Apertura de puerto saliente HTTPS (443) en firewalls de sucursales
- [ ] Máquina/servidor designado en cada sucursal para instalar agente

---

## APROBACIÓN

| Aspecto | Estado |
|---------|--------|
| EDARSA HUB como cerebro | ✅ |
| Cero dependencia de conectividad inversa | ✅ |
| Fuentes configuradas en HUB | ✅ |
| Soporte SR y MPRO sin duplicar arquitectura | ✅ |
| Cola local con reintentos | ✅ |
| Idempotencia y deduplicación | ✅ |
| Seguridad y autenticación | ✅ |
| Observabilidad | ✅ |
| Versionado y actualización | ✅ |
| Instalación mínima | ✅ |
| Riesgos documentados | ✅ |
| Plan de implementación | ✅ |

---

**DISEÑO TÉCNICO COMPLETADO**

Este documento define la arquitectura del EDARSA Sync Agent sin iniciar implementación.
Requiere aprobación del usuario antes de proceder a cualquier desarrollo.
