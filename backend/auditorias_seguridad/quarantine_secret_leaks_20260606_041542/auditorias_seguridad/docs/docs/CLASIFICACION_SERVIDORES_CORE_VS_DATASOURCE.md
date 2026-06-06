# CLASIFICACIÓN DE SERVIDORES: CORE vs DATA_SOURCE

**Fecha:** 2026-04-20  
**Versión:** 3.4.1  
**Autor:** Arquitectura Senior

---

## 1. OBJETIVO

Separar conceptualmente EDARSA HUB (cerebro del sistema) del catálogo de servidores operativos SIN romper nada, sin perder data, sin regresiones.

## 2. PROBLEMA RESUELTO

Existían conexiones en el módulo de servidores que correspondían al cerebro del sistema:
- Host: 54.39.104.176
- Base de datos: EDARSAHUB
- Usuario: HRLectura

Estas conexiones NO deben tratarse como fuentes externas operativas iguales a SoftRestaurant o MPRO.

## 3. SOLUCIÓN IMPLEMENTADA

### 3.1 Nuevos Campos en Modelo Server

```python
# server.py - Modelo Server extendido
tipo_conexion: str = "DATA_SOURCE"  # "DATA_SOURCE" | "CORE"
visible_en_listado: bool = True     # Si aparece en menú de servidores UI
es_editable_ui: bool = True         # Si se puede editar desde UI estándar
es_eliminable_ui: bool = True       # Si se puede eliminar desde UI estándar
uso_sistema: Optional[str] = None   # "CORE_DB" | "RH_INTERNO" | null
```

### 3.2 Clasificación Aplicada

| Servidor | tipo_conexion | visible_en_listado | es_editable_ui | es_eliminable_ui | uso_sistema |
|----------|---------------|-------------------|----------------|------------------|-------------|
| EDARSA HUB (bea40259...) | CORE | False | False | False | CORE_DB |
| EDARSA HUB (f8a9049a...) | CORE | False | False | False | CORE_DB |
| ManagmentPro | DATA_SOURCE | True | True | True | null |
| CIENFUEGOS | DATA_SOURCE | True | True | True | null |
| LA ESTELAR | DATA_SOURCE | True | True | True | null |
| 130° MERIDA | DATA_SOURCE | True | True | True | null |
| MPRO TABLAJERIA | DATA_SOURCE | True | True | True | null |
| CIENFUEGOS TABLAJERIA | DATA_SOURCE | True | True | True | null |
| HR2020 ESCRITURA | DATA_SOURCE | True | True | True | null |

### 3.3 Cambios en Backend

#### GET /api/servers
```python
# Solo devuelve DATA_SOURCE, excluye CORE
servers = await db.servers.find({
    "active": True,
    "$or": [
        {"tipo_conexion": {"$exists": False}},  # Backward compatible
        {"tipo_conexion": "DATA_SOURCE"},
        {"visible_en_listado": True}
    ]
})
servers = [s for s in servers if s.get("tipo_conexion") != "CORE"]
```

#### PUT /api/servers/{server_id}
```python
# Protección CORE
if existing.get("tipo_conexion") == "CORE" or existing.get("es_editable_ui") == False:
    raise HTTPException(403, "Esta conexión es del sistema central (CORE)...")
```

#### DELETE /api/servers/{server_id}
```python
# Protección CORE
if existing.get("tipo_conexion") == "CORE" or existing.get("es_eliminable_ui") == False:
    raise HTTPException(403, "Esta conexión es del sistema central (CORE)...")
```

#### get_servers_for_tablero()
```python
# Solo DATA_SOURCE para tablero ejecutivo
cursor = get_db().servers.find({
    "active": True, 
    "visible_en_operaciones": {"$ne": False},
    "$or": [
        {"tipo_conexion": {"$exists": False}},
        {"tipo_conexion": "DATA_SOURCE"}
    ]
})
```

## 4. VALIDACIONES REALIZADAS

| Validación | Resultado |
|------------|-----------|
| EDARSAHUB no aparece en GET /api/servers | ✅ EXITOSO |
| Tablero Ejecutivo funciona (5 unidades, $10.2M) | ✅ EXITOSO |
| Intento de editar CORE → HTTP 403 | ✅ EXITOSO |
| Intento de eliminar CORE → HTTP 403 | ✅ EXITOSO |
| Dashboard Comercial MPRO funciona | ✅ EXITOSO |
| Unidades de Negocio funcionan | ✅ EXITOSO |

## 5. NO SE REALIZÓ

- ❌ Refactor masivo
- ❌ Cambio de .env ni conexión principal
- ❌ Borrado de base de datos
- ❌ Eliminación física del registro
- ❌ Modificación de módulos no relacionados

## 6. ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `/app/backend/server.py` | Modelo Server extendido + Endpoints protegidos |
| `/app/backend/modules/comercial/repository.py` | get_servers_for_tablero() filtrado |

## 7. SNAPSHOTS

- `/app/docs/snapshots/servers_pre_clasificacion_*.json` - Estado previo
- `/app/docs/snapshots/diff_clasificacion_servidores.md` - Diff de cambios

## 8. REGLA ARQUITECTÓNICA

> **"EDARSA HUB es el cerebro del sistema. Las conexiones CORE no deben ser visibles ni editables desde la UI estándar de servidores operativos."**

---

**Documento generado como parte de la migración quirúrgica CORE vs DATA_SOURCE**
