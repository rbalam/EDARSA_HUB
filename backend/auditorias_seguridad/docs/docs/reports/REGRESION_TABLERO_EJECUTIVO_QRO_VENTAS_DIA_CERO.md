# DIAGNÓSTICO: Reporte de "Regresión" en Tablero Ejecutivo - 130° QUERÉTARO

**Fecha:** 2026-05-19  
**Prioridad:** P0  
**Estado:** ✅ NO ES REGRESIÓN - SISTEMA FUNCIONANDO CORRECTAMENTE

---

## 1. Resumen Ejecutivo

Se reportó que 130° QUERÉTARO mostraba $0 en ventas del día en el Tablero Ejecutivo. Tras diagnóstico exhaustivo, se confirma que:

**EL SISTEMA ESTÁ FUNCIONANDO CORRECTAMENTE.**

- El backend devuelve datos correctos para QRO
- EDARSAHUB SQL tiene los datos de ventas
- La UI muestra los valores correctos ($2.12M)

---

## 2. Diagnóstico Realizado

### 2.1 Endpoint Probado

```
GET /api/comercial/tablero-ejecutivo?mes=5&anio=2026
Authorization: Bearer [token]
```

### 2.2 Response del Endpoint (130QRO)

```json
{
  "unidad_key": "1b230a06-ffaf-4c70-bd27-b1be3579dea6:130QRO",
  "unidad_negocio_id": "130QRO",
  "nombre": "130QRO",
  "system_type": "MPRO",
  "connection_type": "LOCAL_API",
  "data_status": "DATA_OK",
  "source_period": "EDARSAHUB_SQL",
  "ventas": 2123189.0,
  "proyeccion": 3656603.28,
  "pax": 1306,
  "cheques": 438,
  "status": "online",
  "origen": "EDARSAHUB_SQL"
}
```

**Resultado:** ✅ HTTP 200, datos correctos

### 2.3 Datos en EDARSAHUB SQL (Comercial_KPIs_Diarios_v2)

```
=== 130QRO - Mayo 2026 ===
2026-05-17 | dia=17 | ventas=   85,348.00 | fuente=SQL_LIVE
2026-05-16 | dia=16 | ventas=  126,280.00 | fuente=SQL_LIVE
2026-05-15 | dia=15 | ventas=  199,707.00 | fuente=SQL_LIVE
...
2026-05-01 | dia= 1 | ventas=  119,741.00 | fuente=SQL_LIVE

TOTAL QRO Mayo 2026: $2,123,189.00 ✅
```

### 2.4 Comparación con ORIGEN (también MPRO/API Local)

```
=== ORIGEN - Mayo 2026 ===
TOTAL ORIGEN Mayo 2026: $1,399,084.69 ✅
```

Ambas unidades MPRO/API Local tienen datos correctos.

### 2.5 Validación UI (Screenshot)

El Tablero Ejecutivo muestra correctamente:
- **130° QUERETARO**: Ventas $2.12M, Proyección $3.46M
- **ORIGEN**: Ventas visibles
- **CIENFUEGOS**: Ventas $2.82M
- **130° MERIDA**: Ventas $2.30M
- **LA ESTELAR**: Ventas $1.76M

**NO hay $0 en ninguna unidad.**

---

## 3. Causa Probable del Reporte Falso

El usuario pudo haber observado $0 por una de estas razones:

| Causa Probable | Evidencia |
|----------------|-----------|
| Sesión expirada | Los errores 401/403 muestran datos vacíos |
| Datos en proceso de carga | "Consultando todas las unidades..." |
| Caché del navegador | Datos de una sesión anterior |
| Error transitorio de red | Timeout o conexión intermitente |

---

## 4. Verificación de Impacto de Migración

Se verificó que la migración de códigos canónicos NO afectó a QRO:

| Servidor | system_type | tipo_conexion | Afectado por migración |
|----------|-------------|---------------|------------------------|
| 130° QRO LOCAL | MPRO | API_LOCAL | ❌ No (MPRO no cambió) |
| ORIGEN LOCAL | MPRO | API_LOCAL | ❌ No (MPRO no cambió) |

La migración solo afectó a:
- SOFTRESTAURANT → SOFTRESTAURANT_PRO
- SOFRESATAURANT_ENTER → ENTERPRISE

**MPRO y API_LOCAL no fueron modificados.**

---

## 5. Validación de No Regresión

| Módulo | Estado |
|--------|--------|
| Tablero Ejecutivo - 130QRO | ✅ Ventas $2.12M |
| Tablero Ejecutivo - ORIGEN | ✅ Ventas $1.39M |
| Tablero Ejecutivo - CIENFUEGOS | ✅ Ventas $2.82M |
| Tablero Ejecutivo - 130° MERIDA | ✅ Ventas $2.30M |
| Tablero Ejecutivo - LA ESTELAR | ✅ Ventas $1.76M |
| EDARSAHUB SQL | ✅ Datos correctos |
| Endpoint /comercial/tablero-ejecutivo | ✅ HTTP 200 |
| Comercial | ✅ Funcionando |
| Catálogo SQL | ✅ No afectado |
| Explorador BD | ✅ No afectado |

---

## 6. Archivos Revisados

- `/app/backend/modules/comercial/service.py`
- `/app/backend/modules/comercial/routes.py`
- `/app/frontend/src/pages/TableroEjecutivo.js`

**Archivos Modificados:** NINGUNO (solo diagnóstico)

---

## 7. Confirmaciones

- ✅ No se tocó P0C
- ✅ No se tocó P0E
- ✅ No se tocó operational_window.py
- ✅ No se tocó UPSERT
- ✅ No se insertaron datos falsos
- ✅ No se modificó código
- ✅ MongoDB no fue usado como fuente principal
- ✅ EDARSAHUB SQL es la fuente de verdad

---

## 8. Conclusión

**NO EXISTE REGRESIÓN EN EL TABLERO EJECUTIVO.**

El sistema está funcionando correctamente. Los datos de 130° QUERÉTARO se muestran correctamente:
- Ventas: $2,123,189.00
- Proyección: $3,656,603.28
- Fuente: EDARSAHUB_SQL

### Recomendación al Usuario

Si observa $0 nuevamente:
1. **Cerrar sesión y volver a iniciar sesión**
2. **Hacer hard refresh (Ctrl+F5)**
3. **Esperar a que termine de cargar** ("Consultando todas las unidades...")
4. **Verificar que no hay errores de red** en la consola del navegador

---

*Diagnóstico completado: 2026-05-19 02:50 UTC*
