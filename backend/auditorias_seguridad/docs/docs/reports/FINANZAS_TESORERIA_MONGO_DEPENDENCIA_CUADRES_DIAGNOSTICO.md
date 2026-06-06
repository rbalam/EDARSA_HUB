# DIAGNÓSTICO: Dependencia MongoDB en Tesorería Cuadres Z

**Fase:** FINANZAS-TESORERIA-MONGO-001  
**Fecha:** 2026-05-25  
**Estado:** DIAGNÓSTICO COMPLETADO  

---

## 1. DEPENDENCIAS MONGODB ENCONTRADAS

### 1.1 Archivo Principal
**Archivo:** `/app/backend/modules/finanzas/repository_cuadres_z.py`

```python
# Línea 18-21: Conexión MongoDB
from pymongo import MongoClient
mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')
db_name = os.environ.get('DB_NAME', 'edarsahub')
client = MongoClient(mongo_url)

# Línea 66: Colección MongoDB
self.collection_name = "tesoreria_cuadres_z"
```

### 1.2 Operaciones MongoDB
- `collection.insert_one()` - Crear cuadre
- `collection.find_one()` - Buscar cuadre
- `collection.find()` - Listar cuadres
- `collection.update_one()` - Actualizar cuadre
- `collection.delete_one()` - Eliminar cuadre
- `collection.aggregate()` - Resumen estadístico

---

## 2. ENDPOINTS AFECTADOS

| Endpoint | Método | Usa MongoDB | Archivo |
|----------|--------|-------------|---------|
| `/api/finanzas/tesoreria/cuadres` | GET | ✅ SÍ | tesoreria.py:228 |
| `/api/finanzas/tesoreria/cuadres` | POST | ✅ SÍ | tesoreria.py:315 |
| `/api/finanzas/tesoreria/cuadres/resumen` | GET | ✅ SÍ | tesoreria.py:271 |
| `/api/finanzas/tesoreria/cuadres/{id}` | GET | ✅ SÍ | tesoreria.py:341 |
| `/api/finanzas/tesoreria/cuadres/{id}` | PUT | ✅ SÍ | tesoreria.py:400 |
| `/api/finanzas/tesoreria/cuadres/{id}` | DELETE | ✅ SÍ | tesoreria.py:446 |
| `/api/finanzas/tesoreria/cuadres/{id}/validar` | POST | ✅ SÍ | tesoreria.py:521 |

---

## 3. FRONTEND AFECTADO

**Componente:** `/app/frontend/src/components/TesoreriaCorteZ.jsx`  
**Hook:** `/app/frontend/src/components/tesoreria/useTesoreriaCorteZData.js`

El frontend usa `server_id` para filtrar por unidad de negocio, pero el backend MongoDB esperaba `sucursal_id`.

---

## 4. ESTRUCTURA DE tesoreria_cuadres_z (MongoDB)

```javascript
{
  "_id": ObjectId,
  "corte_z": {
    "sucursal_id": "string",
    "sucursal_nombre": "string",
    "fecha_corte": "YYYY-MM-DD",
    "folio_corte": "string",
    "monto_a_depositar": Number,
    // ... otros campos del corte
  },
  "conteo_efectivo": {
    "billetes": {
      "b1000": Number,
      "b500": Number,
      // ...
    },
    "monedas": {
      "m20": Number,
      "m10": Number,
      // ...
    }
  },
  "ficha_deposito": {
    "url": "string",
    "fecha": "date",
    "monto": Number,
    "banco_id": Number
  },
  "estado": "PENDIENTE|EN_PROCESO|CUADRADO|DESCUADRE",
  "monto_esperado": Number,
  "monto_contado": Number,
  "monto_depositado": Number,
  "diferencia": Number,
  "created_at": "datetime",
  "updated_at": "datetime",
  "created_by": "string",
  "validated_by": "string"
}
```

---

## 5. TABLA SQL EQUIVALENTE EXISTENTE

**¡HALLAZGO CRÍTICO!** Ya existe la tabla `Finanzas_CuadresZ` en EDARSAHUB SQL con estructura completa.

### Estructura de Finanzas_CuadresZ

| Columna | Tipo | Descripción |
|---------|------|-------------|
| CuadreZID | bigint | PK, Identity |
| UnidadNegocioID | nvarchar(50) | ✅ Mapeo directo a server_id |
| UnidadNegocioNombre | nvarchar(100) | Nombre de la unidad |
| EmpresaID | nvarchar(50) | Empresa del grupo |
| ServerID | nvarchar(50) | ✅ server_id del frontend |
| SistemaOrigen | nvarchar(20) | SoftRestaurant/MPRO |
| FechaOperacion | date | Fecha de operación |
| FechaCorte | date | Fecha del corte |
| FolioCorte | nvarchar(50) | Folio del corte |
| TotalVenta | decimal | Total venta |
| TotalEfectivo | decimal | Total efectivo |
| TotalTarjeta* | decimal | Totales por forma de pago |
| TotalDepositar | decimal | Monto a depositar |
| ConteoEfectivo_* | int | Conteo desglosado |
| FichaDeposito* | varios | Datos de ficha |
| EstatusCuadreID | tinyint | FK a catálogo |
| EstatusTesoreriaID | tinyint | FK a catálogo |
| Observaciones | nvarchar(500) | Notas |
| UsuarioCaptura* | varios | Auditoría |
| Activo | bit | Flag activo |
| FechaAlta | datetime2 | Timestamp creación |

### Repositorio SQL Existente

**Archivo:** `/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py`

Este repositorio YA EXISTE y NO usa MongoDB. Implementa operaciones CRUD contra `Finanzas_CuadresZ`.

---

## 6. CAMBIOS YA REALIZADOS (PENDIENTES DE REVERTIR/REEMPLAZAR)

### 6.1 En tesoreria.py
Se agregaron cambios para soportar `server_id` **SOBRE MongoDB**:

```python
# Líneas 224-260: Agregado server_id a endpoint /cuadres
# Líneas 276-300: Agregado server_id a endpoint /cuadres/resumen
# PROBLEMA: Estos cambios amplían la dependencia MongoDB
```

### 6.2 En repository_cuadres_z.py (MongoDB)
Se agregaron filtros flexibles para `sucursal_id`:

```python
# Líneas 274-285: Matching regex case-insensitive en listar_cuadres
# Líneas 316-333: Filtro sucursal_id en obtener_resumen
# PROBLEMA: Amplía la lógica MongoDB en lugar de migrar a SQL
```

### 6.3 En useTesoreriaCorteZData.js (Frontend)
Se actualizó para usar `api.js` centralizado y pasar `server_id` a los endpoints.

---

## 7. PLAN DE MIGRACIÓN MongoDB → SQL

### Paso 1: Modificar imports en tesoreria.py
```python
# ANTES (MongoDB)
from .repository_cuadres_z import get_cuadres_repository

# DESPUÉS (SQL)
from .repository_cuadres_z_edarsahub import RepositoryCuadresZEdarsahub
```

### Paso 2: Actualizar endpoints para usar repositorio SQL
Los endpoints deben usar `RepositoryCuadresZEdarsahub` que ya trabaja con:
- `ServerID` (nvarchar) - Mapeo directo a `server_id` del frontend
- `UnidadNegocioID` - UUID de la unidad

### Paso 3: Mapeo server_id → SQL
```sql
-- El ServerID ya está en Finanzas_CuadresZ
-- No requiere resolución adicional, solo filtro directo:
SELECT * FROM Finanzas_CuadresZ WHERE ServerID = @server_id
```

### Paso 4: Migrar datos existentes de MongoDB
```python
# Script de migración (ejecutar una vez)
# 1. Leer todos los cuadres de MongoDB tesoreria_cuadres_z
# 2. Transformar al esquema de Finanzas_CuadresZ
# 3. Insertar en EDARSAHUB SQL
# 4. Validar integridad
# 5. Deshabilitar escritura en MongoDB
```

---

## 8. ESTRATEGIA server_id → sucursal_id USANDO SQL

**NO se requiere resolución compleja.** La tabla `Finanzas_CuadresZ` ya tiene:
- `ServerID` (nvarchar) - Coincide con el `server_id` del frontend
- `UnidadNegocioID` - ID de la unidad de negocio

El flujo correcto es:
```
Frontend (server_id) 
  → Backend (ServerID en WHERE) 
  → Finanzas_CuadresZ
```

Sin necesidad de JOINs a `Servidores_Conexiones` o `Sistema_SucursalServidorMapeo` para filtrar cuadres.

---

## 9. RIESGOS

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Datos existentes en MongoDB no migrados | Alto | Script de migración único |
| Frontend sigue enviando `server_id` | Bajo | Ya está soportado en SQL |
| Cambios recientes ampliaron MongoDB | Medio | Revertir y reemplazar |
| Downtime durante migración | Bajo | Migración puede ser incremental |

---

## 10. CAMBIOS A REVERTIR/REEMPLAZAR

### 10.1 NO continuar ampliando MongoDB
Los cambios del 2026-05-26 en `repository_cuadres_z.py` (regex para sucursal_id) deben:
- **NO ampliarse más**
- **Reemplazarse** con uso de `repository_cuadres_z_edarsahub.py`

### 10.2 Actualizar tesoreria.py
Reemplazar:
```python
from .repository_cuadres_z import get_cuadres_repository
```
Por:
```python
from .repository_cuadres_z_edarsahub import RepositoryCuadresZEdarsahub
```

---

## 11. CONFIRMACIONES

- [x] Se identificó exactamente cómo Finanzas/Tesorería usa MongoDB
- [x] Se identificó tabla SQL equivalente: `Finanzas_CuadresZ`
- [x] Se identificó repositorio SQL existente: `repository_cuadres_z_edarsahub.py`
- [x] Se definió estrategia server_id → SQL (directo, sin resolución)
- [x] Se documentaron cambios ya hechos que amplían MongoDB
- [x] Se confirma NO continuar ampliando dependencia MongoDB

---

## 12. RECOMENDACIÓN FASE SIGUIENTE

### FINANZAS-TESORERIA-MONGO-002 (Migración)

1. **Crear script de migración** MongoDB → SQL para cuadres existentes
2. **Modificar tesoreria.py** para usar `repository_cuadres_z_edarsahub.py`
3. **Validar endpoints** con servidor SQL
4. **Desactivar escritura** en MongoDB para cuadres
5. **Mantener lectura MongoDB** como fallback temporal (solo lectura, con warning)
6. **Eliminar fallback MongoDB** después de validación en producción

### NO AUTORIZADO en fase actual:
- Ejecutar migración de datos
- Modificar endpoints de producción
- Eliminar colección MongoDB

---

## CONCLUSIÓN

**La dependencia MongoDB en Tesorería Cuadres es REMEDIABLE.**

Ya existe la infraestructura SQL completa:
- Tabla `Finanzas_CuadresZ` con todos los campos necesarios
- Repositorio `repository_cuadres_z_edarsahub.py` funcional
- Catálogos `Finanzas_Cat_EstatusCuadreZ` y `Finanzas_Cat_EstatusTesoreria`

Solo requiere:
1. Cambiar import en `tesoreria.py`
2. Migrar datos existentes (script único)
3. Validar y deprecar MongoDB

**Los cambios realizados el 2026-05-26 sobre MongoDB deben PAUSARSE y no continuarse.**
