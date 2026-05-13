# FASE M1: REPORTE SERVER REGISTRY CENTRAL
**Fecha:** 2026-05-13
**Estado:** ✅ COMPLETADO

---

## 1. RESUMEN EJECUTIVO

| Aspecto | Resultado |
|---------|-----------|
| **Funciones agregadas** | 8 |
| **Pruebas pasadas** | 10/10 |
| **MongoDB utilizado** | NO |
| **Tablero Ejecutivo** | ✅ Sin regresión |

---

## 2. FUNCIONES IMPLEMENTADAS

### 2.1 Funciones Principales

| Función | Descripción |
|---------|-------------|
| `list_unidades_negocio(active_only=True)` | Lista 5 unidades desde EDARSAHUB |
| `get_server_by_unidad_codigo(codigo)` | Resuelve servidor por código canónico |
| `resolve_unidad_by_server_sucursal(server_id, sucursal_id)` | Resuelve MPRO por sucursal |
| `normalize_unidad_codigo(codigo)` | Normaliza legacy→canónico |
| `validate_registry_integrity()` | Valida integridad del registro |

### 2.2 Wrappers Opcionales

| Función | Descripción |
|---------|-------------|
| `list_operational_servers()` | Lista servidores operacionales |
| `get_visible_servers_for_operaciones()` | Servidores visibles en operaciones |
| `get_connection_config(server_id)` | Configuración de conexión |

---

## 3. EJEMPLOS DE SALIDA

### list_unidades_negocio()
```python
[
    {'codigo': '130MID', 'nombre': '130° MERIDA', 'server_id': 'a5547321-...', 'sucursal_origen_id': None, 'fuente': 'EDARSAHUB'},
    {'codigo': 'CIENFUEGOS', 'nombre': 'CIENFUEGOS', ...},
    {'codigo': 'ESTELAR', 'nombre': 'LA ESTELAR', ...},
    {'codigo': '130QRO', 'nombre': '130° QUERETARO', 'sucursal_origen_id': '0021', ...},
    {'codigo': 'ORIGEN', 'nombre': 'ORIGEN', 'sucursal_origen_id': '0023', ...}
]
```

### get_server_by_unidad_codigo('130MID')
```python
{
    'unidad_negocio_codigo': '130MID',
    'unidad_negocio_nombre': '130° MERIDA',
    'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6',
    'host': '130mid.ddns.net',
    'port': 1433,
    'database': 'softrestaurant10',
    'system_type': 'SoftRestaurant',
    'fuente': 'EDARSAHUB'
}
```

### resolve_unidad_by_server_sucursal() para MPRO
```python
# server_mpro + sucursal '0021' → 130QRO
>>> resolve_unidad_by_server_sucursal('1b230a06-...', '0021')
{'codigo': '130QRO', 'nombre': '130° QUERETARO', 'sucursal_origen_id': '0021'}

# server_mpro + sucursal '0023' → ORIGEN
>>> resolve_unidad_by_server_sucursal('1b230a06-...', '0023')
{'codigo': 'ORIGEN', 'nombre': 'ORIGEN', 'sucursal_origen_id': '0023'}
```

### validate_registry_integrity()
```python
{
    'ok': True,
    'errors': [],
    'warnings': [],
    'unidades_detectadas': ['130MID', 'CIENFUEGOS', 'ESTELAR', '130QRO', 'ORIGEN'],
    'servidores_asociados': [
        {'id': 'a5547321-...', 'nombre': '130° MERIDA', 'activo': True},
        {'id': '6d053c22-...', 'nombre': 'CIENFUEGOS', 'activo': True},
        {'id': 'a5ff0e25-...', 'nombre': 'LA ESTELAR', 'activo': True},
        {'id': '1b230a06-...', 'nombre': 'ManagmentPro', 'activo': True}
    ],
    'fuente': 'EDARSAHUB'
}
```

---

## 4. CONFIRMACIONES OBLIGATORIAS

| Confirmación | Estado |
|--------------|--------|
| No se usó MongoDB | ✅ CONFIRMADO |
| No se modificaron funciones existentes | ✅ CONFIRMADO |
| No se tocaron consumidores | ✅ CONFIRMADO |
| Tablero Ejecutivo sin regresión | ✅ CONFIRMADO |
| 5 unidades visibles | ✅ CONFIRMADO |
| Variaciones correctas | ✅ CONFIRMADO |

---

## 5. ARCHIVO MODIFICADO

**Archivo:** `/app/backend/core/server_registry.py`

**Líneas agregadas:** ~350 (de 1701 a ~2050)

**Sección:** `# FASE M1: FUNCIONES DE UNIDADES DE NEGOCIO (EDARSAHUB-ONLY)`

---

## 6. PRÓXIMOS PASOS (NO AUTORIZADOS AÚN)

| Prioridad | Tarea |
|-----------|-------|
| P1 | FASE T2: Migrar Finanzas (Tesorería/Propinas) de MongoDB a EDARSAHUB |
| P1 | FASE T3: Migrar Compras de MongoDB a EDARSAHUB |
| P2 | Migrar primer consumidor a usar `server_registry` en lugar de `db.servers` |
| P2 | Crear `/api/v2/unidades` endpoint público |

---

**Generado:** 2026-05-13
**Fuente:** EDARSAHUB (cerebro del sistema)
