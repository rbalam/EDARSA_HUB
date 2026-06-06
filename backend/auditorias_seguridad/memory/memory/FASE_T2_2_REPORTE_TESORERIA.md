# FASE T2.2: REPORTE DE MIGRACIÓN TESORERÍA FALLBACK
**Fecha:** 2026-05-13
**Estado:** ✅ COMPLETADO

---

## 1. RESUMEN EJECUTIVO

| Aspecto | Resultado |
|---------|-----------|
| **Archivo modificado** | 1 |
| **Referencias db.servers eliminadas** | 1 |
| **Sucursales devueltas** | 4 (sin cambio) |
| **MongoDB utilizado** | NO |
| **Tablero Ejecutivo** | ✅ Sin regresión |

---

## 2. ARCHIVO MODIFICADO

### `/app/backend/modules/finanzas/tesoreria.py`

**Líneas:** 619-673 (fallback)

**Referencia eliminada:** `db.servers.find(mongo_query, {'_id': 0}).to_list(50)`

---

## 3. CÓDIGO ANTERIOR VS CÓDIGO NUEVO

### Código Anterior (MongoDB Fallback)
```python
# FALLBACK LEGACY: MongoDB (solo si EDARSAHUB falló)
try:
    from server import db
    
    logger.warning("[TESORERIA][MONGODB_FALLBACK] Usando MongoDB como fallback legacy")
    
    mongo_query = {
        'active': True,
        'tipo_conexion': {'$nin': ['CORE', 'API_LOCAL']},
        'system_type': {'$in': ['SoftRestaurant', 'SOFTRESTAURANT', 'SR', 'ManagementPro', 'MANAGEMENTPRO', 'MPRO']}
    }
    
    mongo_servers = await db.servers.find(mongo_query, {'_id': 0}).to_list(50)
    # ... procesamiento de servidores MongoDB ...
```

### Código Nuevo (server_registry Fallback)
```python
# FALLBACK: server_registry.py (FASE T2.2: Reemplaza MongoDB)
try:
    from core.server_registry import list_operational_servers
    
    logger.info("[TESORERIA][REGISTRY_FALLBACK] Usando server_registry.py como fallback")
    
    registry_servers = list_operational_servers()
    
    for s in registry_servers:
        vis_op = s.get('visible_en_operaciones')
        if vis_op is None or not vis_op:
            continue
        # ... procesamiento idéntico ...
```

---

## 4. FUNCIÓN DE SERVER_REGISTRY USADA

`list_operational_servers()` desde `/app/backend/core/server_registry.py`

Esta función:
- Lee servidores desde EDARSAHUB (Servidores_Conexiones)
- Filtra por `activo = True`
- Excluye servidores CORE
- Devuelve lista con campos: id, name, host, port, database, system_type, visible_en_operaciones

---

## 5. RESULTADO DE /api/finanzas/tesoreria/sucursales

### Antes (con MongoDB fallback)
```json
{
  "sucursales": [
    {"id": "a5547321-...", "nombre": "130° MERIDA", "fuente": "SOFTRESTAURANT"},
    {"id": "6d053c22-...", "nombre": "CIENFUEGOS", "fuente": "SOFTRESTAURANT"},
    {"id": "a5ff0e25-...", "nombre": "LA ESTELAR", "fuente": "SOFTRESTAURANT"},
    {"id": "1b230a06-...", "nombre": "ManagmentPro", "fuente": "MPRO"}
  ]
}
```

### Después (con server_registry fallback)
```json
{
  "sucursales": [
    {"id": "a5547321-...", "nombre": "130° MERIDA", "fuente": "SOFTRESTAURANT"},
    {"id": "6d053c22-...", "nombre": "CIENFUEGOS", "fuente": "SOFTRESTAURANT"},
    {"id": "a5ff0e25-...", "nombre": "LA ESTELAR", "fuente": "SOFTRESTAURANT"},
    {"id": "1b230a06-...", "nombre": "ManagmentPro", "fuente": "MPRO"}
  ]
}
```

**✅ Mismas 4 sucursales, mismo orden, mismo formato**

---

## 6. CONFIRMACIONES

| Confirmación | Estado |
|--------------|--------|
| Sin cambio en contrato API | ✅ CONFIRMADO |
| 4 sucursales devueltas | ✅ CONFIRMADO |
| No se usó MongoDB | ✅ CONFIRMADO |
| No se tocó Propinas TPV | ✅ CONFIRMADO |
| No se tocó CxP | ✅ CONFIRMADO |
| No se tocó Comercial | ✅ CONFIRMADO |
| No se tocó frontend | ✅ CONFIRMADO |
| Tablero Ejecutivo sin regresión | ✅ CONFIRMADO |

---

## 7. REFERENCIAS db.servers RESTANTES EN FINANZAS

Después de FASE T2.2, quedan **8 referencias** en Propinas TPV:

| Archivo | Línea | Propósito | Fase |
|---------|-------|-----------|------|
| `propinas_tpv/service.py` | 79 | Listar servidores SR | T2.4 |
| `propinas_tpv/service_sql.py` | 160 | Listar servidores SR | T2.4 |
| `propinas_tpv/routes.py` | 222 | Detectar esquema | T2.3 |
| `propinas_tpv/routes.py` | 262 | Detectar esquema todos | T2.3 |
| `propinas_tpv/routes.py` | 358 | Validar periodo | T2.3 |
| `propinas_tpv/routes_sql.py` | 408 | Detectar esquema | T2.3 |
| `propinas_tpv/routes_sql.py` | 440 | Detectar esquema todos | T2.3 |
| `propinas_tpv/routes_sql.py` | 516 | Validar periodo | T2.3 |

---

## 8. RECOMENDACIÓN PARA FASE T2.3

**Siguiente módulo:** Propinas TPV Routes (`routes.py` y `routes_sql.py`)

**Razón:**
- 6 referencias similares (3 + 3 en archivos espejo)
- Todas son operaciones de lectura (find, find_one)
- No afectan escritura de propinas
- Riesgo MEDIO

**Funciones de server_registry a usar:**
- `get_server_by_id()` para find_one
- `list_operational_servers()` filtrado para find

---

**Generado:** 2026-05-13
**Fase:** T2.2 — Migrar Tesorería Fallback
