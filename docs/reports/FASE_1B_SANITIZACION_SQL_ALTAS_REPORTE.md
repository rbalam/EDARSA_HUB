# FASE 1B: Sanitización SQL - Vulnerabilidades ALTAS
## Reporte de Correcciones A01, A02, A03, A04

**Fecha:** 2026-05-15  
**Hora:** 11:15 UTC  
**Ejecutado por:** E1 Agent  
**Estado:** COMPLETADO

---

## 1. RESUMEN EJECUTIVO

| Métrica | Valor |
|---------|-------|
| **Vulnerabilidades corregidas** | 4 (A01, A02, A03, A04) |
| **Archivos modificados** | 1 (`server.py`) |
| **Funciones helper creadas** | 5 |
| **Endpoints corregidos** | 6 |
| **Backend operativo** | ✅ |
| **Sin regresiones** | ✅ |

---

## 2. VULNERABILIDADES CORREGIDAS

### A01 - `/servers/{server_id}/almacenes` (sucursal_id)

**Riesgo:** ALTO  
**Tipo:** SQL Injection por concatenación de string

**Antes (vulnerable):**
```python
query = f"SELECT ... WHERE Sc_Cve_Sucursal = '{sucursal_id}' ..."
```

**Después (seguro):**
```python
# Validación
if not _validate_identifier(sucursal_id, max_length=50):
    raise HTTPException(status_code=400, detail="sucursal_id contiene caracteres no permitidos")

# Parametrización con %s (pymssql)
query = f"SELECT ... WHERE Sc_Cve_Sucursal = %s ..."
results = execute_sql_query_params(..., query, (sucursal_id,))
```

**Driver:** pymssql  
**Placeholder:** `%s`

---

### A02 - Múltiples endpoints con `almacen` en LIKE

**Riesgo:** ALTO  
**Tipo:** SQL Injection via caracteres especiales LIKE (`%`, `_`, `[`)

**Antes (vulnerable):**
```python
query = f"WHERE nombre LIKE '%{almacen}%'"
```

**Después (seguro):**
```python
almacen_safe = _escape_like_pattern(almacen) if almacen else ""
query = f"WHERE nombre LIKE '%{almacen_safe}%'"
```

**Función reutilizada:** `_escape_like_pattern()` (FASE 1A)

**Endpoints corregidos:**
- `/reports/inventory-analysis` (líneas 3557, 4163, 4303)

---

### A03 - `/explorador/columnas/{server_id}/{tabla}`

**Riesgo:** ALTO  
**Tipo:** SQL Injection por nombre de tabla no validado

**Antes (vulnerable):**
```python
query = f"WHERE TABLE_NAME = '{tabla}'"
# Solo validaba: tabla.replace('_', '').isalnum()
```

**Después (seguro):**
```python
# Validación contra whitelist
is_valid, error_msg = _validate_table_name(tabla, system_type)
if not is_valid:
    raise HTTPException(status_code=400, detail=error_msg)

# Parametrización
query = "WHERE TABLE_NAME = %s"
results = execute_sql_query_params(..., query, (tabla,))
```

**Endpoints corregidos:**
- `/explorador/columnas/{server_id}/{tabla}`
- `/explorador/relaciones/{server_id}/{tabla}`
- `/explorador/preview/{server_id}/{tabla}`

**Whitelist implementada:**
```python
EXPLORADOR_TABLAS_PERMITIDAS = {
    # SoftRestaurant
    'almacen', 'cheques', 'cheqdet', 'productos', 'categorias', 'turnos',
    'meseros', 'cuentas', 'folios', 'formasdepago', 'movsinventario', 
    'movsalmacen', 'gruposi', 'gruposiclasificacion', 'productosreceta',
    'productosi', 'usuarios', 'tiposdecheques', 'impuestos', 'preciosi',
    # MPRO
    'producto', 'almacen', 'sucursal', 'proveedor', 'movimiento', 
    'entrada', 'salida', 'fisico', 'compras', 'ventas', 'clientes',
    'categoria', 'familia', 'subfamilia', 'unidad', 'tipo_movimiento',
    # Sistema
    'information_schema.tables', 'information_schema.columns',
}
```

---

### A04 - `/reports/inventory-analysis` (folios)

**Riesgo:** ALTO  
**Tipo:** SQL Injection via lista de folios interpolados

**Antes (vulnerable):**
```python
folios_ini_sql = ",".join([f"'{f}'" for f in lista_folios_ini])
# No validaba contenido de folios
```

**Después (seguro):**
```python
def _sanitize_folio_list(folios: list, max_count: int = 50) -> list:
    sanitized = []
    for f in folios[:max_count]:
        if f and isinstance(f, str):
            if _validate_identifier(str(f), max_length=50):
                sanitized.append(str(f).replace("'", "''"))
            else:
                logging.warning(f"[A04-SANITIZADO] Folio inválido rechazado")
    return sanitized

lista_folios_ini = _sanitize_folio_list(lista_folios_ini)
lista_folios_fin = _sanitize_folio_list(lista_folios_fin)
```

**Protecciones:**
- Límite máximo: 50 folios por lista
- Validación de caracteres alfanuméricos
- Escape de comillas simples
- Logging de folios rechazados

---

## 3. FUNCIONES HELPER CREADAS

| Función | Línea | Propósito |
|---------|-------|-----------|
| `_validate_identifier()` | ~12168 | Valida identificadores seguros |
| `_sanitize_identifier()` | ~12180 | Escapa comillas en identificadores |
| `_validate_table_name()` | ~12210 | Valida tablas contra whitelist |
| `_build_safe_folios_condition()` | ~12240 | Construye IN seguro para folios |
| `_sanitize_folio_list()` | ~3418 | Sanitiza lista de folios |

---

## 4. PAYLOADS MALICIOSOS PROBADOS

### A01 - sucursal_id
| Payload | Esperado | Resultado |
|---------|----------|-----------|
| `1' OR 1=1--` | Rechazado | ✅ HTTP 400 |
| `1; DROP TABLE--` | Rechazado | ✅ HTTP 400 |
| `sucursal_normal` | Aceptado | ✅ HTTP 200 |

### A03 - tabla
| Payload | Esperado | Resultado |
|---------|----------|-----------|
| `almacen` | Aceptado | ✅ HTTP 200 |
| `malicious_table` | Rechazado | ✅ HTTP 400 "no está en lista" |
| `almacen' OR 1=1--` | Rechazado | ✅ HTTP 400 "caracteres no permitidos" |

---

## 5. VALIDACIONES EJECUTADAS

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | `python -m py_compile server.py` | ✅ Sin errores |
| 2 | Backend arranca | ✅ RUNNING |
| 3 | Login funciona | ✅ Token obtenido |
| 4 | `/api/servers` funciona | ✅ Lista servidores |
| 5 | A01 payload malicioso | ✅ Rechazado |
| 6 | A01 valor normal | ✅ Aceptado |
| 7 | A03 tabla permitida | ✅ Columnas devueltas |
| 8 | A03 tabla maliciosa | ✅ Rechazada |
| 9 | FASE 1A `/explorador/buscar` | ✅ Sin regresión |
| 10 | FASE 3 Repository | ✅ 18/18 checks |

---

## 6. NO REGRESIONES CONFIRMADAS

| Componente | Estado |
|------------|--------|
| FASE 1A - `/explorador/buscar` | ✅ Funciona |
| FASE 3 - Repository SQL-First | ✅ 18/18 tests |
| Login | ✅ Funciona |
| `/api/servers` | ✅ Funciona |
| Catálogo SQL legacy | ✅ Sin cambios |
| Frontend | ✅ Sin modificaciones |

---

## 7. ARCHIVOS MODIFICADOS

| Archivo | Cambios |
|---------|---------|
| `/app/backend/server.py` | +5 funciones helper, correcciones A01/A02/A03/A04 |

**Sin modificar:**
- Frontend
- catalogo_consultas.py
- server_registry.py
- MongoDB
- Endpoints legacy
- Scheduler
- Fecha operativa

---

## 8. RIESGOS PENDIENTES

| Riesgo | Severidad | Descripción |
|--------|-----------|-------------|
| A02 parcial | MEDIA | Quedan ~15 instancias de LIKE sin escapar en otros endpoints |
| Whitelist incompleta | BAJA | Pueden faltar tablas legítimas en whitelist |

**Nota:** Las instancias restantes de A02 serán abordadas en fases futuras de sanitización.

---

## 9. PRÓXIMOS PASOS RECOMENDADOS

1. **FASE 1C**: Completar sanitización de todas las instancias LIKE restantes
2. **FASE 4**: Crear endpoints `/api/consultas-sql/*`
3. Ampliar whitelist de tablas según necesidades del usuario

---

## 10. CONCLUSIÓN

**FASE 1B COMPLETADA EXITOSAMENTE**

- 4 vulnerabilidades ALTAS corregidas (A01, A02, A03, A04)
- Parametrización con `%s` (pymssql) implementada
- Whitelist estricta para nombres de tablas
- Sanitización de folios con límites y validación
- Sin regresiones en FASE 1A ni FASE 3
- Backend estable y operativo

---

*Documento generado por E1 Agent*  
*Fecha: 2026-05-15*
