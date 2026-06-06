# CIERRE Y BLINDAJE - OPERACIONES / ANÁLISIS EDARSA HUB
## Documento de Control de Cambios y Protección
## Fecha de Cierre: 2026-04-19
## Versión: 1.0.0 - CONGELADA

---

# ⚠️ ADVERTENCIA CRÍTICA

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   OPERACIONES / ANÁLISIS CERRADO Y BLINDADO                                  ║
║                                                                               ║
║   NO MODIFICAR SIN AUTORIZACIÓN EXPRESA Y CAMBIO CONTROLADO                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

# I. RESUMEN EJECUTIVO

## Estado del Módulo
- **Estado**: ✅ ESTABLE, VALIDADO, CONGELADO FUNCIONALMENTE
- **Fecha de Cierre**: 2026-04-19
- **Funcionalidad Principal**: Análisis operativo, inventarios, reportes
- **Sistemas Integrados**: SoftRestaurant, MPRO

---

# II. ALCANCE CERRADO

## Funcionalidades Incluidas
1. ✅ Análisis de inventarios físicos
2. ✅ Comparación inventario inicial vs final
3. ✅ Cálculo de diferencias y mermas
4. ✅ KPIs de rotación
5. ✅ Indicadores de eficiencia operativa
6. ✅ Generación de reportes
7. ✅ Análisis de productividad (tablajería)
8. ✅ Control de recetas/rendimientos
9. ✅ Dashboard operativo consolidado
10. ✅ Filtros por unidad/almacén/categoría

---

# III. KPIs Y DEFINICIONES

## 3.1 Diferencias de Inventario
- **Definición**: Inventario físico - Inventario teórico
- **Fuente**: Conteos físicos vs movimientos registrados
- **Clasificación**: Faltante / Sobrante / En rango

## 3.2 Mermas
- **Definición**: Pérdida de producto por vencimiento, daño, etc.
- **Cálculo**: Registros de merma por categoría
- **Análisis**: Por almacén, por producto, por período

## 3.3 Rotación de Inventario
- **Definición**: Veces que rota el inventario en el período
- **Fórmula**: Costo de ventas / Inventario promedio

## 3.4 Rendimiento Tablajería
- **Definición**: Producto obtenido vs producto esperado (receta)
- **Cálculo**: Comparación contra estándares de corte

## 3.5 Eficiencia Operativa
- **Indicadores**: Costos, tiempos, productividad
- **Análisis**: Por turno, por área, por responsable

---

# IV. FUENTES DE DATOS

| Fuente | Tabla/Endpoint | Uso |
|--------|----------------|-----|
| Inventarios | inventarios_fisicos | Base de análisis |
| Movimientos | movimientos_almacen | Teórico vs real |
| Ventas | cheques/Venta_Encabezado | Rotación |
| Mermas | registro_mermas | Pérdidas |
| Recetas | recetas_produccion | Rendimientos |
| Almacenes | almacen | Catálogo |

---

# V. CONEXIONES

| Sistema | Tipo | Origen | Uso |
|---------|------|--------|-----|
| SoftRestaurant | SQL | Menú Servidores | Inventarios, movimientos |
| MPRO | SQL | Menú Servidores | Inventarios MPRO |
| MongoDB | NoSQL | Local | Análisis, reportes |

---

# VI. FILTROS

| Filtro | Valores | Comportamiento |
|--------|---------|----------------|
| Unidad de Negocio | ID unidad | Contexto principal |
| Almacén | ID almacén | Filtra por ubicación |
| Categoría | ID categoría | Filtra productos |
| Fecha inicio | YYYY-MM-DD | Rango de análisis |
| Fecha fin | YYYY-MM-DD | Rango de análisis |
| Tipo análisis | diferencias/mermas/rotacion | Tipo de reporte |

---

# VII. REGLAS DE NEGOCIO

## 7.1 Reglas de Cálculo
1. Diferencia = Físico - Teórico (con signo)
2. Merma solo se registra con evidencia
3. Rotación usa promedio móvil de inventario
4. Rendimiento compara vs receta estándar

## 7.2 Reglas de Fuentes
1. Inventario físico: SQL del servidor asignado
2. Movimientos: SQL del servidor asignado
3. NO mezclar fuentes de diferentes sistemas

## 7.3 Reglas PROHIBIDAS de Modificar
- Fórmula de diferencias
- Lógica de comparación inventarios
- Cálculo de rotación
- Estándares de rendimiento

---

# VIII. PARAMETRIZACIONES

| Parámetro | Valor | Configurable |
|-----------|-------|--------------|
| Tolerancia diferencia | 2% | Sí, por categoría |
| Días rotación base | 30 | Sí |
| Umbral merma crítica | 5% | Sí |
| Rendimiento mínimo | 85% | Sí, por producto |

---

# IX. FLUJOS

```
INVENTARIO INICIAL → MOVIMIENTOS → INVENTARIO FINAL
                          ↓
                   CÁLCULO TEÓRICO
                          ↓
              COMPARACIÓN CON FÍSICO
                          ↓
                ¿Diferencia > Umbral?
                    ↓           ↓
                   SÍ           NO
                    ↓            ↓
             GENERA ALERTA      OK
                    ↓
           ANÁLISIS DE CAUSA
                    ↓
              REPORTE FINAL
```

---

# X. ARCHIVOS CRÍTICOS

| Archivo | Función | Criticidad |
|---------|---------|------------|
| `/app/backend/modules/fase2_operativo/service.py` | Lógica operativa | 🔴 CRÍTICO |
| `/app/backend/modules/fase2_operativo/routes.py` | Endpoints | 🔴 CRÍTICO |
| `/app/frontend/src/pages/Reportes.js` | UI análisis | 🟡 ALTO |
| `/app/frontend/src/components/fase2_operativo/` | Componentes UI | 🟡 ALTO |

---

# XI. CASOS DE PRUEBA BASE

## Prueba 1: Análisis de Diferencias
```
INPUT: Inventario inicial 100, Final 95, Movimientos -10
ESPERADO: Diferencia +5 (sobrante teórico vs físico)
```

## Prueba 2: Cálculo de Mermas
```
INPUT: Registro de merma por vencimiento
ESPERADO: Suma correcta por categoría y período
```

## Prueba 3: Consolidado por Unidad
```
INPUT: Múltiples almacenes
ESPERADO: Totales cuadran con suma de detalle
```

## Prueba 4: Filtros Correctos
```
INPUT: Filtro por almacén específico
ESPERADO: Solo datos de ese almacén
```

---

# XII. RIESGOS CONOCIDOS

| Riesgo | Mitigación | Estado |
|--------|------------|--------|
| Inventario no cerrado | Advertencia en UI | ✅ |
| Movimientos pendientes | Incluir en cálculo | ✅ |
| Sin datos históricos | Mensaje informativo | ✅ |

---

# XIII. REGLA DE NO MODIFICACIÓN

```
CUALQUIER MODIFICACIÓN REQUIERE:
1. Solicitud explícita documentada
2. Análisis de impacto
3. Snapshot previo
4. Pruebas de no regresión
5. Validación de cálculos
6. Actualización documental
7. Aprobación formal

PROHIBIDO:
- Cambiar fórmulas de cálculo
- Modificar fuentes de datos
- Alterar lógica de comparación
- Cambiar umbrales sin documentar
```

---

```
╔═══════════════════════════════════════════════════════════════╗
║  OPERACIONES / ANÁLISIS - CERRADO Y BLINDADO                 ║
║  Versión: 1.0.0 | Fecha: 2026-04-19                          ║
║  NO MODIFICAR SIN AUTORIZACIÓN                               ║
╚═══════════════════════════════════════════════════════════════╝
```
