# Diagnóstico Columnas SoftRestaurant CIENFUEGOS

**Fecha:** 2026-06-02  
**Base de datos:** softrestaurant95pro  
**Host:** servercienfuegos.ddns.net,6669\nationalsoft

---

## 1. Columnas Candidatas de Importe

### Tabla `cheques` (Encabezado)
| Columna | Tipo | Uso |
|---------|------|-----|
| `total` | money | ✅ **PRINCIPAL** - Total del ticket |
| `subtotal` | money | Subtotal sin impuestos |
| `totalsindescuento` | money | Total sin descuentos aplicados |
| `totalalimentos` | money | Subtotal alimentos |
| `totalbebidas` | money | Subtotal bebidas |
| `totalotros` | money | Subtotal otros |
| `totaldescuentos` | money | Total descuentos |

### Tabla `cheqdet` (Detalle)
| Columna | Tipo | Uso |
|---------|------|-----|
| `totalsrx` | numeric | ❌ **NO USAR** - Viene como -1 (centinela) |
| `subtotalsrx` | numeric | ❌ **NO USAR** - Viene como -1 (centinela) |
| `precio` | money | ✅ **USAR** - Precio unitario del producto |
| `cantidad` | numeric | ✅ **USAR** - Cantidad vendida |
| `preciosinimpuestos` | money | Precio sin IVA |

---

## 2. Fórmula de Cálculo de Importe

```python
def _calcular_importe_item(row):
    # 1. Intentar totalsrx/subtotalsrx (ignorar si <= 0)
    candidatos = [row.get("item_totalsrx"), row.get("item_subtotalsrx")]
    for valor in candidatos:
        if valor and float(valor) > 0:
            return float(valor)
    
    # 2. Fallback: cantidad * precio
    cantidad = float(row.get("item_quantity") or 0)
    precio = float(row.get("item_price") or 0)
    if cantidad > 0 and precio > 0:
        return round(cantidad * precio, 2)
    
    return 0.0
```

---

## 3. Muestra de Datos Reales (2025-06-01)

### Cheque #85358
- **Total encabezado:** $450.00
- **PAX:** 1
- **Items:**
  - A050050 BETABEL TATEMADO | Cant: 1 | Precio: $215 | TotalSRX: -1
  - A060106 COLIFLORES ROCA | Cant: 1 | Precio: $235 | TotalSRX: -1

**Nota:** `totalsrx = -1` indica que no se usa ese campo. El importe se calcula como `cantidad * precio`.

### Cheque #85359
- **Total encabezado:** $2,855.00
- **PAX:** 2
- **Items (muestra):**
  - A060102 BARBACHERA** | Cant: 1 | Precio: $420
  - A060106 COLIFLORES ROCA | Cant: 1 | Precio: $235
  - A060110 ESCAMOLES | Cant: 1 | Precio: $700
  - B070972 COCA COLA | Cant: 1 | Precio: $55
  - B100039 LIMONADA | Cant: 4 | Precio: $75

---

## 4. Items con Precio 0

Algunos productos tienen `precio = 0`:
- **A060036 SERVICIO DE ENTRADA** - precio: $0.001 (marcador)
- **B120038 MOC BB FIZZ** - precio: $0 (cortesía o promoción)

Estos se contabilizan como "items sin importe" pero son legítimos.

---

## 5. Validación Dry-Run CIENFUEGOS (2025-06-01)

| Métrica | Valor |
|---------|-------|
| Tickets | 19 |
| Monto total (encabezado) | $43,224.00 |
| Monto items (calculado) | $44,224.02 |
| PAX total | 53 |
| Items con importe | 164 |
| Items sin importe | 67 (29%) |
| Recomendación | ✅ EJECUTAR |

---

**Conclusión:** La diferencia de ~$1,000 entre monto encabezado y suma de items puede deberse a:
1. Impuestos no incluidos en `precio` pero sí en `total`
2. Descuentos aplicados al encabezado
3. Redondeos

Se recomienda usar `cheques.total` como MontoTotal principal.
