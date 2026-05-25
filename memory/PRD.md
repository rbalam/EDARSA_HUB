# EDARSA HUB - Product Requirements Document

## Problema Original
Sistema ERP integrado para EDARSA con CRM Comercial Enterprise, conectado a múltiples fuentes de datos SQL Server (MPRO, SoftRestaurant, EDARSAHUB).

## Máximas del Proyecto
1. **EDARSAHUB SQL Server es el cerebro absoluto** - CERO dependencias de MongoDB
2. **Política de Autorización Controlada** - No asumir reglas; esperar autorización explícita
3. **No Testing Agent** - Pruebas exclusivas vía cURL, bash, python -c

## Arquitectura Técnica
- **Frontend**: React (`/app/frontend/src/`)
- **Backend**: FastAPI (`/app/backend/`)
- **Base de Datos Principal**: EDARSAHUB SQL Server (54.39.104.176)
- **Legacy (ELIMINADO)**: MongoDB → Reemplazado por StubDatabase

## Credenciales de Prueba
- Admin: `admin@edarsa.com` / `admin123`

---


### ✅ BUG-COMPETIDORES-001: Campos No Guardados + Redes Sociales - RESUELTO

**Fecha:** 2026-05-25

#### Problema Reportado:
1. "Ubicación de Referencia" y "Nivel de Precio" no se guardaban al editar competidor
2. Usuario solicitó agregar campos para monitoreo de redes sociales

#### Causa Raíz:
El frontend usaba nombres de campos incorrectos:
- `tipo_negocio` → debía ser `tipo_restaurante`
- `nivel_precio_percibido` → debía ser `segmento_precio`
- `ubicacion_referencia` → debía ser `zona_comercial`

#### Solución Implementada:
1. **Backend:** Agregadas columnas `UrlFacebook` y `Notas` a `Comercial_Competidores`
2. **Backend:** Actualizado schema y service para manejar nuevos campos
3. **Frontend:** Corregido mapeo de campos en `CompetidorModal`
4. **Frontend:** Agregada sección "Redes Sociales y Monitoreo" con:
   - Google Maps, Instagram, Facebook, TripAdvisor, OpenTable

#### Archivos Modificados:
- `/app/backend/modules/comercial/services/pricing_schemas.py`
- `/app/backend/modules/comercial/services/competidores_service.py`
- `/app/frontend/src/pages/comercial/PricingIA.jsx`

#### Archivos Creados:
- `/app/backend/scripts/ddl_competidores_nuevos_campos.py`
- `/app/docs/reports/BUG_COMPETIDORES_CAMPOS_NO_GUARDADOS_FIX.md`


### ✅ COSTOS-ALERTAS-001-C: Servicios Backend Reglas de Margen - COMPLETADO

**Fecha:** 2026-05-25

#### Implementado:
1. **Repository** (`alertas_margen_repository.py`): CRUD SQL + Lógica jerárquica
2. **Service** (`alertas_margen_service.py`): Validaciones de negocio
3. **Routes** (`routes_alertas_margen.py`): 9 endpoints REST
4. **Router registrado** en `server.py`

#### Endpoints:
- `GET/POST /api/comercial/alertas-margen/reglas` - CRUD reglas
- `GET /api/comercial/alertas-margen/resolver-regla` - Jerarquía Producto>Subfamilia>Familia>Grupo
- `POST /api/comercial/alertas-margen/evaluar` - Evaluar margen vs esperado
- `GET /api/comercial/alertas-margen/umbrales` - Umbrales de severidad
- `GET /api/comercial/alertas-margen/estadisticas` - Stats de reglas

#### Pruebas curl: ✅ EXITOSAS
- Crear reglas GRUPO/FAMILIA/PRODUCTO
- Resolución jerárquica correcta
- Evaluación de margen con severidad

#### Reporte:
- `/app/docs/reports/COSTOS_ALERTAS_001C_SERVICIOS_REGLAS_MARGEN.md`

---

### ✅ FASE 1C-3I-B v2: Corrección Arquitectónica Competidores Enterprise - COMPLETADO

**Fecha:** 2026-05-25

#### Problema Resuelto:
EDARSAHUB es multiempresa/multiunidad. Los competidores NO deben ser globales - cada unidad tiene sus propios competidores según ciudad, zona, mercado local.

#### Arquitectura Implementada:
1. **`Comercial_CompetidoresCatalogo`**: Catálogo maestro (datos únicos del competidor)
2. **`Comercial_CompetidoresUnidad`**: Relación competidor-unidad (prioridad, tipo relación)
3. **`vw_CompetidoresPorUnidad`**: Vista consolidada

#### Ventajas:
- Un competidor puede estar en múltiples unidades con diferente configuración
- Filtro OBLIGATORIO por `UnidadNegocioID` en todas las consultas
- RBAC limita acceso por unidad

#### Endpoints Enterprise:
- `POST /api/comercial/competidores-catalogo` - Crear en catálogo maestro
- `POST /api/comercial/competidores-unidad/relacionar` - Relacionar con unidad
- `GET /api/comercial/competidores?unidad_negocio_id=X` - Listar por unidad

#### Archivos:
- `/app/backend/scripts/ddl_competidores_enterprise_unidad.py`
- `/app/backend/modules/comercial/services/competidores_enterprise_service.py`
- `/app/backend/modules/comercial/routes_competidores_enterprise.py`

#### Reporte:
- `/app/docs/reports/FASE_1C_3I_B_COMPETIDORES_ENTERPRISE_UNIDAD.md`

---

### ✅ COSTOS-ALERTAS-001-D: UI Reglas de Margen - COMPLETADO

**Fecha:** 2026-05-25

#### Implementado:
1. **Tab "Reglas de Margen"** en Costos y Márgenes (5to tab)
2. **Vista principal** con estadísticas, umbrales, tabla de reglas y jerarquía visual
3. **Modal Nueva/Editar Regla** con selector de nivel, margen, severidad
4. **Modal Resolver Regla** para probar jerarquía
5. **Modal Evaluar Margen** para evaluar margen vs esperado

#### Funcionalidades:
- Ver, crear, editar, desactivar reglas
- Resolver regla por jerarquía (Producto > Subfamilia > Familia > Grupo)
- Evaluar margen individual
- Filtrar por nivel, buscar por código
- Visualización de umbrales de severidad

#### Archivos:
- `/app/frontend/src/pages/comercial/TabReglasMargen.jsx` (NUEVO)
- `/app/frontend/src/pages/comercial/CostosMargenes.jsx` (MODIFICADO)

#### Reporte:
- `/app/docs/reports/COSTOS_ALERTAS_001D_UI_REGLAS_MARGEN_DESTINATARIOS.md`

---



---

## Estado Actual (Mayo 2026)

### ✅ Mejoras UI Costos y Márgenes - COMPLETADO

**Fecha:** 2026-05-25

#### Cambios Implementados:
1. **% Margen bajo ahora es editable** - Input numérico junto al checkbox (default 20%)
2. **Botón "Agrupar" en Precios Sugeridos** - Vista agrupada por familia igual que Resumen/Productos
3. **Badges de estado** - SUSPENDIDO/BAJA (rojo), Precio $0 (amarillo)

#### Archivos Modificados:
- `CostosMargenes.jsx` - Estado `umbralMargenBajo`, input editable, vista agrupada en TabPreciosSugeridos
- `routes.py` - Nuevo parámetro `umbral_margen`
- `repository.py` - Query con umbral dinámico

---

### ✅ BUG-COSTOS-001-R2: Corrección Filtro Estado Producto - RESUELTO

**Fecha:** 2026-05-25

#### Problema:
El filtro anterior usaba `PrecioVenta > 0` como criterio de activo, lo cual es INCORRECTO.
Un producto puede tener precio $0 y estar ACTIVO (pendiente de configuración).

#### Solución:
- **Retirado:** Filtro `p.PrecioVenta > 0`
- **Correcto:** Solo usar `p.Activo = 1`
- **SoftRestaurant:** Campo `suspendido` → `Activo` (suspendido=1 → Activo=0)
- **ManagementPro:** Campo `Es_Cve_Estado` → `Activo` (AC=1, BA/IN=0)
- **UI:** Badges "SUSPENDIDO"/"BAJA" (rojo) y "Precio $0" (amarillo)

#### Archivos Modificados:
- `repository.py` - Filtro corregido, campo `activo` agregado
- `precios_sugeridos_consolidado_service.py` - Filtro corregido, campo `activo` agregado
- `sync_recetas.py` - MPRO trae todos los productos y mapea `Es_Cve_Estado`
- `CostosMargenes.jsx` - Badges de estado

#### Acción Requerida:
⚠️ Ejecutar resincronización para actualizar campo `Activo` en Sync_Productos.

#### Archivo de Reporte:
- `/app/docs/reports/BUG_COSTOS_001_R2_ESTADO_PRODUCTO_SUSPENDIDO_BAJA_NO_PRECIO_CERO.md`

---

### ✅ BUG-COSTOS-001: Filtrado de Productos Inactivos/Baja - RESUELTO (Fix Extendido)

**Fecha:** 2026-05-25

#### Problema Reportado:
CLAM CHOWDER (producto suspendido con Precio $0 en SoftRestaurant) aparecía en Costos y Márgenes aunque el checkbox "Incluir inactivos/baja" NO estaba marcado.

#### Causa Raíz:
El job `sync_recetas.py` NO sincronizaba el campo `Suspendido` de SoftRestaurant → el campo `Activo` siempre era `1`.

#### Solución Implementada (Dos Niveles):

**Nivel A (Workaround Inmediato):**
- Filtro adicional `p.PrecioVenta > 0` (productos con precio $0 típicamente están suspendidos)
- Aplicado en: `repository.py`, `precios_sugeridos_consolidado_service.py`

**Nivel B (Fix Definitivo - Sync):**
- Modificado `sync_recetas.py` para traer `productosdetalle.suspendido` de SoftRestaurant
- MERGE ahora actualiza campo `Activo` basado en `Suspendido`
- Modelo `ProductoSync` extendido con campo `activo: bool`

#### Archivos Modificados:
- `/app/backend/modules/costos_margenes/repository.py`
- `/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py`
- `/app/backend/modules/sync_recetas/models.py`
- `/app/backend/modules/sync_recetas/sync_recetas.py`

#### Acción Requerida:
⚠️ Ejecutar resincronización de productos para actualizar campo `Activo` en Sync_Productos.

#### Archivo de Reporte:
- `/app/docs/reports/BUG_COSTOS_001_FILTRADO_PRODUCTOS_INACTIVOS_BAJA.md`

---

### 🔵 FASE COSTOS-ALERTAS-001: Diagnóstico Completado - EN ESPERA DE AUTORIZACIÓN

**Fecha:** 2026-05-25

#### Diagnóstico Realizado:
- **¿Existen tablas de snapshots/históricos de recetas?** NO
- Email: Configurado (SMTP Neubox)
- WhatsApp: Configurado (Twilio Sandbox) pero sin número destino
- DDL propuesto para 6 tablas nuevas
- Jerarquía de resolución: Producto > Subfamilia > Familia > Grupo

#### Archivo de Diagnóstico:
- `/app/docs/reports/COSTOS_ALERTAS_001_DIAGNOSTICO_PREVIO_IMPLEMENTACION.md`

#### Pendiente:
- Autorización para ejecutar DDL
- Implementación de backend (repository, service, job)
- Implementación de frontend (nueva pestaña "Alertas de Margen")

---

### ✅ FASE COSTOS-ALERTAS-001-B: DDL de Alertas de Margen y Snapshots - COMPLETADO

**Fecha:** 2026-05-25

#### Tablas Creadas (7):
1. `Comercial_AlertasMargenReglas` - Reglas de margen esperado por nivel
2. `Comercial_AlertasMargenEventos` - Eventos de alerta detectados
3. `Comercial_AlertasMargenDestinatarios` - Destinatarios de alertas
4. `Comercial_AlertasMargenEnvios` - Registro de envíos
5. `Comercial_AlertasUmbralesSeveridad` - Configuración de severidades (4 umbrales insertados)
6. `Comercial_RecetasSnapshot` - Fotografías históricas de recetas
7. `Comercial_RecetasSnapshotDetalle` - Detalle de snapshots

#### Validaciones:
- ✅ DDL idempotente
- ✅ CERO MongoDB
- ✅ No se modificaron precios/recetas
- ✅ Login funciona
- ✅ Jerarquía soportada: Producto > Subfamilia > Familia > Grupo

#### Archivo de Reporte:
- `/app/docs/reports/COSTOS_ALERTAS_001B_DDL_ALERTAS_MARGEN_SNAPSHOTS.md`

#### Próxima Fase:
- **COSTOS-ALERTAS-001-C:** Servicios backend para reglas de margen (repository, service, routes)

---

### ✅ FASE 1C-3G-F: Precios Sugeridos en Costos y Márgenes + Rangos Vinos - COMPLETADO

**Fecha:** 2026-05-25

#### Resumen
Se integró el sistema de precios sugeridos directamente en la pantalla de Costos y Márgenes, permitiendo ver recomendaciones de precio basadas en reglas configuradas (VINOS_RANGOS para vinos, COSTO_MARGEN para otros productos).

#### Backend Creado:
- Endpoint `GET /api/comercial/pricing/precios-sugeridos` - Lista productos con precio sugerido calculado
- CRUD completo para rangos de vinos:
  - `GET /api/comercial/pricing/reglas/vinos/rangos`
  - `POST/PUT/PATCH` para crear/editar/desactivar rangos
- Validación de traslapes entre rangos
- Detección automática de vinos por familia

#### Frontend Modificado:
- `CostosMargenes.jsx`: Nuevos tabs "Precios Sugeridos" y "Rangos Vinos"
- Tabla de productos con columnas: Precio Sugerido, Fuente, Diferencia, Estado
- Modal de detalle de cálculo
- Mantenimiento de rangos de vinos (crear, editar, desactivar)

#### Fuentes de Sugerencia:
- `VINOS_RANGOS`: Multiplicadores según costo botella (13 rangos configurados)
- `COSTO_MARGEN`: Fórmula: costo / (1 - margen_objetivo)
- `SIN_DATOS`: Sin costo suficiente

#### Archivo de Reporte:
- `/app/docs/reports/FASE_1C_3G_F_PRECIOS_SUGERIDOS_COSTOS_MARGENES_RANGOS_VINOS.md`

---

### ✅ FASE 1C-3I-H: Listas de Competidores como Filtro en IA - COMPLETADO

**Fecha:** 2026-05-25

#### Resumen
Se integró el sistema de listas de competidores como filtro opcional en los análisis de IA y Benchmark. Los usuarios pueden ahora seleccionar una lista específica para limitar el contexto de análisis.

#### Cambios Backend:
- `analizar_benchmark_con_ia`: Añadido parámetro `lista_id`
- `_obtener_competidores_para_contexto`: Fix comparación case-insensitive de UUIDs
- Validación de lista activa y con competidores
- Persistencia de `ListaCompetidoresID` en SQL Server
- Retorno de `lista_usada` en respuesta JSON

#### Cambios Frontend:
- `AnalisisIAProductoModal`: Añadido selector de lista de competidores
- `AnalisisBenchmarkModal`: Nuevo modal dedicado con selector de lista
- `ResultadoAnalisisModal`: Muestra lista usada si aplica

#### Validaciones Realizadas:
- ✅ Benchmark con lista funciona
- ✅ Benchmark sin lista funciona (general)
- ✅ Análisis producto con lista funciona
- ✅ Validación de lista inactiva
- ✅ Validación de lista vacía

#### Archivo de Reporte:
- `/app/docs/reports/FASE_1C_3I_H_LISTAS_COMPETIDORES_FILTRO_IA_BENCHMARK.md`

---

### ✅ FASE 1C-3I-F: Visualización Avanzada y Exportación - COMPLETADO

**Fecha:** 2026-05-25

#### Resumen
Se implementaron gráficas interactivas con Recharts y exportación a Excel para el Dashboard de Métricas IA.

#### Gráficas Implementadas:
- **LineChart**: Análisis por día (tendencia 30 días)
- **PieChart**: Distribución de confianza (ALTA/MEDIA/BAJA)
- **BarChart**: Top productos analizados

#### Exportación:
- Botón "Exportar Excel" genera archivo `.xlsx` con 5 hojas de métricas
- PDF dejado como P2 (sin infraestructura estable)

#### Archivo de Reporte:
- `/app/docs/reports/FASE_1C_3I_F_VISUALIZACION_EXPORTACION_PRICING_IA.md`

---

### ✅ FASE 1C-3I-G: Listas Manuales de Competidores - COMPLETADO

**Fecha:** 2026-05-25

#### Resumen
Se implementó el sistema de listas manuales para agrupar competidores por ciudad, segmento o estrategia comercial.

#### Tablas SQL Creadas:
- `Comercial_CompetidoresListas`: Tabla principal
- `Comercial_CompetidoresListasDetalle`: Relación lista-competidor

#### Endpoints Creados (9):
- CRUD listas: GET/POST/PUT/DELETE `/api/comercial/pricing/listas-competidores`
- Gestión competidores: GET/POST/DELETE `.../competidores`

#### Componentes Frontend:
- `TabListasCompetidores`: Nueva pestaña "Listas"
- `ListaCompetidoresModal`: Crear/editar listas
- `AgregarCompetidoresModal`: Gestionar miembros

#### Funcionalidades:
- Un competidor puede estar en múltiples listas
- Constraint SQL evita duplicados dentro de una lista
- Color identificador por lista
- Contador de competidores

#### Archivo de Reporte:
- `/app/docs/reports/FASE_1C_3I_G_LISTAS_MANUALES_COMPETIDORES_PRICING_IA.md`

---

### ✅ FASE 1C-3I-E: Dashboard de Métricas IA Pricing - COMPLETADO

**Fecha:** 2026-05-25  
**Componentes:** 
- Backend: `/app/backend/modules/comercial/services/metricas_ia_service.py`
- Frontend: `TabDashboardIA` en `PricingIA.jsx`

#### Resumen
Se implementó el dashboard ejecutivo de métricas IA dentro del módulo Pricing IA, mostrando estadísticas en tiempo real desde EDARSAHUB SQL.

#### Endpoints Creados:
- `GET /api/comercial/pricing-ai/dashboard/metricas`
- `GET /api/comercial/pricing-ai/dashboard/estadisticas-competidores`

#### Métricas Implementadas:
1. Total de análisis IA realizados
2. Análisis por día (últimos 30 días)
3. Productos más analizados (top 10)
4. Distribución de confianza (ALTA/MEDIA/BAJA con barras de progreso)
5. Cantidad de análisis que requieren revisión humana
6. Competidores más usados en benchmark
7. Últimos análisis realizados (top 15)
8. Promedio precio sugerido vs actual
9. Porcentaje de recomendaciones con confianza alta

#### Componentes UI:
- 5 tarjetas KPI gradiente (Total, Confianza Alta, Revisión, Hoy, Mes)
- Panel de distribución de confianza con barras
- Panel de comparación precios sugerido vs actual
- Estadísticas de benchmark (competidores, items, categorías)
- Tablas de productos más analizados y últimos análisis
- Badges de competidores más usados

#### Confirmaciones:
- ✅ Datos desde EDARSAHUB SQL (tabla Comercial_PricingAnalisisIA)
- ✅ No usa MongoDB
- ✅ No modifica precios oficiales
- ✅ No expone secretos
- ✅ Sin regresiones en tabs existentes

#### Archivo de Reporte:
- `/app/docs/reports/FASE_1C_3I_E_DASHBOARD_METRICAS_IA_PRICING.md`

---

### ✅ FASE 1C-3I-D: Frontend Motor de Precios Sugeridos IA - COMPLETADO

**Fecha:** 2026-05-25  
**Componente:** `/app/frontend/src/pages/comercial/PricingIA.jsx`  
**Ruta:** `/comercial/pricing-ia`

#### Resumen
Se implementó el frontend completo para el Motor de Precios Sugeridos IA y Benchmark, con interfaz para gestionar competidores, capturar precios, solicitar análisis IA y visualizar resultados.

#### Archivos Creados:
| Archivo | Propósito |
|---------|-----------|
| `PricingIA.jsx` | Componente principal (~1,800 líneas) |
| `FASE_1C_3I_D_FRONTEND_PRICING_IA_BENCHMARK.md` | Reporte de implementación |

#### Archivos Modificados:
| Archivo | Cambio |
|---------|--------|
| `App.js` | Nueva ruta `/comercial/pricing-ia` |
| `Layout.js` | Enlace "Pricing IA" en menú Comercial |

#### Funcionalidades UI:
- **Tab Competidores**: CRUD de competidores, badges tipo/nivel precio
- **Tab Precios Competencia**: Captura manual de precios de competidores
- **Tab Análisis IA**: Botones "Analizar Producto" y "Analizar Benchmark"
- **Tab Historial**: Consulta de análisis previos desde SQL

#### Componentes Visuales:
- `ConfianzaBadge`: ALTA (verde), MEDIA (amarillo), BAJA (rojo)
- `RevisionHumanaBadge`: Indicador naranja obligatorio
- Modales para crear/editar competidores, precios y análisis IA
- Cards de resumen con métricas de benchmark

#### Confirmaciones:
- ✅ No usa MongoDB
- ✅ No modifica precios oficiales
- ✅ No expone claves/secretos
- ✅ Alertas visuales de "RECOMENDACIONES"
- ✅ Sin regresiones en módulos existentes

#### Archivo de Reporte:
- `/app/docs/reports/FASE_1C_3I_D_FRONTEND_PRICING_IA_BENCHMARK.md`

---

### ✅ FASE 1C-3I-C: Integración GPT-5.2 para Pricing IA - COMPLETADO

**Fecha:** 2026-05-25  
**Modelo IA:** GPT-5.2 (OpenAI via Emergent LLM Key)  
**Regla:** GPT-5.2 sugiere, NO autoriza ni aplica precios

#### Resumen
Se integró GPT-5.2 como proveedor IA oficial para análisis de pricing y benchmark competitivo. Todo se guarda en EDARSAHUB SQL (sin MongoDB).

#### Archivos Creados:
| Archivo | Propósito |
|---------|-----------|
| `pricing_ai_service.py` | Servicio de integración GPT-5.2 (~1300 líneas) |
| `routes_pricing_ai.py` | 5 endpoints IA FastAPI |

#### Endpoints IA Creados:
| Endpoint | Descripción |
|----------|-------------|
| `POST /api/comercial/pricing-ai/analizar-producto` | Análisis completo con justificación |
| `POST /api/comercial/pricing-ai/sugerir-comparables` | Sugerir productos comparables |
| `POST /api/comercial/pricing-ai/generar-justificacion` | Justificar precio propuesto |
| `POST /api/comercial/pricing-ai/analizar-benchmark` | Análisis estratégico de benchmark |
| `GET /api/comercial/pricing-ai/analisis/{id}` | Recuperar análisis guardado |

#### Tabla de Auditoría:
- `Comercial_PricingAnalisisIA` (DDL idempotente, se crea automáticamente)

#### Sistema de Confianza:
| Nivel | Criterio |
|-------|----------|
| ALTA | Costo + precio + benchmark + datos validados |
| MEDIA | Costo + impuesto, benchmark parcial |
| BAJA | Faltan datos, requiere revisión humana |

#### Confirmaciones:
- ✅ GPT-5.2 sugiere, NO autoriza ni aplica
- ✅ NO se usa MongoDB
- ✅ NO se hace scraping
- ✅ NO se modifican precios oficiales
- ✅ NO se crean solicitudes automáticas
- ✅ Regla de vinos intacta

#### Archivos:
- `/app/docs/reports/FASE_1C_3I_C_INTEGRACION_GPT52_PRICING_BENCHMARK.md`

---

### ✅ FASE 1C-3I-B: Servicios Backend Pricing IA y Benchmark - COMPLETADO

**Fecha:** 2026-05-25  
**Proveedor IA Autorizado:** GPT-5.2 (OpenAI) - NO ejecutado en esta fase

#### Resumen
Se implementaron los servicios backend y endpoints CRUD para el Motor de Precios Sugeridos con IA y Benchmark Competitivo, sin ejecutar IA real.

#### Archivos Creados:
| Archivo | Propósito |
|---------|-----------|
| `pricing_schemas.py` | 19 esquemas Pydantic |
| `perfil_unidad_service.py` | CRUD Perfil Digital |
| `competidores_service.py` | CRUD Competidores y Menu Items |
| `benchmark_service.py` | CRUD Benchmark + Resumen + Estado IA |
| `pricing_sugerido_service.py` | Cálculo precios base (sin IA) |
| `routes_pricing_ia.py` | 21 endpoints FastAPI |

#### Endpoints Creados:
- **Perfil Digital**: GET/POST/PUT `/api/comercial/perfil-unidad/*`
- **Competidores**: GET/POST/PUT/DELETE `/api/comercial/competidores/*`
- **Menu Items**: GET/POST/PUT/DELETE `/api/comercial/competidores/{id}/menu-items/*`
- **Benchmark**: GET/POST/PUT/DELETE `/api/comercial/benchmark/productos/*`
- **Resumen**: GET `/api/comercial/benchmark/resumen/{unidad_id}`
- **Estado IA**: GET `/api/comercial/benchmark/estado-preparacion/{unidad_id}`
- **Cálculo Base**: POST `/api/comercial/precios-sugeridos/calcular-base`

#### Motores de Precio:
| Motor | Estado | Descripción |
|-------|--------|-------------|
| VINOS_RANGOS | ✅ Activo | Regla de rangos existente |
| COSTO_MARGEN | ✅ Activo | precio = costo/(1-margen) |
| BENCHMARK_COMPETENCIA | ✅ Activo | Promedio competidores |
| MIXTO_COSTO_COMPETENCIA | ✅ Activo | Combina ambos |

#### Subfases Actualizadas:
| Subfase | Estado | Descripción |
|---------|--------|-------------|
| 1C-3I-A | ✅ Completado | Modelo de Datos DDL |
| 1C-3I-B | ✅ Completado | Servicios Backend + Endpoints |
| 1C-3I-C | ✅ Completado | Integración GPT-5.2 |
| 1C-3I-D | ⏳ Pendiente | Frontend |

#### Confirmaciones:
- ✅ NO se ejecutó IA
- ✅ NO se usó MongoDB
- ✅ RBAC aplicado en todos los endpoints
- ✅ Baja lógica para DELETE
- ✅ Costos y Márgenes funciona (no regresión)

#### Archivos:
- `/app/docs/reports/FASE_1C_3I_B_SERVICIOS_BACKEND_PRICING_BENCHMARK.md`

---

### ✅ FASE 1C-3I-A: Modelo de Datos Pricing IA y Benchmark - COMPLETADO

**Fecha:** 2026-05-25  
**Proveedor IA Autorizado:** GPT-5.2 (OpenAI)

#### Resumen
Se creó el modelo de datos base en EDARSAHUB SQL para soportar el motor de precios sugeridos con IA, benchmark competitivo y perfil digital de unidad de negocio.

#### Tablas Creadas:
| Tabla | Columnas | Propósito |
|-------|----------|-----------|
| Sistema_UnidadesNegocioPerfilDigital | 31 | Perfil digital de unidad (URLs, concepto, segmento) |
| Comercial_Competidores | 25 | Catálogo de competidores |
| Comercial_CompetidoresMenuItems | 17 | Precios de menú de competidores |
| Comercial_PricingBenchmarkProducto | 19 | Mapeo producto vs competencia |

#### Tabla Extendida:
- **Comercial_PreciosSugeridos**: +16 campos para IA/benchmark

#### Permisos RBAC: 13 permisos en categoría "Pricing IA"

#### Perfiles Digitales Creados (URLs reales del usuario):
- Cienfuegos (https://www.cienfuegos.mx)
- 130 Grados Querétaro/Mérida (https://130grados.mx)
- La Estelar (https://laestelar.mx)
- Origen (OpenTable Mérida)

#### GPT-5.2 Autorizado Para:
1. Analizar perfil digital de unidades
2. Comparar productos vs competidores
3. Sugerir productos comparables
4. Generar justificación de precios
5. Clasificar confianza (ALTA/MEDIA/BAJA)

#### Regla Principal:
> **GPT-5.2 sugiere, pero NO autoriza ni aplica precios.**

#### Archivos:
- `/app/docs/reports/FASE_1C_3I_A_MODELO_DATOS_PRICING_IA_BENCHMARK.md`

---

### ✅ FASE 1C-3G-E3-R1: Clasificación Comercial de Vinos Sin Costo - COMPLETADO

**Fecha:** 2026-05-25

#### Resumen
Se implementó clasificación comercial para los productos sin costo, separando botellas reales de servicios, presentaciones y claves operativas.

#### Clasificación Implementada:
| Categoría | Cantidad | % | Descripción |
|-----------|----------|---|-------------|
| SERVICIO_CAVA | 21 | 2.4% | Suscripciones, membresías, descorche |
| PRESENTACION_O_VARIANTE | 471 | 53.2% | Copas, medias botellas |
| CLAVE_OPERATIVA | 78 | 8.8% | Tasting, cortesías, ZZZ |
| **PRODUCTO_VENTA_REAL** | **308** | **34.8%** | Botellas que SÍ requieren costo |

#### Impacto en Cobertura:
| Métrica | Antes | Después |
|---------|-------|---------|
| Vinos "pendientes críticos" | 878 | **308** |
| Excluidos (no aplica rango) | 0 | 578 |
| Cobertura de elegibles | 42% | **~55%** |

#### Motor de Cálculo Actualizado:
- Nuevos estados: `NO_APLICA_RANGO_SERVICIO`, `NO_APLICA_RANGO_PRESENTACION`, `NO_APLICA_RANGO_OPERATIVO`
- Función `clasificar_producto_comercial()` añadida
- Exclusión automática por patrones de nombre

#### Archivos:
- `/app/docs/reports/FASE_1C_3G_E3_SYNC_COSTO_BASE_VINOS_ORIGEN.md` (sección R1 añadida)
- `/app/backend/modules/comercial/services/precios_vinos_service.py` (clasificación implementada)

---

### ✅ FASE 1C-3G-E3: Sincronización Costos Origen - CRITERIO DE PARO

**Fecha:** 2026-05-25

#### Resumen
Diagnóstico exhaustivo de fuentes de costo en sistemas origen. **CRITERIO DE PARO**: Los costos ya están sincronizados en `Sync_Productos_Insumos`. Los 878 vinos sin costo NO tienen datos en origen.

#### Hallazgos Clave:
| Fuente | Total Registros | Estado |
|--------|-----------------|--------|
| Sync_Productos_Insumos (MPRO) | 5,414 | ✅ Sincronizado |
| Sync_Productos_Insumos (SR) | 6,321 | ✅ Sincronizado |
| Compras_Detalle | 0 | ❌ VACÍA |
| Inventario_Existencias | 0 | ❌ VACÍA |

#### Por qué no se puede mejorar la cobertura:
1. Los costos que existen en origen YA están en EDARSAHUB
2. Los 878 vinos sin costo NO tienen costo en MPRO/SoftRestaurant
3. Muchos son productos tipo servicio (CAVA suscripciones)
4. Re-sincronizar no crearía costos que no existen

#### Opciones para el Usuario:
| Opción | Descripción |
|--------|-------------|
| A | Costear productos en sistemas origen (MPRO/SR) |
| B | Captura manual en EDARSAHUB (UI con trazabilidad) |
| C | Importar lista de costos (Excel/CSV) |
| D | Excluir servicios CAVA del cálculo |
| E | Continuar con cobertura actual (634 vinos) |

#### Archivos:
- `/app/docs/reports/FASE_1C_3G_E3_SYNC_COSTO_BASE_VINOS_ORIGEN.md`

---

### ✅ FASE 1C-3G-E2: Diagnóstico de Vinos Sin Costo - COMPLETADO (CRITERIO DE PARO)

**Fecha:** 2026-05-25

#### Resumen
Se realizó diagnóstico exhaustivo de los 886 vinos sin CostoBaseVino. **CRITERIO DE PARO APLICADO**: No existen fuentes reales de costo disponibles en EDARSAHUB para 878 vinos.

#### Hallazgos Clave:
| Métrica | Valor |
|---------|-------|
| Vinos sin costo inicial | 886 |
| Recuperables vía CostoEstandar | 8 (valores dudosos: $0.18-$0.53) |
| Irrecuperables (sin fuente) | 878 |
| Tablas Compras/Inventarios | **VACÍAS** |

#### Clasificación de Vinos Sin Costo:
- Sin registro en Sync_Productos_Insumos: 356 (40.2%)
- Con insumo pero sin ningún costo: 530 (59.8%)

#### Jerarquía Actualizada (5 niveles):
| Prioridad | Fuente | Descripción |
|-----------|--------|-------------|
| 1 | `CostoReceta` | Si > 0 y confiable |
| 2 | `Sync_Productos_Insumos.Costo` | Costo de botella |
| 3 | `UltimoCosto` | Último costo |
| 4 | `CostoPromedio` | Costo promedio |
| 5 | `CostoEstandar` | **AÑADIDO en E2** |
| 6-9 | (Futuro) | Compras, proveedor, override |

#### Acciones Pendientes:
1. Sincronización desde sistemas origen (MPRO/SoftRestaurant) para poblar costos
2. O captura manual autorizada con trazabilidad

#### Archivos:
- `/app/docs/reports/FASE_1C_3G_E2_COSTO_BASE_VINOS_SIN_COSTO.md`
- `/app/backend/modules/comercial/services/precios_vinos_service.py` (actualizado)

---

### ✅ FASE 1C-3G-E: Reglas de Precio por Rango para Vinos - COMPLETADO CON CORRECCIÓN CONCEPTUAL

**Fecha:** 2026-05-25  
**Actualizado:** 2026-05-25 (Corrección Conceptual CostoBaseVino)

#### Resumen
Se crearon las reglas de precio por rango para productos clasificados como vino. **CORRECCIÓN CONCEPTUAL**: La tabla de rangos determina el PRECIO DE VENTA SUGERIDO, no calcula el costo del vino.

#### Resultados Actuales (post E2):
| Estado | Cantidad | % |
|--------|----------|---|
| CALCULADO | ~634 | 41.9% |
| COSTO_BASE_NO_CONFIGURADO | ~878 | 58.1% |

#### Tablas Creadas
| Tabla | Propósito |
|-------|-----------|
| `Comercial_ReglasPrecio` | Reglas maestras con redondeo |
| `Comercial_ReglasPrecioRangos` | 13 rangos con margen multiplicador |
| `Comercial_PreciosSugeridos` | Resultados de cálculo |

#### Regla VINOS_RANGOS_MX
- **13 rangos** configurados ($0 a $20,000)
- **Gap detectado**: $4,000.01 - $4,999.99 (pendiente definición usuario)
- **Método redondeo**: MAS_CERCANO
- **Múltiplo**: 5
- **Usa CostoReceta**: SÍ, si > 0 y confiable (corregido)

#### Fórmula de Cálculo
```
CostoBaseVino (jerarquía: CostoReceta → Insumo.Costo → Último → Promedio)
  × MargenMultiplicador (según rango)
  + Impuesto (resolver_tasa_impuesto, NUNCA hardcodear 16%)
  → Redondear a múltiplo de 5
  = Precio Sugerido de Venta
```

#### Prueba Obligatoria (Costo $450)
```
CostoBaseVino = 450.00 (fuente: INSUMO_COSTO)
450 × 2.50 = $1,125.00 (base)
$1,125.00 × 0.16 = $180.00 (impuesto resuelto)
$1,125.00 + $180.00 = $1,305.00 ✓
```

#### Resultados de Cálculo (1,512 vinos procesados)
| Estado | Cantidad | % |
|--------|----------|---|
| CALCULADO | 626 | 41.4% |
| COSTO_BASE_NO_CONFIGURADO | 886 | 58.6% |
| IMPUESTO_NO_CONFIGURADO | 0 | 0% |
| RANGO_NO_CONFIGURADO | 0 | 0% |

#### Fuentes de Costo Utilizadas
- INSUMO_COSTO: 618
- INSUMO_PROMEDIO: 8
- COSTO_RECETA: 0 (ningún vino tiene CostoReceta > 0)

#### Validaciones Confirmadas
- ✅ CostoReceta: prioridad 1 si > 0 (corregido)
- ✅ No se hardcodeó 16%
- ✅ Usa resolver_tasa_impuesto() del modelo canónico
- ✅ Gap $4,000-$5,000 marca RANGO_NO_CONFIGURADO
- ✅ No se modifican precios oficiales
- ✅ NO-LIVE confirmado
- ✅ Sin MongoDB
- ✅ No regresión Costos y Márgenes

#### Archivos Actualizados
- `/app/backend/modules/comercial/services/precios_vinos_service.py` (jerarquía corregida)
- `/app/docs/reports/FASE_1C_3G_E_REGLAS_PRECIO_RANGO_VINOS.md` (sección corrección conceptual añadida)

#### Pendiente (Requiere Autorización)
1. FASE 1C-3G-F: Frontend de administración fiscal para productos NO_CONFIGURADO
2. Definir si cerrar gap $4,000.01 - $4,999.99
3. Configurar costos para 886 vinos sin costo base

---

### ✅ FASE 1C-3G-D: Productos Clasificados como Vino - COMPLETADO (Diagnóstico)

**Fecha:** 2026-05-25

#### Resumen
Se completó el diagnóstico de productos clasificados como vino. Los vinos son productos normales en `Sync_Productos`, identificables por familia/subfamilia.

#### Hallazgos Clave
| Métrica | Valor |
|---------|-------|
| Productos vino identificados | 1,439 |
| Con insumo asociado | 1,126 (78%) |
| Con costo de botella disponible | 604 (42%) |
| Sin costo (requiere configuración) | 835 (58%) |
| Con impuesto CONFIGURADO | 100% |

#### Familias de Vino Detectadas
- VINOS TINTOS, VINOS BLANCOS, VINOS ROSADOS
- CHAMPAGNES Y COGNACS
- VINOS ESPUMOSOS/POSTRE
- CAVAS, B VINOS, B VINOS DE POSTRE

#### Decisiones Arquitectónicas
1. **NO se creó catálogo separado** - Los vinos son productos en `Sync_Productos`
2. **NO se reutiliza CavaSocios_Botellas** - Esa tabla es para gestión de socios
3. **Fuente de costo**: `Sync_Productos_Insumos` (Costo, UltimoCosto, CostoPromedio)
4. **Tabla extensión pendiente**: `Comercial_ProductosVinoDetalle` solo si se requieren atributos especializados

#### Archivos Creados
- `/app/docs/reports/FASE_1C_3G_D_PRODUCTOS_CLASIFICADOS_VINO_EXTENSION_ATRIBUTOS.md`

#### Pendiente (Requiere Autorización)
1. FASE 1C-3G-E: Reglas de Precio por Rango
2. Crear tabla extensión si se requieren atributos de vino (bodega, añada, varietal)
3. Configurar costos para los 835 vinos sin costo

---

### ✅ FASE 1C-3G-C: Modelo Canónico de Impuestos EDARSAHUB - COMPLETADO

**Fecha:** 2026-05-25

#### Resumen
Se creó el Modelo Canónico de Impuestos en EDARSAHUB SQL para homologar tasas fiscales desde SoftRestaurant y MPRO.

#### Tablas Creadas
| Tabla | Propósito |
|-------|-----------|
| `Comercial_ImpuestosCatalogo` | Catálogo maestro de impuestos canónicos |
| `Comercial_ImpuestosTasas` | Tasas vigentes por período |
| `Sync_Impuestos_Origen` | Mapeo de impuestos desde sistemas origen |
| `Comercial_ImpuestosMapeo` | Mapeo de productos a impuestos canónicos |
| `Comercial_ImpuestosOverrides` | Sobreescrituras autorizadas |

#### Impuestos Canónicos Registrados
- IVA_16 (16%), IVA_0 (0%), IVA_EXENTO
- IEPS_8 (8%), IEPS_26_5 (26.5%), IEPS_30 (30%), IEPS_53 (53%)
- SIN_IMPUESTO (para NO_CONFIGURADO)

#### Productos Mapeados
| Estado Fiscal | MPRO | SoftRestaurant | Total |
|---------------|------|----------------|-------|
| CONFIGURADO | 3,651 | 4,489 | 8,140 |
| TASA_CERO_VALIDADA | 1,701 | 2 | 1,703 |
| NO_CONFIGURADO | 62 | 0 | 62 |
| **TOTAL** | **5,414** | **4,491** | **9,905** |

#### Servicio de Resolución
Creado `/app/backend/modules/comercial/services/impuestos_service.py`:
- `resolver_tasa_impuesto()` - Resuelve tasa por jerarquía
- `get_estado_fiscal_producto()` - Estado fiscal completo
- `get_productos_sin_impuesto()` - Lista productos NO_CONFIGURADO

#### Validaciones Confirmadas
- ✅ 62 productos MPRO como NO_CONFIGURADO (no 0% inválido)
- ✅ resolver_tasa_impuesto funciona correctamente
- ✅ NO_CONFIGURADO bloquea cálculo de precio
- ✅ Costos y Márgenes sigue funcionando
- ✅ No se hardcodeó 16%

#### Archivos Creados
- `/app/backend/modules/comercial/services/impuestos_service.py`
- `/app/docs/reports/FASE_1C_3G_C_MODELO_CANONICO_IMPUESTOS_EDARSAHUB.md`

#### Pendiente (Requiere Autorización)
1. FASE 1C-3G-D: Catálogo Comercial de Vinos
2. FASE 1C-3G-E: Reglas de Precio por Rango
3. FASE 1C-3G-F: UI Administración Fiscal (62 productos)

---

### ✅ FASE 1C-3G-B: SYNC REAL Impuestos MPRO - COMPLETADO

**SyncRunID:** `SYNC-IMPUESTOS-20260525025423-ba8b9796`  
**Fecha:** 2026-05-25

#### Resultado SYNC REAL
| Categoría | Cantidad | Porcentaje |
|-----------|----------|------------|
| Total productos MPRO | 5,414 | 100% |
| Con tasa > 0 (IVA/IEPS) | 3,651 | 67.4% |
| Con tasa = 0 (válida) | 1,701 | 31.4% |
| IMPUESTO_NO_CONFIGURADO | 62 | 1.1% |
| **Errores** | **0** | - |

#### Cambios Realizados
1. **Sync de productos MPRO** con impuestos corregidos desde `CENTRAL2020`
2. **Endpoint Costos y Márgenes** actualizado para devolver `tasa_impuesto` y `estado_impuesto`
3. **Schemas Pydantic** actualizados con campos de impuesto
4. **No se hardcodeó 16%** - Tasas provienen de tabla `Impuesto` de MPRO

#### Archivos Modificados
- `/app/backend/modules/sync_recetas/sync_recetas.py` - Query fiscal corregida
- `/app/backend/modules/costos_margenes/repository.py` - Campos de impuesto agregados
- `/app/backend/modules/costos_margenes/schemas.py` - Enum EstadoImpuesto
- `/app/backend/modules/costos_margenes/routes.py` - Endpoint actualizado

#### Reportes Generados
- `/app/docs/reports/FASE_1C_3G_B_DIAGNOSTICO_CORRECCION_IMPUESTOS_MPRO.md`
- `/app/docs/reports/FASE_1C_3G_B_SYNC_REAL_IMPUESTOS_MPRO.md`

#### Pendiente (Requiere Autorización)
1. ~~Ejecutar SYNC REAL de productos MPRO~~ ✅ COMPLETADO
2. Crear Modelo Canónico de Impuestos en EDARSAHUB SQL
3. Catálogo de Vinos (`Comercial_VinosCatalogo`)
4. Reglas de Precio por Rango
5. UI para administrar los 62 productos sin impuesto configurado
2. Crear Modelo Canónico de Impuestos en EDARSAHUB
3. UI de administración para 62 productos sin impuesto

---

### ✅ Completado

#### FASE P2 - RBAC por Unidad de Negocio (25 Mayo 2026) ✅ COMPLETADO
- [x] **Implementación de RBAC basado en servidores/unidades**:
  - Utiliza tablas existentes: `Usuario_Catalogo`, `Usuario_ServidoresAsignacion`, `Usuario_Roles`
  - Función `_get_user_allowed_servers()` que determina acceso del usuario
  - Usuarios corporativos (ADMIN, SUPERADMIN, o sin asignaciones) ven todos los datos
  - Usuarios con asignaciones solo ven datos de sus unidades
- [x] **Endpoints modificados con RBAC**:
  - `GET /api/costos-margenes/productos` - Filtra por servidores permitidos
  - `GET /api/costos-margenes/unidades-negocio` - Retorna `es_corporativo` y filtra unidades
  - `GET /api/costos-margenes/familias` - Filtra familias por unidades permitidas
- [x] **Validación de acceso**:
  - Si usuario selecciona unidad no permitida → Error 403 "ACCESO_DENEGADO_UNIDAD"
  - Nuevo parámetro `servidores_ids` en `get_productos_con_costos()` para filtro múltiple
- [x] **Resultados de prueba**:
  - Admin corporativo: 9,905 productos, 5 unidades, 125 familias
  - Usuario CIENFUEGOS (simulado): 2,022 productos, 1 unidad

#### Corrección de Bugs FASE 1C-3F (25 Mayo 2026) ✅ COMPLETADO
- [x] **Bug 1 - Costo de Receta $0.00**: CORREGIDO
  - Problema: El campo `CostoReceta` en `Sync_Productos` estaba vacío (0.00) para todos los productos
  - Solución: Modificado `repository.py` para calcular costo sumando `CostoTotal` de `Sync_Productos_Recetas` vía subquery SQL
  - Resultado: `(S) AJO ROSTIZADO KG` ahora muestra $87.35 correctamente
- [x] **Bug 2 - Doble click en Elaborados fallaba**: CORREGIDO
  - Problema: Al hacer doble click en insumo "Elaborado", error "Producto no encontrado" porque los elaborados no existen en `Sync_Productos`
  - Solución: 
    - Nueva función `get_receta_elaborado()` que busca en `Sync_Productos_Insumos` y `Sync_Productos_Elaborados`
    - Endpoint `/api/costos-margenes/productos/{id}/receta` ahora acepta parámetro `es_elaborado` y hace auto-detección
    - Frontend actualizado para pasar `codigo_fuente` y `server_id` al cargar sub-recetas
  - Resultado: Elaborado `A300087` muestra 9 componentes con costo $2,087.22
- [x] **Bug 3 - Modal de Receta fijo (no movible)**: CORREGIDO
  - Problema: El modal de receta expandida estaba fijo en el centro de pantalla
  - Solución: Implementado drag & drop con `onMouseDown/onMouseMove/onMouseUp` y transformaciones CSS
  - Resultado: Modal ahora es arrastrable, con indicador "(Arrastre para mover)" en el header
- [x] **Bug 4 - % del Total en 0.0%**: CORREGIDO
  - Problema: La columna "% del Total" mostraba 0.0% para todos los componentes
  - Solución: Modificado backend para calcular porcentaje dinámicamente basado en `costo_comp / costo_total_receta * 100`
  - Resultado: Componentes ahora muestran porcentajes reales (ej: CAMARÓN 45.6%, CALLO 40.8%)
- [x] **Bug 5 - Margen $ y Margen % en ceros**: CORREGIDO
  - Problema: La tabla principal mostraba $0.00 y 0.0% en las columnas de margen
  - Solución: Modificado `get_productos_con_costos()` para calcular `precio_venta - costo_receta` y porcentaje dinámicamente
  - Resultado: `(S) AJO ROSTIZADO KG` muestra Margen $62.65 (41.8%)
- [x] **Mejora - Ordenamiento en tablas**: IMPLEMENTADO
  - Todas las columnas de las 3 tablas (principal, modal receta, modal insumos) ahora son clickeables para ordenar
  - Indicador visual con flecha (ChevronUp/Down) muestra la dirección del ordenamiento
  - Soporta ordenamiento ascendente/descendente alternando con click
- [x] **Mejora - Sub-elaborados anidados**: IMPLEMENTADO
  - Los componentes de un elaborado que también son elaborados ahora muestran la etiqueta "Elaborado"
  - Doble click recursivo permite navegar infinitos niveles de sub-recetas

#### Mejoras en Costos y Márgenes (25 Mayo 2026) ✅ COMPLETADO
- [x] **Vista agrupada por Familia**:
  - Botón "Agrupar" para alternar entre vista lista y vista agrupada
  - Familias expandibles con click (chevron up/down)
  - Contador de productos por familia
- [x] **Filtros mejorados**:
  - Dropdown "Unidades de Negocio" (reemplazó filtro por Sistema)
  - Dropdown "Familias" con contador de productos
  - Dropdown "Subfamilias" (aparece al seleccionar familia)
- [x] **Doble click en Elaborados**:
  - Modal de receta permite ver sub-recetas de insumos elaborados
  - Navegación con breadcrumb entre recetas padre/hijo
  - Botón "Volver" para regresar a receta anterior
  - Mensaje informativo sobre la funcionalidad
- [x] **Backend endpoints nuevos**:
  - `GET /api/costos-margenes/unidades-negocio` - Lista unidades activas
  - `GET /api/costos-margenes/familias` - Lista familias con totales
  - `GET /api/costos-margenes/subfamilias` - Lista subfamilias filtradas

#### FASE 1C-3F - Simulación y Solicitudes de Precio (24 Mayo 2026) ✅ COMPLETADO
- [x] **Backend completado** (sesión anterior):
  - Tablas SQL: `Comercial_SolicitudesCambioPrecio`, `Comercial_SolicitudesCambioPrecioDetalle`, `Comercial_SolicitudesCambioPrecioHistorial`, `Comercial_SimulacionesPrecio`
  - Endpoints de workflow: crear, enviar, aprobar, rechazar, aplicar, cancelar
  - RBAC implementado en todos los endpoints
  - Máquina de estados: BORRADOR → SOLICITADA → EN_REVISION → APROBADA → APLICADA
- [x] **Frontend completado** (esta sesión):
  - Componente refactorizado: `/app/frontend/src/pages/comercial/CostosMargenes.jsx`
  - Sistema de Tabs: "Resumen/Productos" + "Solicitudes de Precio"
  - Modal de Simulación: cálculo en tiempo real de márgenes y advertencias
  - Vista de Solicitudes: tabla con filtros, estados y acciones
  - Modal de Detalle: historial, comentarios, acciones según estado
  - Migración de auth: de `localStorage.getItem('token')` a cliente API centralizado (`@/lib/api`)
- [x] **Validaciones implementadas**:
  - Motivo obligatorio (mín. 5 caracteres)
  - Precio propuesto > 0
  - Advertencias: margen negativo, margen bajo <20%, variación >15%
  - Null mostrado como "Sin dato"
  - Sin receta mostrado como advertencia
- [x] **Endpoints consumidos**: 14 endpoints de `/api/costos-margenes/*`
- [x] **NO-LIVE confirmado**: Solo consume EDARSAHUB SQL
- [x] **Sin MongoDB**: Confirmado
- [x] **Sin regresión**: Login, Dashboard, Costos funcionan
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1C_3F_FRONTEND_SIMULACION_SOLICITUDES_PRECIO.md`

#### FASE 1C-3D - Frontend Costos y Márgenes (24 Mayo 2026) ✅ COMPLETADO
- [x] **Ruta implementada**: `/comercial/costos-margenes`
- [x] **Componente creado**: `/app/frontend/src/pages/comercial/CostosMargenes.jsx` (730 líneas)
- [x] **Tarjetas de resumen**: Total Productos, Con Receta, Total Recetas, Total Insumos
- [x] **Tabla de productos**: Filtros, búsqueda, paginación
- [x] **Modal de receta**: Componentes jerárquicos con costos y %
- [x] **Modal de insumos**: Lista consolidada con % del costo
- [x] **Sync status**: Indicador de estado de sincronización
- [x] **Manejo NULL vs cero**: "Sin dato" para NULL, no $0 falso
- [x] **NO-LIVE confirmado**: Solo consume endpoints EDARSAHUB SQL
- [x] **Sin MongoDB**: Confirmado
- [x] **No regresión**: Login, Tablero, Ventas funcionan
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1C_3D_COSTOS_MARGENES_FRONTEND.md`

#### FASE 1C-3C - Endpoints NO-LIVE Costos y Márgenes (24 Mayo 2026) ✅ COMPLETADO
- [x] **5 Endpoints creados**: Módulo `/app/backend/modules/costos_margenes/`
  - `GET /api/costos-margenes/resumen` - Resumen general
  - `GET /api/costos-margenes/productos` - Lista paginada con filtros
  - `GET /api/costos-margenes/productos/{id}/receta` - Receta expandida
  - `GET /api/costos-margenes/productos/{id}/insumos` - Insumos consolidados
  - `GET /api/costos-margenes/sync-status` - Estado de sincronización
- [x] **Source Type**: EDARSAHUB_SQL en todas las respuestas
- [x] **NO-LIVE confirmado**: Sin conexiones a sistemas externos
- [x] **Sin MongoDB**: Confirmado
- [x] **Validación SR**: QUESADILLA DE FLOR DE CALABAZA - 7 componentes, $30.15 costo
- [x] **Validación MPRO**: AGUACHILE DE NEW YORK - 9 componentes
- [x] **Permisos RBAC**: Definidos (comentados para SuperAdmin)
- [x] **No regresión**: Login, Tablero Ejecutivo, Ventas Tiempo funcionan
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1C_3C_COSTOS_MARGENES_ENDPOINTS_NO_LIVE.md`

#### FASE 1C-3E - Validación Integral, RBAC, Seguridad y Exportación (24 Mayo 2026) ✅ COMPLETADO
- [x] **RBAC implementado**: `_verify_costos_margenes_access()` en todos los endpoints
- [x] **Roles permitidos**: SuperAdmin, Admin, Supervisor, Comercial, Gerente, Usuario
- [x] **Seguridad SQL validada**: SQLSanitizer activo, no exposición de credenciales
- [x] **Arquitectura NO-LIVE confirmada**: Todos los endpoints retornan `source_type: EDARSAHUB_SQL`
- [x] **Exportación CSV implementada**: `GET /api/costos-margenes/exportar`
  - Formato: CSV con BOM UTF-8
  - Filtros: familia, sistema, solo_con_receta
  - Límite: 10,000 registros
  - Columnas: Código, Nombre, Familia, SubFamilia, Sistema, Precio, Costo, Margen
- [x] **No regresión validada**: Todos los módulos funcionan correctamente
  - Login, Auth, Menú SQL: ✅
  - Dashboard Comercial, Tablero Ejecutivo: ✅
  - Compras, Inventarios: ✅
- [x] **Datos intactos**: 9,905 productos, 39,299 registros totales
- [x] **Restricciones cumplidas**:
  - ❌ No se editaron precios
  - ❌ No se editaron recetas
  - ❌ No se editaron costos
  - ❌ No se programó job nocturno
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1C_3E_VALIDACION_RBAC_EXPORTACION.md`

#### FASE 1C-3B-R3 - Fix Bug Decimal en Familias SR (24 Mayo 2026) ✅ COMPLETADO
- [x] **Bug corregido**: `Decimal.replace()` en `sync_recetas.py` líneas 318-328, 394-408, 634-648
- [x] **Causa raíz**: Campo `clasificacion` de SoftRestaurant devolvía tipo `Decimal` en lugar de string
- [x] **DRY-RUN exitoso**: 116 familias, 156 subfamilias (0 errores)
- [x] **Sync Real COMPLETADO**: SyncRunID `SYNC-RECETAS-20260524151422-c1122c37`
  - Duración: 28.71 segundos
  - Registros insertados: 272 (116 familias + 156 subfamilias)
  - Errores: 0
- [x] **Familias recuperadas**:
  - CIENFUEGOS: 37 familias
  - 130° MÉRIDA: 33 familias
  - LA ESTELAR: 46 familias
- [x] **Conteos finales**: Familias 189, SubFamilias 264
- [x] **Validación duplicados**: 0 duplicados
- [x] **Integridad de datos**: Productos (9,905), Insumos (11,735), Recetas (13,313), Elaborados (3,893) intactos
- [x] **Endpoints NO-LIVE funcionan**: Filtro por familia operativo
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1C_3B_R3_FIX_DECIMAL_FAMILIAS_SR.md`

#### FASE 1C-3B-R2 - Sincronización CIENFUEGOS (24 Mayo 2026) ✅ COMPLETADO
- [x] **Conexión DDNS resuelta**: `servercienfuegos.ddns.net` → IP `189.162.155.142`
- [x] **DRY-RUN exitoso**: 37 familias, 57 subfamilias, 2,022 productos, 2,493 insumos, 4,164 recetas, 1,843 elaborados
- [x] **Sync Real COMPLETADO**: SyncRunID `SYNC-RECETAS-20260524145132-968ad406`
  - Duración: 8 min 53 seg (531.78s)
  - Registros insertados: 10,579
  - Servidor: CIENFUEGOS (SOFTRESTAURANT_PRO)
- [x] **Conteos CIENFUEGOS en EDARSAHUB**:
  - Productos: 2,022 | SubFamilias: 57 | Insumos: 2,493 | Recetas: 4,164 | Elaborados: 1,843
- [x] **Conteos TOTALES en EDARSAHUB**:
  - Productos: 9,905 | SubFamilias: 264 | Insumos: 11,735 | Recetas: 13,313 | Elaborados: 3,893 | Total: 39,183
- [x] **Validación duplicados**: 0 duplicados
- [x] **Validación cantidades negativas**: 0
- [x] **Validación costos negativos**: 35 (provienen del origen - ajustes)
- [x] **Integridad otras unidades**: LA ESTELAR (611), 130° MÉRIDA (1,858), MPRO (5,414) intactos
- [x] **Endpoints NO-LIVE funcionan**: `/api/costos-margenes/*` retornan `source_type: EDARSAHUB_SQL`
- [x] **CIENFUEGOS visible en endpoints**: Confirmado en sync-status y productos
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1C_3B_R2_SYNC_RECETAS_CIENFUEGOS.md`
- [⚠️] **Bug familias SR**: 37 familias CIENFUEGOS no insertadas por bug Decimal (P2, bajo impacto)

#### FASE 1C-3B - Implementación Job Sync Recetas (24 Mayo 2026) ✅ COMPLETADO Y CERRADO
- [x] **Job sync_recetas.py creado**: 1,084 líneas de código ETL
- [x] **Tablas destino creadas**: 6 tablas `Sync_Productos*` en EDARSAHUB SQL
- [x] **DRY-RUN exitoso**: 152 familias, 207 subfamilias, 7,883 productos, 14,524 insumos, 9,341 recetas
- [x] **Sync Real COMPLETADO**: SyncRunID `SYNC-RECETAS-20260524133926-b652313f`
  - Duración: 26.7 minutos
  - Registros insertados: 34,078
  - Servidores: 3/3 exitosos (LA ESTELAR, 130° MERIDA, ManagmentPro)
- [x] **Conteos finales en BD**: 28,604 registros totales
  - Productos: 7,883 | Insumos: 9,242 | Recetas: 9,149 | Elaborados: 2,050
- [x] **Validación duplicados**: 0 duplicados en todas las tablas
- [x] **Validación cantidades**: 0 cantidades negativas en recetas
- [x] **Validación producto SR**: QUESADILLA DE FLOR DE CALABAZA ✅ (7 insumos)
- [x] **Validación producto MPRO**: Prod B Naranja en Gajos ✅ 
- [x] **NO-LIVE confirmado**: Endpoints NO consultan BD remotas
- [x] **No regresión**: Login, dashboard, menús funcionan correctamente
- [x] **Proceso background cerrado**: PID 7622 terminó exitosamente
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1C_3B_COSTOS_MARGENES_SYNC_RECETAS_IMPLEMENTACION.md`
- [✅] **CIENFUEGOS**: Sincronizado en FASE 1C-3B-R2
- [⚠️] **Bug familias SR**: 79+37 familias no insertadas por bug Decimal (no bloqueante)

#### FASE 1C-3A - Diseño Técnico Costos y Márgenes (24 Mayo 2026) ✅ COMPLETADO
- [x] **Diagnóstico de tablas**: 50+ tablas analizadas en EDARSAHUB
- [x] **Tablas reutilizables**: `Sync_Control_Ejecuciones`, parcialmente `Operaciones_Tablaje_*`
- [x] **Tablas faltantes identificadas**: 6 tablas Sync_Productos_* propuestas
- [x] **Hallazgo crítico**: `Producto_Catalogo` y `Producto_Familias` VACÍAS en EDARSAHUB
- [x] **DDL propuesto**: 6 tablas con índices (no ejecutado)
- [x] **Diseño job sync_recetas.py**: Flujo y queries por sistema
- [x] **Fuentes mapeadas**: SoftRestaurant (611 productos, 1199 insumos) + MPRO (7957 productos, 554 fórmulas)
- [x] **Endpoints diseñados**: 7 endpoints propuestos
- [x] **Frontend diseñado**: Tabla jerárquica expandible con filtros y ordenamiento
- [x] **RBAC diseñado**: 8 permisos propuestos
- [x] **Reglas NO-LIVE**: Documentadas y validadas
- [x] **Riesgos identificados**: 8 riesgos con mitigaciones
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1C_3A_COSTOS_MARGENES_DISENO_TECNICO.md`
- [✅] **Corrección usuario**: Recetas SoftRestaurant en tabla `costos` (1,583 líneas, 559 productos con receta = 91%)

#### FASE 1C-0 - Diagnóstico Comercial/Ventas para Subfases (24 Mayo 2026) ✅ COMPLETADO
- [x] **Rutas inventariadas**: 18 rutas revisadas (Comercial + CRM)
- [x] **Endpoints catalogados**: 30+ endpoints identificados
- [x] **Tablas EDARSAHUB**: 50+ tablas relacionadas encontradas
- [x] **Fuentes remotas analizadas**: SoftRestaurant (explosioninsumosdetalle, insumosdetalle, productos)
- [x] **Duplicidades**: Ninguna crítica, solo alias de navegación
- [x] **Dependencias MongoDB**: NINGUNA
- [x] **Dependencias Live**: NINGUNA (arquitectura NO-LIVE confirmada)
- [x] **Permisos RBAC**: 7 existentes, 14 faltantes identificados
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1C_0_DIAGNOSTICO_COMERCIAL_VENTAS_SUBFASES.md`
- [x] **Propuesta subfases**: 1C-1 a 1C-6 definidas
- [x] **Recomendación**: Implementar FASE 1C-3 (Costos/Márgenes) primero

#### FASE 1B-R3 - Ejecución Job Sync_Ventas_PorHora (24 Mayo 2026) ✅ COMPLETADO
- [x] **Bug corregido**: `zoneinfo.ZoneInfo` no tiene `.localize()` → usar `.replace(tzinfo=)`
- [x] **DRY-RUN exitoso**: 232 registros identificados, 2 servidores, 0 errores
- [x] **Sincronización ejecutada**: 232 registros insertados en `Sync_Ventas_PorHora`
- [x] **Servidores sincronizados**: LA ESTELAR, ManagmentPro, 130° MERIDA
- [x] **Estado tabla**: 605 registros, fecha máx 2026-05-23 (antes 306 / 2026-05-15)
- [x] **Endpoint validado**: `/api/comercial/ventas-tiempo` retorna `source_type: EDARSAHUB_SQL` con datos frescos
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1B_R3_SYNC_VENTAS_PORHORA_JOB_VALIDACION.md`
- [⚠️] **CIENFUEGOS**: No sincronizado (servidor remoto no disponible - timeout de red)

#### FASE 1B-R2 - Migración Ventas por Hora a EDARSAHUB SQL (24 Mayo 2026) ✅ COMPLETADO
- [x] **Endpoint migrado**: `/api/comercial/ventas-tiempo/{server_id}` ahora lee de `Sync_Ventas_PorHora`
- [x] **Eliminadas conexiones remotas**: SoftRestaurant y MPRO (~180 líneas)
- [x] **source_type únicos**: EDARSAHUB_SQL, STALE_EDARSAHUB_SQL, SIN_DATOS_EDARSAHUB
- [x] **Compatible frontend**: Mismos campos de respuesta
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1B_R2_NO_LIVE_VENTAS_TIEMPO_SYNC_VENTAS_PORHORA.md`
- [⚠️] **Observación**: Datos en Sync_Ventas_PorHora tienen 9 días de antigüedad - Job sync debe ejecutarse

#### Portal de Clientes - Arquitectura (24 Mayo 2026) 📋 DOCUMENTADO
- [x] **Documento arquitectónico creado**: `/app/docs/reports/PORTAL_CLIENTES_AUTOFACTURACION_ARQUITECTURA.md`
- [x] **Modelo de acceso externo**: Tablas `Cliente_UsuariosPortal`, `Cliente_RolUsuarioPortal` ya existen
- [x] **Flujo de autofacturación**: Diseñado con validaciones SAT
- [x] **20+ endpoints propuestos**: /api/portal-clientes/*
- [x] **RBAC definido**: 22 permisos para clientes y administradores
- [ ] **Implementación**: Requiere autorización para Fase PC-1

#### FASE 1B-R1 - Corrección NO-LIVE Dashboard Comercial (24 Mayo 2026) ✅ COMPLETADO
- [x] **Eliminados fallbacks remotos**: SoftRestaurant (~200 líneas) y MPRO (~400 líneas)
- [x] **Eliminado query remoto** "último día con ventas" (~70 líneas)
- [x] **Agregada función** `get_last_valid_snapshot_edarsahub()` para datos STALE
- [x] **source_type únicos permitidos**: EDARSAHUB_SQL, STALE_EDARSAHUB_SQL, SIN_DATOS_EDARSAHUB
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1B_R1_NO_LIVE_DASHBOARD_COMERCIAL_CORRECCION.md`
- [x] **Actualizado reporte FASE 1B** a v2.0
- [⚠️] **Pendiente**: Migrar Ventas por Hora a EDARSAHUB (endpoint separado)

#### FASE 1B - Dashboard Comercial EDARSAHUB SQL (24 Mayo 2026) ✅ COMPLETADO
- [x] **Diagnóstico completado**: Dashboard YA usa EDARSAHUB SQL como fuente principal
- [x] **Código clave validado**: `get_dashboard_kpis_from_edarsahub()` en service.py
- [x] **NO se requirieron modificaciones** - Arquitectura correcta existente
- [x] **Tablas utilizadas**: Comercial_KPIs_Diarios_v2, Sync_Ventas_PorHora
- [x] **Endpoint validado**: /api/comercial/dashboard → source_type: EDARSAHUB_SQL
- [x] **Pruebas no regresión**: 29/29 pasaron
- [x] **Reporte técnico**: `/app/docs/reports/FASE_1B_DASHBOARD_COMERCIAL_EDARSAHUB_SQL.md`

#### FASE 1A - Comercial/Ventas Integración Menú SQL (24 Mayo 2026) ✅ COMPLETADO
- [x] **Validación de rutas:**
  - `/comercial` - Dashboard funciona (blindado)
  - `/comercial/clientes` → Redirige a `/crm/cuentas`
  - `/comercial/costos-margenes` → Redirige a `/comercial` (temporal)
  - `/crm/cotizaciones`, `/crm/pedidos`, `/crm/remisiones` - Funcionan
- [x] **Menú SQL validado:** 28 módulos, Comercial con 6 submenús
- [x] **Pruebas no regresión:** 29/29 pasaron
- [x] **Correcciones menores:** 2 rutas redirect en App.js
- [x] **Reporte técnico:** `/app/docs/reports/FASE_1A_COMERCIAL_VENTAS_MENU_GOBERNADO.md`
- [x] **Rutas canónicas faltantes documentadas** (para FASE 1B+)

#### FASE 0.6 - Migración Layout.js a Menús SQL (24 Mayo 2026) ✅ COMPLETADO
- [x] **Frontend Layout.js modificado**:
  - Carga dinámica de menús desde `/api/sistema/menus/usuario`
  - Sistema de fallback a menús hardcodeados
  - Renderizado separado: Módulos, Satélites (amber), Portales (azul), Sistema
  - Indicador de fuente de menús en modo desarrollo
- [x] **Validaciones ejecutadas** (29/29 pasaron):
  - Login funciona ✅
  - Auth SQL-first ✅
  - Endpoint menus responde (28 módulos) ✅
  - POS y Comandero como satélites separados ✅
  - Portales contemplados ✅
  - No errores 500 ✅
  - No dependencia MongoDB ✅
- [x] **Reporte técnico generado**: `/app/docs/reports/FASE_0_6_MIGRACION_LAYOUT_MENUS_SQL.md`

#### FASE 0.5 - Validación Arquitectónica (24 Mayo 2026) ✅
- [x] Validación de estructura de tablas Sistema_*
- [x] Verificación de no regresión
- [x] Reporte: `/app/docs/reports/FASE_0_5_VALIDACION_ARQUITECTURA_MENUS_Y_COMERCIAL.md`

#### FASE 0 - Estabilización Arquitectónica (24 Mayo 2026) ✅
- [x] **Sistema de Menús Gobernados**:
  - Tabla `Sistema_Modulos`: 28 módulos según manifiesto arquitectónico
  - Tabla `Sistema_ModulosMenus`: 52 menús con rutas y permisos
  - Tabla `Sistema_ModulosPermisos`: Estructura para permisos granulares
  - API: `/api/sistema/menus/usuario` - Menús filtrados por permisos
- [x] **Módulos registrados**:
  - 21 Principales (Dirección, Comercial, Compras, Inventarios, Finanzas, etc.)
  - 4 Satélites (Comandero, POS, EDARSA GO, Chef IA)
  - 3 Portales (Proveedores, Comisionistas, Clientes)
- [x] **Archivos creados**:
  - `/app/backend/modules/sistema/menu_service.py`
  - `/app/backend/modules/sistema/menu_routes.py`

#### Notificaciones Cava de Socios (24 Mayo 2026) ✅
- [x] **Servicio de notificaciones** `/app/backend/modules/cava_socios/notification_service.py`:
  - Envío de reportes PDF por Email (SMTP interno)
  - Envío de notificaciones por WhatsApp (Twilio)
  - Soporte multicanal (Email + WhatsApp simultáneo)
- [x] **API Endpoints de notificaciones**:
  - `POST /api/cava-socios/socios/{id}/enviar-reporte` - Envío individual
  - `POST /api/cava-socios/socios/{id}/enviar-todos-reportes` - Envío masivo
- [x] **Frontend** - Menú desplegable en `SocioDetail.jsx`:
  - Descarga PDFs (Ficha, Consumos, Estado Cuenta)
  - Envío por Email (3 tipos de reporte)
  - Envío por WhatsApp (Ficha, Estado Cuenta)
  - Envío masivo (Email o Email+WA)
- [x] **Dependencias**: `twilio==9.10.9` instalado

#### Migración MongoDB → SQL Server (COMPLETA)
- [x] Auth/Login migrado a SQL (login < 1s)
- [x] RBAC migrado a SQL Server (Usuario_Roles)
- [x] **Tablas Sesiones/SesionesHistorico creadas**
- [x] Scheduler usa StubDatabase para operaciones no críticas
- [x] **Tablas Scheduler_* creadas para tracking de jobs**
- [x] `sql_repository.py` creado con funciones SQL

#### CRM Comercial Enterprise (Fase 4)
- [x] Backend endpoints creados (`/api/crm/*`)
- [x] Datos: 18 cuentas, 2 cotizaciones
- [x] Rutas frontend y submenús agregados

#### Tablajería Fase 4: Captura Directa (24 Mayo 2026) ✅ NUEVO
- [x] **Endpoint `/api/tablajeria/ordenes/captura-directa` funcional**
- [x] **Creación de órdenes sin plantilla predefinida**
- [x] **Flujo completo verificado**: Crear → Iniciar → Registrar Resultados → Cerrar
- [x] **Corrección de columnas SQL**: Alineación `PorcentajeEsperado` vs `PorcentajeRendimientoEsperado`
- [x] **UUID especial para captura directa**: `00000000-0000-0000-0000-000000000001`
- [x] **UI Frontend**: Página `/tablajeria/captura-directa` con formulario completo

#### RBAC Tablajería (24 Mayo 2026) ✅ NUEVO
- [x] **11 módulos creados** en `Usuario_Modulos`:
  - tablajeria, tablajeria.dashboard, tablajeria.ordenes
  - tablajeria.captura_directa, tablajeria.plantillas, tablajeria.rendimientos
  - tablajeria.mermas, tablajeria.costeo, tablajeria.polizas
  - tablajeria.sync, tablajeria.config
- [x] **199 permisos asignados** a 8 roles (SUPERADMIN, ADMIN, GERENCIA, GERENTE_OPS, SUPERVISOR, OPERADOR, AUDITOR, VISOR)
- [x] **Script RBAC**: `/app/backend/scripts/create_tablajeria_rbac.py`

#### Dashboard y Reportes Tablajería (24 Mayo 2026) ✅ NUEVO
- [x] **Servicio dashboard_service.py** con funcionalidades:
  - KPIs generales (órdenes, rendimientos, mermas, costeo)
  - Rendimientos por plantilla
  - Tendencia histórica
  - Top mermas
  - Alertas de desviación
  - Resumen de costeo
- [x] **8 endpoints API de dashboard**:
  - `/api/tablajeria/dashboard/kpis`
  - `/api/tablajeria/dashboard/rendimientos-plantilla`
  - `/api/tablajeria/dashboard/tendencia`
  - `/api/tablajeria/dashboard/top-mermas`
  - `/api/tablajeria/dashboard/alertas`
  - `/api/tablajeria/dashboard/resumen-costeo`
- [x] **3 endpoints de reportes exportables**:
  - `/api/tablajeria/reportes/ordenes`
  - `/api/tablajeria/reportes/mermas`
  - `/api/tablajeria/reportes/costeo`
- [x] **Frontend TablajeriaDashboard.jsx** actualizado con:
  - Cards de KPIs
  - Alertas de rendimiento
  - Gráfico de rendimientos por plantilla
  - Tabla de top mermas
  - Resumen de costeo con desglose

#### Módulo Cava de Socios (24 Mayo 2026) ✅ NUEVO
- [x] **5 tablas SQL creadas** en EDARSAHUB:
  - `CavaSocios_Socios` - Catálogo de socios
  - `CavaSocios_Botellas` - Inventario en custodia
  - `CavaSocios_Movimientos` - Entradas, consumos, retiros
  - `CavaSocios_Cargos` - Cargos por servicios
  - `CavaSocios_Configuracion` - Configuración por empresa
- [x] **Servicio backend** `/app/backend/modules/cava_socios/`:
  - CRUD de socios
  - Registro de botellas
  - Consumos parciales/totales
  - Cargos automáticos con IVA
  - Dashboard con KPIs
- [x] **API Endpoints**:
  - `GET /api/cava-socios/dashboard`
  - `GET/POST /api/cava-socios/socios`
  - `GET /api/cava-socios/socios/{id}`
  - `POST /api/cava-socios/socios/{id}/botellas`
  - `POST /api/cava-socios/botellas/{id}/consumo`
- [x] **Script SQL**: `/app/backend/scripts/create_cava_socios_tables.py`
- [x] **Script RBAC**: `/app/backend/scripts/create_cava_socios_rbac.py` (9 módulos, 138 permisos)
- [x] **Frontend completo** `/app/frontend/src/pages/cava-socios/`:
  - `CavaSociosDashboard.jsx` - Dashboard con KPIs (Socios, Botellas, Valor, Pendientes)
  - `SociosList.jsx` - Lista de socios con filtros y paginación
  - `SocioForm.jsx` - Formulario crear/editar socio
  - `SocioDetail.jsx` - Detalle socio con gestión de botellas y consumos
- [x] **Menú lateral** integrado con submenús (Dashboard, Socios)

#### Tablajería Fase 6: Inventarios, Costeo, Contabilidad (24 Mayo 2026) ✅ INTEGRADO
- [x] **Credenciales hardcodeadas removidas** - Ahora usa variables de entorno `EDARSAHUB_*`
- [x] **6 tablas SQL creadas**:
  - `Tablajeria_MovimientosInventario`
  - `Tablajeria_CosteoProduccion`
  - `Tablajeria_CosteoDetalle`
  - `Tablajeria_PolizasContables`
  - `Tablajeria_PolizasDetalle`
  - `Tablajeria_ConfigContable`
- [x] **Servicio fase6_service.py operativo** con funcionalidades:
  - Afectación de inventarios (SALIDA_INSUMO, ENTRADA_DERIVADO, SALIDA_MERMA)
  - Costeo de producción (reglas PROPORCIONAL, FIJO, RESIDUAL)
  - Generación de pólizas contables
  - Proceso completo de cierre
- [x] **Integración automática con cierre de órdenes**:
  - Al cerrar orden con `ejecutar_fase6=true` y `costo_unitario_insumo`:
    1. Afecta inventarios automáticamente
    2. Calcula costeo con regla proporcional
    3. Genera póliza contable
- [x] **Endpoints API**:
  - `PUT /api/tablajeria/ordenes/{id}/cerrar` (con parámetros Fase 6)
  - `POST /api/tablajeria/ordenes/{id}/fase6/procesar-cierre`
  - `POST /api/tablajeria/ordenes/{id}/fase6/afectar-inventario`
  - `POST /api/tablajeria/ordenes/{id}/fase6/calcular-costeo`
  - `POST /api/tablajeria/ordenes/{id}/fase6/generar-poliza`
  - `GET/PUT /api/tablajeria/fase6/config-contable/{empresa_id}`

#### Correcciones de Columnas SQL (24 Mayo 2026)
- [x] `EsInventariable` → Usar `GeneraMovimiento` + inferencia por `TipoDerivado`
- [x] `FechaAfectacionInventario` → `MovimientoInventarioGenerado`
- [x] Limpieza de cache `__pycache__` para reflejar cambios

#### Migración P0 Workflows/SLA (24 Mayo 2026)
- [x] **OrquestadorService migrado a SQL** (11 → 0 refs MongoDB)
- [x] **SLA Service migrado a SQL** (17 → 0 refs MongoDB)
- [x] **Tablas creadas en EDARSAHUB**

#### Migración Referencias MongoDB Restantes
- [x] **Referencias MongoDB reducidas**: 80 → 21 en producción (-74%)

---

## Pendiente

### 🔄 En Progreso

#### Jobs del Scheduler
- [x] 9 jobs funcionando (sync_comercial, notificaciones, etc.)
- [x] `inventarios_detector` y `pedidos_detector` con protección `_is_stub_db()`

---

### ⏳ Pendiente

#### P1 - Alta Prioridad
1. **Triggers automáticos Cava Socios** - Envío mensual de estados de cuenta
2. **Flujos avanzados CRM** - Sincronización y seguimiento de oportunidades

#### P2 - Media Prioridad
1. **Reportes PDF Tablajería** - Orden de Tablaje, Costeo, Rendimientos
2. **Restructuración modular** - Alinear directorios con manifiesto ERP

#### P3 - Backlog Técnico
1. Modularización backend (separar server.py por módulos)
2. Portales externos (Proveedores, Comisionistas, Clientes)
3. Módulos satélite (Comandero, Chef IA, EDARSA GO)

---

## Actualizaciones Recientes (24 Mayo 2026)

### ✅ Reportes PDF Cava de Socios (COMPLETO)
- **Servicio** `/app/backend/modules/cava_socios/report_service.py`
- **Endpoints API**:
  - `GET /api/cava-socios/reportes/socio/{id}/ficha` - Ficha completa del socio
  - `GET /api/cava-socios/reportes/socio/{id}/consumos` - Historial de consumos
  - `GET /api/cava-socios/reportes/socio/{id}/estado-cuenta` - Estado de cuenta
- **Frontend**: Botones de descarga en `SocioDetail.jsx` (Ficha PDF, Consumos, Estado Cuenta)
- **Tecnología**: ReportLab 4.4.10 para generación PDF profesional

### ✅ CRM Flujos Avanzados (24 Mayo 2026) - NUEVO
- **Sistema de Triggers**:
  - 9 tipos de evento: OPORTUNIDAD_CREADA/ACTUALIZADA, ETAPA_CAMBIADA, GANADA/PERDIDA, ACTIVIDAD_VENCIDA, SLA_VENCIDO, MONTO_ACTUALIZADO, RESPONSABLE_CAMBIADO
  - 7 tipos de acción: CREAR_ACTIVIDAD, ENVIAR_EMAIL, ENVIAR_WHATSAPP, CREAR_NOTIFICACION, ACTUALIZAR_CAMPO, WEBHOOK, CREAR_TAREA_SEGUIMIENTO
  - Condiciones JSON con operadores: `$gt`, `$lt`, `$in`, `$ne`, etc.
- **Endpoints API**: `/api/crm/triggers/*`
- **Jobs Scheduler**:
  - `crm_sync` - Sincronización CRMs externos (cada 30 min)
  - `crm_sla_check` - Verificación SLAs (cada hora)
  - `crm_actividades_vencidas` - Recordatorios (cada 15 min)
- **Tablas SQL**: `CRM_Triggers`, `CRM_Trigger_Log`, `CRM_Tareas`
- **Triggers de ejemplo creados**: 3 (Seguimiento inicial, Alerta SLA, Celebración ganada)
- **Configuración**:
  - Email SMTP: `mail.edarsa.com.mx:587` (notificaciones@edarsa.com.mx)
  - WhatsApp: Twilio `+14155238886`
- **Endpoints**:
  - `POST /api/cava-socios/socios/{id}/enviar-reporte` - Envío individual
  - `POST /api/cava-socios/socios/{id}/enviar-todos-reportes` - Envío masivo
- **Canales soportados**: `email`, `whatsapp`, combinados
- **Job Automático Mensual**:
  - `cava_socios_monthly` - Envío de estados de cuenta a socios activos
  - Cron: `0 9 1 * *` (9:00 AM, día 1 de cada mes)
  - Archivo: `/app/backend/core/scheduler/jobs/cava_socios_monthly_job.py`

---

## Actualizaciones Recientes (24 Mayo 2026)

### ✅ Valor Declarado Botellas (CORREGIDO)
- Campo `CapacidadML` → `Capacidad` corregido en servicio
- `valor_declarado` y `añada` ahora se incluyen en respuesta de botellas
- `valor_total_declarado` calculado correctamente en detalle de socio

### ✅ CRM Pipeline Automation (NUEVO)
- **Tablas SQL creadas**:
  - `CRM_Automation_Reglas` - Reglas de automatización
  - `CRM_Automation_Log` - Log de ejecuciones
  - Columna `DiasSLAMaximo` agregada a `CRM_Config_PipelineEtapas`
- **Servicio** `/app/backend/modules/crm/automation_service.py`
- **Endpoints API** `/api/crm/automation/*`:
  - `GET /reglas` - Listar reglas activas
  - `POST /reglas` - Crear nueva regla
  - `GET /sla/verificar` - Verificar SLA de oportunidades
  - `GET /estadisticas` - Estadísticas de automatizaciones
  - `POST /ejecutar/cambio-etapa` - Trigger manual
- **3 reglas de ejemplo** insertadas:
  1. Seguimiento en Propuesta (crear actividad)
  2. Probabilidad en Negociación (actualizar campo)
  3. Notificación Cierre Ganado (enviar notificación)

### ✅ Pool pymssql Optimizado (MEJORADO)
- `LOGIN_TIMEOUT`: 30s → 45s
- `QUERY_TIMEOUT`: 90s → 120s  
- `CONNECT_TIMEOUT`: 30s → 45s
- `MAX_RETRIES`: 3 → 4
- `HEALTH_CHECK_TIMEOUT`: 15s → 20s
- Nuevos errores recuperables agregados

---

## Archivos Clave - Tablajería

### Backend
- `/app/backend/modules/tablajeria/ordenes_service.py` - Servicio principal de órdenes
- `/app/backend/modules/tablajeria/fase6_service.py` - Inventario, Costeo, Contabilidad
- `/app/backend/modules/tablajeria/routes.py` - Endpoints API
- `/app/backend/modules/tablajeria/schemas.py` - Modelos Pydantic

### Tablas SQL Server
- `Operaciones_Tablaje_Ordenes` - Órdenes de tablaje
- `Operaciones_Tablaje_OrdenesDetalle` - Detalles (derivados)
- `Operaciones_Tablaje_Plantillas` - Plantillas de transformación
- `Operaciones_Tablaje_PlantillasDetalle` - Detalles de plantillas
- `Tablajeria_MovimientosInventario` - Afectación de inventarios
- `Tablajeria_CosteoProduccion` - Costeo de producción
- `Tablajeria_CosteoDetalle` - Detalle de costeo por producto
- `Tablajeria_PolizasContables` - Pólizas generadas
- `Tablajeria_PolizasDetalle` - Asientos contables
- `Tablajeria_ConfigContable` - Configuración por empresa

---

## API Endpoints Tablajería

### Órdenes
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/tablajeria/ordenes` | Listar órdenes |
| GET | `/api/tablajeria/ordenes/{id}` | Obtener orden con detalles |
| POST | `/api/tablajeria/ordenes` | Crear orden desde plantilla |
| POST | `/api/tablajeria/ordenes/captura-directa` | Crear orden sin plantilla |
| PUT | `/api/tablajeria/ordenes/{id}/iniciar` | Iniciar ejecución |
| PUT | `/api/tablajeria/ordenes/{id}/resultados` | Registrar resultados |
| PUT | `/api/tablajeria/ordenes/{id}/cerrar` | Cerrar (con Fase 6 opcional) |
| PUT | `/api/tablajeria/ordenes/{id}/cancelar` | Cancelar orden |
| PUT | `/api/tablajeria/ordenes/{id}/autorizar` | Autorizar desviaciones |

### Fase 6 (Inventario, Costeo, Contabilidad)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/tablajeria/ordenes/{id}/fase6/procesar-cierre` | Proceso completo |
| POST | `/api/tablajeria/ordenes/{id}/fase6/afectar-inventario` | Solo inventario |
| POST | `/api/tablajeria/ordenes/{id}/fase6/calcular-costeo` | Solo costeo |
| POST | `/api/tablajeria/ordenes/{id}/fase6/generar-poliza` | Solo póliza |
| GET | `/api/tablajeria/fase6/config-contable/{empresa_id}` | Config contable |
| PUT | `/api/tablajeria/fase6/config-contable/{empresa_id}` | Guardar config |

---

## Payload Captura Directa (Ejemplo)

```json
{
  "empresa_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "fecha_operacion_mexico": "2026-05-24",
  "insumo_base_codigo": "INS-SALMON-001",
  "insumo_base_nombre": "Salmón fresco",
  "cantidad_base_planeada": 5.0,
  "detalles": [
    {
      "producto_derivado_nombre": "Filete de salmón",
      "tipo_derivado": "PRINCIPAL",
      "cantidad_esperada": 3.5,
      "porcentaje_esperado": 70.0
    },
    {
      "producto_derivado_nombre": "Recortes",
      "tipo_derivado": "MERMA",
      "cantidad_esperada": 1.0,
      "porcentaje_esperado": 20.0
    }
  ]
}
```

## Payload Cerrar con Fase 6 (Ejemplo)

```json
{
  "observaciones": "Cierre con costeo",
  "ejecutar_fase6": true,
  "costo_unitario_insumo": 180.00,
  "costo_mano_obra": 30.00,
  "costo_indirectos": 20.00,
  "costo_energia": 10.00,
  "otros_costos": 5.00
}
```

---

## Notas Técnicas

### Diferencias de Columnas SQL
| Tabla | Columna Plantilla | Columna Orden |
|-------|-------------------|---------------|
| PlantillasDetalle | `PorcentajeRendimientoEsperado` | - |
| OrdenesDetalle | - | `PorcentajeEsperado` |
| PlantillasDetalle | `EsInventariable` | - |
| OrdenesDetalle | - | `GeneraMovimiento` |

### Reglas de Costeo
1. **PROPORCIONAL**: Costo distribuido según cantidad producida
2. **FIJO**: Costo según % predefinido en plantilla
3. **RESIDUAL**: (Futuro) Costo asignado al producto residual

### Tolerancia de Desviación
- Default: 5%
- Si desviación > tolerancia: Estado `PENDIENTE_AUTORIZACION`
- Si desviación <= tolerancia: Estado `CERRADA` + Fase 6 ejecutada
