# FASE T3.4-B1 — Diagnóstico y Diseño de Migración de `tipos_movimiento` a EDARSAHUB

**Fecha:** 14-Mayo-2026  
**Estado:** DISEÑO COMPLETADO  
**Autorización:** Pendiente para DDL y migración de datos

---

## 1. Estructura Real de `tipos_movimiento` en MongoDB

### 1.1 Tipo de Dato
- **Tipo:** `list` (array de strings)
- **Elementos:** Códigos de 2-5 caracteres alfanuméricos
- **Almacenamiento actual:** Campo JSON array dentro del documento `servers`

### 1.2 Ejemplos Reales por Servidor/Unidad

| Unidad (Código Canónico) | server_id | system_type | Total Tipos | Entradas | Salidas |
|--------------------------|-----------|-------------|-------------|----------|---------|
| **CIENFUEGOS** | 6d053c22-... | SoftRestaurant | 22 | 12 (E*) | 10 (S*) |
| **ESTELAR** | a5ff0e25-... | SoftRestaurant | 19 | 9 (E*) | 10 (S*) |
| **130MID** | a5547321-... | SoftRestaurant | 18 | 10 (E*) | 8 (S*) |
| **MPRO** | 1b230a06-... | MPRO | 35 | 17 (0xx/1xx) | 14 (4xx/5xx) |

### 1.3 Valores Detallados por Unidad

#### CIENFUEGOS (SoftRestaurant)
```
Entradas: ['EAL', 'ECA', 'ECS', 'ECO', 'EDE', 'EEH', 'EPB', 'EPC', 'EPL', 'EPR', 'ETA', 'ETR']
Salidas:  ['SCP', 'SCS', 'SDE', 'SDV', 'SPC', 'SPM', 'SPR', 'SPV', 'STA', 'STR']
```

#### ESTELAR (SoftRestaurant)
```
Entradas: ['ECA', 'ECS', 'ECI', 'EDA', 'EPC', 'EPD', 'EPP', 'EPT', 'ETA']
Salidas:  ['SCS', 'SCP', 'SDA', 'SDV', 'SPC', 'SPM', 'SPD', 'SPP', 'SPT', 'STA']
```

#### 130MID (SoftRestaurant)
```
Entradas: ['ECA', 'EDE', 'EIE', 'EPA', 'EPB', 'EPC', 'EPCON', 'EPL', 'ETA', 'ETB']
Salidas:  ['SCP', 'SDE', 'SIE', 'SPC', 'SPD', 'SPM', 'STA', 'STB']
```

#### MPRO (ManagementPro)
```
Entradas (0xx/1xx): ['050', '051', '052', '053', '060', '061', '100', '101', '104', '105', '106', '107', '108', '112', '113', '114', '115']
Salidas (4xx/5xx):  ['400', '401', '500', '501', '506', '507', '508', '509', '510', '511', '512', '513', '514', '515']
Otros (2xx/9xx):    ['202', '203', '942', '943']
```

---

## 2. Uso Exacto en `auditoria-operativa`

### 2.1 Campos Leídos
```python
tipos_mov_activos = server.get('tipos_movimiento', [])
```

### 2.2 Lógica de Clasificación (líneas 7679-7687)
```python
# SoftRestaurant: Códigos empiezan con E (entrada) o S (salida)
tipos_entrada_activos = [t for t in tipos_mov_activos if t.startswith('E')]
tipos_salida_activos = [t for t in tipos_mov_activos if t.startswith('S')]

# Subtipos específicos
tipos_entrada_compra = [t for t in tipos_entrada_activos if t in ['EPC', 'ECS', 'EPB', 'EDE', 'EEH', 'ECO', 'ECA', 'EPL', 'EPR']]
tipos_entrada_traspaso = [t for t in tipos_entrada_activos if t in ['ETR', 'ETA', 'EAL']]
tipos_salida_traspaso = [t for t in tipos_salida_activos if t in ['STR', 'STA', 'SAL']]
```

### 2.3 Uso en Queries SQL
Los tipos filtrados se usan en cláusulas `WHERE ... IN (...)` para:
- Calcular movimientos de entrada (compras)
- Calcular traspasos entrada/salida
- Determinar consumos del período

### 2.4 Aplica Solo a SoftRestaurant
El código verifica:
```python
if is_softrestaurant_system(server.get('system_type')):
    # Usa tipos_movimiento
```
**MPRO no usa `tipos_movimiento` en la misma lógica** (usa queries diferentes).

---

## 3. Tablas EDARSAHUB Existentes Revisadas

### 3.1 Tablas Actuales Relacionadas
- `Servidores_Conexiones` — Datos de conexión de servidores
- `Unidades_Negocio` — Catálogo de unidades con código canónico
- `Comercial_KPIs_Diarios_v2` — KPIs comerciales
- `Finanzas_KPIs_Historico` — KPIs financieros

### 3.2 Campos JSON Existentes en `Servidores_Conexiones`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `sucursales` | NVARCHAR(MAX) | JSON array de sucursales |
| `categorias` | NVARCHAR(MAX) | JSON array de categorías |
| `departamentos` | NVARCHAR(MAX) | JSON array de departamentos |
| `query_ventas` | NVARCHAR(MAX) | JSON de query personalizada |
| `query_inventario` | NVARCHAR(MAX) | JSON de query personalizada |
| `query_movimientos` | NVARCHAR(MAX) | JSON de query personalizada |

**NOTA:** Ya existe el patrón de almacenar arrays JSON en `Servidores_Conexiones`.

---

## 4. Recomendación de Diseño

### 4.1 Opciones Evaluadas

| Opción | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| **A** | Campo JSON en `Servidores_Conexiones` | Consistente con patrón existente, sin nueva tabla | Todos los campos quedan en una tabla |
| **B** | Tabla hija `Servidores_TiposMovimiento` | Normalización, consultas más rápidas | Nueva tabla, más complejidad |
| **C** | Tabla catálogo por unidad | Flexibilidad | Duplica concepto de servidor |
| **D** | Tabla específica de Compras | Separación de concerns | Desacopla de servidor |

### 4.2 RECOMENDACIÓN: OPCIÓN A — Campo JSON en `Servidores_Conexiones`

**Justificación:**
1. **Consistencia:** Ya existen 6 campos JSON en `Servidores_Conexiones` (sucursales, categorias, departamentos, queries)
2. **Simplicidad:** No requiere nueva tabla ni foreign keys adicionales
3. **Patrón probado:** El código en `server_registry.py` ya parsea campos JSON
4. **Mínimo cambio:** Solo agregar columna `tipos_movimiento`
5. **Migración simple:** UPDATE directo desde MongoDB

---

## 5. DDL Propuesto (NO EJECUTAR)

### 5.1 Agregar Columna a `Servidores_Conexiones`

```sql
-- ============================================================================
-- FASE T3.4-B1: Agregar campo tipos_movimiento a Servidores_Conexiones
-- Autor: Agente E1
-- Fecha: 14-Mayo-2026
-- Estado: PENDIENTE AUTORIZACIÓN
-- ============================================================================

-- PASO 1: Agregar columna
ALTER TABLE Servidores_Conexiones
ADD tipos_movimiento NVARCHAR(MAX) NULL;

-- PASO 2: Comentario descriptivo (opcional, depende del motor)
-- COMMENT ON COLUMN Servidores_Conexiones.tipos_movimiento IS 
--   'JSON array de códigos de tipos de movimiento activos para auditoría. Ej: ["EPC","ECS","STR"]';

-- PASO 3: Verificar estructura
SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Servidores_Conexiones'
  AND COLUMN_NAME = 'tipos_movimiento';
```

### 5.2 Índice (Opcional)
```sql
-- Índice para búsquedas por tipos_movimiento (opcional, solo si hay consultas por este campo)
-- No recomendado inicialmente porque el campo se lee con el servidor completo
```

---

## 6. Script de Migración de Datos (NO EJECUTAR)

### 6.1 Extracción desde MongoDB
```python
"""
Script de migración: MongoDB → EDARSAHUB
FASE T3.4-B1
Estado: PENDIENTE AUTORIZACIÓN
"""
import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
import pymssql
import os

async def migrate_tipos_movimiento():
    """
    Migra tipos_movimiento de MongoDB a EDARSAHUB.
    SOLO EJECUTAR CON AUTORIZACIÓN EXPLÍCITA.
    """
    # Conexiones
    mongo_client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    mongo_db = mongo_client.edarsa_hub
    
    sql_conn = pymssql.connect(
        server='<REDACTED_EDARSAHUB_SQL_HOST>',
        user='<USER_ESCRITURA>',  # Requiere usuario con permisos UPDATE
        password='<PASSWORD>',
        database='EDARSAHUB'
    )
    sql_cursor = sql_conn.cursor()
    
    # Obtener servidores con tipos_movimiento de MongoDB
    servers = await mongo_db.servers.find(
        {"tipos_movimiento": {"$exists": True, "$ne": []}},
        {"id": 1, "tipos_movimiento": 1, "_id": 0}
    ).to_list(100)
    
    print(f"Servidores a migrar: {len(servers)}")
    
    # Backup previo (SELECT INTO)
    sql_cursor.execute("""
        SELECT id, nombre, tipos_movimiento
        INTO Servidores_Conexiones_Backup_TiposMov_20260514
        FROM Servidores_Conexiones
    """)
    sql_conn.commit()
    print("Backup creado: Servidores_Conexiones_Backup_TiposMov_20260514")
    
    # Migrar cada servidor
    migrated = 0
    errors = []
    
    for srv in servers:
        server_id = srv['id']
        tipos_json = json.dumps(srv['tipos_movimiento'])
        
        try:
            # UPDATE con tipos_movimiento
            sql_cursor.execute("""
                UPDATE Servidores_Conexiones
                SET tipos_movimiento = %s,
                    updated_at = GETDATE()
                WHERE CAST(id AS VARCHAR(50)) = %s
                   OR mongodb_id = %s
            """, (tipos_json, server_id, server_id))
            
            if sql_cursor.rowcount > 0:
                migrated += 1
                print(f"  ✓ Migrado: {server_id}")
            else:
                errors.append(f"No encontrado en SQL: {server_id}")
                
        except Exception as e:
            errors.append(f"Error {server_id}: {str(e)}")
    
    sql_conn.commit()
    
    print(f"\n=== RESULTADO ===")
    print(f"Migrados: {migrated}")
    print(f"Errores: {len(errors)}")
    for err in errors:
        print(f"  - {err}")
    
    mongo_client.close()
    sql_conn.close()

# NO EJECUTAR SIN AUTORIZACIÓN
# asyncio.run(migrate_tipos_movimiento())
```

### 6.2 SQL Directo (Alternativa)
```sql
-- ============================================================================
-- MIGRACIÓN DE DATOS: tipos_movimiento
-- SOLO EJECUTAR CON AUTORIZACIÓN
-- ============================================================================

-- Los valores deben extraerse de MongoDB primero y ejecutarse como UPDATEs:

BEGIN TRANSACTION;

-- Backup
SELECT id, nombre, tipos_movimiento
INTO Servidores_Conexiones_Backup_TiposMov_20260514
FROM Servidores_Conexiones;

-- CIENFUEGOS
UPDATE Servidores_Conexiones
SET tipos_movimiento = '["EAL","ECA","ECS","ECO","EDE","EEH","EPB","EPC","EPL","EPR","ETA","ETR","SCP","SCS","SDE","SDV","SPC","SPM","SPR","SPV","STA","STR"]',
    updated_at = GETDATE()
WHERE mongodb_id = '6d053c22-523e-48c0-b72b-96081e2d781b';

-- ESTELAR
UPDATE Servidores_Conexiones
SET tipos_movimiento = '["ECA","ECS","ECI","EDA","EPC","EPD","EPP","EPT","ETA","SCS","SCP","SDA","SDV","SPC","SPM","SPD","SPP","SPT","STA"]',
    updated_at = GETDATE()
WHERE mongodb_id = 'a5ff0e25-f029-43db-b634-d4ac814c904f';

-- 130MID (130° MERIDA)
UPDATE Servidores_Conexiones
SET tipos_movimiento = '["ECA","EDE","EIE","EPA","EPB","EPC","EPCON","EPL","ETA","ETB","SCP","SDE","SIE","SPC","SPD","SPM","STA","STB"]',
    updated_at = GETDATE()
WHERE mongodb_id = 'a5547321-1139-4d2b-9d53-182ca737b6b6';

-- MPRO (ManagementPro)
UPDATE Servidores_Conexiones
SET tipos_movimiento = '["050","051","052","053","060","061","100","101","104","105","106","107","108","112","113","114","115","202","203","400","401","500","501","506","507","508","509","510","511","512","513","514","515","942","943"]',
    updated_at = GETDATE()
WHERE mongodb_id = '1b230a06-ffaf-4c70-bd27-b1be3579dea6';

-- Verificar antes de COMMIT
SELECT id, nombre, tipos_movimiento
FROM Servidores_Conexiones
WHERE tipos_movimiento IS NOT NULL;

-- SOLO EJECUTAR SI LOS DATOS SON CORRECTOS
-- COMMIT TRANSACTION;
-- En caso de error:
-- ROLLBACK TRANSACTION;
```

---

## 7. Modificación a `server_registry.py` (Post-Migración)

### 7.1 Actualizar `_sql_row_to_server_dict`
```python
# En /app/backend/core/server_registry.py, función _sql_row_to_server_dict:
# Agregar después de 'query_movimientos':

'tipos_movimiento': _parse_json_field(row.get('tipos_movimiento')),
```

### 7.2 Actualizar `get_server_connection_info`
```python
# En la función get_server_connection_info, agregar al return:
'tipos_movimiento': server.get('tipos_movimiento', []),
```

---

## 8. Plan de Modificación de `auditoria-operativa` (Post-Migración)

### 8.1 Cambio Propuesto
```python
# ANTES (MongoDB):
server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))

# DESPUÉS (EDARSAHUB via server_registry):
from core.server_registry import get_server_connection_info
server = await get_server_connection_info(request.server_id, db=db)
```

**Nota:** Una vez que `tipos_movimiento` esté en SQL y `server_registry` lo devuelva, el cambio es idéntico a los endpoints ya migrados en T3.1-T3.3.

---

## 9. Plan de Validación

### 9.1 Conteos Antes/Después
| Métrica | MongoDB | SQL (Post-Migración) |
|---------|---------|----------------------|
| Servidores con tipos_movimiento | 4 | 4 |
| Total tipos CIENFUEGOS | 22 | 22 |
| Total tipos ESTELAR | 19 | 19 |
| Total tipos 130MID | 18 | 18 |
| Total tipos MPRO | 35 | 35 |

### 9.2 Pruebas de Endpoint
```bash
# Pre-migración: Registrar baseline
curl -X POST /api/compras/auditoria-operativa \
  -d '{"server_id":"a5547321-...", "sucursal":"130", ...}' \
  > baseline_auditoria.json

# Post-migración: Comparar
curl -X POST /api/compras/auditoria-operativa \
  -d '{"server_id":"a5547321-...", "sucursal":"130", ...}' \
  > postmigration_auditoria.json

# Validar
diff baseline_auditoria.json postmigration_auditoria.json
```

### 9.3 No Regresión
- [ ] Finanzas: `/api/finanzas/tesoreria/sucursales` HTTP 200
- [ ] Tablero Ejecutivo: `/api/v2/comercial/dashboard` HTTP 200
- [ ] Inventarios Físicos: `/api/compras/inventarios-fisicos` HTTP 200
- [ ] Endpoints T3.1-T3.3: Sin cambios

---

## 10. Confirmación de No Modificación

- ✅ **NO se modificó** `/app/backend/server.py`
- ✅ **NO se modificó** `/app/backend/core/server_registry.py`
- ✅ **NO se ejecutó** ningún DDL en EDARSAHUB
- ✅ **NO se ejecutó** ningún INSERT/UPDATE
- ✅ **NO se tocó** MongoDB (solo lectura para diagnóstico)
- ✅ Diagnóstico 100% pasivo

---

## 11. Fases de Implementación Propuestas

| Subfase | Acción | Autorización |
|---------|--------|--------------|
| T3.4-B2 | Ejecutar DDL: `ALTER TABLE ... ADD tipos_movimiento` | ⏸️ PENDIENTE |
| T3.4-B3 | Ejecutar migración de datos MongoDB → SQL | ⏸️ PENDIENTE |
| T3.4-B4 | Actualizar `server_registry.py` para devolver `tipos_movimiento` | ⏸️ PENDIENTE |
| T3.4-B5 | Modificar `auditoria-operativa` para usar `server_registry` | ⏸️ PENDIENTE |
| T3.4-B6 | Validación y pruebas | ⏸️ PENDIENTE |

---

**Reporte generado:** 14-Mayo-2026  
**Autor:** Agente E1 (Diagnóstico Pasivo)  
**Pendiente:** Autorización para FASE T3.4-B2 (DDL)
