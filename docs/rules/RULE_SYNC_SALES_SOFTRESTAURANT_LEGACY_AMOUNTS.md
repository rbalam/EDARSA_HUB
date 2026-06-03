# REGLA PERMANENTE — Sync_Sales SoftRestaurant Legacy

**Versión:** 1.0  
**Fecha:** 2026-06-02  
**Estado:** ACTIVA - OBLIGATORIA

---

## Problema confirmado

En SoftRestaurant legacy, incluyendo **CIENFUEGOS** y posiblemente **130MID / ESTELAR**, SQL Server puede ser antiguo y no soportar `FOR JSON PATH`.

Además, en `cheqdet` los campos:

- `totalsrx`
- `subtotalsrx`

pueden venir con valor centinela `-1`, por lo que **NO son confiables** como importe real del item.

---

## Hallazgo validado

Para SoftRestaurant legacy:

| Campo | Estado | Uso |
|-------|--------|-----|
| `cheques.total` | ✅ CONFIABLE | Total del ticket cuando > 0 |
| `cheqdet.precio` | ✅ CONFIABLE | Precio unitario correcto |
| `cheqdet.cantidad` | ✅ CONFIABLE | Cantidad correcta |
| `cheqdet.totalsrx` | ❌ NO USAR | Puede ser -1 (centinela) |
| `cheqdet.subtotalsrx` | ❌ NO USAR | Puede ser -1 (centinela) |

El importe del item **DEBE** calcularse como:

```python
item_total = cantidad * precio
```

---

## Reglas obligatorias

### Prohibiciones absolutas

1. **Prohibido** usar `FOR JSON PATH` contra SoftRestaurant legacy.
2. **Prohibido** construir items JSON en SQL origen SoftRestaurant.
3. **Prohibido** usar `cheqdet.totalsrx` como importe confiable.
4. **Prohibido** usar `cheqdet.subtotalsrx` como importe confiable.

### Requisitos obligatorios

5. La consulta origen debe traer **filas planas**.
6. El JSON `Sync_Sales.items` debe construirse en Python con `json.dumps()`.
7. Para cada item:
   - `quantity = cheqdet.cantidad`
   - `price = cheqdet.precio`
   - `total = quantity * price`
8. `MontoTotal` debe tomar `cheques.total` si viene mayor a 0.
9. Si `cheques.total` viene NULL, 0 o inconsistente, recalcular `MontoTotal` como suma de items.

### Validaciones de dry-run

10. El dry-run **debe fallar** si hay tickets pero monto total cero.
11. El dry-run **debe fallar** si los items tienen total cero sin justificación.
12. **No se autoriza `--execute`** si una unidad tiene tickets y monto cero.

---

## Aplicación mínima

Esta regla aplica como mínimo a:

| Unidad | Sistema | Obligatorio |
|--------|---------|-------------|
| CIENFUEGOS | SoftRestaurant | ✅ SÍ |
| 130MID | SoftRestaurant | ✅ SÍ |
| ESTELAR | SoftRestaurant | ✅ SÍ |

---

## Código de referencia

### Fuente correcta de cálculo de item

```python
def calculate_softrestaurant_item_total(row):
    """
    Regla permanente:
    NO usar totalsrx/subtotalsrx como importe porque pueden venir en -1.
    SoftRestaurant legacy debe calcular item_total como cantidad * precio.
    """
    quantity = _safe_float(row.get("item_quantity"))
    price = _safe_float(row.get("item_price"))
    return quantity * price
```

### Campos no confiables para importe

```
cheqdet.totalsrx    ← PROHIBIDO como fuente de importe
cheqdet.subtotalsrx ← PROHIBIDO como fuente de importe
```

Estos campos pueden ser consultados para diagnóstico, pero **NO deben alimentar `Sync_Sales.items.total`**.

---

## Validador

Ejecutar para verificar cumplimiento:

```bash
bash /app/scripts/validate_sync_sales_softrestaurant_legacy_rules.sh /app
```

---

## Historial

| Fecha | Cambio |
|-------|--------|
| 2026-06-02 | Regla creada tras diagnóstico de CIENFUEGOS con totalsrx = -1 |

---

**Esta regla es PERMANENTE y no debe ser modificada sin aprobación explícita.**
