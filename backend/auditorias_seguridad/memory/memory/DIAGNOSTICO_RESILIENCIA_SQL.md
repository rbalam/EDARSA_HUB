# Diagnóstico: Integración Resiliencia SQL Server

## Fecha: Abril 2026

## 1. Problema Original

**Error recurrente**: `DBPROCESS is dead or not enabled` / `Adaptive Server connection timed out`

**Causa raíz identificada**:
1. Timeouts insuficientes (15s login / 45s query) para servidor SQL remoto
2. Pool de conexiones sin autocommit, causando que UPDATEs no se persistan
3. Manejo incorrecto de queries sin resultados (UPDATE/INSERT)
4. Falta de reintentos automáticos con backoff

## 2. Solución Implementada

### Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `/app/backend/core/pool.py` | Timeouts resilientes (30s login, 90s query), autocommit=True |
| `/app/backend/core/db.py` | Reintentos con backoff exponencial, clasificación de errores, health check |
| `/app/backend/server.py` | Endpoints `/api/sistema/sql-health` y `/api/sistema/sql-health/test-query` |

### Configuración Resiliente Final

```python
class ResilientConfig:
    LOGIN_TIMEOUT = 30          # Antes: 15s
    QUERY_TIMEOUT = 90          # Antes: 45s
    CONNECT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2
    RETRY_DELAY_MAX = 15
    RETRY_BACKOFF = 2           # Exponencial
```

### Mejoras Implementadas

1. **Timeouts incrementados**: Adaptados para latencia de servidor remoto (~160ms)
2. **Autocommit habilitado**: UPDATEs se commitean inmediatamente
3. **Reintentos con backoff**: 3 intentos con delay exponencial (2s, 4s, 8s)
4. **Clasificación de errores**:
   - `NETWORK`: Errores de red (reintentar)
   - `TIMEOUT`: Timeouts (reintentar)
   - `DEAD_CONNECTION`: Pool corrupto (limpiar y reintentar)
   - `AUTH`: Autenticación (no reintentar)
   - `QUERY`: Error de sintaxis SQL (no reintentar)
5. **Manejo de queries sin resultados**: UPDATE/INSERT correctamente manejados
6. **Limpieza automática de pool corrupto**: Detecta y limpia conexiones muertas

## 3. Resultados de Pruebas

### A. Health Check

| Métrica | Resultado |
|---------|-----------|
| Healthy | ✅ True |
| Server | <REDACTED_EDARSAHUB_SQL_HOST>:1433 |
| Database | EDARSAHUB |
| Latency | ~160ms |
| Driver | pytds |
| Config | Login=30s, Query=90s, Retries=3 |

### B. Query de Lectura

| Métrica | Resultado |
|---------|-----------|
| Success | ✅ True |
| Tabla | sys.tables |
| Registros | 5 |
| Latency | ~250ms |

### C. CRUD Funcional (Finanzas_ConfiguracionTPV_Sucursal)

| Operación | Resultado |
|-----------|-----------|
| Lectura lista | ✅ 8 registros |
| Lectura individual | ✅ Datos completos |
| Edición | ✅ Persistido correctamente |
| Verificación | ✅ Cambio confirmado |

### Prueba de Edición

```
ANTES:  ComisionAmex = 2.4
EDICIÓN: ComisionAmex -> 2.55
DESPUÉS: ComisionAmex = 2.55 ✅ PERSISTIDO
RESTAURACIÓN: ComisionAmex -> 2.4 ✅ CONFIRMADO
```

## 4. Endpoints de Diagnóstico

### GET /api/sistema/sql-health
Realiza health check de conexión SQL con diagnóstico detallado.

**Respuesta**:
```json
{
    "healthy": true,
    "server": "<REDACTED_EDARSAHUB_SQL_HOST>:1433",
    "database": "EDARSAHUB",
    "latency_ms": 160.0,
    "error": null,
    "error_type": null,
    "driver_used": "pytds",
    "config": {
        "login_timeout": 30,
        "query_timeout": 90,
        "max_retries": 3
    },
    "recommendations": ["Conexión saludable - sin problemas detectados"]
}
```

### POST /api/sistema/sql-health/test-query
Ejecuta query de prueba para validar conectividad real.

**Parámetros**:
- `tabla`: Tabla a consultar (default: sys.tables)
- `server_id`: ID del servidor (default: EDARSA HUB)

## 5. Diagnóstico Final

### Estabilidad de Conexión
✅ **SUFICIENTEMENTE ESTABLE** para operaciones productivas

- Health check consistente (~160ms latencia)
- CRUD funcional validado
- Reintentos automáticos efectivos
- Pool con autocommit operativo

### Recomendaciones

1. **Monitoreo**: Usar `/api/sistema/sql-health` periódicamente
2. **Reset manual**: Si persisten problemas, usar `/api/sistema/pool-reset`
3. **Logs**: Revisar `/var/log/supervisor/backend.err.log` para diagnóstico

### Siguiente Fase Autorizada

✅ **Proceder con**:
1. Validación final de Catálogos/TPV desde UI
2. Conexión del módulo Finanzas UI a SQL Server real

## 6. Advertencias Conocidas

- El servidor SQL remoto puede tener latencia variable (100-300ms)
- En caso de timeouts repetidos, el sistema entra en cooldown (5-30 min)
- Ejecutar pool-reset limpia el cooldown inmediatamente
