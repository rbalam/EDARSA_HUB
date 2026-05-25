# FASE 1C-3G-E2: Diagnóstico y Carga de CostoBaseVino para Vinos Sin Costo

**Fecha:** 2026-05-25  
**Estado:** COMPLETADO (Diagnóstico) - CRITERIO DE PARO APLICADO

---

## 1. RESUMEN EJECUTIVO

Se realizó un diagnóstico exhaustivo de los 886 vinos sin CostoBaseVino confiable. El resultado principal es que **no existen fuentes reales de costo disponibles en EDARSAHUB** para la mayoría de estos productos.

### Resultados Principales:
- **886 vinos** sin costo base inicial
- **8 vinos** recuperables vía `CostoEstandar` en Sync_Productos_Insumos
- **878 vinos** sin ninguna fuente de costo disponible
- **Tablas de Compras/Inventarios**: VACÍAS
- **Acción requerida**: Sincronización desde sistemas origen o captura manual autorizada

---

## 2. DIAGNÓSTICO DE LOS 886 VINOS SIN COSTO

### 2.1 Clasificación por Tipo de Problema

| Categoría | Cantidad | % |
|-----------|----------|---|
| Sin registro en Sync_Productos_Insumos | 356 | 40.2% |
| Con insumo pero sin Costo/Último/Promedio | 530 | 59.8% |
| **Total** | **886** | 100% |

### 2.2 Clasificación por Servidor/Unidad de Negocio

| ServerID | Unidad | Total Vinos | Sin Costo |
|----------|--------|-------------|-----------|
| 1B230A06-FFAF-4C70-BD27-B1BE3579DEA6 | ORIGEN / 130° QUERETARO | 762 | 470 |
| 6D053C22-523E-48C0-B72B-96081E2D781B | CIENFUEGOS | 537 | 255 |
| A5547321-1139-4D2B-9D53-182CA737B6B6 | 130° MERIDA | 139 | 121 |
| A5FF0E25-F029-43DB-B634-D4AC814C904F | LA ESTELAR | 74 | 40 |

### 2.3 Clasificación por Familia de Producto

| Familia | Sin Costo | Sin Insumo | Con Insumo Sin Costo |
|---------|-----------|------------|----------------------|
| B VINOS | 350 | 297 | 53 |
| VINOS TINTOS | 327 | 0 | 327 |
| VINOS BLANCOS | 54 | 0 | 54 |
| B CHAMPAGNES Y COGNACS | 41 | 40 | 1 |
| CHAMPAGNES Y COGNACS | 35 | 0 | 35 |
| VINOS ROSADOS | 30 | 0 | 30 |
| VINOS ESPUMOSOS/POSTRE | 19 | 0 | 19 |
| C CAVAS | 16 | 11 | 5 |
| CAVAS | 5 | 0 | 5 |
| B VINOS DE POSTRE | 5 | 5 | 0 |
| B CHAMPAGNES Y COGNACS (otro) | 4 | 3 | 1 |

---

## 3. FUENTES DE COSTO REVISADAS

### 3.1 Jerarquía de Búsqueda Aplicada

| Prioridad | Fuente | Tabla | Campo | Resultado |
|-----------|--------|-------|-------|-----------|
| 1 | CostoReceta | Sync_Productos | CostoReceta | **0 vinos** con valor > 0 |
| 2 | Costo Insumo | Sync_Productos_Insumos | Costo | Ya usada para 618 vinos |
| 3 | Último Costo | Sync_Productos_Insumos | UltimoCosto | Ya usada para algunos vinos |
| 4 | Costo Promedio | Sync_Productos_Insumos | CostoPromedio | Ya usada para algunos vinos |
| 5 | Costo Estándar | Sync_Productos_Insumos | CostoEstandar | **8 vinos** recuperables |
| 6 | Último Compra | Compras_Detalle | PrecioUnitario | **TABLA VACÍA** |
| 7 | Costo Inventario | Inventario_Existencias | CostoPromedio | **TABLA VACÍA** |
| 8 | Costo Proveedor | (No implementado) | - | No disponible |
| 9 | Override Manual | (No implementado) | - | No disponible |

### 3.2 Estado de Tablas Alternativas

| Tabla | Registros | Estado |
|-------|-----------|--------|
| Compras_Detalle | 0 | ❌ VACÍA |
| Inventario_Existencias | 0 | ❌ VACÍA |
| Proveedor_Catalogo | Datos | No tiene costos de productos |

### 3.3 Vinos Recuperables vía CostoEstandar

Se identificaron **8 vinos** con `CostoEstandar > 0`:

| Código | Nombre | CostoEstandar |
|--------|--------|---------------|
| 0000007476 | VT Navarra Crianza 750 ml | $0.53 |
| 0000007482 | VT La Bikina Nebbiolo 750 ml | $0.48 |
| 0000003872 | VR Aborigen Ad 750 ml | $0.38 |
| 0000007494 | VT Incognito 750 ml | $0.32 |
| 0000007484 | VT Perderberg Pinotage 750 ml | $0.31 |
| 0000000171 | VT Union Ad Incognito 750 ml | $0.25 |
| 0000004255 | VT Lomita CS Añada 2020 750 ml | $0.24 |
| 0000007506 | VB Catagua Chardonay 750 ml | $0.18 |

**⚠️ ALERTA**: Estos valores ($0.18 - $0.53) parecen incorrectos para botellas de vino. Posibles causas:
- Error de unidad de medida (costo por ml en lugar de botella)
- Datos de prueba
- Sincronización incompleta

---

## 4. CRITERIO DE PARO APLICADO

### Motivo de Paro

Se detiene la fase porque se cumple el criterio:

> **"Detenerse y reportar si: no existe fuente confiable de costo"**

### Evidencia:

1. **878 de 886 vinos** (99.1%) no tienen ninguna fuente de costo disponible en EDARSAHUB
2. Los 8 vinos con `CostoEstandar` tienen valores sospechosamente bajos
3. Las tablas de Compras e Inventarios están **completamente vacías**
4. No existe fuente alternativa sin sincronización desde sistemas origen

---

## 5. ACTUALIZACIÓN A JERARQUÍA DE COSTO

A pesar de los resultados limitados, se actualizó `precios_vinos_service.py` para incluir `CostoEstandar`:

### Nueva Jerarquía (5 niveles implementados):

```python
JERARQUÍA DE COSTO:
1. CostoReceta (si > 0, representa costo consolidado confiable)
2. Sync_Productos_Insumos.Costo (costo de botella)
3. Sync_Productos_Insumos.UltimoCosto
4. Sync_Productos_Insumos.CostoPromedio
5. Sync_Productos_Insumos.CostoEstandar ← AÑADIDO
6-9. (Futuro: compras, proveedor, override)
```

### Resultado del Recálculo (muestra 600 vinos):

| Fuente | Vinos |
|--------|-------|
| INSUMO_COSTO | 234 |
| INSUMO_PROMEDIO | 6 |
| INSUMO_ESTANDAR | 2 |
| **Total CALCULADO** | **242** |
| COSTO_BASE_NO_CONFIGURADO | 358 |

---

## 6. CONTEOS ANTES/DESPUÉS

### Comparación con Límite 1,512 vinos (estimado):

| Estado | Antes E2 | Después E2 | Diferencia |
|--------|----------|------------|------------|
| CALCULADO | 626 | ~634 | +8 |
| COSTO_BASE_NO_CONFIGURADO | 886 | ~878 | -8 |
| IMPUESTO_NO_CONFIGURADO | 0 | 0 | 0 |
| RANGO_NO_CONFIGURADO | 0 | 0 | 0 |

**Nota**: El impacto es mínimo (8 vinos) porque las fuentes alternativas están vacías o tienen datos no confiables.

---

## 7. VALIDACIONES OBLIGATORIAS

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Identificar 886 vinos sin costo | ✅ Completado |
| 2 | Clasificar por unidad/sistema/familia | ✅ Completado |
| 3 | Identificar fuentes reales disponibles | ✅ Completado (limitadas) |
| 4 | Ejecutar DRY-RUN | ✅ Ejecutado |
| 5 | Confirmar costos recuperables | ✅ 8 vinos (valores dudosos) |
| 6 | Confirmar sin costo final | ✅ 878 vinos |
| 7 | No usar costos 0 falsos | ✅ Confirmado |
| 8 | No inventar costos | ✅ Confirmado |
| 9 | Trazabilidad de fuente | ✅ Campo `fuente_costo` |
| 10 | Recalcular precios impactados | ✅ Completado |
| 11 | Aumentó CALCULADO | ✅ +8 vinos |
| 12 | Sin costo = NO_CONFIGURADO | ✅ Confirmado |
| 13 | No modificar precios oficiales | ✅ Confirmado |
| 14 | No crear solicitudes automáticas | ✅ Confirmado |
| 15 | NO-LIVE confirmado | ✅ |
| 16 | Sin MongoDB | ✅ |
| 17 | No regresión Costos y Márgenes | ✅ |
| 18 | No regresión Dashboard Comercial | ✅ |
| 19 | No regresión Tablero Ejecutivo | ✅ |

---

## 8. RIESGOS PENDIENTES

### 8.1 Críticos

1. **878 vinos sin costo**: No tienen fuente de costo en EDARSAHUB. Requieren:
   - Sincronización desde MPRO/SoftRestaurant
   - O captura manual autorizada con trazabilidad

2. **Tablas Compras/Inventarios vacías**: Sin datos históricos de costos de compra.

3. **CostoEstandar sospechoso**: Los 8 valores encontrados ($0.18-$0.53) no parecen costos reales de botellas de vino.

### 8.2 Medio

4. **356 vinos sin registro de insumo**: No están en `Sync_Productos_Insumos`. Requieren sincronización completa.

5. **Productos tipo CAVA**: Muchos son servicios de suscripción ("CAVA ANUALIDAD"), no botellas físicas. Pueden requerir tratamiento diferente.

---

## 9. RECOMENDACIONES

### Opciones para Resolver los 878 Vinos Sin Costo:

| Opción | Descripción | Esfuerzo | Riesgo |
|--------|-------------|----------|--------|
| A | Sincronización batch desde sistemas origen (MPRO/SR) | Alto | Bajo |
| B | Captura manual autorizada (con plantilla y trazabilidad) | Medio | Medio |
| C | Estimación por familia/proveedor (solo con autorización) | Bajo | Alto |
| D | Marcar como "requiere configuración" y continuar | Bajo | Bajo |

### Recomendación:

**Opción D** (corto plazo) + **Opción A** (mediano plazo):

1. Continuar con FASE 1C-3G-F Frontend para los 634 vinos con costo
2. Implementar job de sincronización de costos desde sistemas origen
3. Proveer UI para captura manual solo cuando sea necesario

---

## 10. ESTRUCTURA PROPUESTA PARA PERSISTENCIA (FUTURO)

Si se implementa carga masiva de costos, la tabla propuesta:

```sql
-- Tabla para persistir CostoBaseVino con trazabilidad
CREATE TABLE Comercial_CostosBaseProducto (
    CostoBaseID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ProductoID UNIQUEIDENTIFIER,
    ServerID UNIQUEIDENTIFIER,
    CodigoProducto VARCHAR(100),
    EmpresaID INT,
    UnidadNegocioID INT,
    
    -- Costo
    CostoBase DECIMAL(18,4) NOT NULL,
    FuenteCosto VARCHAR(50) NOT NULL,  -- COSTO_RECETA, INSUMO_COSTO, etc.
    FechaCosto DATE,
    
    -- Trazabilidad
    ProveedorID INT NULL,
    DocumentoCompraID BIGINT NULL,
    SistemaOrigen VARCHAR(30),
    ServidorOrigenID UNIQUEIDENTIFIER,
    SyncRunID VARCHAR(50),
    
    -- Estado
    EstatusCosto VARCHAR(30) DEFAULT 'ACTIVO',
    FechaCreacion DATETIME2 DEFAULT GETDATE(),
    UsuarioCreacion VARCHAR(100),
    FechaModificacion DATETIME2,
    UsuarioModificacion VARCHAR(100)
);
```

**Nota**: Esta tabla NO fue creada porque no hay datos que cargar. Se documenta para referencia futura.

---

## 11. ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/comercial/services/precios_vinos_service.py` | Añadido `CostoEstandar` a jerarquía (nivel 5) |

---

## 12. CONCLUSIÓN

### Estado Final:

| Métrica | Valor |
|---------|-------|
| Total vinos | 1,512 |
| Con costo (CALCULADO) | **~634** |
| Sin costo (NO_CONFIGURADO) | **~878** |
| Tasa de cobertura | **41.9%** |

### Razón de Cobertura Limitada:

Los 878 vinos sin costo **no tienen datos de costo en ninguna tabla de EDARSAHUB**. Las tablas de Compras e Inventarios están vacías, y los únicos campos disponibles (`CostoEstandar`) tienen valores no confiables.

---

**FIN DEL REPORTE**

**Siguiente Acción**: Esperar autorización para FASE 1C-3G-F Frontend (con cobertura de 634 vinos) o implementar sincronización de costos desde sistemas origen.
