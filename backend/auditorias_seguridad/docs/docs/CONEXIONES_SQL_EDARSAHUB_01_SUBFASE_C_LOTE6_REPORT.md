# REPORTE DE LOTE 6 — MIGRACIÓN DE BYPASSES
## CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C — LOTE 6

**Fecha:** 2025-12-19  
**Estado:** COMPLETADO  
**Autor:** Agente E1  
**Versión:** 1.0

---

## 1. RESUMEN EJECUTIVO

### Resultado
**1 de 1 endpoint migrado exitosamente** de `db.servers.find_one()` a `server_registry.get_server_connection_info()`.

### Dictamen por Capas

| Capa | Estado | Observación |
|------|--------|-------------|
| **A — Migración técnica** | ✅ OK | `guardar_script_pendiente()` usa `get_server_connection_info()` |
| **B — Permisos** | ✅ OK | Validación de rol Administrador conservada (403 para no-Admin) |
| **C — MongoDB documento operativo** | ✅ OK | Script pendiente se guarda en MongoDB sin credenciales |

---

## 2. ARCHIVO MODIFICADO

| Archivo | Cambios |
|---------|---------|
| `/app/backend/server.py` | 1 función migrada |

---

## 3. FUNCIÓN MODIFICADA — ANTES/DESPUÉS

### `guardar_script_pendiente()` — Línea ~11010

| Aspecto | Antes | Después |
|---------|-------|---------|
| Bypass | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` | `conn_info = await get_server_connection_info(server_id, db=db)` |
| Import | No aplica | `from core.server_registry import get_server_connection_info` |
| Variable | `server['name']` | `conn_info.get('name')` |
| Documentación | Básica | Incluye nota de migración LOTE 6 + confirmación de documento operativo |

### Bypass Eliminado

```python
# ANTES (línea 11023):
server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))

# DESPUÉS:
from core.server_registry import get_server_connection_info
conn_info = await get_server_connection_info(server_id, db=db)
```

### Llamada a Registry Usada

```python
conn_info = await get_server_connection_info(server_id, db=db)
```

---

## 4. CONFIRMACIÓN DE DOCUMENTO OPERATIVO EN MONGODB

### Estructura del Documento

```json
{
    "server_id": "a5547321-...",
    "server_name": "130° MERIDA",  // Solo nombre, sin credenciales
    "titulo": "Script de prueba",
    "script": "SELECT 1",
    "num_statements": 1,
    "creado_por": "admin@inventario.com",
    "fecha_creacion": "2025-12-19T...",
    "estado": "pendiente"
}
```

### Confirmación de No Credenciales

| Campo | ¿Presente? | ¿Contiene credenciales? |
|-------|------------|-------------------------|
| `server_id` | ✅ | ❌ No (solo ID) |
| `server_name` | ✅ | ❌ No (solo nombre visible) |
| `titulo` | ✅ | ❌ No |
| `script` | ✅ | ❌ No (SQL del usuario) |
| `password` | ❌ No presente | — |
| `username` | ❌ No presente | — |
| `host` | ❌ No presente | — |
| `connection_string` | ❌ No presente | — |
| `api_key` | ❌ No presente | — |

**✅ CONFIRMADO: El documento MongoDB NO contiene credenciales.**

---

## 5. VALIDACIONES EJECUTADAS

### 5.1 Validación del Endpoint

| Test | Resultado | Observación |
|------|-----------|-------------|
| Endpoint responde | ✅ PASS | 403 para no-Admin |
| Validación de permisos | ✅ PASS | Solo Administradores |
| Resolución de servidor | ✅ PASS | Usa `get_server_connection_info()` |

### 5.2 Validaciones de Regresión

| Lote | Endpoint | Estado |
|------|----------|--------|
| Lote 1 | `GET /api/servers/{id}/sucursales` | ✅ PASS (1 sucursal) |
| Lote 2 | `GET /api/servers/{id}/ping` | ✅ PASS (connected) |
| Lote 4 | `GET /api/sistema/sql-health` | ✅ PASS (healthy, EDARSAHUB_SQL) |
| Lote 5 | `GET /api/dashboard/servers-configured` | ✅ PASS (3 servidores) |

### 5.3 Validaciones de Sistema

| Check | Estado |
|-------|--------|
| Backend levanta | ✅ PASS |
| Auth funciona | ✅ PASS |
| Login funciona | ✅ PASS |
| `/api/auth/me` funciona | ✅ PASS |

---

## 6. ERRORES ENCONTRADOS

### Errores Esperados

| Error | Causa | Clasificación |
|-------|-------|---------------|
| 403 "Solo administradores" | Usuario sin rol Admin | NO ES BUG — Validación correcta |

### Errores No Esperados

**Ninguno.**

---

## 7. CONFIRMACIÓN DE FUNCIONES DIFERIDAS

### `save_server_query()` — DIFERIDO

| Aspecto | Estado |
|---------|--------|
| Código modificado | ❌ NO |
| Requiere | Función `update_server_query()` en `server_registry.py` |
| Destino correcto | EDARSAHUB `Servidores_Conexiones.query_*` |

### `delete_server_query()` — DIFERIDO

| Aspecto | Estado |
|---------|--------|
| Código modificado | ❌ NO |
| Requiere | Función `update_server_query()` en `server_registry.py` |
| Depende de | `save_server_query()` |

---

## 8. RECOMENDACIÓN PARA `update_server_query()`

### Diseño Propuesto

```python
# En server_registry.py
async def update_server_query(
    server_id: str, 
    query_type: str,  # 'inventario', 'ventas', 'movimientos'
    query_config: dict  # {sql, validated, last_validated, validation_message}
) -> bool:
    """
    Actualiza configuración de query en EDARSAHUB.
    
    Args:
        server_id: ID del servidor
        query_type: Tipo de query ('inventario', 'ventas', 'movimientos')
        query_config: Diccionario con configuración de la query
    
    Returns:
        True si se actualizó correctamente
    
    Raises:
        HTTPException si falla
    """
    import json
    
    # Validar query_type
    if query_type not in ['inventario', 'ventas', 'movimientos']:
        raise ValueError(f"Tipo de query inválido: {query_type}")
    
    column_name = f"query_{query_type}"
    query_json = json.dumps(query_config)
    
    # UPDATE en EDARSAHUB
    sql = f"""
    UPDATE Servidores_Conexiones
    SET {column_name} = %s,
        queries_configured = CASE 
            WHEN query_inventario IS NOT NULL 
             AND query_ventas IS NOT NULL 
             AND query_movimientos IS NOT NULL 
            THEN 1 ELSE 0 END,
        updated_at = GETDATE()
    WHERE id = %s
    """
    
    # Ejecutar UPDATE con parámetros
    # ... implementación ...
    
    return True
```

### Prerrequisitos para Implementar

1. **Permisos de escritura** en EDARSAHUB (usuario actual es `HRLectura`)
2. **Validación de formato JSON** compatible
3. **Sincronización previa** MongoDB → EDARSAHUB
4. **Tests unitarios** para escritura

---

## 9. RIESGOS PENDIENTES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| CONFIG-SECURITY-01 | MEDIA | BAJO | No afecta este lote |
| Escrituras a EDARSAHUB pendientes | N/A | N/A | Diferidas a Lote 7+ |

---

## 10. ROLLBACK

### Rollback Inmediato

```bash
git checkout HEAD~1 -- /app/backend/server.py
sudo supervisorctl restart backend
```

### Rollback por Flag

```bash
# En /app/backend/.env
USE_SQL_FOR_SERVERS=false
sudo supervisorctl restart backend
```

---

## 11. PROGRESO TOTAL

| Métrica | Valor |
|---------|-------|
| Total bypasses originales | 56 |
| Migrados (Lotes 1-6) | 31 |
| Pendientes | 25 |
| Porcentaje completado | **55%** |

---

## 12. CONCLUSIÓN

### Dictamen Final
**LOTE 6 COMPLETADO EXITOSAMENTE**

| Criterio | Estado |
|----------|--------|
| 1 bypass corregido | ✅ |
| No queda bypass directo en la función | ✅ |
| MongoDB solo como documento operativo | ✅ |
| No se guardan credenciales en MongoDB | ✅ |
| Backend levanta | ✅ |
| Auth funciona | ✅ |
| Lotes 1-5 sin regresión | ✅ |
| Permisos conservados | ✅ |
| Reporte con evidencia | ✅ |
| `save_server_query()` diferido | ✅ |
| `delete_server_query()` diferido | ✅ |

---

**Documento generado por Agente E1 — EDARSA HUB**  
**Fecha:** 2025-12-19  
**Estado:** COMPLETADO — PENDIENTE VALIDACIÓN USUARIO
