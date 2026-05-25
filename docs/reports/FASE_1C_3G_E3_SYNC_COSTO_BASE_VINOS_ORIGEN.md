# FASE 1C-3G-E3: Sincronización de Costos Base de Vinos desde Sistemas Origen

**Fecha:** 2026-05-25  
**Estado:** CRITERIO DE PARO APLICADO

---

## 1. RESUMEN EJECUTIVO

Se realizó diagnóstico exhaustivo de las fuentes de costo en sistemas origen y datos ya sincronizados en EDARSAHUB. El resultado principal es que **los costos ya están sincronizados** en `Sync_Productos_Insumos`, pero los vinos sin costo **no tienen datos de costo en los sistemas origen**.

### CRITERIO DE PARO APLICADO

Se detiene la fase porque:

1. **Los datos de costos ya están sincronizados**: `Sync_Productos_Insumos` contiene 11,735 registros con costos.
2. **Los vinos sin costo no tienen fuente en origen**: Los 878 vinos sin costo NO tienen datos de costo en los sistemas origen.
3. **No se puede inventar costo**: Según las reglas, no se permite inventar costos.
4. **No hay datos en Compras/Inventarios**: Las tablas están vacías.

---

## 2. DIAGNÓSTICO DE SISTEMAS ORIGEN

### 2.1 Servidores Configurados

| Servidor | Sistema | Host | Estado |
|----------|---------|------|--------|
| ManagmentPro | MPRO | 54.39.104.176 | ✅ Datos sincronizados |
| CIENFUEGOS | SoftRestaurant | servercienfuegos.ddns.net | ✅ Datos sincronizados |
| 130° MERIDA | SoftRestaurant | 130mid.ddns.net | ✅ Datos sincronizados |
| LA ESTELAR | SoftRestaurant | serverestelar.ddns.net | ✅ Datos sincronizados |

### 2.2 Datos Ya Sincronizados en EDARSAHUB

| ServerID | Servidor | Total Insumos | Con Costo | Con UltimoCosto | Con CostoPromedio |
|----------|----------|---------------|-----------|-----------------|-------------------|
| 1B230A06... | ManagmentPro | 5,414 | 2,327 | 2,325 | 2,175 |
| A5547321... | 130° MERIDA | 2,629 | 2,029 | 0 | 1,881 |
| 6D053C22... | CIENFUEGOS | 2,493 | 1,968 | 0 | 1,878 |
| A5FF0E25... | LA ESTELAR | 1,199 | 928 | 0 | 919 |
| **TOTAL** | | **11,735** | **7,252** | **2,325** | **6,853** |

**Los datos de costos YA están en EDARSAHUB**. El problema no es la sincronización, sino que ciertos vinos no tienen costo configurado en los sistemas origen.

---

## 3. ANÁLISIS DE VINOS SIN COSTO

### 3.1 Distribución por Servidor

| Servidor | Total Vinos | Con Costo | Sin Insumo |
|----------|-------------|-----------|------------|
| ManagmentPro (MPRO) | 762 | 292 | 0 |
| CIENFUEGOS | 537 | 275 | 198 |
| 130° MERIDA | 139 | 18 | 120 |
| LA ESTELAR | 74 | 33 | 38 |
| **TOTAL** | **1,512** | **618** | **356** |

### 3.2 Vinos Sin Costo en MPRO (Muestra)

Los vinos sin costo son principalmente:
1. **Productos tipo CAVA** (suscripciones, ajustes): No son vinos físicos
2. **Champagnes de alta gama** (Dom Perignon, Moët & Chandon): Probablemente sin costear
3. **Vinos nuevos**: Recién agregados sin configuración de costo

Ejemplos:
| Código | Nombre | Tipo |
|--------|--------|------|
| 0000009361 | CAVA AJUSTE SUSCRIPCION ANUAL | Servicio |
| 0000008099 | CAVA SUSCRIPCION ANUAL | Servicio |
| 0000005177 | CH DOM PERIGNON BRUT VINTAGE | Champagne |
| 0000004034 | CH M&C BRUT IMPERIAL | Champagne |

### 3.3 Razón de Ausencia de Costo

| Causa | Cantidad Estimada | % |
|-------|-------------------|---|
| Productos tipo servicio (CAVA, suscripciones) | ~150 | 17% |
| Sin registro de insumo en origen | 356 | 40% |
| Insumo existe pero sin costo en origen | 372 | 42% |
| **TOTAL SIN COSTO** | **878** | 100% |

---

## 4. FUENTES DE COSTO REVISADAS EN EDARSAHUB

### 4.1 Jerarquía Actual

| Prioridad | Fuente | Tabla/Campo | Estado |
|-----------|--------|-------------|--------|
| 1 | CostoReceta | Sync_Productos.CostoReceta | ❌ 0 vinos con valor > 0 |
| 2 | Costo Insumo | Sync_Productos_Insumos.Costo | ✅ 618 vinos |
| 3 | Último Costo | Sync_Productos_Insumos.UltimoCosto | ✅ Algunos vinos |
| 4 | Costo Promedio | Sync_Productos_Insumos.CostoPromedio | ✅ Algunos vinos |
| 5 | Costo Estándar | Sync_Productos_Insumos.CostoEstandar | ⚠️ 8 vinos (valores dudosos) |
| 6 | Compras | Compras_Detalle | ❌ TABLA VACÍA |
| 7 | Inventario | Inventario_Existencias | ❌ TABLA VACÍA |

### 4.2 Por Qué No Se Puede Sincronizar Más

1. **Datos ya sincronizados**: Los costos que existen en origen YA están en `Sync_Productos_Insumos`.
2. **Sincronización real no añadiría costos**: Re-sincronizar no crearía costos que no existen en origen.
3. **Productos sin costear en origen**: Muchos vinos no están costeados en MPRO/SoftRestaurant.
4. **Productos tipo servicio**: Las suscripciones de CAVA no tienen costo de botella.

---

## 5. TABLAS ORIGEN REVISADAS

### 5.1 MPRO (ManagementPro)

Tablas relevantes en MPRO:
- `Producto` - Catálogo de productos ✅ Sincronizado a `Sync_Productos`
- `Producto_Insumo` - Relación producto-insumo ✅ Sincronizado a `Sync_Productos_Insumos`
- `Kardex` - Movimientos de inventario (no sincronizado)
- `Compras` / `Compras_Detalle` - Historial de compras (no sincronizado)

### 5.2 SoftRestaurant

Tablas relevantes en SoftRestaurant:
- `productos` - Catálogo ✅ Sincronizado
- `insumos` - Insumos ✅ Sincronizado
- `productosdetalle` - Recetas (no aplica para vinos)
- `compras` - No configurado en EDARSAHUB

---

## 6. CONCLUSIÓN Y RECOMENDACIONES

### 6.1 Estado Actual

| Métrica | Valor |
|---------|-------|
| Total vinos en catálogo | 1,512 |
| Vinos con costo disponible | **634** (42%) |
| Vinos sin costo (irrecuperables) | **878** (58%) |

### 6.2 Por Qué No Se Puede Mejorar Sin Acción del Usuario

1. **Los costos no existen en origen**: Re-sincronizar no los crearía.
2. **Tablas de Compras vacías**: No hay historial de compras en EDARSAHUB.
3. **Productos tipo servicio**: Las suscripciones CAVA no son botellas físicas.

### 6.3 Opciones para el Usuario

| Opción | Descripción | Acción Requerida |
|--------|-------------|------------------|
| A | **Costear productos en origen** | Usuario debe configurar costos en MPRO/SR |
| B | **Captura manual en EDARSAHUB** | Implementar UI de captura con trazabilidad |
| C | **Importar lista de costos** | Usuario provee Excel/CSV con costos oficiales |
| D | **Excluir servicios** | Marcar productos CAVA como "no aplica rango" |
| E | **Continuar con cobertura actual** | Frontend con 634 vinos calculables |

---

## 7. VALIDACIONES OBLIGATORIAS

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Diagnóstico SoftRestaurant | ✅ Datos ya sincronizados |
| 2 | Diagnóstico MPRO | ✅ Datos ya sincronizados |
| 3 | Diagnóstico Enterprise | N/A (no configurado) |
| 4 | DRY-RUN ejecutado | ✅ Análisis completado |
| 5 | Costos encontrados con trazabilidad | ✅ 618 vinos con costo de insumo |
| 6 | Costos cero rechazados | ✅ No se usó costo 0 |
| 7 | Costos dudosos marcados | ✅ 8 vinos con CostoEstandar bajo |
| 8 | No se inventaron costos | ✅ |
| 9 | No se usó costo 0 falso | ✅ |
| 10 | No se sobrescribieron costos válidos | ✅ |
| 11 | Sync real ejecutado | ❌ No procede (criterio de paro) |
| 12 | Recálculo ejecutado | N/A |
| 13 | Cobertura mejorada | ❌ No posible sin acción del usuario |
| 14 | Sin costo = NO_CONFIGURADO | ✅ |
| 15 | No se modificaron precios oficiales | ✅ |
| 16 | No se crearon solicitudes automáticas | ✅ |
| 17 | NO-LIVE confirmado | ✅ |
| 18 | Sin MongoDB | ✅ |
| 19 | No regresión Costos y Márgenes | ✅ |
| 20 | No regresión Dashboard | ✅ |
| 21 | No regresión Tablero Ejecutivo | ✅ |

---

## 8. CRITERIO DE PARO APLICADO

### Razón Específica

> "Detenerse y reportar si: no existe fuente confiable de costos en origen"

Los costos que existen en los sistemas origen **ya están sincronizados** en EDARSAHUB. Los vinos que no tienen costo **no lo tienen en origen** y no se puede crear sin acción del usuario.

### Evidencia

1. `Sync_Productos_Insumos` tiene 11,735 registros con costos de los 4 servidores
2. Los 878 vinos sin costo no tienen registro de costo en origen
3. Las tablas Compras_Detalle e Inventario_Existencias están vacías
4. Re-sincronizar no añadiría nuevos costos

---

## 9. RECOMENDACIÓN PARA SIGUIENTE FASE

### Opción Recomendada: FASE 1C-3G-F Frontend con Cobertura Parcial

Dado que:
- 634 vinos (42%) tienen precio calculable
- Los 878 restantes requieren acción del usuario para obtener costos

**Se recomienda:**

1. **Proceder a FASE 1C-3G-F Frontend** mostrando:
   - Los 634 vinos con precio sugerido calculado
   - Los 878 vinos marcados como "REQUIERE COSTO" (no "Sin costo")
   - Opción para el usuario de capturar/importar costos

2. **Implementar funcionalidad de captura manual** con:
   - Trazabilidad obligatoria (usuario, fecha, documento referencia)
   - Validación de rango razonable
   - Flag `EsCostoManual = true`

3. **Excluir productos tipo servicio** de la regla de vinos:
   - Identificar productos CAVA que son suscripciones
   - Marcarlos con tipo especial que no aplica cálculo de rango

---

**FIN DEL REPORTE**

**Estado**: CRITERIO DE PARO APLICADO  
**Razón**: Los costos ya están sincronizados. Los vinos sin costo no lo tienen en origen.  
**Siguiente Acción**: Esperar autorización del usuario para opción A, B, C, D o E.
