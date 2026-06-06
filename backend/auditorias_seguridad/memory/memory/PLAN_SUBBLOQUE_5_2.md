# PLAN SUB-BLOQUE 5.2

**Fecha:** 2026-04-23  
**Estado:** PENDIENTE DE APROBACIÓN  
**Prerrequisito:** Sub-Bloque 5.1 cerrado formalmente

---

## 1. RESUMEN

El Sub-Bloque 5.2 propone migrar la **sección MPRO** del endpoint `/comercial/dashboard/{server_id}` para consumir queries centralizadas.

**NOTA IMPORTANTE**: Este sub-bloque requiere primero **extender** la función `query_ventas_periodo_mpro()` para soportar filtro opcional de sucursal, o usar `query_ventas_por_sucursal_mpro()` con agregación posterior.

---

## 2. ENDPOINT EXACTO A INTERVENIR

| Aspecto | Valor |
|---------|-------|
| **Endpoint** | `/comercial/dashboard/{server_id}` |
| **Sección** | MPRO (líneas ~3030-3200) |
| **Archivo** | `/app/backend/modules/comercial/routes.py` |

---

## 3. TIPO DE SISTEMA

| Sistema | Estado en 5.1 | Estado propuesto 5.2 |
|---------|---------------|---------------------|
| SoftRestaurant | ✅ Migrado | Sin cambios |
| **MPRO** | ❌ SQL directo | 🎯 A migrar |

---

## 4. FUNCIÓN CENTRALIZADA A USAR

### 4.1 Opción A: Extender `query_ventas_periodo_mpro()`

Agregar parámetro opcional `sucursal`:

```python
def query_ventas_periodo_mpro(
    server: Dict,
    fecha_ini: str,
    fecha_fin: str,
    sucursal: Optional[str] = None  # NUEVO
) -> VentasPeriodoResult:
```

**Ventaja**: Consistencia con SR, retorna consolidado
**Desventaja**: Requiere modificar función existente

### 4.2 Opción B: Usar `query_ventas_por_sucursal_mpro()` con agregación

```python
result = query_ventas_por_sucursal_mpro(server, fecha_ini, fecha_fin)
if result.success:
    # Filtrar por sucursal si se especifica
    if sucursal:
        sucursales = [s for s in result.sucursales if s['sucursal_id'] == sucursal]
    else:
        sucursales = result.sucursales
    
    # Agregar totales
    ventas = sum(s['ventas'] for s in sucursales)
    pax = sum(s['pax'] for s in sucursales)
    cheques = sum(s['cheques'] for s in sucursales)
```

**Ventaja**: No modifica funciones existentes
**Desventaja**: Más procesamiento en el endpoint

### 4.3 Recomendación

**Opción A** (extender `query_ventas_periodo_mpro`) es preferible porque:
- Mantiene consistencia con el patrón de SR
- Menor código en el endpoint
- Mejor rendimiento (filtro en SQL)

---

## 5. QUERIES SQL A REEMPLAZAR

| ID | Líneas | Query | Métricas |
|----|--------|-------|----------|
| M1 | 3094-3104 | `SELECT MAX(CONVERT(DATE, VE.Vn_Fecha))` | último día |
| M2 | 3115-3130 | `SELECT cheques, ventas, pax FROM Venta_Encabezado...periodo actual` | Base actual |
| M3 | 3145-3155 | `SELECT ventas WHERE mes_anterior` | Ventas anterior |
| M4 | 3165-3180 | `SELECT ventas, pax, cheques WHERE año_anterior` | Base año ant |

---

## 6. EVIDENCIA REQUERIDA PARA COMPARABILIDAD NUMÉRICA

Para evitar el problema del Sub-Bloque 5.1 (cambio de estado entre capturas):

### 6.1 Pre-Requisitos

1. **Servidor MPRO con datos estables**: Identificar un servidor MPRO que tenga conectividad desde el ambiente de prueba
2. **Captura ANTES sincronizada**: Ejecutar captura ANTES inmediatamente antes de aplicar el cambio
3. **Sin cambios de datos entre capturas**: Idealmente en horario sin operaciones

### 6.2 Protocolo de Captura

```bash
# 1. Capturar ANTES (con código actual)
curl /api/comercial/dashboard/{mpro_server_id}?periodo=mes > antes_mpro.json

# 2. Aplicar migración
# (modificar routes.py)

# 3. Reiniciar backend
sudo supervisorctl restart backend

# 4. Capturar DESPUÉS (mismo momento, mismos parámetros)
curl /api/comercial/dashboard/{mpro_server_id}?periodo=mes > despues_mpro.json

# 5. Comparar
python3 comparar_json.py antes_mpro.json despues_mpro.json
```

### 6.3 Criterio de Éxito Numérico

| Métrica | Criterio |
|---------|----------|
| ventas | Diff = 0 |
| pax | Diff = 0 |
| cheques | Diff = 0 |
| vs_periodo_anterior | Diff = 0 |
| vs_ano_anterior | Diff = 0 |

---

## 7. RIESGOS DEL SUB-BLOQUE 5.2

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | Extensión de función rompe código existente | BAJA | ALTO | Test de regresión antes de modificar |
| R2 | Filtro de sucursal no equivalente | MEDIA | MEDIO | Comparar SQL generado |
| R3 | Diferencia en manejo de NULL/0 | BAJA | BAJO | Validar edge cases |
| R4 | MPRO no accesible desde preview | ALTA | MEDIO | Validar en ambiente con conectividad |

---

## 8. CRITERIO DE APROBACIÓN

### 8.1 Para Aprobar el PLAN

- [ ] Definir opción de función (A o B)
- [ ] Identificar servidor MPRO de prueba
- [ ] Confirmar protocolo de captura

### 8.2 Para Aprobar la IMPLEMENTACIÓN

- [ ] Diff numérico = 0 en métricas base
- [ ] Diff numérico = 0 en KPIs derivados
- [ ] Estructura JSON idéntica
- [ ] HTTP 200
- [ ] RBAC intacto
- [ ] Filtro de sucursal funcional

---

## 9. DECISIONES PENDIENTES

| # | Decisión | Opciones |
|---|----------|----------|
| 1 | Función a usar | A: Extender existente / B: Usar por sucursal con agregación |
| 2 | Servidor MPRO de prueba | ManagmentPro / MPRO TABLAJERIA |
| 3 | ¿Proceder sin validación numérica si no hay conectividad? | Sí (riesgo documentado) / No (posponer) |

---

## 10. PROPUESTA

**No implementar Sub-Bloque 5.2 hasta:**

1. Cerrar formalmente 5.1 (HECHO ✅)
2. Decidir opción de función (A o B)
3. Confirmar si hay servidor MPRO accesible para validación numérica
4. Si no hay acceso: decidir si proceder con riesgo abierto o posponer

---

**DICTAMEN DEL PLAN:**

## 🟡 SUB-BLOQUE 5.2 PLAN PRESENTADO - PENDIENTE DECISIONES

El plan está documentado pero requiere decisiones del usuario antes de proceder con implementación.

---

Firma: E1 Agent  
Fecha: 2026-04-23
