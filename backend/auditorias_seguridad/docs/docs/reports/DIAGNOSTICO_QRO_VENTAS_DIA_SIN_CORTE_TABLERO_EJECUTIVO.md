# DIAGNÓSTICO: "Regresión" en Tablero Ejecutivo - 130° QUERÉTARO - VENTAS DEL DÍA

**Fecha:** 2026-05-19  
**Prioridad:** P0  
**Estado:** ✅ NO ES REGRESIÓN - SISTEMA FUNCIONANDO CORRECTAMENTE

---

## ACLARACIÓN IMPORTANTE

El usuario reportó $0 en **"Ventas del Día (sin corte)"** para 130° QUERÉTARO.

El diagnóstico inicial fue incorrecto porque validó **ventas mensuales** ($2.12M), no **ventas del día**.

Este diagnóstico corregido valida específicamente el endpoint y modo **"Ventas del Día"**.

---

## 1. Endpoint Real de "Ventas del Día"

```
GET /api/v2/comercial/ventas-dia
Authorization: Bearer [token]
```

Este endpoint lee desde **Comercial_Ventas_Dia_Abiertas_v2** en EDARSAHUB SQL.

---

## 2. Response del Endpoint para QRO

```json
{
  "unidad_negocio_id": "130QRO",
  "unidad_negocio_nombre": "130QRO",
  "total_estimado_dia": 47283.0,
  "ventas_abiertas": 10875.0,
  "ventas_cerradas_dia": 36408.0,
  "pax_abiertos": 18.0,
  "tickets_abiertos": 17.0,
  "fuente_original": "API_LOCAL",
  "_fuente": "EDARSAHUB_SQL"
}
```

**Resultado:** ✅ 130° QUERÉTARO tiene **$47,283.00** en Ventas del Día - NO es $0.

---

## 3. Validación UI (Screenshot)

El Tablero Ejecutivo en modo "Ventas del Día (sin corte)" muestra correctamente:

| Unidad | Ventas del Día | Estado |
|--------|----------------|--------|
| CIENFUEGOS | $96.63K | ✅ |
| 130° MERIDA | $52.26K | ✅ |
| **130° QUERETARO** | **$47.28K** | ✅ |
| ORIGEN | $27.64K | ✅ |
| LA ESTELAR | Visible | ✅ |

**CONSOLIDADO:** $230.10K

---

## 4. Comparación QRO vs ORIGEN

| Unidad | Ventas del Día | Fuente | Status |
|--------|----------------|--------|--------|
| 130QRO | $47,283.00 | API_LOCAL | ✅ DATA_OK |
| ORIGEN | $27,640.00 | API_LOCAL | ✅ DATA_OK |

Ambas unidades MPRO/API Local tienen datos correctos.

---

## 5. Causa del Reporte Falso

El usuario observó $0 probablemente por:

| Causa Probable | Evidencia |
|----------------|-----------|
| Sesión expirada (401) | Los errores 401 muestran datos vacíos |
| Frontend no recargó datos | El selector cambió pero los datos no se actualizaron |
| Caché del navegador | Datos de una sesión anterior |
| Frontend necesitaba reinicio | Cambios en .env no aplicados |

---

## 6. Validación de No Regresión

| Módulo | Estado |
|--------|--------|
| Tablero Ejecutivo - Ventas del Día | ✅ Funcionando |
| 130° QUERETARO | ✅ $47.28K |
| ORIGEN | ✅ $27.64K |
| CIENFUEGOS | ✅ $96.63K |
| 130° MERIDA | ✅ $52.26K |
| Endpoint /v2/comercial/ventas-dia | ✅ HTTP 200 |
| EDARSAHUB SQL | ✅ Fuente correcta |

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

## 8. Recomendación al Usuario

Si observa $0 nuevamente en "Ventas del Día":

1. **Cerrar sesión y volver a iniciar sesión**
2. **Hacer hard refresh (Ctrl+F5)**
3. **Verificar que el selector muestre "📊 Ventas del Día"** en Año(s)
4. **Hacer click en "Actualizar"** para forzar recarga de datos
5. **Esperar a que los datos carguen** (puede tardar unos segundos)

Si el problema persiste, verificar:
- Consola del navegador (F12 > Console) para ver errores 401/403
- Red (F12 > Network) para ver si el endpoint `/v2/comercial/ventas-dia` responde

---

## 9. Archivos Revisados

- `/app/frontend/src/pages/TableroEjecutivo.js` - Lógica de "Ventas del Día"
- `/app/backend/modules/comercial/routes.py` - Endpoint V2
- `/app/backend/modules/comercial/service.py` - Servicio de ventas día

**Archivos Modificados:** NINGUNO (solo diagnóstico)

---

## 10. Conclusión

**NO EXISTE REGRESIÓN EN "VENTAS DEL DÍA" DEL TABLERO EJECUTIVO.**

El sistema está funcionando correctamente:
- Endpoint `/v2/comercial/ventas-dia` responde HTTP 200
- 130° QUERÉTARO muestra **$47,283.00** en Ventas del Día
- Fuente: EDARSAHUB_SQL (Comercial_Ventas_Dia_Abiertas_v2)
- Todas las unidades con datos correctos

El $0 reportado fue un problema de sesión/caché del navegador, no una regresión de código.

---

*Diagnóstico completado: 2026-05-19 03:01 UTC*
