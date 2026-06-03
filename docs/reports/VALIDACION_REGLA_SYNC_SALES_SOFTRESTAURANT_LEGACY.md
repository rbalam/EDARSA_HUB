# VALIDACIÓN REGLA SYNC_SALES SOFTRESTAURANT LEGACY

**Generado:** 2026-06-03T00:37:19+00:00
**Archivo validado:** /app/backend/tools/sync_sales_dry_run.py

---

## Regla

SoftRestaurant legacy no debe usar FOR JSON PATH ni totalsrx/subtotalsrx como importe.
El item_total debe calcularse en Python como `cantidad * precio`.

---

## 1. Coincidencias FOR JSON PATH

```
273:    COMPATIBLE CON SQL SERVER LEGACY - NO USA FOR JSON PATH.
335:# - Usar FOR JSON PATH contra SoftRestaurant legacy
368:    Compatible con SQL Server legacy (NO depende de FOR JSON PATH).
459:    COMPATIBLE CON SQL SERVER LEGACY - NO USA FOR JSON PATH.
499:    Compatible con SQL Server legacy - NO usa FOR JSON PATH.
```

## 2. Referencias a totalsrx/subtotalsrx

```
278:    - cheqdet: totalsrx, subtotalsrx, precio, cantidad
292:        dc.totalsrx AS item_totalsrx,
293:        dc.subtotalsrx AS item_subtotalsrx,
336:# - Usar cheqdet.totalsrx como importe (puede ser -1)
337:# - Usar cheqdet.subtotalsrx como importe (puede ser -1)
348:    NO usar totalsrx/subtotalsrx como importe porque pueden venir en -1.
361:    # NO usar totalsrx ni subtotalsrx
372:    - NO se usa totalsrx ni subtotalsrx como fuente de importe
410:            # NO usar totalsrx/subtotalsrx
```

## 3. Evidencia cálculo Python cantidad * precio

```
340:# - Calcular item_total como cantidad * precio
344:def calculate_softrestaurant_item_total(row: Dict) -> float:
349:    SoftRestaurant legacy DEBE calcular item_total como cantidad * precio.
352:        row: Fila con campos item_quantity e item_price
355:        float: El importe calculado como quantity * price
360:    # Regla permanente: item_total = cantidad * precio
362:    return round(quantity * price, 2)
371:    - El importe de cada item se calcula con calculate_softrestaurant_item_total()
409:            # REGLA PERMANENTE: Calcular importe con calculate_softrestaurant_item_total
413:            item_total = calculate_softrestaurant_item_total(row)
438:                "Revisar cantidad/precio SoftRestaurant legacy."
```

## 4. Evidencia json.dumps

```
341:# - Usar json.dumps() para construir items JSON en Python
373:    - El JSON items se construye con json.dumps() en Python
449:            "items": json.dumps(ticket["items"], ensure_ascii=False) if ticket["items"] else "[]",
```

## 5. Función calculate_softrestaurant_item_total

```
344:def calculate_softrestaurant_item_total(row: Dict) -> float:
```

---

## Resultado

✅ PASS: No hay FOR JSON PATH activo.
⚠️ WARNING: Referencias a totalsrx/subtotalsrx encontradas (validar que sean solo diagnóstico).
✅ PASS: Cálculo Python cantidad * precio presente.
✅ PASS: json.dumps presente.
✅ PASS: Función calculate_softrestaurant_item_total presente.

---

## **RESULTADO = OK** ✅
(con 1 warnings)
