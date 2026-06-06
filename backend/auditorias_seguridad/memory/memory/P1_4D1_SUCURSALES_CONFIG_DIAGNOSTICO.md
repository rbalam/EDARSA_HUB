# P1.4-D1: DIAGNÓSTICO SUCURSALES-CONFIG

**Fecha:** 14-Dic-2025  
**Estado:** ✅ OBJETIVO CUMPLIDO (db.servers ya no se usa)  
**Autorizado por:** Usuario (Mensaje 14-Dic-2025)

---

## 1. RESUMEN

El objetivo de P1.4-D1 era "eliminar uso funcional de MongoDB `db.servers` en el endpoint de configuración de sucursales".

**HALLAZGO:** Los endpoints de `/servers/{id}/sucursales-config` **YA NO USAN `db.servers`**. Fueron migrados en una fase anterior (CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 2).

---

## 2. ESTADO ACTUAL DE LOS ENDPOINTS

| Endpoint | Usa `db.servers`? | Usa `server_registry`? | Usa otra colección MongoDB? |
|----------|------------------|------------------------|---------------------------|
| `GET /servers/{id}/sucursales-config` | ❌ NO | ✅ `get_server_connection_info()` | ✅ `db.server_sucursales_config` |
| `POST /servers/{id}/sucursales-config/sync` | ❌ NO | ✅ `get_server_connection_info()` | ✅ `db.server_sucursales_config` |
| `PUT /servers/{id}/sucursales-config/{suc_id}` | ❌ NO | ❌ (no necesita servidor) | ✅ `db.server_sucursales_config` |
| `PUT /servers/{id}/sucursales-config/bulk` | ❌ NO | ❌ (no necesita servidor) | ✅ `db.server_sucursales_config` |

---

## 3. COLECCIÓN `db.server_sucursales_config`

Esta colección MongoDB es **independiente de `db.servers`** y almacena la configuración de visibilidad de sucursales en UI:

```json
{
  "server_id": "uuid-del-servidor",
  "sucursal_origen_id": "0021",
  "sucursal_nombre_origen": "130° QUERETARO",
  "nombre_visible": "130QRO",
  "visible_en_operaciones": true,
  "activa": true,
  "orden": 1,
  "fecha_creacion": "2025-12-01T00:00:00Z",
  "usuario_creacion": "admin@inventario.com"
}
```

### Propósito

Permite configurar desde UI qué sucursales de un servidor MPRO/SoftRestaurant son visibles en dashboards operativos, sin modificar `Unidades_Negocio`.

---

## 4. MIGRACIÓN A EDARSAHUB (FUERA DE ALCANCE P1.4-D1)

Migrar `db.server_sucursales_config` a EDARSAHUB requeriría:

### DDL Propuesto (NO AUTORIZADO)

```sql
CREATE TABLE dbo.Config_Sucursales_Visibilidad (
    id INT IDENTITY(1,1) PRIMARY KEY,
    server_id VARCHAR(50) NOT NULL,
    sucursal_origen_id VARCHAR(50) NOT NULL,
    sucursal_nombre_origen NVARCHAR(200),
    nombre_visible NVARCHAR(200),
    visible_en_operaciones BIT DEFAULT 1,
    activa BIT DEFAULT 1,
    orden INT DEFAULT 0,
    fecha_creacion DATETIME2 DEFAULT GETUTCDATE(),
    fecha_modificacion DATETIME2,
    usuario_creacion VARCHAR(100),
    usuario_modificacion VARCHAR(100),
    CONSTRAINT UQ_Config_Sucursales_Server_Suc UNIQUE(server_id, sucursal_origen_id)
);
```

### Archivos a Modificar

1. `server.py` - 4 endpoints
2. Posiblemente `server_registry.py` - nuevas funciones

**ESTADO:** NO AUTORIZADO - Requiere propuesta formal y DDL aprobado.

---

## 5. CONCLUSIÓN

| Objetivo P1.4-D1 | Estado |
|------------------|--------|
| Eliminar `db.servers` de sucursales-config | ✅ YA CUMPLIDO (migrado previamente) |
| Migrar `db.server_sucursales_config` a SQL | ❌ FUERA DE ALCANCE |

---

## 6. PRÓXIMOS PASOS RECOMENDADOS

1. **Cerrar P1.4-D1** como cumplido (objetivo original logrado).
2. **Crear nueva fase P1.4-D2** si se desea migrar `db.server_sucursales_config` a EDARSAHUB.
3. Continuar con **P1.4-E** (Auditorías) que sí tiene referencias activas a `db.servers`.

---

## 7. GREP DE VALIDACIÓN

```bash
$ grep -n "db\.servers\." server.py | grep -E "2313|2348|2455|2492"
(vacío - no hay referencias a db.servers en estos endpoints)
```

✅ Confirmado: Los endpoints de sucursales-config no usan `db.servers`.

---

**CIERRE:** P1.4-D1 cumplido. La eliminación de `db.servers` en sucursales-config ya fue realizada en una migración anterior.

*Documento generado bajo régimen de Autorización Controlada.*
