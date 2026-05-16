# FASE SYNC-2C: Aplicación de Corrección MPRO PorHora
## Reporte de Escritura Real

**Fecha:** 2026-05-16  
**Ejecutado por:** E1 Agent  
**Estado:** ✅ COMPLETADO EXITOSAMENTE

---

## 1. RESUMEN EJECUTIVO

Se aplicó la corrección de query MPRO con `Fecha_Alta` para obtener hora real de ventas. Los 7 registros originales con hora 0 fueron reemplazados por 87 registros con distribución horaria real.

| Métrica | Antes | Después |
|---------|-------|---------|
| Registros MPRO | 7 | 87 |
| Horas distintas | 1 (solo 0) | 17 (0,1,9-23) |
| Totales | Correctos | Correctos (±$0.01 redondeo) |

---

## 2. BASELINE DESDE EDARSAHUB SQL (NO LIVE)

### Datos MPRO originales (incorrectos)

| Fecha | Hora | Tickets | VentaHora |
|-------|------|---------|-----------|
| 2026-05-08 | 00:00 | 68 | $230,443.79 |
| 2026-05-09 | 00:00 | 116 | $340,786.53 |
| 2026-05-10 | 00:00 | 128 | $400,476.13 |
| 2026-05-11 | 00:00 | 33 | $87,490.41 |
| 2026-05-12 | 00:00 | 42 | $117,376.50 |
| 2026-05-13 | 00:00 | 38 | $122,498.51 |
| 2026-05-14 | 00:00 | 72 | $249,986.51 |

**Problema:** Todo concentrado artificialmente en hora 0

---

## 3. DRY-RUN EXITOSO

### Resultado con query corregida (Fecha_Alta)

| Fecha | Registros | Tickets | VentaTotal | Horas |
|-------|-----------|---------|------------|-------|
| 2026-05-08 | 14 | 68 | $230,443.79 | [0,1,10-23] |
| 2026-05-09 | 13 | 116 | $340,786.53 | [0,1,10-23] |
| 2026-05-10 | 13 | 128 | $400,476.13 | [9-23] |
| 2026-05-11 | 10 | 33 | $87,490.41 | [13-23] |
| 2026-05-12 | 12 | 42 | $117,376.50 | [0,1,13-23] |
| 2026-05-13 | 12 | 38 | $122,498.51 | [0,11-23] |
| 2026-05-14 | 13 | 72 | $249,986.51 | [0,12-23] |

**Total registros generados:** 87

---

## 4. VALIDACIÓN TOTALES vs HISTÓRICOS

| Fecha | Histórica | PorHora Sum | Diferencia | Status |
|-------|-----------|-------------|------------|--------|
| 2026-05-07 | $98,938.00 | $0.00 | $98,938.00 | ⚠️ Fuera de rango |
| 2026-05-08 | $230,443.79 | $230,443.79 | $0.00 | ✅ |
| 2026-05-09 | $340,786.53 | $340,786.53 | $0.00 | ✅ |
| 2026-05-10 | $400,476.13 | $400,476.14 | -$0.01 | ✅ (redondeo) |
| 2026-05-11 | $87,490.41 | $87,490.42 | -$0.01 | ✅ (redondeo) |
| 2026-05-12 | $117,376.50 | $117,376.50 | $0.00 | ✅ |
| 2026-05-13 | $122,498.51 | $122,498.51 | $0.00 | ✅ |
| 2026-05-14 | $249,986.51 | $249,986.51 | $0.00 | ✅ |

**Nota:** 2026-05-07 no tiene PorHora porque está fuera del rango de últimos 7 días.
**Tolerancia:** $0.01 por redondeo decimal es aceptable.

---

## 5. VALIDACIÓN HORA 0 ES REAL

Ventas registradas entre 00:00-00:59 (madrugada post-cierre):

| Fecha Op. | Tickets | Venta |
|-----------|---------|-------|
| 2026-05-08 | 6 | $27,724.99 |
| 2026-05-09 | 11 | $48,715.00 |
| 2026-05-12 | 8 | $15,329.01 |
| 2026-05-13 | 1 | $5,230.00 |
| 2026-05-14 | 5 | $3,780.00 |

**Total hora 0:** 31 tickets (ventas reales de madrugada)

✅ **Hora 0 corresponde a ventas REALES**, no al error anterior donde TODO estaba en hora 0.

---

## 6. ESCRITURA REAL EJECUTADA

### Operación UPSERT

- **Servidor:** ManagmentPro (1b230a06-ffaf-4c70-bd27-b1be3579dea6)
- **Rango:** 2026-05-08 a 2026-05-14 (7 días)
- **SyncRunID:** SYNC-2C-20260515210629
- **Registros procesados:** 87
- **Errores:** 0

### Limpieza de registros antiguos

Se eliminaron los 7 registros originales con hora 0 (SyncRunID anterior) que fueron reemplazados por la distribución correcta.

---

## 7. RESULTADO FINAL - MPRO 2026-05-14

**ANTES:**
```
Hora 00:00 | 72 tickets | $249,986.51 (TODO CONCENTRADO)
```

**DESPUÉS:**
```
Hora   | Tickets | VentaHora
00:00  |    5    |    3,780.00
12:00  |    1    |      565.01
13:00  |    7    |    4,091.54
14:00  |    4    |    7,839.99
15:00  |    1    |    2,975.00
16:00  |    5    |   31,839.00
17:00  |   11    |   47,441.99
18:00  |    4    |   32,423.00
19:00  |    6    |   19,160.00
20:00  |    4    |   14,590.00
21:00  |   10    |   42,500.00
22:00  |    9    |   26,555.98
23:00  |    5    |   16,225.00
----------------------------
TOTAL  |   72    |  249,986.51
```

---

## 8. NO REGRESIÓN SOFTRESTAURANT

| Fecha | Histórica | PorHora | Diff | Status |
|-------|-----------|---------|------|--------|
| 2026-05-07 | $87,372.00 | $0.00 | $87,372.00 | ⚠️ Sin PorHora |
| 2026-05-08 | $150,247.00 | $150,247.00 | $0.00 | ✅ |
| 2026-05-09 | $181,868.00 | $181,868.00 | $0.00 | ✅ |
| 2026-05-10 | $199,744.00 | $199,744.00 | $0.00 | ✅ |
| 2026-05-11 | $122,962.00 | $122,962.00 | $0.00 | ✅ |
| 2026-05-12 | $87,186.00 | $87,186.00 | $0.00 | ✅ |
| 2026-05-13 | $165,747.00 | $165,747.00 | $0.00 | ✅ |
| 2026-05-14 | $31,693.00 | $31,693.00 | $0.00 | ✅ |

✅ **SoftRestaurant NO fue modificado** - datos intactos

---

## 9. VALIDACIONES CUMPLIDAS

| Validación | Resultado |
|------------|-----------|
| Baseline desde EDARSAHUB SQL | ✅ |
| No tocar SoftRestaurant | ✅ |
| No tocar Sync_Ventas_Historicas | ✅ |
| No tocar Sync_Ventas_PorDiaSemana | ✅ |
| Solo corregir MPRO ManagmentPro | ✅ |
| Rango últimos 7 días | ✅ |
| Ventana México 13:00-11:00 | ✅ |
| Usar Fecha_Alta para DATEPART(HOUR) | ✅ |
| Mantener Vn_Fecha para fecha operativa | ✅ |
| Dry-run primero | ✅ |
| Distribución no concentrada en hora 0 | ✅ |
| Escritura real post dry-run | ✅ |
| UPSERT idempotente | ✅ |
| Anti-$0 falso | ✅ |
| No borrar históricos | ✅ |
| No expandir a 8 servidores | ✅ |
| No correr 30 días | ✅ |
| No scheduler | ✅ |

---

## 10. CONCLUSIÓN

**FASE SYNC-2C APLICACIÓN COMPLETADA EXITOSAMENTE**

- La distribución horaria MPRO ahora refleja datos reales
- Los totales cuadran 100% con Sync_Ventas_Historicas (±$0.01 tolerancia)
- SoftRestaurant no fue afectado
- El sistema está listo para FASE SYNC-3

---

*Documento generado por E1 Agent*  
*Fecha: 2026-05-16*
