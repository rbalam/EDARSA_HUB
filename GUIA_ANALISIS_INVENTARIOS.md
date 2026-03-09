# Análisis Completo de Inventarios - Guía de Uso

## Descripción General

El **Análisis Completo de Inventarios** es la funcionalidad principal del sistema que permite calcular las diferencias entre el inventario teórico y el inventario físico real, ordenado por Familia, SubFamilia y Producto.

## Fórmula de Cálculo

El sistema realiza los siguientes cálculos automáticamente:

```
Inventario Teórico = Inventario Inicial + Movimientos - Ventas
Diferencias = Inventario Teórico - Inventario Final
```

## Parámetros Requeridos

Para generar el análisis completo, debes configurar los siguientes parámetros:

### 1. Servidor
Selecciona el servidor SQL Server donde se encuentra la base de datos.

### 2. Sucursal
Lista desplegable que se carga dinámicamente desde el servidor seleccionado. Contiene todas las sucursales disponibles.

### 3. Almacén
Lista desplegable filtrada por la sucursal seleccionada. Solo muestra los almacenes correspondientes a esa sucursal.

### 4. Fecha Inicio y Fin de Ventas
Rango de fechas para considerar las ventas y movimientos de inventario.

**Formato:** YYYY-MM-DD (ej: 2026-01-01)

### 5. Inventario Inicial (Folio)
Selecciona el folio del inventario físico que se usará como punto de partida. La lista muestra:
- Folio del inventario
- Fecha de captura

### 6. Inventario Final (Folio)
Selecciona el folio del inventario físico que se usará como punto de comparación final.

## Columnas del Reporte

El reporte generado incluye las siguientes columnas:

### Información del Producto
- **Categoria**: Categoría del producto
- **Familia**: Familia del producto
- **SubFamilia**: SubFamilia del producto
- **Codigo**: Código único del producto
- **Producto**: Nombre descriptivo del producto
- **Unidad**: Unidad de medida (KG, PZ, LT, etc.)
- **Costo_Unitario**: Costo por unidad

### Inventario Inicial
- **Inv_Inicial_Cantidad**: Cantidad en inventario inicial
- **Inv_Inicial_Costo**: Valor en costo del inventario inicial

### Movimientos
- **Movimientos**: Cantidad de movimientos (+ entradas, - salidas)
- **Movimientos_Costo**: Valor en costo de los movimientos

### Ventas
- **Ventas**: Cantidad vendida en el período
- **Ventas_Costo**: Valor en costo de las ventas

### Inventario Teórico (Calculado)
- **Inv_Teorico_Cantidad**: Cantidad calculada (Inicial + Movimientos - Ventas)
- **Inv_Teorico_Costo**: Valor en costo del inventario teórico

### Inventario Final (Real)
- **Inv_Final_Cantidad**: Cantidad física contada
- **Inv_Final_Costo**: Valor en costo del inventario final

### Diferencias (Calculadas)
- **Diferencia_Cantidad**: Diferencia en unidades (Teórico - Final)
- **Diferencia_Costo**: Diferencia en valor monetario
- **Diferencia_Porcentaje**: Porcentaje de diferencia sobre el teórico

## Interpretación de Resultados

### Diferencias Positivas (Rojo)
**Significado:** Hay más inventario teórico que físico (faltante)

**Ejemplo:**
```
Inv_Teorico: 100 unidades
Inv_Final: 80 unidades
Diferencia: +20 unidades (ROJO)
```

**Posibles causas:**
- Mermas no registradas
- Robos
- Errores en conteo físico
- Ventas no registradas
- Consumos internos no documentados

### Diferencias Negativas (Verde)
**Significado:** Hay más inventario físico que teórico (sobrante)

**Ejemplo:**
```
Inv_Teorico: 100 unidades
Inv_Final: 110 unidades
Diferencia: -10 unidades (VERDE)
```

**Posibles causas:**
- Entradas no registradas
- Errores en conteo físico
- Devoluciones no registradas
- Errores en registro de ventas

### Sin Diferencias (Gris)
**Significado:** El inventario físico coincide con el teórico

## Flujo de Uso Recomendado

### 1. Preparación
1. Asegúrate de tener un servidor SQL configurado
2. Verifica que los inventarios físicos estén capturados en el sistema

### 2. Configuración de Filtros
1. Selecciona el **Servidor**
2. Espera a que carguen las **Sucursales**
3. Selecciona la **Sucursal** deseada
4. Espera a que carguen los **Almacenes**
5. Selecciona el **Almacén**
6. Espera a que carguen los **Inventarios físicos**
7. Selecciona el **Inventario Inicial** (más antiguo)
8. Selecciona el **Inventario Final** (más reciente)
9. Define las **Fechas** del período a analizar

### 3. Generación del Reporte
1. Haz clic en **Generar Reporte**
2. El sistema ejecutará la consulta SQL compleja
3. Los resultados aparecerán en la tabla inferior

### 4. Análisis de Resultados
1. Revisa las diferencias más grandes (ordenadas por valor)
2. Identifica patrones por familia/subfamilia
3. Presta especial atención a productos con alto valor de diferencia

### 5. Exportación
1. **Excel**: Para análisis detallado y pivot tables
2. **PDF**: Para reportes impresos
3. **Email**: Para enviar automáticamente a supervisores

## Ejemplo Práctico

**Escenario:** Análisis mensual de inventario de alimentos en Querétaro

**Configuración:**
```
Servidor: Servidor Querétaro (MPRO)
Sucursal: QUERETARO
Almacén: ALMACEN PRINCIPAL
Fecha Inicio: 2026-01-01
Fecha Fin: 2026-01-31
Inventario Inicial: Folio 12345 (2026-01-01)
Inventario Final: Folio 12378 (2026-01-31)
```

**Resultado Esperado:**
```
Categoría: Alimentos
Familia: CARNES FRESCAS
SubFamilia: CARNES Y MARISCOS
Producto: (C) Atun Steak c/Tostadas kg
Unidad: KG
Costo Unitario: $147.70

Inv_Inicial_Cantidad: 10.00 kg
Movimientos: +5.00 kg (entradas)
Ventas: 12.00 kg
Inv_Teorico_Cantidad: 3.00 kg (10 + 5 - 12)
Inv_Final_Cantidad: 2.50 kg
Diferencia_Cantidad: +0.50 kg (faltante)
Diferencia_Costo: $73.85
Diferencia_Porcentaje: 16.67%
```

## Mejores Prácticas

1. **Frecuencia de Análisis**
   - Semanal: Para productos de alta rotación
   - Mensual: Para inventario general
   - Trimestral: Para auditorías completas

2. **Revisión de Diferencias**
   - Prioriza diferencias > 5% del valor teórico
   - Investiga patrones recurrentes en familias específicas
   - Documenta las causas identificadas

3. **Acciones Correctivas**
   - Diferencias pequeñas (<2%): Tolerables
   - Diferencias medianas (2-5%): Revisar procesos
   - Diferencias grandes (>5%): Investigación inmediata

4. **Configuración de Alertas**
   - Configura alertas automáticas para productos críticos
   - Define umbrales según el valor del producto
   - Asigna responsables por familia de productos

## Limitaciones Conocidas

1. El análisis requiere que los inventarios físicos estén capturados en el sistema
2. Solo soporta el sistema MPRO actualmente (SoftRestaurant en desarrollo)
3. Las fechas de ventas deben estar dentro del rango del inventario inicial y final
4. La tabla muestra máximo 100 registros (exporta para ver todos)

## Soporte Técnico

Para problemas o dudas:
1. Verifica que todos los filtros estén seleccionados correctamente
2. Confirma que el servidor SQL esté accesible
3. Revisa los logs del backend en caso de errores
4. Contacta al administrador del sistema

## Próximas Mejoras

- Soporte para SoftRestaurant
- Filtros adicionales por categoría y familia
- Gráficos de análisis de tendencias
- Comparación entre múltiples períodos
- Exportación con formato personalizado
