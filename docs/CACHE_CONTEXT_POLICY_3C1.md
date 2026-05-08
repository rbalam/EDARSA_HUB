# FASE 3C.1 — Política Global de Cache Contextual e Invalidación Segura

**Fecha:** 2026-04-25  
**Autor:** E1 Agent  
**Estado:** COMPLETADA  

---

## 1. RESUMEN EJECUTIVO

La FASE 3C.1 define e implementa una política global de cache seguro para EDARSA HUB, evitando datos pegados, contaminados o incorrectos entre diferentes contextos (servidores, sucursales, usuarios, sistemas origen, fechas).

### Problema Detectado

Durante la FASE 3C, se identificó que `secret_manager._get_fernet()` podía quedarse con una clave de cifrado anterior en cache, incluso después de cambiar la variable de entorno. Este patrón podía afectar otros caches del sistema.

### Solución Implementada

1. **Cache key contextual**: Helper central `cache_key_builder.py`
2. **Detección automática de cambios**: `secret_manager` con fingerprint de clave
3. **Documentación de política**: Este documento

---

## 2. REGLA CENTRAL

> **Un cache solo es válido mientras no cambie el contexto completo que lo generó.**

Si cambia cualquier parte del contexto (servidor, sucursal, usuario, fecha, permisos, sistema origen, configuración), debe generarse una cache_key distinta o invalidarse el cache.

---

## 3. INVENTARIO DE CACHES

| Archivo | Tipo | Qué guarda | Contexto actual | Contexto faltante | Riesgo | Acción |
|---------|------|------------|-----------------|-------------------|--------|--------|
| `secret_manager.py` | Global variable | Fernet instance | fingerprint de clave | - | BAJO (corregido) | ✅ Detección automática |
| `comercial/cache_service.py` | MongoDB collection | Datos de dashboard, metas, etc. | endpoint, server_id, sucursal, fecha, system_type | user_id (si aplica) | BAJO | ✅ Ya incluye system_type |
| `finanzas/repository_real.py` | Instance variable | Config servidor EDARSA_HUB | server_id fijo | - | BAJO | ✅ Sin cambios necesarios |
| `finanzas/propinas_tpv/cache_manager.py` | MongoDB collection | Datos de propinas | fecha, server_id, sucursal_id, params | - | BAJO | ✅ Ya contextualizado |
| Frontend localStorage | Browser storage | Token, user, filters | - | - | BAJO | ⚠️ Token-only, user refrescado |

### Clasificación

- **A) Seguro**: `comercial/cache_service.py`, `finanzas/propinas_tpv/cache_manager.py`
- **B) Corregido**: `secret_manager.py` (ahora con fingerprint)
- **C) No aplica**: `finanzas/repository_real.py` (servidor fijo)
- **F) Frontend**: Tokens y filtros con contexto de servidor/sucursal

---

## 4. HELPER CENTRAL DE CACHE KEY

**Archivo:** `/app/backend/core/cache_key_builder.py`

### Funciones Principales

```python
# Hash estable de cualquier valor
stable_hash(value: Any, length: int = 8) -> str

# Cache key completa con contexto
build_context_cache_key(
    namespace: str,
    endpoint: str = None,
    server_id: str = None,
    sucursal_id: str = None,
    unidad_negocio_id: str = None,
    empresa_id: str = None,
    system_type: str = None,
    system_type_normalized: str = None,
    user: Dict = None,
    fecha_inicio: str = None,
    fecha_fin: str = None,
    filters: Dict = None,
    **extra
) -> str

# Hash de permisos de usuario
build_permissions_hash(user: Dict, length: int = 8) -> str

# Hash de filtros
build_filters_hash(filters: Dict, length: int = 8) -> str
```

### Ejemplo de Uso

```python
from core.cache_key_builder import build_context_cache_key

key = build_context_cache_key(
    namespace="comercial",
    endpoint="dashboard",
    server_id="abc123",
    sucursal_id="suc001",
    system_type_normalized="MANAGEMENTPRO",
    fecha="2026-04-25"
)
# Resultado: "comercial:dashboard:srv:abc123:suc:suc001:sys:MANAGEMENTPRO:date:2026-04-25"
```

---

## 5. SECRET MANAGER - CORRECCIÓN DE CACHE

### Problema Original

```python
# Antes: Cache sin detección de cambios
_fernet_loaded = False

def get_fernet():
    global _fernet_loaded
    if not _fernet_loaded:
        _fernet_instance = _get_fernet()
        _fernet_loaded = True
    return _fernet_instance  # ❌ No detecta cambio de clave
```

### Solución Implementada

```python
# Después: Cache con fingerprint de clave
_fernet_instance = None
_fernet_key_fingerprint = None

def get_fernet():
    global _fernet_instance, _fernet_key_fingerprint
    
    current_fingerprint = _get_key_fingerprint()
    
    # Si cambió la clave, invalidar cache automáticamente
    if _fernet_key_fingerprint != current_fingerprint:
        logger.info("[SECRET_MANAGER][CACHE_INVALIDATED] Clave cambió")
        _fernet_instance = _get_fernet()
        _fernet_key_fingerprint = current_fingerprint
    
    return _fernet_instance  # ✅ Detecta cambio automáticamente
```

### Nuevas Funciones

```python
# Validar configuración sin exponer clave
validate_secret_key_config() -> dict

# Limpiar cache explícitamente
clear_secret_manager_cache()
```

---

## 6. COMERCIAL CACHE - YA CONTEXTUALIZADO

El cache de comercial (`cache_service.py`) ya implementa correctamente la política desde FASE 3A.3:

```python
def build_cache_key(
    modulo: str,
    endpoint: str,
    server_id: str,
    sucursal: str = "",
    fecha: str = "",
    system_type: str = "",  # ✅ Incluido desde FASE 3A.3
    **extra_params
) -> str:
```

**Contextos incluidos:**
- ✅ endpoint
- ✅ server_id
- ✅ sucursal
- ✅ fecha
- ✅ system_type_normalized
- ✅ filtros extra

**Nota:** Si algún endpoint depende de permisos de usuario, debe agregarse `user_id` o `permissions_hash` a los `extra_params`.

---

## 7. FINANZAS CACHE - SIN CAMBIOS NECESARIOS

### repository_real.py

Cache de servidor EDARSA_HUB es seguro porque:
- Es un servidor fijo (`EDARSA_HUB_SERVER_ID`)
- Se invalida si el servidor no está disponible
- No depende de contexto de usuario

### propinas_tpv/cache_manager.py

Ya implementa `_generar_cache_key` que incluye:
- ✅ fecha_inicio, fecha_fin
- ✅ server_id
- ✅ sucursal_id
- ✅ Parámetros ordenados

---

## 8. FRONTEND CACHE

### localStorage

| Clave | Contenido | Riesgo |
|-------|-----------|--------|
| `token` | JWT de autenticación | BAJO - Expira |
| `user` | Datos de usuario | BAJO - Se refresca |
| `auditoria_filters_*` | Filtros con contexto server+sucursal | ✅ YA CONTEXTUALIZADO |
| `inventarioManualCaptura_backup` | Backup temporal | BAJO - Limpiado al guardar |

### Recomendaciones

1. Al cambiar usuario/token: Limpiar estado sensible
2. Al cambiar unidad de negocio: Limpiar datos del tablero anterior
3. No guardar secretos en localStorage

---

## 9. LOGS DE CACHE

Se agregaron logs para auditoría:

```
[CACHE][KEY_BUILT] comercial:dashboard:srv:abc123...
[SECRET_MANAGER][CACHE_INVALIDATED] Clave de cifrado cambió (fingerprint: d60e... -> db44...)
[SECRET_MANAGER][CACHE_RESET] Cache de Fernet limpiado manualmente
```

**NO se loguean:**
- Secretos
- Tokens
- Passwords
- API keys

---

## 10. TTLs RECOMENDADOS

| Tipo de Cache | TTL | Justificación |
|--------------|-----|---------------|
| Dashboard | 180s (3 min) | Datos cambian frecuentemente |
| Reporte Pax | 180s (3 min) | Datos del día |
| Ticket Perfecto | 300s (5 min) | Estadísticas |
| Metas | 900s (15 min) | Objetivos mensuales |
| Propinas | 300s (5 min) | Datos de turno |
| Configuración | 3600s (1 hora) | Cambios raros |
| Secret Manager | Indefinido (con fingerprint) | Cambia solo si la clave cambia |

---

## 11. PRUEBAS REALIZADAS

### Secret Manager

| Prueba | Resultado |
|--------|-----------|
| Clave A cifra | ✅ OK |
| Cambiar env a clave B | ✅ OK |
| get_fernet usa clave B sin limpieza manual | ✅ OK |
| clear_secret_manager_cache funciona | ✅ OK |
| validate_secret_key_config no expone clave | ✅ Solo fingerprint |

### Comercial

| Prueba | Resultado |
|--------|-----------|
| SoftRestaurant y MPRO generan cache_key diferente | ✅ Verificado (FASE 3A.3) |
| Cambio de fecha genera cache_key diferente | ✅ Verificado |
| Cambio de sucursal genera cache_key diferente | ✅ Verificado |

### General

| Prueba | Resultado |
|--------|-----------|
| `python -m compileall /app/backend` | ✅ OK |
| Backend RUNNING | ✅ OK |
| `/api/servers` | ✅ OK |

---

## 12. ARCHIVOS CREADOS/MODIFICADOS

### Creados
- `/app/backend/core/cache_key_builder.py`
- `/app/docs/CACHE_CONTEXT_POLICY_3C1.md` (este documento)

### Modificados
- `/app/backend/core/secret_manager.py` (detección automática de cambio de clave)

### Sin cambios (ya correctos)
- `/app/backend/modules/comercial/cache_service.py`
- `/app/backend/modules/finanzas/repository_real.py`
- `/app/backend/modules/finanzas/propinas_tpv/cache_manager.py`

---

## 13. CRITERIOS DE ACEPTACIÓN

| Criterio | Estado |
|----------|--------|
| Existe inventario de caches | ✅ |
| secret_manager no queda pegado a clave anterior | ✅ |
| cache_key_builder existe | ✅ |
| Comercial/Compras no comparten cache entre system_type | ✅ |
| server_registry no comparte cache entre alcances incompatibles | ✅ |
| No se cachean secretos en texto plano | ✅ |
| Backend compila | ✅ |
| Documentación completa | ✅ |

---

## 14. RIESGOS RESIDUALES

1. **Módulos no revisados a profundidad**: Inventarios, Configuración. Se recomienda revisar si implementan cache.

2. **Frontend useMemo**: Algunos componentes usan `useMemo` con datos de servidor. Si el servidor cambia, React debe re-renderizar (generalmente lo hace automáticamente).

3. **MongoDB sin TTL automático**: Los caches en MongoDB (`comercial_cache`) deben limpiarse manualmente o con job programado si se acumulan demasiados.

---

**FASE 3C.1 COMPLETADA EXITOSAMENTE**
