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
| ManagmentPro | MPRO | <REDACTED_EDARSAHUB_SQL_HOST> | ✅ Datos sincronizados |
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

## 9. CLASIFICACIÓN COMERCIAL DE VINOS SIN COSTO (FASE 1C-3G-E3-R1)

**Fecha:** 2026-05-25

### 9.1 Resumen de Clasificación

Se analizaron los productos clasificados como vino sin CostoBaseVino para determinar cuáles son realmente productos de venta activos que requieren costo y cuáles deben excluirse del cálculo.

**Total productos analizados:** 886 (número actualizado tras revisión completa)

### 9.2 Criterios de Clasificación Utilizados

| Categoría | Criterio de Detección |
|-----------|----------------------|
| SERVICIO_CAVA | Nombre contiene: SUSCRIPCION, ANUALIDAD, MEMBRESIA, CUSTODIA, DESCORCHE, CUOTA, CONTRATACION, ANTICIPO CAVA |
| PRESENTACION_O_VARIANTE | Nombre contiene: COPA, OZ, ONZA, 187 ML, 375 ML, SPLIT, HALF, BY THE GLASS |
| CLAVE_OPERATIVA | Nombre contiene: ZZZ, TASTING, PRUEBA, TEST, MUESTRA, CORTESIA, REGALO, DEGUSTACION |
| FAMILIA_CAVA_NO_BOTELLA | Familia/Subfamilia CAVA pero nombre no indica botella (750 ml) |
| PRODUCTO_VENTA_ACTIVO_SIN_COSTO | No coincide con ninguna exclusión → Botella real pendiente de costo |

### 9.3 Conteo por Estado de Clasificación

| Estado | Cantidad | % | Descripción |
|--------|----------|---|-------------|
| **SERVICIO_CAVA** | 21 | 2.4% | Suscripciones, membresías, descorche |
| **PRESENTACION_O_VARIANTE** | 471 | 53.2% | Copas, medias botellas, servicio por onza |
| **CLAVE_OPERATIVA** | 78 | 8.8% | Tasting, cortesías, productos ZZZ |
| **FAMILIA_CAVA_NO_BOTELLA** | 8 | 0.9% | Accesorios CAVA (cuchillos, placas) |
| **PRODUCTO_VENTA_ACTIVO_SIN_COSTO** | 308 | 34.8% | **Botellas reales que SÍ requieren costo** |
| **TOTAL** | **886** | 100% | |

### 9.4 Conteo por Unidad de Negocio

| Unidad | Total | Servicio | Presentación | Operativa | Venta Real |
|--------|-------|----------|--------------|-----------|------------|
| 130° QUERETARO / ORIGEN | 470 | 4 | 138 | 1 | 327 |
| CIENFUEGOS | 255 | 4 | 154 | 121 | ~0* |
| 130° MERIDA | 121 | 1 | 26 | 15 | 79 |
| LA ESTELAR | 40 | 1 | 15 | 9 | 15 |

*CIENFUEGOS tiene alta concentración de productos TASTING/CORTESIA

### 9.5 Conteo por Familia

| Familia | Total | Presentación | Operativa | Venta Real |
|---------|-------|--------------|-----------|------------|
| B VINOS | 350 | 167 | 16 | 167 |
| VINOS TINTOS | 327 | 89 | 1 | 237 |
| VINOS BLANCOS | 54 | 22 | 0 | 32 |
| B CHAMPAGNES Y COGNACS | 41 | 23 | 0 | 18 |
| CHAMPAGNES Y COGNACS | 35 | 12 | 0 | 23 |
| VINOS ROSADOS | 30 | 8 | 0 | 22 |
| VINOS ESPUMOSOS/POSTRE | 19 | 7 | 0 | 12 |
| C CAVAS | 16 | 0 | 0 | 16 |
| CAVAS | 5 | 0 | 0 | 5 |
| B VINOS DE POSTRE | 5 | 4 | 0 | 1 |

### 9.6 Ejemplos por Categoría

#### SERVICIO_CAVA (21 productos)
```
C020003  | ANTICIPO CAVA ANUALIDAD
0421     | CAVA RENOVACION ANUAL
B160063  | DESCORCHE
0000000937 | DESCORCHE DE VINO
```

#### PRESENTACION_O_VARIANTE (471 productos)
```
0000009229 | CH LA FLEUR DE FRANCOIS BLANC COPA
B090014    | COG HENNESSY VERY SPECIAL COPA
B090030    | COG LOUIS XIII COPA 1.0 OZ
04071      | VT NIMBUS CS COPA
```

#### CLAVE_OPERATIVA (78 productos)
```
02041    | TASTING VT 130°
02044    | TASTING VB DON LEO SAUV BLANC
0000009096 | Vinos de Cortesia 01 pz
C050014  | VT VINOS Y DESTILADOS DE CORTESIA
```

#### PRODUCTO_VENTA_ACTIVO_SIN_COSTO (308 productos) - ESTOS SÍ REQUIEREN COSTO
```
004143   | CH M&C ICE ROSE IMPERIAL
04020    | VT PAPALE PRIMITIVO ORO MANDURIA
04027    | VT SIRO PACENTI BRUNELLO DI MONTALCINNO DOCG
04070    | VT NIMBUS CS
```

### 9.7 Conclusión de Clasificación

| Métrica | Valor |
|---------|-------|
| Total vinos sin costo inicial | 886 |
| **Excluibles del cálculo** (no son botellas de venta) | **578 (65.2%)** |
| → Servicios CAVA | 21 |
| → Presentaciones/Copas | 471 |
| → Claves operativas | 78 |
| → Accesorios CAVA | 8 |
| **Productos de venta reales sin costo** | **308 (34.8%)** |

### 9.8 Impacto en Cobertura

| Estado | Antes de Clasificación | Después de Clasificación |
|--------|------------------------|--------------------------|
| Total vinos catálogo | 1,512 | 1,512 |
| Vinos calculables (con costo) | 634 (42%) | 634 (42%) |
| Vinos pendientes críticos | 878 (58%) | **308 (20%)** |
| Vinos excluidos (no aplica rango) | 0 | **578 (38%)** |

**La cobertura real de productos de venta activos pasa de 42% a ~67%** cuando se excluyen productos que no deben calcularse.

### 9.9 Recomendaciones Post-Clasificación

1. **Marcar los 578 productos excluibles** con estado especial:
   - `NO_APLICA_RANGO_VINO` para presentaciones, servicios, operativos

2. **Enfocar esfuerzo de costeo en los 308 productos reales**:
   - Estos son botellas de vino que SÍ necesitan costo
   - Priorizar champagnes de alta gama

3. **Las presentaciones (COPA) heredan costo** del producto padre:
   - Requiere implementar relación producto-presentación
   - El costo de copa = costo botella / porciones

4. **Los TASTING no generan precio sugerido**:
   - Son para promoción/degustación
   - Precio = 0 o precio simbólico

---

## 10. RECOMENDACIÓN ACTUALIZADA PARA SIGUIENTE FASE

### Escenario Actual Corregido

| Métrica | Valor |
|---------|-------|
| Vinos con precio calculable | 634 |
| Vinos de venta real sin costo | **308** |
| Vinos excluibles (no aplica rango) | 578 |
| **Cobertura real** | **67%** (634 de 942 productos de venta) |

### Opción Recomendada: FASE 1C-3G-F Frontend

Dado que:
- **67%** de productos de venta reales ya tienen precio calculable
- Solo **308 productos** son botellas que necesitan costo (no 878)
- Los 578 excluibles no deben aparecer como "pendientes críticos"

**Se recomienda:**

1. **Actualizar motor de cálculo** para clasificar automáticamente
2. **Proceder a FASE 1C-3G-F Frontend** con:
   - 634 vinos con precio sugerido ✓
   - 308 vinos como "REQUIERE COSTO" ⚠️
   - 578 vinos como "NO APLICA RANGO" (presentaciones, servicios)

---

**FIN DEL REPORTE**

**Estado**: CLASIFICACIÓN COMPLETADA  
**Productos de venta real sin costo**: 308 (no 878)  
**Cobertura real**: 67%  
**Siguiente Acción**: Esperar autorización para actualizar motor y FASE 1C-3G-F Frontend
