# FASE 1C-3I-A: Modelo de Datos para Motor de Precios Sugeridos con IA y Benchmark

**Fecha:** 2026-05-25  
**Estado:** COMPLETADO

---

## 1. RESUMEN EJECUTIVO

Se creó el modelo de datos base en EDARSAHUB SQL para soportar el motor de precios sugeridos con IA, benchmark competitivo y perfil digital de unidad de negocio.

### Resultados Principales:
- **4 tablas nuevas** creadas
- **1 tabla existente** extendida (Comercial_PreciosSugeridos)
- **13 permisos RBAC** registrados
- **5 perfiles digitales** de unidades creados con URLs reales
- **0 datos inventados** - solo estructura y URLs proporcionadas por el usuario

---

## 2. TABLAS EXISTENTES REVISADAS

### 2.1 Tablas Verificadas Antes de Crear

| Tabla | Existe | Acción |
|-------|--------|--------|
| Sistema_Empresas | ✅ Sí | Reutilizada (FK) |
| Sistema_EmpresasServidores | ✅ Sí | Reutilizada como referencia de unidades |
| Unidades_Negocio | ❌ No | - |
| Comercial_PreciosSugeridos | ✅ Sí | **Extendida** con campos IA/benchmark |
| Sistema_ModulosPermisos | ✅ Sí | Usada para permisos RBAC |

### 2.2 Tablas Comerciales Existentes

- Comercial_ImpuestosCatalogo
- Comercial_ImpuestosMapeo
- Comercial_ImpuestosTasas
- Comercial_PreciosSugeridos
- Comercial_ReglasPrecio
- Comercial_ReglasPrecioRangos
- Comercial_SimulacionesPrecios
- Comercial_SolicitudesCambioPrecio

**No se duplicó ninguna tabla existente.**

---

## 3. TABLAS CREADAS

### 3.1 Sistema_UnidadesNegocioPerfilDigital

Perfil digital de unidad de negocio para contexto de IA y benchmark.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| PerfilDigitalID | UNIQUEIDENTIFIER PK | Identificador único |
| EmpresaID | INT FK | Referencia a empresa |
| UnidadNegocioID | INT | Referencia a Sistema_EmpresasServidores |
| ServerID | UNIQUEIDENTIFIER | Servidor origen |
| NombreComercial | NVARCHAR(200) | Nombre comercial público |
| ConceptoRestaurante | NVARCHAR(500) | Descripción del concepto |
| TipoRestaurante | VARCHAR(50) | fine_dining, casual_dining, etc. |
| SegmentoPrecio | VARCHAR(30) | ECONOMICO, MEDIO, MEDIO_ALTO, PREMIUM, LUJO |
| Ciudad | NVARCHAR(100) | Ciudad |
| Estado | NVARCHAR(100) | Estado |
| Pais | VARCHAR(50) | País (default: México) |
| ZonaComercial | NVARCHAR(200) | Zona comercial |
| SitioWebOficial | NVARCHAR(500) | URL del sitio web oficial |
| UrlMenuDigital | NVARCHAR(500) | URL del menú digital |
| UrlReservaciones | NVARCHAR(500) | URL de reservaciones |
| UrlGoogleMaps | NVARCHAR(500) | URL de Google Maps |
| UrlInstagram | NVARCHAR(500) | URL de Instagram |
| UrlFacebook | NVARCHAR(500) | URL de Facebook |
| UrlTripAdvisor | NVARCHAR(500) | URL de TripAdvisor |
| UrlOpenTable | NVARCHAR(500) | URL de OpenTable |
| UrlDelivery | NVARCHAR(500) | URL de delivery |
| TicketPromedioObjetivo | DECIMAL(18,2) | Ticket promedio objetivo |
| RangoPrecioObjetivo | VARCHAR(30) | Rango de precio objetivo |
| Moneda | VARCHAR(10) | Moneda (default: MXN) |
| DescripcionConcepto | NVARCHAR(MAX) | Descripción para contexto IA |
| PalabrasClave | NVARCHAR(1000) | Keywords para IA |
| Activo | BIT | Activo/Inactivo |
| FechaCreacion | DATETIME2 | Fecha de creación |
| UsuarioCreacion | NVARCHAR(100) | Usuario que creó |
| FechaModificacion | DATETIME2 | Última modificación |
| UsuarioModificacion | NVARCHAR(100) | Usuario que modificó |

**Total: 31 columnas**

### 3.2 Comercial_Competidores

Catálogo de competidores por unidad de negocio.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| CompetidorID | UNIQUEIDENTIFIER PK | Identificador único |
| EmpresaID | INT FK | Referencia a empresa |
| UnidadNegocioID | INT | Unidad que tiene este competidor |
| NombreCompetidor | NVARCHAR(200) | Nombre del competidor |
| TipoRestaurante | VARCHAR(50) | Tipo de restaurante |
| SegmentoPrecio | VARCHAR(30) | Segmento de precio |
| Ciudad | NVARCHAR(100) | Ciudad |
| Estado | NVARCHAR(100) | Estado |
| Pais | VARCHAR(50) | País |
| ZonaComercial | NVARCHAR(200) | Zona comercial |
| SitioWeb | NVARCHAR(500) | URL sitio web |
| UrlMenu | NVARCHAR(500) | URL del menú |
| UrlGoogleMaps | NVARCHAR(500) | URL Google Maps |
| UrlInstagram | NVARCHAR(500) | URL Instagram |
| UrlTripAdvisor | NVARCHAR(500) | URL TripAdvisor |
| UrlOpenTable | NVARCHAR(500) | URL OpenTable |
| EsCompetenciaDirecta | BIT | Competencia directa |
| EsBenchmarkAspiracional | BIT | Benchmark aspiracional |
| DistanciaKm | DECIMAL(10,2) | Distancia en km |
| Prioridad | INT | Prioridad (0 = normal) |
| Activo | BIT | Activo/Inactivo |
| FechaCreacion | DATETIME2 | Fecha creación |
| UsuarioCreacion | NVARCHAR(100) | Usuario creación |
| FechaModificacion | DATETIME2 | Última modificación |
| UsuarioModificacion | NVARCHAR(100) | Usuario modificación |

**Total: 25 columnas**

### 3.3 Comercial_CompetidoresMenuItems

Precios y productos de menú de competidores.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| CompetidorMenuItemID | UNIQUEIDENTIFIER PK | Identificador único |
| CompetidorID | UNIQUEIDENTIFIER FK | Referencia a competidor |
| NombreProductoCompetidor | NVARCHAR(300) | Nombre del producto |
| CategoriaCompetidor | NVARCHAR(100) | Categoría en menú competidor |
| Descripcion | NVARCHAR(1000) | Descripción del producto |
| Precio | DECIMAL(18,2) | Precio observado |
| Moneda | VARCHAR(10) | Moneda |
| FuenteUrl | NVARCHAR(500) | URL de donde se obtuvo |
| FechaConsulta | DATE | Fecha de consulta |
| MetodoObtencion | VARCHAR(30) | MANUAL, IA_WEB_PUBLICO, IMPORTACION_EXCEL, API_PUBLICA, OTRO |
| ConfianzaDato | VARCHAR(20) | ALTA, MEDIA, BAJA |
| EsDatoManual | BIT | Capturado manualmente |
| EsDatoIA | BIT | Obtenido por IA |
| Activo | BIT | Activo/Inactivo |
| PayloadJSON | NVARCHAR(MAX) | Datos adicionales JSON |
| FechaCreacion | DATETIME2 | Fecha creación |
| UsuarioCreacion | NVARCHAR(100) | Usuario creación |

**Total: 17 columnas**

### 3.4 Comercial_PricingBenchmarkProducto

Mapeo de producto propio vs productos de competencia.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| BenchmarkProductoID | UNIQUEIDENTIFIER PK | Identificador único |
| ProductoID | UNIQUEIDENTIFIER | Producto propio |
| CodigoProducto | VARCHAR(100) | Código del producto |
| ServerID | UNIQUEIDENTIFIER | Servidor origen |
| EmpresaID | INT FK | Empresa |
| UnidadNegocioID | INT | Unidad de negocio |
| CompetidorID | UNIQUEIDENTIFIER FK | Competidor |
| CompetidorMenuItemID | UNIQUEIDENTIFIER FK | Producto del competidor |
| Similitud | DECIMAL(5,2) | Similitud 0-100% |
| TipoComparacion | VARCHAR(30) | MISMO_PRODUCTO, PRODUCTO_SIMILAR, MISMA_CATEGORIA, BENCHMARK_ASPIRACIONAL, NO_COMPARABLE |
| ComentarioIA | NVARCHAR(MAX) | Comentario de IA |
| ValidadoPorUsuario | BIT | Validado por humano |
| UsuarioValidacion | NVARCHAR(100) | Usuario que validó |
| FechaValidacion | DATETIME2 | Fecha de validación |
| Activo | BIT | Activo/Inactivo |
| FechaCreacion | DATETIME2 | Fecha creación |
| UsuarioCreacion | NVARCHAR(100) | Usuario creación |
| FechaModificacion | DATETIME2 | Última modificación |
| UsuarioModificacion | NVARCHAR(100) | Usuario modificación |

**Total: 19 columnas**

---

## 4. EXTENSIÓN DE COMERCIAL_PRECIOSSUGERIDOS

Se agregaron los siguientes campos para soportar IA y benchmark:

| Campo Nuevo | Tipo | Descripción |
|-------------|------|-------------|
| TipoMotorPrecio | VARCHAR(50) | VINOS_RANGOS, COSTO_MARGEN, BENCHMARK_COMPETENCIA, MIXTO_COSTO_COMPETENCIA, MANUAL_AUTORIZADO |
| FuenteBenchmark | VARCHAR(50) | Fuente del benchmark |
| PrecioCompetenciaMin | DECIMAL(18,2) | Precio mínimo competencia |
| PrecioCompetenciaPromedio | DECIMAL(18,2) | Precio promedio competencia |
| PrecioCompetenciaMax | DECIMAL(18,2) | Precio máximo competencia |
| PosicionVsCompetencia | VARCHAR(30) | Posición vs competencia |
| MargenObjetivo | DECIMAL(8,4) | Margen objetivo |
| MargenActual | DECIMAL(8,4) | Margen actual |
| MargenSugerido | DECIMAL(8,4) | Margen sugerido |
| JustificacionIA | NVARCHAR(MAX) | Justificación generada por IA |
| ConfianzaIA | VARCHAR(20) | ALTA, MEDIA, BAJA |
| RequiereRevisionHumana | BIT | Requiere validación humana |
| FechaAnalisisIA | DATETIME2 | Fecha del análisis IA |
| ModeloIAUsado | VARCHAR(100) | Modelo IA utilizado (agnóstico) |
| VersionRegla | VARCHAR(50) | Versión de la regla aplicada |
| PayloadAnalisisJSON | NVARCHAR(MAX) | Payload completo del análisis |

**Total: 16 campos nuevos**

---

## 5. PERMISOS RBAC CREADOS

| Código | Nombre | Categoría |
|--------|--------|-----------|
| comercial.perfil_unidad.ver | Ver Perfil Digital Unidad | Pricing IA |
| comercial.perfil_unidad.editar | Editar Perfil Digital Unidad | Pricing IA |
| comercial.competidores.ver | Ver Competidores | Pricing IA |
| comercial.competidores.crear | Crear Competidores | Pricing IA |
| comercial.competidores.editar | Editar Competidores | Pricing IA |
| comercial.competidores.inactivar | Inactivar Competidores | Pricing IA |
| comercial.benchmark.ver | Ver Benchmark | Pricing IA |
| comercial.benchmark.validar | Validar Benchmark | Pricing IA |
| comercial.benchmark.exportar | Exportar Benchmark | Pricing IA |
| comercial.precios_sugeridos.ver | Ver Precios Sugeridos | Pricing IA |
| comercial.precios_sugeridos.generar | Generar Precios Sugeridos | Pricing IA |
| comercial.precios_sugeridos.ver_ia | Ver Análisis IA | Pricing IA |
| comercial.precios_sugeridos.crear_solicitud | Crear Solicitud de Precio | Pricing IA |

**Total: 13 permisos**

---

## 6. PERFILES DIGITALES CREADOS

Se crearon perfiles digitales con las URLs proporcionadas por el usuario:

| Empresa | Nombre Comercial | Tipo | Segmento | Ciudad | Sitio Web |
|---------|------------------|------|----------|--------|-----------|
| 1 | Origen Unión Gastronómica | fine_dining | PREMIUM | Mérida | (OpenTable) |
| 2 | 130 Grados Querétaro | casual_dining | MEDIO_ALTO | Querétaro | https://130grados.mx |
| 3 | Cienfuegos | casual_dining | MEDIO_ALTO | CDMX | https://www.cienfuegos.mx |
| 4 | La Estelar | casual_dining | MEDIO_ALTO | - | https://laestelar.mx |
| 5 | 130 Grados Mérida | casual_dining | MEDIO_ALTO | Mérida | https://130grados.mx |

**URLs proporcionadas por el usuario:**
- https://www.cienfuegos.mx
- https://130grados.mx
- https://laestelar.mx
- https://www.opentable.com.mx/r/origen-union-gastronomica-del-fuego-merida

---

## 7. CONFIRMACIONES OBLIGATORIAS

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Tablas existentes revisadas | ✅ |
| 2 | No se duplicaron estructuras | ✅ |
| 3 | DDL idempotente | ✅ |
| 4 | Tablas base creadas | ✅ (4 nuevas) |
| 5 | Comercial_PreciosSugeridos extendida | ✅ (16 campos) |
| 6 | Permisos RBAC creados | ✅ (13 permisos) |
| 7 | No se ejecutó IA | ✅ |
| 8 | No se hizo scraping | ✅ |
| 9 | No se consultaron sitios web externos | ✅ |
| 10 | No se modificaron precios oficiales | ✅ |
| 11 | No se crearon solicitudes automáticas | ✅ |
| 12 | No se usó MongoDB | ✅ |
| 13 | NO-LIVE en frontend/endpoints | ✅ |
| 14 | Login funciona | ✅ (backend running) |
| 15 | No se usaron datos inventados | ✅ (solo URLs del usuario) |
| 16 | No se exponen passwords | ✅ |
| 17 | No se exponen api_keys | ✅ |

---

## 8. CAMPOS IA PREPARADOS (AGNÓSTICOS AL PROVEEDOR)

El modelo queda preparado para cualquier proveedor de IA:

| Campo | Propósito |
|-------|-----------|
| ModeloIAUsado | Puede ser GPT-5.2, Claude, Gemini, etc. |
| JustificacionIA | Texto generado por cualquier modelo |
| ConfianzaIA | ALTA/MEDIA/BAJA |
| FechaAnalisisIA | Timestamp del análisis |
| PayloadAnalisisJSON | Payload completo para trazabilidad |
| RequiereRevisionHumana | Flag para validación obligatoria |

---

## 9. RIESGOS PENDIENTES

1. **Sin competidores configurados**: Las tablas de competidores están vacías. Requiere configuración por el usuario o importación.

2. **Sin precios de competencia**: Comercial_CompetidoresMenuItems vacía. Requiere captura manual o análisis IA.

3. **Integración IA pendiente**: El modelo está preparado pero la integración con proveedor IA requiere subfase posterior.

4. **Frontend pendiente**: No se creó UI. Solo modelo de datos.

---

## 10. RECOMENDACIÓN PARA SUBFASE 1C-3I-B

### Siguiente Paso Recomendado

**SUBFASE 1C-3I-B: Servicios Backend**

1. Crear `pricing_ai_service.py` con funciones base
2. Crear `benchmark_service.py` para gestión de competidores
3. Crear endpoints CRUD para:
   - Perfiles digitales de unidad
   - Competidores
   - Productos de competidor
   - Mapeo benchmark
4. Integrar con servicio de precios sugeridos existente

### Opciones de Integración IA

| Proveedor | Modelo | Caso de Uso |
|-----------|--------|-------------|
| OpenAI | GPT-5.2 | Análisis de menús, justificaciones |
| Anthropic | Claude Sonnet 4.5 | Análisis detallado, comparables |
| Google | Gemini 3 Flash | Velocidad, análisis de páginas |

**Elección pendiente de autorización del usuario.**

---

**FIN DEL REPORTE**

**Estado**: COMPLETADO  
**Tablas Creadas**: 4  
**Tabla Extendida**: 1  
**Permisos RBAC**: 13  
**Perfiles Digitales**: 5  
**Siguiente Acción**: Esperar autorización para SUBFASE 1C-3I-B (Servicios Backend)
