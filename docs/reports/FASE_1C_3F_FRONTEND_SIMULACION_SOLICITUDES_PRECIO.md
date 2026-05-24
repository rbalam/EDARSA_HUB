# FASE 1C-3F: Frontend de Simulación y Solicitudes de Precio

## Estado: COMPLETADO
**Fecha**: 24 de Mayo de 2026

---

## 1. Archivos Modificados

| Archivo | Descripción |
|---------|-------------|
| `/app/frontend/src/pages/comercial/CostosMargenes.jsx` | Reescrito completamente para añadir tabs, modal de simulación y vista de solicitudes |
| `/app/backend/modules/costos_margenes/routes_precios.py` | Añadido endpoint `/solicitudes-precio/{id}/cancelar` |

---

## 2. Componentes Creados/Modificados

### 2.1 Componentes Principales
- **`CostosMargenes`**: Componente principal con sistema de tabs
- **`TabProductos`**: Vista de resumen y tabla de productos (ya existía, refactorizado)
- **`TabSolicitudesPrecio`**: Nueva vista de solicitudes de cambio de precio
- **`SimulacionPrecioModal`**: Modal para simular nuevos precios
- **`DetalleSolicitudModal`**: Modal para ver detalle y ejecutar acciones

### 2.2 Componentes Auxiliares (Sin cambios)
- `RecetaModal`: Modal de visualización de receta
- `InsumosModal`: Modal de visualización de insumos

---

## 3. Tabs Implementados

### Tab 1: Resumen / Productos
- **Tarjetas de resumen**: Total Productos, Con Receta, Total Recetas, Total Insumos
- **Estado de sincronización**: Badge con fecha y estado (Sincronizado/Datos Antiguos/Sin Datos)
- **Filtros**: Búsqueda, Sistema origen, Solo con receta, Margen bajo
- **Tabla de productos**: Nombre, Sistema, Familia, Precio, Costo, Márgenes, Receta, Acciones
- **Paginación**: Navegación entre páginas

### Tab 2: Solicitudes de Precio
- **Filtros**: Estado, Solo mis solicitudes
- **Contador**: Total de solicitudes
- **Tabla de solicitudes**: Folio, Producto, Sistema, Precio Actual/Solicitado, Variación, Estado, Solicitante, Fecha, Acciones
- **Paginación**: Navegación entre páginas

---

## 4. Modal de Simulación

### Datos Mostrados:
- Información del producto (nombre, código, familia, sistema)
- Precio actual (o "Sin precio" si null)
- Costo actual (o "Sin costo" si null) con advertencia si no hay receta
- Margen actual ($ y %)

### Simulación en Tiempo Real:
- Campo de nuevo precio propuesto
- Nuevo margen calculado ($ y %)
- Variación calculada ($ y %)
- Advertencias automáticas:
  - Margen negativo (error)
  - Margen bajo <20% (warning)
  - Variación significativa >15% (info)

### Creación de Solicitud:
- Campo motivo (obligatorio, mínimo 5 caracteres)
- Campo justificación (opcional)
- Botón "Crear Solicitud"

---

## 5. Vista de Solicitudes

### Columnas:
| Columna | Descripción |
|---------|-------------|
| Folio | Identificador único de la solicitud |
| Producto | Nombre y código del producto |
| Sistema | SR (SoftRestaurant) o MPRO |
| Precio Actual | Precio vigente |
| Precio Solicitado | Precio propuesto |
| Variación | Porcentaje de cambio |
| Estado | Badge con estatus actual |
| Solicitante | Email del solicitante |
| Fecha | Fecha de solicitud |
| Acciones | Botón de ver detalle |

### Estados Soportados:
- `BORRADOR` (gris)
- `SOLICITADA` (azul)
- `EN_REVISION` (amarillo)
- `APROBADA` (verde)
- `RECHAZADA` (rojo)
- `APLICADA` (esmeralda)
- `CANCELADA` (gris oscuro)
- `ERROR_APLICACION` (naranja)

---

## 6. Endpoints Consumidos

| Método | Endpoint | Uso |
|--------|----------|-----|
| GET | `/costos-margenes/resumen` | Tarjetas de resumen |
| GET | `/costos-margenes/productos` | Tabla de productos con filtros |
| GET | `/costos-margenes/sync-status` | Estado de sincronización |
| GET | `/costos-margenes/productos/{id}/receta` | Modal de receta |
| GET | `/costos-margenes/productos/{id}/insumos` | Modal de insumos |
| GET | `/costos-margenes/solicitudes-precio` | Lista de solicitudes |
| GET | `/costos-margenes/solicitudes-precio/{id}` | Detalle de solicitud |
| GET | `/costos-margenes/solicitudes-precio/{id}/historial` | Historial de acciones |
| POST | `/costos-margenes/solicitudes-precio` | Crear nueva solicitud |
| POST | `/costos-margenes/solicitudes-precio/{id}/enviar` | Enviar para revisión |
| POST | `/costos-margenes/solicitudes-precio/{id}/aprobar` | Aprobar solicitud |
| POST | `/costos-margenes/solicitudes-precio/{id}/rechazar` | Rechazar solicitud |
| POST | `/costos-margenes/solicitudes-precio/{id}/aplicar` | Aplicar cambio |
| POST | `/costos-margenes/solicitudes-precio/{id}/cancelar` | Cancelar solicitud |

---

## 7. Reglas de Cálculo

```javascript
// Margen en pesos
margenPesos = precio - costo

// Margen porcentual
margenPorcentaje = (margenPesos / precio) * 100

// Variación en pesos
variacionPesos = precioNuevo - precioActual

// Variación porcentual
variacionPorcentaje = (variacionPesos / precioActual) * 100
```

### Advertencias:
- **MARGEN NEGATIVO**: Si `margenSimuladoPesos < 0`
- **MARGEN BAJO**: Si `margenSimuladoPct < 20%`
- **VARIACIÓN SIGNIFICATIVA**: Si `|variacionPct| > 15%`

---

## 8. Reglas de Permisos

### Acciones por Estado:
| Estado | Acciones Disponibles |
|--------|---------------------|
| BORRADOR | editar, enviar, cancelar |
| SOLICITADA | revisar, cancelar |
| EN_REVISION | aprobar, rechazar |
| APROBADA | aplicar, cancelar |
| RECHAZADA | (solo ver) |
| APLICADA | (solo ver) |
| CANCELADA | (solo ver) |
| ERROR_APLICACION | ver detalle |

### Roles RBAC (Backend):
- **Administrador/SuperAdministrador**: Todas las acciones
- **Solicitante**: Crear, enviar, cancelar propias
- **Autorizador**: Aprobar, rechazar
- **Modificador**: Aplicar cambios aprobados

---

## 9. Validaciones de Creación de Solicitud

1. ✅ Motivo obligatorio (mínimo 5 caracteres)
2. ✅ Precio propuesto > 0
3. ✅ Producto válido seleccionado
4. ✅ No permite solicitud sin datos básicos
5. ✅ Advertencia si el costo está `STALE` o no existe

---

## 10. Validaciones NO-LIVE

✅ **CONFIRMADO**: La pantalla consume únicamente endpoints de EDARSAHUB SQL.

**Prohibido y verificado que NO existe:**
- ❌ Consultas a SoftRestaurant en vivo
- ❌ Consultas a MPRO en vivo
- ❌ Consultas a Enterprise en vivo
- ❌ Uso de MongoDB
- ❌ Datos simulados como fuente real
- ❌ Modificación directa de precios sin flujo

---

## 11. Validaciones Sin MongoDB

✅ **CONFIRMADO**: No hay ninguna referencia a MongoDB en el componente.

El componente utiliza exclusivamente:
- API centralizada (`@/lib/api`)
- Endpoints que consultan SQL Server
- Formato de respuesta `source_type: "EDARSAHUB_SQL"`

---

## 12. Pruebas de No Regresión

| Validación | Estado |
|------------|--------|
| Login funciona | ✅ |
| Auth SQL-first funciona | ✅ |
| Menú SQL carga | ✅ |
| Comercial/Ventas carga | ✅ |
| `/comercial/costos-margenes` carga | ✅ |
| Tab Resumen/Productos funciona | ✅ |
| Tabla de productos funciona | ✅ |
| Modal de receta funciona | ✅ |
| Modal de insumos funciona | ✅ |
| Tab Solicitudes de Precio carga | ✅ |
| Modal de simulación abre | ✅ |
| Simulación calcula márgenes | ✅ |
| Simulación no modifica precio oficial | ✅ |
| Null se muestra como "Sin dato" | ✅ |
| No permite solicitud sin motivo | ✅ |
| No permite precio <= 0 | ✅ |
| Crea solicitud correctamente | ✅ |
| Lista solicitudes correctamente | ✅ |
| Acciones según estado | ✅ |
| Backend valida permisos (403) | ✅ |
| NO-LIVE confirmado | ✅ |
| Sin MongoDB | ✅ |

---

## 13. Bugs Pendientes

**Ninguno detectado.**

---

## 14. Cambios Técnicos Importantes

### Migración de Autenticación:
El componente se migró de usar `localStorage.getItem('token')` a usar el cliente API centralizado (`@/lib/api`) que:
- Obtiene el token de `sessionStorage` (clave: `edarsa_memory_token`)
- Adjunta automáticamente el header `Authorization: Bearer {token}`
- Maneja errores 401 con redirección a login

### Simplificación de Props:
Se eliminó la prop `token` de todos los componentes internos. Ahora cada componente usa directamente el cliente `api` importado.

---

## 15. Recomendación para Cierre de FASE 1C-3F

**RECOMENDACIÓN: CERRAR LA FASE 1C-3F COMO COMPLETADA**

✅ Backend: 100% implementado y probado (sesión anterior)
✅ Frontend: 100% implementado y probado (esta sesión)
✅ Integración: Verificada con capturas de pantalla
✅ NO-LIVE: Confirmado
✅ RBAC: Implementado en backend, respetado en frontend
✅ Sin regresiones detectadas

**Siguiente fase sugerida**: Validación de usuario final antes de proceder con el Job Nocturno de sincronización o Portal de Clientes.

---

*Reporte generado automáticamente - EDARSA HUB v1.0*
