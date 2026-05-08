# DIAGNÓSTICO: SUCURSALES MPRO EN FINANZAS

**Fecha**: 2025-12-28
**Objetivo**: Validar si las sucursales MPRO (ORIGEN y 130° QRO) están correctamente configuradas y visibles en el módulo de Finanzas.

---

## TABLA RESUMEN DE DIAGNÓSTICO

| Revisión | Resultado |
|---|---|
| Server ID ManagementPro | `1b230a06-ffaf-4c70-bd27-b1be3579dea6` |
| Sucursales EDARSAHUB asociadas | ORIGEN, 130° QUERETARO (2 sucursales) |
| ORIGEN existe | ✅ Sí |
| 130° QRO existe | ✅ Sí |
| Código ORIGEN | `0023` |
| Código 130° QRO | `0021` |
| Activas | ✅ Sí (ambas `activo=True`) |
| Autorizadas para usuario admin | ✅ Sí (aparecen en `/api/unidades-negocio`) |
| Aparecen en Comercial | ✅ Sí (API MPRO Local responde 200) |
| **Aparecen en Finanzas** | ❌ **NO** |
| Diferencia detectada | **MPRO nunca se consulta - SoftRestaurant tiene prioridad** |
| Causa probable | **BACKEND FINANZAS TIENE LÓGICA "PRIMERO SR, FALLBACK MPRO"** |
| Acción recomendada | **Cambiar lógica a "COMBINAR SR + MPRO" en lugar de fallback** |

---

## DATOS VERIFICADOS EN CENTRAL2020 (MPRO)

| Sucursal | ID | Facturas CxP | Saldo Total |
|----------|-----|--------------|-------------|
| **ORIGEN** | 0023 | 1,073 | $11,501,659.82 |
| **130° QUERETARO** | 0021 | 524 | $8,984,825.24 |
| 130° TULUM | 0012 | 263 | $5,752,992.93 |
| MECA | 0026 | 87 | $3,926,417.14 |
| CIEN FUEGOS | 0027 | 4 | $86,865.34 |

**TOTAL MPRO DISPONIBLE**: ~$30M en CxP (solo para las primeras 5 sucursales)

---

## 1. DATOS EN EDARSAHUB (Unidades_Negocio)

```
ID: 23ca0b76-6580-4874-ba9b-672b122ca197
Nombre: ORIGEN
Código: ORIGEN
Server ID: 1b230a06-ffaf-4c70-bd27-b1be3579dea6 (ManagementPro)
Sucursal Origen ID: 0023
System Type: MPRO
Activo: True

ID: 9bc05ced-6b2b-4a0a-aa90-ce649b78e12c
Nombre: 130° QUERETARO
Código: 130QRO
Server ID: 1b230a06-ffaf-4c70-bd27-b1be3579dea6 (ManagementPro)
Sucursal Origen ID: 0021
System Type: MPRO
Activo: True
```

---

## 2. ENDPOINT `/api/unidades-negocio`

**Estado**: ✅ OK

El endpoint devuelve las 5 unidades correctamente:
- 130 MID (SoftRestaurant)
- **130 QRO (MPRO)** ✅
- CIENFUEGOS (SoftRestaurant)
- LA ESTELAR (SoftRestaurant)
- **ORIGEN (MPRO)** ✅

---

## 3. SUBMÓDULOS DE FINANZAS Y SOPORTE MPRO

| Submódulo | ¿Soporta MPRO? | Estado | Observaciones |
|-----------|---------------|--------|---------------|
| Dashboard | ❓ | NO VERIFICADO | Depende de KPIs |
| CxP Listado | ✅ Código soporta | ⚠️ **NO RETORNA DATOS MPRO** | `mpro_repo` configurado pero sin resultados |
| CxP Resumen | ✅ Código soporta | ⚠️ Fuente dice `SOFTRESTAURANT_REAL` | Solo muestra SR |
| Control Ingresos | ❌ | N/A | Solo SoftRestaurant (cortes Z) |
| Tesorería | ❌ | N/A | Solo SoftRestaurant (cortes Z) |
| Propinas TPV | ❌ | N/A | Solo SoftRestaurant (cheques.propinatarjeta) |
| Presupuestos | ❓ | NO VERIFICADO | Depende de tabla EDARSAHUB |

---

## 4. ANÁLISIS DE CÓDIGO CxP

### Backend `cuentas_por_pagar.py`

**Línea 320-325**:
```python
if mpro_repo and not es_filtro_softrest:
    # Si se filtra por sucursal MPRO específica, usar ese filtro
    mpro_sucursal = sucursal_id if sucursal_id and sucursal_id not in softrest_sucursales else None
    
    cxp_mpro = await mpro_repo.get_cuentas_por_pagar(
        sucursal_id=mpro_sucursal,
        ...
    )
```

**Hallazgo**: El código SÍ intenta consultar MPRO si:
1. `mpro_repo` está configurado (✅ Se configura en `server.py` línea 339-340)
2. El filtro NO es para una sucursal SoftRestaurant

**Problema potencial**: La query a MPRO puede estar retornando vacío o fallando silenciosamente.

### Repositorio MPRO (`repository_mpro.py`)

**Línea 62-74**: Usa `execute_sql_query()` directo (no subprocess)
```python
results = execute_sql_query(
    host=server['host'],
    port=server['port'],
    database=server['database'],
    username=server['username'],
    password=server['password'],
    query=query,
    timeout_seconds=timeout
)
```

**Hallazgo**: El repositorio MPRO usa `execute_sql_query()` directamente, NO el subprocess con encoding fix. Esto podría causar fallos silenciosos si hay caracteres especiales.

---

## 5. HIPÓTESIS DEL PROBLEMA

1. **Más probable**: El repositorio MPRO consulta CENTRAL2020 exitosamente pero la tabla `Cuenta_X_Pagar` puede:
   - No tener registros con `Cxp_Precio_Neto_Saldo > 0`
   - No tener sucursales ORIGEN (0023) o 130 QRO (0021)

2. **Alternativa**: Error de encoding silencioso en la conexión MPRO (no usa subprocess)

---

## 6. PRUEBAS PENDIENTES

1. [ ] Verificar si `Cuenta_X_Pagar` en CENTRAL2020 tiene datos para sucursales 0021 y 0023
2. [ ] Verificar si el repositorio MPRO está retornando datos (agregar logging)
3. [ ] Comparar query MPRO con datos reales en CENTRAL2020

---

## 7. SUBMÓDULOS QUE NO APLICAN A MPRO

Los siguientes submódulos de Finanzas operan sobre tablas específicas de SoftRestaurant y NO tienen equivalente en MPRO:

| Submódulo | Razón |
|-----------|-------|
| Control de Ingresos | Usa tabla `movtoscaja` (Cortes Z de SoftRestaurant) |
| Tesorería / Cuadre Z | Usa tabla `movtoscajadetalles` (SoftRestaurant) |
| Propinas TPV | Usa `cheques.propinatarjeta` (SoftRestaurant) |

Estos submódulos **NO deben incluir MPRO** en sus filtros porque la fuente de datos es exclusiva de SoftRestaurant.

---

## 8. CAUSA RAÍZ IDENTIFICADA

El problema NO es de configuración de sucursales. **Las sucursales MPRO (ORIGEN y 130° QRO) están correctamente configuradas en EDARSAHUB y tienen datos CxP reales**.

El problema está en la **LÓGICA DE NEGOCIO** del módulo CxP:

### Lógica actual (incorrecta):
```
1. Intentar SoftRestaurant
2. SI SoftRestaurant retorna datos → TERMINAR (no consultar MPRO)
3. SI SoftRestaurant falla → Fallback a MPRO
```

### Lógica correcta (requerida):
```
1. Consultar SoftRestaurant
2. Consultar MPRO
3. COMBINAR ambos resultados
4. Etiquetar fuente de cada factura (SR o MPRO)
```

### Archivos a modificar:
1. `/app/backend/modules/finanzas/cuentas_por_pagar.py`:
   - Función `get_resumen_cuentas_por_pagar()` línea 743-810
   - Función `listar_facturas_pendientes()` línea 224 (ya intenta combinar pero tiene bugs)
   - Función `listar_sucursales_cxp()` línea 921-990

---

## 9. ACCIÓN RECOMENDADA

**PRIORIDAD P0**: Modificar endpoint `/resumen` para combinar SR + MPRO en lugar de fallback.

**PRIORIDAD P1**: Modificar endpoint raíz (`/cuentas-por-pagar`) para asegurar que MPRO siempre se consulte.

**PRIORIDAD P2**: Modificar endpoint `/sucursales` para listar TODAS las sucursales (SR + MPRO).

**NO MODIFICAR**: Submódulos que no aplican a MPRO (Control Ingresos, Tesorería, Propinas TPV).

---

*Generado automáticamente por E1 Agent - 2025-12-28*
*Actualizado con causa raíz identificada*

---

## ACTUALIZACIÓN: CORRECCIÓN IMPLEMENTADA (2025-12-28)

### Estado: ✅ RESUELTO

La corrección **FINANZAS-CXP-MPRO-COMBINE-01** fue implementada exitosamente.

### Cambios realizados:
1. Endpoint `/resumen` ahora combina SR + MPRO (no fallback)
2. Endpoint `/sucursales` ahora lista SR + MPRO
3. Repositorio MPRO migrado a subprocess (evita encoding issues)
4. Contraseña del servidor MPRO ahora se descifra correctamente

### Validaciones pasadas:
| Sucursal | Facturas | Saldo |
|----------|----------|-------|
| ORIGEN | 1,073 | $11,501,659.82 ✅ |
| 130° QRO | 524 | $8,984,825.24 ✅ |
| CIENFUEGOS | 369 | $6,791,664.14 ✅ |

### Reporte completo:
Ver `/app/docs/FINANZAS_CXP_MPRO_COMBINE_01_REPORT.md`

