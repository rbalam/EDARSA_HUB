# FINANZAS-CXP-MPRO-CREDENTIALS-SECURITY-01 - REPORTE

**Fecha**: 2025-12-28  
**Estado**: ✅ COMPLETADO  
**Autor**: E1 Agent

---

## 1. RESUMEN EJECUTIVO

Se corrigió el manejo de credenciales MPRO en CxP para cumplir con los estándares de seguridad:

1. ✅ Credenciales ahora vienen de EDARSAHUB SQL via `server_registry.py`
2. ✅ Subprocess recibe credenciales via stdin (no argv)
3. ✅ Password no aparece en logs ni en argumentos CLI
4. ✅ CxP sigue funcionando (ORIGEN, 130 QRO, Todas)

---

## 2. TABLA DE VERIFICACIÓN DE SEGURIDAD

| Punto | Resultado esperado | Resultado real | Estado |
|-------|-------------------|----------------|--------|
| Fuente credenciales | EDARSAHUB/server_registry.py | config_origin: EDARSAHUB_SQL | ✅ CUMPLE |
| MongoDB usado para password | NO | NO (usa get_server_by_id con prefer_sql=True) | ✅ CUMPLE |
| config_origin | EDARSAHUB_SQL | EDARSAHUB_SQL | ✅ CUMPLE |
| Password en argv | NO | NO (sql_query_worker_secure.py sin argumentos) | ✅ CUMPLE |
| Password en logs | NO | NO (verificado en backend.*.log) | ✅ CUMPLE |
| Connection string en logs | NO | NO (verificado) | ✅ CUMPLE |
| CxP ORIGEN | 1,073 facturas, $11,501,659.82 | 1,073 facturas, $11,501,659.82 | ✅ CUMPLE |
| CxP 130 QRO | 524 facturas, $8,984,825.24 | 524 facturas, $8,984,825.24 | ✅ CUMPLE |
| CxP Todas | SR+MPRO combinado | 2,851 facturas, $48,897,056.58 | ✅ CUMPLE |

---

## 3. EVIDENCIA DE SEGURIDAD

### 3.1 Fuente de credenciales

```python
# repository_mpro.py - _get_credentials()
from core.server_registry import get_server_by_id, get_decrypted_credentials

server = await get_server_by_id(
    server_id=MPRO_SERVER_ID,
    db=self.db,
    prefer_sql=True,           # Priorizar EDARSAHUB SQL
    allow_mongo_fallback=True, # Fallback solo si SQL falla
    mask_secrets=False         # Obtener password real
)
```

Resultado de test directo:
```
Server encontrado: ManagmentPro
config_origin: EDARSAHUB_SQL  ✅
Host: 54.39.104.176
Database: CENTRAL2020
```

### 3.2 Subprocess sin credenciales en argv

Proceso durante query MPRO:
```
/root/.venv/bin/python /app/backend/modules/finanzas/sql_query_worker_secure.py
```

**NO hay host, usuario, ni password en los argumentos.**

Las credenciales se pasan via stdin como JSON:
```python
# sql_subprocess_helper.py - execute_sql_subprocess_secure()
stdin_payload = json.dumps({
    'host': host,
    'port': port,
    'database': database,
    'username': username,
    'password': password,  # Solo en JSON stdin, no en argv
    'query_b64': query_b64
})

process = await asyncio.create_subprocess_exec(
    *cmd,
    stdin=asyncio.subprocess.PIPE,  # Recibe credenciales por stdin
    ...
)
await process.communicate(input=stdin_payload.encode('utf-8'))
```

### 3.3 Sin leaks en logs

Comando de verificación:
```bash
grep -i "National09\|password=\|password\":" /var/log/supervisor/backend.*.log
```
Resultado: **NO se encontraron passwords en logs**

### 3.4 Manejo de errores seguro

Los errores en el worker eliminan cualquier password accidental:
```python
# sql_query_worker_secure.py - execute_query()
if password and password in error_msg:
    error_msg = error_msg.replace(password, '***')
```

---

## 4. ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/finanzas/repository_mpro.py` | Usa server_registry.py para credenciales |
| `/app/backend/modules/finanzas/sql_subprocess_helper.py` | Nueva función `execute_sql_subprocess_secure()` |
| `/app/backend/modules/finanzas/sql_query_worker_secure.py` | **NUEVO**: Worker que lee stdin |

---

## 5. FLUJO DE CREDENCIALES

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FLUJO SEGURO DE CREDENCIALES                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. FUENTE: EDARSAHUB SQL                                            │
│     ┌─────────────────────┐                                          │
│     │ Servidores_Conexiones│                                          │
│     │ (tabla SQL)          │                                          │
│     └──────────┬──────────┘                                          │
│                │                                                      │
│                ▼                                                      │
│  2. REGISTRY: server_registry.py                                     │
│     ┌─────────────────────┐                                          │
│     │ get_server_by_id()  │  config_origin = EDARSAHUB_SQL           │
│     │ prefer_sql=True     │                                          │
│     └──────────┬──────────┘                                          │
│                │                                                      │
│                ▼                                                      │
│  3. DESCIFRADO: get_decrypted_credentials()                          │
│     ┌─────────────────────┐                                          │
│     │ secret_manager.py   │  Usa SERVER_SECRET_KEY (env var)         │
│     │ decrypt_secret()    │                                          │
│     └──────────┬──────────┘                                          │
│                │                                                      │
│                ▼                                                      │
│  4. TRANSMISIÓN: STDIN (no argv)                                     │
│     ┌─────────────────────┐                                          │
│     │ subprocess_secure   │  Credenciales en JSON por stdin          │
│     │ (no visible en ps)  │  NO aparecen en /proc/[pid]/cmdline      │
│     └──────────┬──────────┘                                          │
│                │                                                      │
│                ▼                                                      │
│  5. WORKER: sql_query_worker_secure.py                               │
│     ┌─────────────────────┐                                          │
│     │ Lee stdin JSON      │  Password solo en memoria                │
│     │ Ejecuta query       │  Errores sanitizados (sin password)      │
│     │ Retorna JSON        │                                          │
│     └─────────────────────┘                                          │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. NOTA SOBRE SOFTRESTAURANT

⚠️ El módulo SoftRestaurant (`repository_softrestaurant.py`) aún usa `execute_sql_subprocess` (legacy) que **SÍ expone credenciales en argv**. 

Esta corrección solo aplica a **MPRO CxP** según el alcance autorizado. 

La migración de SoftRestaurant a subprocess seguro queda como tarea futura si se requiere.

---

## 7. ROLLBACK

En caso de regresión, revertir:
```bash
git checkout HEAD~1 -- \
  backend/modules/finanzas/repository_mpro.py \
  backend/modules/finanzas/sql_subprocess_helper.py
rm backend/modules/finanzas/sql_query_worker_secure.py
sudo supervisorctl restart backend
```

---

*Generado automáticamente - 2025-12-28*
