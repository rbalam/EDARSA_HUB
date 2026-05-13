# FASE T3.4-A — Diagnóstico Quirúrgico del Endpoint Crítico
## Análisis de `POST /compras/auditoria-operativa`

**Fecha:** 14-Mayo-2026  
**Estado:** DIAGNÓSTICO COMPLETADO  
**Tipo:** Análisis pasivo de código

---

## 1. Ubicación Exacta de la Referencia MongoDB

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea inicio** | 7426 |
| **Línea referencia** | 7440 |
| **Línea fin** | 8137 |
| **Total líneas** | ~711 |

---

## 2. Fragmento de Código Actual

```python
# Línea 7440
server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
if not server:
    raise HTTPException(status_code=404, detail="Servidor no encontrado")
```

---

## 3. Datos que Obtiene de MongoDB

### 3.1 Datos de Conexión (usados en 26 llamadas a `execute_sql_query`)
| Campo | Uso |
|-------|-----|
| `host` | Conexión SQL |
| `port` | Conexión SQL |
| `database` | Conexión SQL |
| `username` | Conexión SQL |
| `password` | Conexión SQL (descifrado) |

### 3.2 Datos de Configuración
| Campo | Uso | Línea |
|-------|-----|-------|
| `system_type` | Determinar si es SoftRestaurant o MPRO | 7483, 8112 |
| `tipos_movimiento` | **⚠️ CAMPO CRÍTICO** - Lista de tipos de movimiento configurados | 7675 |

---

## 4. ⚠️ HALLAZGO CRÍTICO: Campo `tipos_movimiento`

### 4.1 Descripción del Problema

El endpoint usa `server.get('tipos_movimiento', [])` en la línea 7675.

Este campo:
- ✅ **EXISTE** en MongoDB (`db.servers`)
- ❌ **NO EXISTE** en EDARSAHUB SQL (`Servidores_Conexiones`)
- ❌ **NO EXISTE** en `server_registry.py`

### 4.2 Estructura del Campo en MongoDB

```json
{
  "tipos_movimiento": ["EPC", "ECS", "EPB", "EDE", "STR", "STA", "SPV", ...]
}
```

### 4.3 Uso en el Endpoint

```python
# Línea 7675
tipos_mov_activos = server.get('tipos_movimiento', [])

# Línea 7679-7686
tipos_entrada_activos = [t for t in tipos_mov_activos if t.startswith('E')]
tipos_salida_activos = [t for t in tipos_mov_activos if t.startswith('S')]

tipos_entrada_compra = [t for t in tipos_entrada_activos if t in ['EPC', 'ECS', 'EPB', 'EDE', 'EEH', 'ECO', 'ECA', 'EPL', 'EPR']]
tipos_entrada_traspaso = [t for t in tipos_entrada_activos if t in ['ETR', 'ETA', 'EAL']]
tipos_salida_traspaso = [t for t in tipos_salida_activos if t in ['STR', 'STA', 'SAL']]
```

### 4.4 Impacto si el Campo no Existe

Si `tipos_movimiento` no está presente en el servidor:
1. `tipos_mov_activos = []` (lista vacía)
2. `tipos_entrada_compra = []`
3. `tipos_salida_traspaso = []`
4. **NINGÚN movimiento se procesa**
5. **La auditoría devuelve resultados incorrectos/vacíos**

---

## 5. Análisis de Riesgos

### 5.1 Riesgo de Sustitución Directa

| Aspecto | Riesgo |
|---------|--------|
| Reemplazo de conexión (`host`, `port`, `database`, `username`, `password`) | 🟢 **BAJO** - Mismos campos disponibles |
| Reemplazo de `system_type` | 🟢 **BAJO** - Disponible en `server_registry` |
| Reemplazo de `tipos_movimiento` | 🔴 **ALTO** - Campo NO disponible en `server_registry` |

### 5.2 Opciones para Resolver `tipos_movimiento`

**OPCIÓN A: Preservar fallback MongoDB para este campo**
```python
# Obtener servidor desde registry
from core.server_registry import get_server_connection_info
server = await get_server_connection_info(request.server_id, db=db)

# Obtener tipos_movimiento desde MongoDB (fallback parcial)
mongo_server = await db.servers.find_one({"id": request.server_id}, {"tipos_movimiento": 1, "_id": 0})
server['tipos_movimiento'] = mongo_server.get('tipos_movimiento', []) if mongo_server else []
```

**OPCIÓN B: Migrar `tipos_movimiento` a EDARSAHUB SQL**
- Agregar columna `tipos_movimiento` (JSON/VARCHAR) a `Servidores_Conexiones`
- Migrar datos de MongoDB
- Actualizar `server_registry.py`
- Requiere **autorización DDL** en EDARSAHUB

**OPCIÓN C: Usar valores por defecto estándar**
- Definir tipos de movimiento estándar para SoftRestaurant
- Solo aplica si todos los servidores usan los mismos tipos
- **NO RECOMENDADO** porque la configuración es personalizada

---

## 6. Confirmaciones

### 6.1 Cambio de Bajo Impacto vs Lógica Afectada

| Aspecto | Impacto |
|---------|---------|
| Cambio de fuente de conexión | 🟢 BAJO IMPACTO |
| Cambio de `system_type` | 🟢 BAJO IMPACTO |
| Cambio de `tipos_movimiento` | 🔴 **AFECTA LÓGICA** |

### 6.2 El Endpoint NO Requiere Tocar:

- ✅ Cálculo de auditoría (Inv Inicial + Compras - Consumos)
- ✅ Consultas SQL (26 queries)
- ✅ Filtros por almacén/sucursal
- ✅ Validaciones de existencia
- ✅ Respuesta JSON
- ✅ Parámetros de entrada
- ✅ Lógica de comparación físico vs teórico
- ✅ Generación de acta de auditoría

### 6.3 El Endpoint USA un Solo `server_id`

Confirmado: el endpoint recibe un único `server_id` vía `request.server_id` y usa ese mismo servidor para todas las operaciones.

### 6.4 Dependencias

El endpoint depende de:
- `execute_sql_query()` para todas las consultas SQL
- `is_softrestaurant_system()` y `is_mpro_system()` para routing
- Configuración de `tipos_movimiento` del servidor

---

## 7. Pruebas Obligatorias (Pre y Post Migración)

### 7.1 Pre-Migración (Baseline)
```bash
# Registrar comportamiento actual
POST /api/compras/auditoria-operativa
{
  "server_id": "a5547321-1139-4d2b-9d53-182ca737b6b6",
  "sucursal": "130",
  "fecha_inv_inicial": "2026-05-01",
  "fecha_auditoria": "2026-05-14",
  "folio_inv_inicial": "3814",
  "almacenes": ["2", "3"]
}
```

### 7.2 Post-Migración (Validación)
1. Mismo request → Mismo response (estructura y valores)
2. Verificar que `tipos_movimiento` se obtiene correctamente
3. Verificar cálculos de existencia teórica
4. Verificar diferencias favor/contra

---

## 8. Plan de Rollback

```python
# ACTUAL (MongoDB):
server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))

# PROPUESTO (Registry + fallback):
from core.server_registry import get_server_connection_info
server = await get_server_connection_info(request.server_id, db=db)
if server:
    mongo_server = await db.servers.find_one({"id": request.server_id}, {"tipos_movimiento": 1, "_id": 0})
    server['tipos_movimiento'] = mongo_server.get('tipos_movimiento', []) if mongo_server else []

# ROLLBACK: Revertir a línea original
```

---

## 9. Confirmación de No Modificación

- ✅ **NO se modificó** `/app/backend/server.py`
- ✅ **NO se ejecutó** ningún cambio
- ✅ **NO se tocó** MongoDB ni EDARSAHUB
- ✅ Diagnóstico 100% pasivo (solo lectura)

---

## 10. Recomendación para T3.4-B

### Estrategia Recomendada: OPCIÓN A (Preservar fallback parcial)

**Razón:**
1. Permite migrar la conexión a `server_registry` (objetivo principal)
2. Preserva el campo `tipos_movimiento` desde MongoDB (mínimo cambio)
3. No requiere cambios DDL en EDARSAHUB
4. Mantiene la funcionalidad exacta del endpoint
5. Puede migrarse completamente en una fase futura (cuando se agregue la columna a SQL)

### Código Propuesto (NO EJECUTAR SIN AUTORIZACIÓN)

```python
@api_router.post("/compras/auditoria-operativa")
async def realizar_auditoria_operativa(request: AuditoriaOperativaRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """..."""
    verify_token(credentials.credentials)
    
    logging.info(f"[AUDITORIA] Iniciando auditoría - server: {request.server_id}, sucursal: {request.sucursal}")
    
    # FASE T3.4: Migrado de db.servers a server_registry (EDARSAHUB) para conexión
    # Preserva fallback MongoDB para tipos_movimiento (campo no migrado a SQL)
    from core.server_registry import get_server_connection_info
    server = await get_server_connection_info(request.server_id, db=db)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # FASE T3.4: Obtener tipos_movimiento desde MongoDB (aún no migrado a SQL)
    mongo_config = await db.servers.find_one(
        {"id": request.server_id}, 
        {"tipos_movimiento": 1, "_id": 0}
    )
    server['tipos_movimiento'] = mongo_config.get('tipos_movimiento', []) if mongo_config else []
    
    # ... resto del endpoint sin cambios ...
```

---

## 11. Resumen Ejecutivo

| Aspecto | Estado |
|---------|--------|
| **Ubicación** | Línea 7440 de `server.py` |
| **Referencia MongoDB** | `db.servers.find_one({"id": request.server_id, "active": True})` |
| **Función reemplazo** | `get_server_connection_info(request.server_id, db=db)` |
| **¿Cambio simple?** | ⚠️ **PARCIAL** - Requiere fallback para `tipos_movimiento` |
| **Riesgo** | MEDIO (por dependencia a campo no migrado) |
| **Estrategia** | Migrar conexión + preservar fallback para `tipos_movimiento` |

---

**Reporte generado:** 14-Mayo-2026  
**Autor:** Agente E1 (Diagnóstico Pasivo)  
**Pendiente:** Autorización para FASE T3.4-B (implementación con fallback parcial)
