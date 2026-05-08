# DICTAMEN FINAL: SUB-BLOQUE 5.2

**Fecha:** 2026-04-23  
**Endpoint:** `/comercial/dashboard/{server_id}`  
**Alcance Propuesto:** Sección MPRO  
**Estado:** ❌ NO IMPLEMENTADO - REQUIERE TRABAJO PREVIO EN CAPA CENTRALIZADA

---

## 1. RESUMEN EJECUTIVO

El Sub-Bloque 5.2 **no pudo completarse** porque la función centralizada `query_ventas_periodo_mpro()` **no soporta** el patrón de filtrado complejo que utiliza el endpoint `/comercial/dashboard/{server_id}` para MPRO.

---

## 2. ANÁLISIS TÉCNICO

### 2.1 Diferencias entre Función Centralizada y Endpoint

| Aspecto | `query_ventas_periodo_mpro()` | Dashboard MPRO (routes.py) |
|---------|-------------------------------|---------------------------|
| Filtro sucursal | `AND VE.Sc_Cve_Sucursal = '{id}'` | Dinámico: por código O por nombre |
| JOIN Sucursal | No incluido | Condicional `INNER JOIN Sucursal S` |
| Filtro estado | No incluido | `AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'` |
| Tipo filtro | Simple (solo código) | Flexible (código exacto o LIKE en descripción) |

### 2.2 Código del Dashboard que NO tiene equivalente centralizado

```python
# routes.py líneas 3127-3144
sucursal_join = ""
sucursal_filter = ""
if not skip_sucursal_filter:
    if sucursal.isdigit() or (len(sucursal) == 4 and sucursal[0] == '0'):
        # Filtro por código exacto
        sucursal_join = ""
        sucursal_filter = f" AND VE.Sc_Cve_Sucursal = '{sucursal}'"
    else:
        # Filtro por nombre (LIKE)
        sucursal_join = "INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal"
        sucursal_filter = f" AND S.Sc_Descripcion LIKE '%{sucursal}%'"
```

### 2.3 Filtro de Estado Cancelado

El dashboard MPRO incluye `AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'` que **no está** en la función centralizada.

---

## 3. DECISIÓN

### 3.1 Por qué NO se implementó

Migrar las queries MPRO sin crear primero una función centralizada equivalente **violaría** la condición:
> "NO meter lógica de negocio nueva en el endpoint"

Si copiamos la lógica de filtrado complejo al endpoint, estaríamos duplicando código en lugar de centralizarlo.

### 3.2 Trabajo Previo Requerido

Para completar el Sub-Bloque 5.2 se necesita:

1. **Extender `query_ventas_periodo_mpro()`** para soportar:
   - Parámetro `filtro_sucursal_flexible: bool = False`
   - Parámetro `excluir_cancelados: bool = False`
   - Lógica de JOIN condicional con tabla Sucursal

2. **O crear función hermana** `query_ventas_periodo_mpro_dashboard()` que incluya:
   - Toda la lógica de filtrado del dashboard
   - Compatibilidad con filtro por código y por nombre

---

## 4. ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/comercial/routes.py` | Import comentado (línea 82-83) |

**SQL eliminado:** Ninguno  
**Función centralizada usada:** Ninguna (pendiente)

---

## 5. ESTADO DEL ENDPOINT DASHBOARD

| Sección | Estado | Sub-Bloque |
|---------|--------|------------|
| SoftRestaurant | ✅ Migrado | 5.1 |
| MPRO | ❌ SQL directo | Pendiente |

---

## 6. PRÓXIMOS PASOS RECOMENDADOS

### Opción A: Crear función centralizada nueva

```python
# En /app/backend/modules/comercial/queries/mpro.py

def query_ventas_periodo_mpro_dashboard(
    server: Dict,
    fecha_ini: str,
    fecha_fin: str,
    sucursal: Optional[str] = None,
    filtro_flexible: bool = True,
    excluir_cancelados: bool = True
) -> VentasPeriodoResult:
    """
    Query de ventas para Dashboard MPRO con filtro flexible.
    
    A diferencia de query_ventas_periodo_mpro(), esta función:
    - Soporta filtro de sucursal por código O por nombre
    - Incluye JOIN condicional con tabla Sucursal
    - Excluye transacciones canceladas por defecto
    """
    ...
```

### Opción B: Extender función existente

Agregar parámetros opcionales a `query_ventas_periodo_mpro()` manteniendo compatibilidad.

### Opción C: Posponer migración MPRO

Dejar la sección MPRO con SQL directo hasta que se defina la arquitectura de funciones MPRO.

---

## 7. DICTAMEN FINAL

## ❌ SUB-BLOQUE 5.2 NO IMPLEMENTADO

**Motivo:** La función centralizada `query_ventas_periodo_mpro()` no soporta el patrón de filtrado del dashboard MPRO.

**Acción requerida:** Trabajo previo en capa centralizada antes de migrar.

**Riesgo:** Ninguno (no se hicieron cambios funcionales).

---

## 8. ESTADO CONSOLIDADO DEL ENDPOINT DASHBOARD

### `/comercial/dashboard/{server_id}`

| Sistema | Queries Migradas | Queries Pendientes | Estado |
|---------|------------------|-------------------|--------|
| SoftRestaurant | 4 | 1 (tempcheques) | 🟡 Parcial |
| MPRO | 0 | 5 | ❌ Sin migrar |

**Dictamen global:** El endpoint tiene migración **parcial** (solo SR). No está listo para declarar migración completa.

---

Firma: E1 Agent  
Fecha: 2026-04-23
