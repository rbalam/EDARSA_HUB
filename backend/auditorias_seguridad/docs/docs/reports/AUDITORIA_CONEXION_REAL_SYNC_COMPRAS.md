# AUDITORÍA CONEXIÓN REAL SYNC COMPRAS
Fecha: Thu Jun  4 07:43:17 UTC 2026

---

## 1. Análisis de sync_compras_job.py

### 1.1 Configuración EDARSAHUB en el job
```python
57:EDARSAHUB_CONFIG = {
58-    'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
59-    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
60-    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
61-    'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
62-    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
63-}
64-
65-
66-# =============================================================================
67-# LOCK ANTI-CONCURRENCIA SQL
--
79:            server=EDARSAHUB_CONFIG['host'],
80:            port=EDARSAHUB_CONFIG['port'],
81:            database=EDARSAHUB_CONFIG['database'],
82:            user=EDARSAHUB_CONFIG['username'],
83:            password=EDARSAHUB_CONFIG['password'],
84-            login_timeout=15,
85-            autocommit=False
86-        )
```

### 1.2 Función _get_servers_to_sync
```python
197:def _get_servers_to_sync() -> List[Dict]:
198-    """
199-    Obtiene la lista de servidores activos configurados para sincronización.
200-    Lee desde Servidores_Conexiones y Unidades_Negocio en EDARSAHUB.
201-    """
202-    from core.secret_manager import decrypt_secret
203-    
204-    try:
205-        conn = get_edarsahub_connection()
206-        cursor = conn.cursor(as_dict=True)
207-        
208-        # Obtener servidores SQL activos con su unidad asociada
209-        cursor.execute("""
210-            SELECT 
211-                s.id, s.nombre as server_name, s.host, s.port, s.database_name,
212-                s.username, s.password_encrypted, s.system_type, s.activo,
213-                u.id as unidad_id, u.codigo as unidad_codigo, u.nombre as unidad_nombre
214-            FROM Servidores_Conexiones s
215-            LEFT JOIN Unidades_Negocio u ON u.server_id = CAST(s.id AS NVARCHAR(36))
216-            WHERE s.activo = 1
217-              AND s.tipo_conexion IN ('SQL_SERVER', 'DATA_SOURCE')
218-              AND s.system_type IN ('SOFTRESTAURANT', 'MPRO', 'MANAGEMENTPRO', 'SOFTRESTAURANT_PRO')
219-              AND s.host IS NOT NULL AND s.host != ''
220-        """)
221-        rows = cursor.fetchall()
222-        conn.close()
223-        
224-        servers = []
225-        for row in rows:
226-            # Desencriptar contraseña si está encriptada
227-            password = ''
228-            if row.get('password_encrypted'):
229-                try:
230-                    password = decrypt_secret(row['password_encrypted'])
231-                except Exception as e:
232-                    logger.warning(f"[SYNC-COMPRAS] No se pudo desencriptar password de {row['server_name']}: {e}")
233-                    continue
234-            
235-            servers.append({
236-                'id': str(row.get('id', '')),
237-                'name': row.get('server_name', ''),
238-                'host': row.get('host', ''),
239-                'port': int(row.get('port', 1433)),
240-                'database': row.get('database_name', ''),
241-                'username': row.get('username', ''),
242-                'password': password,
243-                'system_type': row.get('system_type', ''),
244-                'unidad_id': str(row.get('unidad_id', '')),
245-                'unidad_codigo': row.get('unidad_codigo', ''),
246-                'unidad_nombre': row.get('unidad_nombre', ''),
247-            })
248-        
249-        logger.info(f"[SYNC-COMPRAS] Servidores encontrados: {len(servers)}")
250-        return servers
251-        
252-    except Exception as e:
253-        logger.error(f"[SYNC-COMPRAS] Error obteniendo servidores: {e}")
254-        return []
255-
256-
257-# =============================================================================
258-# FUNCIÓN PRINCIPAL DE EJECUCIÓN
259-# =============================================================================
260-
261-def execute_sync_compras(dry_run: bool = False) -> Dict[str, Any]:
262-    """
263-    Ejecuta la sincronización completa de Compras.
264-    
265-    Args:
266-        dry_run: Si True, no guarda cambios en la base de datos
267-    
268-    Returns:
269-        Dict con resultados de la sincronización
270-    """
271-    run_id = f"COMPRAS-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
272-    logger.info(f"[SYNC-COMPRAS] ========== INICIO SINCRONIZACIÓN {run_id} ==========")
273-    
274-    # Adquirir lock
275-    if not _acquire_sync_lock(run_id):
276-        return {
277-            "status": "SKIPPED",
```

### 1.3 Llamadas a pymssql.connect
```text
78:        conn = pymssql.connect(
138:        conn = pymssql.connect(
```

### 1.4 Imports de sync_service
```text
36:from modules.compras.sync_service import (
```

---

## 2. Análisis de sync_service.py

### 2.1 Función get_edarsahub_connection
```python
30:def get_edarsahub_connection():
31-    """Obtiene conexión a EDARSAHUB"""
32-    return pymssql.connect(
33-        server=EDARSAHUB_CONFIG['host'],
34-        user=EDARSAHUB_CONFIG['username'],
35-        password=EDARSAHUB_CONFIG['password'],
36-        database=EDARSAHUB_CONFIG['database'],
37-        port=EDARSAHUB_CONFIG['port'],
38-        timeout=30
39-    )
40-
41-
42-# =============================================================================
43-# LECTURA DE DATOS SINCRONIZADOS (Endpoints usan estas funciones)
44-# =============================================================================
45-
46-def obtener_inventarios_fisicos_sync(
47-    unidad_negocio_id: str = None,
48-    server_id: str = None,
49-    sucursal: str = None,
50-    almacen: str = None,
51-    limit: int = 500
52-) -> List[Dict]:
53-    """
54-    Obtiene inventarios físicos DESDE EDARSAHUB (sincronizados).
55-    NO se conecta a servidores en vivo.
56-    """
57-    try:
58-        conn = get_edarsahub_connection()
59-        cursor = conn.cursor(as_dict=True)
60-        
```

### 2.2 Configuración EDARSAHUB en service
```python
21:EDARSAHUB_CONFIG = {
22-    'host': '54.39.104.176',
23-    'port': 1433,
24-    'database': 'EDARSAHUB',
25-    'username': 'HRLectura',
26-    'password': 'National09$'
27-}
28-
29-
30-def get_edarsahub_connection():
31-    """Obtiene conexión a EDARSAHUB"""
--
33:        server=EDARSAHUB_CONFIG['host'],
34:        user=EDARSAHUB_CONFIG['username'],
35:        password=EDARSAHUB_CONFIG['password'],
36:        database=EDARSAHUB_CONFIG['database'],
37:        port=EDARSAHUB_CONFIG['port'],
38-        timeout=30
39-    )
40-
41-
42-# =============================================================================
43-# LECTURA DE DATOS SINCRONIZADOS (Endpoints usan estas funciones)
44-# =============================================================================
45-
46-def obtener_inventarios_fisicos_sync(
47-    unidad_negocio_id: str = None,
```

### 2.3 Uso de execute_sql_fn (conexión origen)
```text
173:    execute_sql_query_func
182:        execute_sql_query_func: Función para ejecutar queries en el servidor origen
240:        rows = execute_sql_query_func(
303:    execute_sql_query_func
373:        rows = execute_sql_query_func(
490:    execute_sql_fn: Callable
524:        result_origen = execute_sql_fn(
567:    execute_sql_fn: Callable
607:        result_origen = execute_sql_fn(
654:    execute_sql_fn: Callable,
734:        encabezados = execute_sql_fn(
742:        detalles = execute_sql_fn(
822:    execute_sql_fn: Callable,
881:        encabezados = execute_sql_fn(
888:        detalles = execute_sql_fn(
964:    execute_sql_fn: Callable,
1023:        encabezados = execute_sql_fn(
1030:        detalles = execute_sql_fn(
1106:    execute_sql_fn: Callable,
1165:        encabezados = execute_sql_fn(
```

---

## 3. Variables de entorno relacionadas
```text
/app/backend/modules/comercial/repository.py:33:    'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
/app/backend/modules/comercial/repository.py:34:    'port': int(os.environ.get('EDARSAHUB_PORT', 1433)),
/app/backend/modules/comercial/repository.py:35:    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/modules/comercial/repository.py:36:    'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
/app/backend/modules/comercial/repository.py:37:    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
/app/backend/modules/comercial/routes.py:1938:        edarsahub_host = os.environ.get('EDARSAHUB_HOST', '54.39.104.176')
/app/backend/modules/comercial/routes.py:1939:        edarsahub_port = int(os.environ.get('EDARSAHUB_PORT', '1433'))
/app/backend/modules/comercial/routes.py:1940:        edarsahub_database = os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB')
/app/backend/modules/comercial/routes.py:1941:        edarsahub_username = os.environ.get('EDARSAHUB_USERNAME', 'HRLectura')
/app/backend/modules/comercial/routes.py:1942:        edarsahub_password = os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
/app/backend/modules/api_connections/universal_test_routes.py:143:            server=os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
/app/backend/modules/api_connections/universal_test_routes.py:144:            port=int(os.environ.get('EDARSAHUB_PORT', '1433')),
/app/backend/modules/api_connections/universal_test_routes.py:145:            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/modules/api_connections/universal_test_routes.py:146:            user=os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
/app/backend/modules/api_connections/universal_test_routes.py:147:            password=os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
/app/backend/modules/api_connections/universal_test_routes.py:182:            server=os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
/app/backend/modules/api_connections/universal_test_routes.py:183:            port=int(os.environ.get('EDARSAHUB_PORT', '1433')),
/app/backend/modules/api_connections/universal_test_routes.py:184:            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/modules/api_connections/universal_test_routes.py:185:            user=os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
/app/backend/modules/api_connections/universal_test_routes.py:186:            password=os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
/app/backend/modules/sistema/menu_service.py:21:            'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
/app/backend/modules/sistema/menu_service.py:22:            'user': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
/app/backend/modules/sistema/menu_service.py:23:            'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
/app/backend/modules/sistema/menu_service.py:24:            'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/modules/sistema/menu_service.py:25:            'port': int(os.environ.get('EDARSAHUB_PORT', 1433))
/app/backend/modules/rh/repository.py:43:    'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
/app/backend/modules/rh/repository.py:44:    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
/app/backend/modules/rh/repository.py:45:    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/modules/rh/repository.py:46:    'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
/app/backend/modules/rh/repository.py:47:    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
```

---

## 4. Tabla Servidores_Conexiones
```text
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:173:                FROM Servidores_Conexiones
/app/backend/core/scheduler/jobs/sync_compras_job.py:200:    Lee desde Servidores_Conexiones y Unidades_Negocio en EDARSAHUB.
/app/backend/core/scheduler/jobs/sync_compras_job.py:214:            FROM Servidores_Conexiones s
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:174:            FROM Servidores_Conexiones s
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:231:            FROM Servidores_Conexiones
```

---

## 5. RESUMEN EJECUTIVO - Respuestas a las 7 Preguntas

### Pregunta 1: ¿Usa la tabla Servidores_Conexiones?

**SÍ** - La función `_get_servers_to_sync()` (línea 197) consulta:
```sql
SELECT ... FROM Servidores_Conexiones s
LEFT JOIN Unidades_Negocio u ON u.server_id = CAST(s.id AS NVARCHAR(36))
WHERE s.activo = 1
  AND s.tipo_conexion IN ('SQL_SERVER', 'DATA_SOURCE')
  AND s.system_type IN ('SOFTRESTAURANT', 'MPRO', 'MANAGEMENTPRO', 'SOFTRESTAURANT_PRO')
```

**Propósito:** Obtener la lista de servidores ORIGEN (SoftRestaurant/MPRO) de donde se extraen los datos.

---

### Pregunta 2: ¿Usa variables .env?

**SÍ, PARCIALMENTE** - Existen dos configuraciones distintas:

| Archivo | Usa ENV? | Fallback Hardcoded |
|---------|----------|-------------------|
| `sync_compras_job.py` (línea 57) | ✅ SÍ | `54.39.104.176` |
| `sync_service.py` (línea 21) | ❌ NO | `54.39.104.176` (hardcoded) |

**⚠️ INCONSISTENCIA DETECTADA:** `sync_service.py` tiene los valores hardcodeados sin usar `os.environ.get()`.

---

### Pregunta 3: ¿Usa get_edarsahub_connection()?

**SÍ** - La función `_get_servers_to_sync()` (línea 205) llama:
```python
conn = get_edarsahub_connection()
```

Esta función está definida en `sync_service.py` línea 30.

---

### Pregunta 4: Host final utilizado

| Componente | Host |
|------------|------|
| `sync_compras_job.py` EDARSAHUB_CONFIG | `os.environ.get('EDARSAHUB_HOST', '54.39.104.176')` |
| `sync_service.py` get_edarsahub_connection() | `54.39.104.176` (hardcoded) |
| `server.py` endpoint validate-columns | `os.environ.get('EDARSAHUB_HOST', '4.255.36.175')` |

**⚠️ INCONSISTENCIA CRÍTICA:**
- `sync_compras_job.py` → `54.39.104.176`
- `server.py` endpoints admin → `4.255.36.175`

---

### Pregunta 5: Base de datos final utilizada

**`EDARSAHUB`** en todos los casos.

---

### Pregunta 6: Usuario final utilizado

**`HRLectura`** en todos los casos (excepto `server.py` que usa `eloyk`).

| Archivo | Usuario | Password |
|---------|---------|----------|
| `sync_compras_job.py` | `HRLectura` | `National09$` |
| `sync_service.py` | `HRLectura` | `National09$` |
| `server.py` admin endpoints | `eloyk` | `Tijuana2020$` |

---

### Pregunta 7: ¿La conexión EDARSAHUB proviene del registro "EDARSA HUB" en Servidores o de otra configuración?

**NO proviene de Servidores_Conexiones.**

La conexión a EDARSAHUB está hardcodeada/configurada vía ENV en cada archivo Python. 
La tabla `Servidores_Conexiones` solo se usa para obtener los servidores **ORIGEN** (SoftRestaurant, MPRO), no el servidor destino EDARSAHUB.

---

## 6. DIAGRAMA DE CONEXIONES

```
execute_sync_compras()
        │
        ├─► [1] get_edarsahub_connection() → EDARSAHUB (54.39.104.176)
        │       └── Para obtener lista de servidores desde Servidores_Conexiones
        │
        ├─► [2] _get_servers_to_sync() → Lista de {host, port, database, user, password}
        │       └── Lee de Servidores_Conexiones (SoftRestaurant/MPRO)
        │
        └─► [3] Para cada servidor ORIGEN:
                │
                ├─► execute_sql_fn() → Servidor Origen (SoftRestaurant/MPRO)
                │       └── Lee datos a sincronizar
                │
                └─► get_edarsahub_connection() → EDARSAHUB (54.39.104.176)
                        └── Escribe datos con MERGE
```

---

## 7. HALLAZGOS Y RECOMENDACIONES

### 🔴 Inconsistencias Críticas

| # | Problema | Archivos Afectados |
|---|----------|-------------------|
| 1 | Host inconsistente: `54.39.104.176` vs `4.255.36.175` | sync_*.py vs server.py |
| 2 | Usuario inconsistente: `HRLectura` vs `eloyk` | sync_*.py vs server.py |
| 3 | sync_service.py no usa ENV, tiene credenciales hardcodeadas | sync_service.py |

### ✅ Recomendación

1. **Unificar configuración EDARSAHUB** en un solo archivo de configuración.
2. **Usar variables de entorno** en todos los archivos.
3. **Verificar cuál host es el correcto** para producción:
   - `54.39.104.176` (sync jobs)
   - `4.255.36.175` (endpoints admin)

---

## 8. CONCLUSIÓN

| Pregunta | Respuesta |
|----------|-----------|
| 1. ¿Usa Servidores_Conexiones? | ✅ SÍ - Para obtener servidores ORIGEN |
| 2. ¿Usa variables .env? | ⚠️ PARCIAL - sync_compras_job.py sí, sync_service.py no |
| 3. ¿Usa get_edarsahub_connection()? | ✅ SÍ |
| 4. Host final | `54.39.104.176` (hardcoded en sync_service.py) |
| 5. Base de datos final | `EDARSAHUB` |
| 6. Usuario final | `HRLectura` (sync) / `eloyk` (admin endpoints) |
| 7. ¿Conexión de registro "EDARSA HUB"? | ❌ NO - Configuración hardcodeada/ENV |

---

*Reporte generado automáticamente - E1 Agent*
