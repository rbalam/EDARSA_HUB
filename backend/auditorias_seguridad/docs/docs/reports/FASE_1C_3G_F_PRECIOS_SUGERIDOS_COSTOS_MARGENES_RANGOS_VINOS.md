# FASE 1C-3G-F: Precios Sugeridos en Costos y Márgenes + Mantenimiento Rangos Vinos

**Fecha**: 25 de Mayo de 2026  
**Estado**: COMPLETADO  
**Versión**: 1.0  

---

## 1. Diagnóstico Inicial

### Estado Encontrado
- Pantalla `CostosMargenes.jsx` existente con tabs: Resumen/Productos, Solicitudes de Precio
- Tabla `Comercial_ReglasPrecio` con regla `VINOS_RANGOS_MX` activa
- Tabla `Comercial_ReglasPrecioRangos` con 13 rangos configurados ($0-$20,000)
- Servicio `pricing_sugerido_service.py` existente pero sin endpoint consolidado
- No existía endpoint `/precios-sugeridos` ni CRUD para rangos de vinos

---

## 2. Tablas SQL Usadas

### Comercial_ReglasPrecio
| Campo | Tipo | Descripción |
|-------|------|-------------|
| ReglaPrecioID | uniqueidentifier | PK |
| Codigo | nvarchar | Código único (VINOS_RANGOS_MX) |
| NombreRegla | nvarchar | Nombre descriptivo |
| TipoRegla | nvarchar | Tipo (VINO, etc.) |
| Activo | bit | Estado |

### Comercial_ReglasPrecioRangos
| Campo | Tipo | Descripción |
|-------|------|-------------|
| ReglaPrecioRangoID | uniqueidentifier | PK |
| ReglaPrecioID | uniqueidentifier | FK a ReglasPrecio |
| LimiteInferior | decimal | Costo mínimo |
| LimiteSuperior | decimal | Costo máximo |
| MargenMultiplicador | decimal | Factor multiplicador |
| Orden | int | Orden de aplicación |
| Descripcion | nvarchar | Descripción |
| Activo | bit | Estado |

### Sync_Productos
- Fuente de productos con campos: CodigoFuente, Nombre, FamiliaNombre, PrecioVenta, CostoReceta, TieneReceta

---

## 3. Endpoints Creados

### GET /api/comercial/pricing/precios-sugeridos
Retorna lista paginada de productos con precio sugerido calculado.

**Parámetros:**
- `page`, `page_size`: Paginación
- `search`: Búsqueda por nombre/código
- `solo_vinos`: Filtrar solo vinos
- `solo_fuera_rango`: Solo productos fuera de rango
- `solo_requiere_revision`: Solo requiere revisión
- `fuente`: Filtrar por fuente (VINOS_RANGOS, COSTO_MARGEN, etc.)
- `margen_objetivo`: Margen objetivo para cálculo (default 0.35)

**Respuesta por producto:**
```json
{
  "producto_id": "string",
  "nombre": "string",
  "familia": "string",
  "precio_actual": 1250.00,
  "costo_receta": 450.00,
  "margen_porcentaje": 64.0,
  "precio_sugerido": 1125.00,
  "fuente_sugerencia": "VINOS_RANGOS",
  "diferencia_monto": -125.00,
  "diferencia_porcentaje": -10.0,
  "estado_revision": "FUERA_RANGO",
  "rango_vinos_aplicado": "0 a 500",
  "multiplicador": 2.5,
  "es_vino": true
}
```

### GET /api/comercial/pricing/reglas/vinos/rangos
Lista todos los rangos de VINOS_RANGOS_MX con detección de traslapes.

### POST /api/comercial/pricing/reglas/vinos/rangos
Crea nuevo rango. Valida traslapes.

### PUT /api/comercial/pricing/reglas/vinos/rangos/{rango_id}
Actualiza rango existente.

### PATCH /api/comercial/pricing/reglas/vinos/rangos/{rango_id}/desactivar
Desactiva rango (soft delete).

### PATCH /api/comercial/pricing/reglas/vinos/rangos/{rango_id}/activar
Activa rango previamente desactivado.

---

## 4. Pantalla Modificada

**Archivo**: `/app/frontend/src/pages/comercial/CostosMargenes.jsx`

### Tabs Agregados
1. **Precios Sugeridos** (Tab con icono Target, color púrpura)
2. **Rangos Vinos** (Tab con icono Wine, color ámbar)

---

## 5. Campos Agregados en UI

### Tab Precios Sugeridos
| Columna | Descripción |
|---------|-------------|
| Producto | Nombre y código |
| Precio Actual | Precio de venta actual |
| Costo | Costo de receta |
| Margen % | Margen actual |
| **Precio Sugerido** | Recomendación calculada |
| **Fuente** | VINOS_RANGOS / COSTO_MARGEN / SIN_DATOS |
| **Diferencia** | % vs precio actual |
| **Estado** | DENTRO_RANGO / FUERA_RANGO / REQUIERE_REVISION |
| Acciones | Ver detalle |

### Tab Rangos Vinos
| Columna | Descripción |
|---------|-------------|
| Orden | Orden de aplicación |
| Limite Inferior | Costo mínimo ($) |
| Limite Superior | Costo máximo ($) |
| Multiplicador | Factor (x2.5, x2.4, etc.) |
| Descripcion | Texto descriptivo |
| Estado | Activo/Inactivo |
| Acciones | Editar / Desactivar |

---

## 6. Funcionamiento VINOS_RANGOS

### Detección de Vino
Familias consideradas vino:
- B CHAMPAGNES Y COGNACS
- B VINOS, B VINOS DE POSTRE
- C CAVAS, CAVAS
- CHAMPAGNES Y COGNACS
- VINOS BLANCOS, TINTOS, ROSADOS
- VINOS ESPUMOSOS/POSTRE

### Cálculo
```
Si producto.familia IN FAMILIAS_VINO:
    costo_base = CostoBotella o CostoReceta
    
    Para cada rango en VINOS_RANGOS_MX:
        Si limite_inferior <= costo_base <= limite_superior:
            precio_sugerido = costo_base * multiplicador
            precio_sugerido = redondear_multiplo_5(precio_sugerido)
            fuente = "VINOS_RANGOS"
```

### Rangos Configurados (13 total)
| Rango | Multiplicador |
|-------|---------------|
| $0 - $500 | x2.5 |
| $500.01 - $750 | x2.4 |
| $750.01 - $1,000 | x2.3 |
| $1,000.01 - $1,250 | x2.2 |
| $1,250.01 - $1,500 | x2.1 |
| $1,500.01 - $1,750 | x2.0 |
| $1,750.01 - $2,000 | x1.9 |
| $2,000.01 - $2,500 | x1.8 |
| $2,500.01 - $2,750 | x1.7 |
| $2,750.01 - $3,000 | x1.6 |
| $3,000.01 - $4,000 | x1.5 |
| $4,000.01 - $6,000 | x1.4 |
| $6,000.01 - $20,000 | x1.3 |

---

## 7. Funcionamiento COSTO_MARGEN / IA_COMPETENCIA

### Para productos NO vino:
```python
Si costo_receta > 0 AND margen_objetivo > 0:
    precio_sugerido = costo_receta / (1 - margen_objetivo)
    precio_sugerido = redondear_multiplo_5(precio_sugerido)
    fuente = "COSTO_MARGEN"
```

### Margen objetivo configurable
- 25%, 30%, 35% (default), 40%, 45%

### Si no hay costo:
```
fuente = "SIN_DATOS"
precio_sugerido = null
```

---

## 8. Mantenimiento de Rangos de Vinos

### Funcionalidades
- ✅ Listar todos los rangos (activos e inactivos)
- ✅ Crear nuevo rango
- ✅ Editar rango existente
- ✅ Desactivar rango (soft delete)
- ✅ Activar rango previamente desactivado
- ✅ Detección de traslapes

### Validaciones
1. `limite_inferior >= 0`
2. `limite_superior > limite_inferior`
3. `multiplicador > 0`
4. No permite rangos activos traslapados
5. Auditoría: FechaCreacion, UsuarioCreacion, FechaModificacion, UsuarioModificacion

---

## 9. Validación de No Traslapes

El backend detecta automáticamente traslapes entre rangos activos:

```sql
-- Traslape si:
-- (nuevo_inf <= existente_sup) AND (nuevo_sup >= existente_inf)
```

Si se detecta traslape:
- POST crear: Rechaza con HTTP 400
- PUT editar: Rechaza con HTTP 400
- GET listar: Muestra alerta visual con rangos conflictivos

---

## 10. Evidencia CERO MongoDB

- ✅ Todas las tablas en EDARSAHUB SQL Server
- ✅ No hay importaciones de MongoDB en código nuevo
- ✅ Conexión exclusiva a `EDARSAHUB_CONFIG`
- ✅ Footer muestra "Fuente: EDARSAHUB_SQL"

---

## 11. Evidencia de No Modificación de Precios Oficiales

### En UI
- Banner púrpura: **"Precios Sugeridos = Recomendaciones. Los precios mostrados son sugerencias basadas en costos, márgenes y reglas configuradas. No modifican precios oficiales."**
- Modal de detalle: **"Importante: Este precio es una recomendación. No modifica el precio oficial del producto."**

### En Backend
- Endpoint `/precios-sugeridos` es solo lectura (GET)
- No hay escritura a `Sync_Productos.PrecioVenta`
- No hay escritura a tablas de SoftRestaurant o ManagementPro

---

## 12. Screenshots

### Tab Precios Sugeridos
- Banner informativo (púrpura)
- Filtros: Buscar, Fuente, Margen Obj., Solo vinos, Fuera de rango, Requiere revisión
- Tabla con columnas: Producto, Precio Actual, Costo, Margen %, Precio Sugerido, Fuente, Diferencia, Estado, Acciones
- Botón "Actualizar"

### Tab Rangos Vinos
- Banner informativo (ámbar) con "Regla: VINOS_RANGOS_MX"
- Botón "+ Nuevo Rango"
- Tabla con 13 rangos activos
- Columnas: Orden, Limite Inferior, Limite Superior, Multiplicador, Descripcion, Estado, Acciones
- Iconos de editar y desactivar por fila

### Modal Detalle Precio
- Precio actual vs precio sugerido
- Costo receta, margen actual
- Fuente de sugerencia (badge)
- Estado de revisión (badge)
- Rango de vinos aplicado (si aplica)
- Diferencia absoluta y porcentual
- Advertencia de "No modifica precio oficial"

---

## 13. Validaciones Funcionales

### Backend
| Validación | Estado |
|------------|--------|
| GET precios-sugeridos responde | ✅ |
| Vinos devuelven fuente VINOS_RANGOS | ✅ |
| No vinos devuelven COSTO_MARGEN | ✅ |
| Productos sin costo devuelven SIN_DATOS | ✅ |
| GET rangos de vinos funciona | ✅ |
| POST crear rango funciona | ✅ |
| PUT editar rango funciona | ✅ |
| PATCH desactivar funciona | ✅ |
| No permite traslapes | ✅ |
| CERO MongoDB | ✅ |

### Frontend
| Validación | Estado |
|------------|--------|
| Tab Precios Sugeridos visible | ✅ |
| Tab Rangos Vinos visible | ✅ |
| Tabla de productos carga | ✅ |
| Filtros funcionan | ✅ |
| Modal detalle abre | ✅ |
| Mantenimiento rangos funciona | ✅ |
| No modifica precio oficial | ✅ |
| Pricing IA sigue funcionando | ✅ |
| Comercial V2 sigue funcionando | ✅ |

---

## 14. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Productos sin costo no tienen sugerencia | BAJA | Mensaje claro "SIN_DATOS" |
| Vino sin familia correcta no aplica VINOS_RANGOS | MEDIA | Revisar catálogo de familias |
| Rangos eliminados por error | BAJA | Soft delete, se puede reactivar |

---

## 15. Recomendación para Siguiente Fase

1. **Integración con IA_COMPETENCIA**: Enriquecer sugerencias de no-vinos con benchmark de competidores
2. **Historial de sugerencias**: Guardar evolución de precios sugeridos
3. **Exportación a Excel**: Exportar análisis de precios sugeridos
4. **Alertas automáticas**: Notificar cuando productos críticos estén fuera de rango

---

## 16. Archivos Creados/Modificados

### Backend
- `/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py` (NUEVO)
- `/app/backend/modules/comercial/routes_precios_sugeridos.py` (NUEVO)
- `/app/backend/server.py` (MODIFICADO - registro de router)

### Frontend
- `/app/frontend/src/pages/comercial/CostosMargenes.jsx` (MODIFICADO - tabs y componentes)

---

**FASE 1C-3G-F COMPLETADA**

---

*Documento generado automáticamente - CRM COMERCIAL ENTERPRISE - EDARSA HUB*
