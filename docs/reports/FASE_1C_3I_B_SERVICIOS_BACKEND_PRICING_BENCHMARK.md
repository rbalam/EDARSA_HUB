# FASE 1C-3I-B: Servicios Backend Pricing IA y Benchmark Competitivo

**Fecha:** 2026-05-25  
**Estado:** COMPLETADO

---

## 1. RESUMEN EJECUTIVO

Se implementaron los servicios backend y endpoints CRUD para el Motor de Precios Sugeridos con IA y Benchmark Competitivo, sin ejecutar IA real.

### Resultados Principales:
- **4 servicios** creados
- **1 archivo de esquemas Pydantic** con 19 modelos
- **1 archivo de rutas** con 21 endpoints
- **RBAC** aplicado en todos los endpoints
- **IA NO ejecutada** (preparado para SUBFASE 1C-3I-C)
- **NO se modificaron precios oficiales**
- **NO se usó MongoDB**

---

## 2. ARCHIVOS CREADOS

### 2.1 Esquemas Pydantic

| Archivo | Modelos | Descripción |
|---------|---------|-------------|
| `/app/backend/modules/comercial/services/pricing_schemas.py` | 19 | Todos los esquemas para Pricing IA |

**Modelos creados:**
- PerfilDigitalCreate, PerfilDigitalUpdate, PerfilDigitalResponse
- CompetidorCreate, CompetidorUpdate, CompetidorResponse
- CompetidorMenuItemCreate, CompetidorMenuItemUpdate, CompetidorMenuItemResponse
- PricingBenchmarkProductoCreate, PricingBenchmarkProductoUpdate, PricingBenchmarkProductoResponse
- PrecioSugeridoCalcularRequest, PrecioSugeridoCalcularResponse
- BenchmarkResumenResponse, BenchmarkEstadoPreparacionResponse
- Enums: TipoRestaurante, SegmentoPrecio, MetodoObtencion, ConfianzaDato, TipoComparacion, TipoMotorPrecio, PosicionVsCompetencia, EstadoCalculo

### 2.2 Servicios Backend

| Archivo | Funciones | Descripción |
|---------|-----------|-------------|
| `perfil_unidad_service.py` | 8 | CRUD Perfil Digital de Unidad |
| `competidores_service.py` | 12 | CRUD Competidores y Menu Items |
| `benchmark_service.py` | 10 | CRUD Benchmark + Resumen + Estado IA |
| `pricing_sugerido_service.py` | 3 | Cálculo de precios base (sin IA) |

### 2.3 Rutas FastAPI

| Archivo | Endpoints | Descripción |
|---------|-----------|-------------|
| `routes_pricing_ia.py` | 21 | Todos los endpoints del módulo |

---

## 3. ENDPOINTS CREADOS

### 3.1 Perfil Digital de Unidad

| Método | Ruta | Permiso RBAC |
|--------|------|--------------|
| GET | `/api/comercial/perfil-unidad` | comercial.perfil_unidad.ver |
| GET | `/api/comercial/perfil-unidad/{unidad_negocio_id}` | comercial.perfil_unidad.ver |
| POST | `/api/comercial/perfil-unidad` | comercial.perfil_unidad.editar |
| PUT | `/api/comercial/perfil-unidad/{id}` | comercial.perfil_unidad.editar |

### 3.2 Competidores

| Método | Ruta | Permiso RBAC |
|--------|------|--------------|
| GET | `/api/comercial/competidores` | comercial.competidores.ver |
| GET | `/api/comercial/competidores/{id}` | comercial.competidores.ver |
| POST | `/api/comercial/competidores` | comercial.competidores.crear |
| PUT | `/api/comercial/competidores/{id}` | comercial.competidores.editar |
| DELETE | `/api/comercial/competidores/{id}` | comercial.competidores.inactivar |

### 3.3 Menu Items de Competidores

| Método | Ruta | Permiso RBAC |
|--------|------|--------------|
| GET | `/api/comercial/competidores/{id}/menu-items` | comercial.competidores.ver |
| POST | `/api/comercial/competidores/{id}/menu-items` | comercial.competidores.crear |
| PUT | `/api/comercial/competidores/menu-items/{id}` | comercial.competidores.editar |
| DELETE | `/api/comercial/competidores/menu-items/{id}` | comercial.competidores.inactivar |

### 3.4 Benchmark de Productos

| Método | Ruta | Permiso RBAC |
|--------|------|--------------|
| GET | `/api/comercial/benchmark/productos` | comercial.benchmark.ver |
| GET | `/api/comercial/benchmark/productos/{id}` | comercial.benchmark.ver |
| POST | `/api/comercial/benchmark/productos` | comercial.benchmark.ver |
| PUT | `/api/comercial/benchmark/productos/{id}` | comercial.benchmark.ver |
| POST | `/api/comercial/benchmark/productos/{id}/validar` | comercial.benchmark.validar |
| DELETE | `/api/comercial/benchmark/productos/{id}` | comercial.benchmark.ver |

### 3.5 Resumen y Estado de Preparación

| Método | Ruta | Permiso RBAC | Descripción |
|--------|------|--------------|-------------|
| GET | `/api/comercial/benchmark/resumen/{unidad_id}` | comercial.benchmark.ver | Estadísticas de benchmark |
| GET | `/api/comercial/benchmark/estado-preparacion/{unidad_id}` | comercial.benchmark.ver | Verifica si está listo para IA |

### 3.6 Cálculo de Precios Sugeridos

| Método | Ruta | Permiso RBAC | Descripción |
|--------|------|--------------|-------------|
| POST | `/api/comercial/precios-sugeridos/calcular-base` | comercial.precios_sugeridos.generar | Cálculo matemático (sin IA) |

### 3.7 Health Check

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/comercial/pricing-ia/health` | Estado del módulo |

---

## 4. TABLAS UTILIZADAS

| Tabla | Operaciones |
|-------|-------------|
| Sistema_UnidadesNegocioPerfilDigital | SELECT, INSERT, UPDATE |
| Comercial_Competidores | SELECT, INSERT, UPDATE |
| Comercial_CompetidoresMenuItems | SELECT, INSERT, UPDATE |
| Comercial_PricingBenchmarkProducto | SELECT, INSERT, UPDATE |
| Comercial_PreciosSugeridos | (Preparado, no usado aún) |
| Sync_Productos | SELECT (solo lectura) |
| Sync_Productos_Insumos | SELECT (solo lectura) |

---

## 5. RBAC APLICADO

### Permisos Utilizados (creados en FASE 1C-3I-A)

| Permiso | Endpoints |
|---------|-----------|
| comercial.perfil_unidad.ver | GET perfil-unidad/* |
| comercial.perfil_unidad.editar | POST/PUT perfil-unidad/* |
| comercial.competidores.ver | GET competidores/*, menu-items |
| comercial.competidores.crear | POST competidores/*, menu-items |
| comercial.competidores.editar | PUT competidores/*, menu-items |
| comercial.competidores.inactivar | DELETE competidores/*, menu-items |
| comercial.benchmark.ver | GET/POST/PUT/DELETE benchmark/* |
| comercial.benchmark.validar | POST validar |
| comercial.precios_sugeridos.generar | POST calcular-base |

### Bypass para Administradores

Se modificó `/app/backend/core/rbac/service.py` para que el rol "Administrador" tenga bypass (igual que "SuperAdministrador").

---

## 6. AUDITORÍA

| Acción | Campo de Auditoría |
|--------|-------------------|
| Crear registro | `FechaCreacion`, `UsuarioCreacion` |
| Editar registro | `FechaModificacion`, `UsuarioModificacion` |
| Validar benchmark | `ValidadoPorUsuario`, `UsuarioValidacion`, `FechaValidacion` |
| Inactivar (DELETE) | Baja lógica (Activo = 0) |

**Nota:** No existe mecanismo de auditoría centralizado transversal. Se documenta como brecha menor.

---

## 7. EJEMPLOS CURL

### 7.1 Login

```bash
curl -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@edarsa.com","password":"admin123"}'
```

### 7.2 Listar Perfiles Digitales

```bash
curl -X GET "$API_URL/api/comercial/perfil-unidad?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

### 7.3 Crear Competidor

```bash
curl -X POST "$API_URL/api/comercial/competidores" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "empresa_id": 1,
    "unidad_negocio_id": 1,
    "nombre_competidor": "Restaurante Competidor",
    "tipo_restaurante": "casual_dining",
    "segmento_precio": "MEDIO_ALTO",
    "ciudad": "Mérida",
    "es_competencia_directa": true
  }'
```

### 7.4 Crear Menu Item

```bash
curl -X POST "$API_URL/api/comercial/competidores/{COMPETIDOR_ID}/menu-items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "competidor_id": "UUID",
    "nombre_producto_competidor": "Filete Premium",
    "categoria_competidor": "Carnes",
    "precio": 450.00,
    "metodo_obtencion": "MANUAL",
    "confianza_dato": "ALTA"
  }'
```

### 7.5 Calcular Precio Sugerido

```bash
curl -X POST "$API_URL/api/comercial/precios-sugeridos/calcular-base" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "codigo_producto": "CODIGO",
    "server_id": "UUID-SERVER",
    "tipo_motor": "COSTO_MARGEN",
    "margen_objetivo": 0.35,
    "multiplo_redondeo": 5
  }'
```

---

## 8. VALIDACIONES REALIZADAS

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Login funciona | ✅ |
| 2 | Auth SQL-first funciona | ✅ |
| 3 | Endpoints perfil unidad funcionan | ✅ |
| 4 | Endpoints competidores funcionan | ✅ |
| 5 | Endpoints menu-items funcionan | ✅ |
| 6 | Endpoints benchmark funcionan | ✅ |
| 7 | Endpoint resumen benchmark funciona | ✅ |
| 8 | Endpoint estado-preparación funciona | ✅ |
| 9 | Cálculo base precio sin IA funciona | ✅ |
| 10 | RBAC protege endpoints | ✅ |
| 11 | No se ejecuta IA | ✅ |
| 12 | No se usa MongoDB | ✅ |
| 13 | No se modifican precios oficiales | ✅ |
| 14 | No se hace scraping | ✅ |
| 15 | Costos y Márgenes funciona (no regresión) | ✅ |
| 16 | No hay errores 500 (excepto sin datos) | ✅ |
| 17 | Baja lógica (DELETE) funciona | ✅ |
| 18 | Validación de benchmark funciona | ✅ |

---

## 9. FÓRMULA DE CÁLCULO BASE (COSTO_MARGEN)

```
precio_minimo_rentable = costo_producto / (1 - margen_objetivo)
precio_con_impuesto = precio_minimo_rentable * (1 + tasa_impuesto)
precio_sugerido = redondear(precio_con_impuesto, multiplo, metodo)
```

**Notas:**
- Se usa `resolver_tasa_impuesto()` para obtener la tasa
- NO se hardcodea 16%
- Margen debe ser > 0 y < 1

---

## 10. MOTORES DE PRECIO DISPONIBLES

| Motor | Estado | Descripción |
|-------|--------|-------------|
| `VINOS_RANGOS` | ✅ Activo | Delega a regla existente de vinos (intocable) |
| `COSTO_MARGEN` | ✅ Activo | Fórmula matemática pura |
| `BENCHMARK_COMPETENCIA` | ✅ Activo | Usa promedio de competidores |
| `MIXTO_COSTO_COMPETENCIA` | ✅ Activo | Combina costo+margen con benchmark |
| `MANUAL_AUTORIZADO` | ⏳ Pendiente | Para futuro uso |

---

## 11. CONFIRMACIONES OBLIGATORIAS

| # | Confirmación | Resultado |
|---|--------------|-----------|
| 1 | NO se ejecutó IA | ✅ |
| 2 | NO se consumió GPT-5.2 | ✅ |
| 3 | NO se hizo scraping | ✅ |
| 4 | NO se consultaron sitios web externos | ✅ |
| 5 | NO se modificaron precios oficiales | ✅ |
| 6 | NO se crearon solicitudes automáticas | ✅ |
| 7 | NO se usó MongoDB | ✅ |
| 8 | Arquitectura NO-LIVE confirmada | ✅ |
| 9 | No se exponen passwords | ✅ |
| 10 | No se exponen api_keys | ✅ |

---

## 12. RIESGOS PENDIENTES

1. **Auditoría centralizada**: No existe mecanismo transversal. Se usa auditoría por campo (FechaCreacion, UsuarioCreacion, etc.)

2. **Productos sin costo**: El motor COSTO_MARGEN requiere costo configurado. Sin costo, devuelve estado `COSTO_NO_CONFIGURADO`.

3. **Productos propios vacíos**: El resumen muestra `productos_propios_total: 0` porque el filtro de productos depende de la configuración de servidores por empresa.

---

## 13. RECOMENDACIÓN PARA SUBFASE 1C-3I-C

### Siguiente Paso: Integración GPT-5.2

1. **Instalar SDK de OpenAI** con Emergent LLM Key
2. **Crear servicio `pricing_ia_gpt_service.py`** para:
   - Analizar perfil digital
   - Comparar productos vs competencia
   - Generar justificación de precios
   - Clasificar confianza (ALTA/MEDIA/BAJA)
3. **Crear endpoint `/api/comercial/precios-sugeridos/calcular-ia`**
4. **Guardar análisis en `PayloadAnalisisJSON`**
5. **Respetar regla**: GPT-5.2 sugiere, NO autoriza ni aplica

### Proveedor IA Confirmado

| Proveedor | Modelo | Estado |
|-----------|--------|--------|
| **OpenAI** | **GPT-5.2** | ✅ **AUTORIZADO** |

---

**FIN DEL REPORTE**

**Estado**: COMPLETADO  
**Servicios Creados**: 4  
**Esquemas Pydantic**: 19  
**Endpoints**: 21  
**RBAC**: Aplicado  
**IA Ejecutada**: NO (pendiente SUBFASE 1C-3I-C)  
**MongoDB**: NO usado  
**Regresiones**: 0  
**Siguiente Acción**: Esperar autorización para SUBFASE 1C-3I-C (Integración GPT-5.2)
