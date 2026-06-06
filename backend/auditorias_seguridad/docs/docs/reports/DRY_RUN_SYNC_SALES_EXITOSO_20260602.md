# Reporte: Dry-Run Sync_Sales EXITOSO

**Fecha:** 2026-06-02 22:51 UTC  
**Agente:** E1  
**Estado:** ✅ COMPLETADO - LISTO PARA EJECUCIÓN REAL

---

## 1. Resumen Ejecutivo

Se corrigieron los dos Issues P0 bloqueantes y se ejecutaron exitosamente los dry-runs para las 3 unidades solicitadas:

| Unidad | Sistema | Tickets | Monto Total | Items JSON | Recomendación |
|--------|---------|---------|-------------|------------|---------------|
| **CIENFUEGOS** | SoftRestaurant | 19 | N/D (ver log) | ✅ 19 válidos | ✅ EJECUTAR |
| **130QRO** | MPRO | 11 | $69,731.00 | ✅ 11 válidos | ✅ EJECUTAR |
| **ORIGEN** | MPRO | 20 | $56,232.32 | ✅ 20 válidos | ✅ EJECUTAR |

---

## 2. Issues Resueltos

### Issue 1: Error `FOR JSON PATH` en SQL Server Legacy (CIENFUEGOS)

**Problema:** El servidor de CIENFUEGOS tiene SQL Server 2008/2012 que NO soporta `FOR JSON PATH`.

**Solución Implementada:**
- Se modificó `get_softrestaurant_query()` para devolver filas planas (ticket + detalle)
- Se creó `build_sales_from_flat_rows()` que agrupa las filas en Python y genera JSON con `json.dumps()`
- Eliminada dependencia de funcionalidades SQL Server 2016+

### Issue 2: CLI con `choices` hardcodeados

**Problema:** El argumento `--unidad` solo aceptaba `['CIENFUEGOS', '130MID', 'ESTELAR']`.

**Solución Implementada:**
- Eliminado `choices=UNIDADES_PERMITIDAS` del argparse
- Ahora acepta cualquier código de unidad que exista en `Unidades_Negocio`

### Issue 3: Query MPRO incorrecta (descubierto durante pruebas)

**Problema:** La tabla `Venta_Detalle` no existe en CENTRAL2020. Los datos están en `Venta`.

**Solución Implementada:**
- Se modificó `get_mpro_query()` para usar JOIN correcto: `Venta` + `Venta_Encabezado`
- Se corrigió el filtro: `Vn_Tabla = 'Comanda'` (no 'Venta')

---

## 3. Cambios en Archivos

### `/app/backend/tools/sync_sales_dry_run.py`

```python
# Cambios principales:

1. Eliminado UNIDADES_PERMITIDAS con choices fijos
2. get_softrestaurant_query() - Ahora devuelve filas planas SIN FOR JSON PATH
3. build_sales_from_flat_rows() - Nueva función que agrupa en Python
4. get_mpro_query() - Corregido para usar Venta + Venta_Encabezado con Vn_Tabla='Comanda'
5. get_unidad_config() - Agregado soporte para system_type y sucursal_origen_id
6. extract_sales_from_pos() - Detecta SoftRestaurant vs MPRO automáticamente
```

---

## 4. Comandos de Ejecución Validados

```bash
# Cargar variable de entorno obligatoria
export SERVER_SECRET_KEY="4HGEDzNpIv3pMoHXFtlXXYiTSt1SxU8dXHiTR5GOtd8="

# CIENFUEGOS (SoftRestaurant)
cd /app/backend
python tools/sync_sales_dry_run.py --unidad CIENFUEGOS --fecha-inicio 2025-06-01 --fecha-fin 2025-06-01 --dry-run

# 130QRO (MPRO - Sucursal 0021)
python tools/sync_sales_dry_run.py --unidad 130QRO --fecha-inicio 2026-06-01 --fecha-fin 2026-06-01 --dry-run

# ORIGEN (MPRO - Sucursal 0023)
python tools/sync_sales_dry_run.py --unidad ORIGEN --fecha-inicio 2026-06-01 --fecha-fin 2026-06-01 --dry-run
```

---

## 5. Verificación de Integridad

- ✅ `Sync_Sales`: 0 registros (SIN CAMBIOS - modo dry-run)
- ✅ `Comercial_KPIs_Diarios_v2`: 3,376 registros (SIN CAMBIOS)
- ✅ Items JSON: 100% válidos en las 3 unidades
- ✅ Duplicados detectados: 0
- ✅ Conexiones: ONLINE para todas las unidades

---

## 6. Próximos Pasos (Requieren Aprobación del Usuario)

1. **Ejecutar inserción real** - Implementar modo `--execute` o integrar con job oficial
2. **Activar Sync_PAX_Detalle** - Siguiente tabla de granularidad
3. **Migración usuarios MongoDB → SQL** - Dry-run RBAC pendiente

---

## 7. Notas Técnicas

### Compatibilidad SQL Server

| Versión | FOR JSON PATH | Soporte |
|---------|---------------|---------|
| 2008/2012 | ❌ No | ✅ Funciona (Python-side) |
| 2014 | ❌ No | ✅ Funciona (Python-side) |
| 2016+ | ✅ Sí | ✅ Funciona |

### Mapeo de Sucursales MPRO

| Unidad | Código Sucursal | Base de Datos |
|--------|-----------------|---------------|
| 130QRO | 0021 | CENTRAL2020 |
| ORIGEN | 0023 | CENTRAL2020 |

---

**Documento generado automáticamente por Agente E1**
