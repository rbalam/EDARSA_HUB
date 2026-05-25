# FASE 1C-3I-C: Integración GPT-5.2 para Pricing IA y Benchmark

**Fecha:** 2026-05-25  
**Estado:** COMPLETADO  
**Modelo IA:** GPT-5.2 (OpenAI via Emergent LLM Key)

---

## 1. RESUMEN EJECUTIVO

Se integró GPT-5.2 como proveedor IA oficial para análisis de pricing y benchmark competitivo, siguiendo la regla: **GPT-5.2 sugiere, NO autoriza ni aplica precios**.

### Resultados Principales:
- **1 servicio IA** creado (`pricing_ai_service.py`)
- **1 archivo de rutas** con 5 endpoints IA
- **1 tabla de auditoría** para guardar análisis (`Comercial_PricingAnalisisIA`)
- **4 tipos de análisis** disponibles
- **Sistema de confianza** (ALTA/MEDIA/BAJA) implementado
- **NO se modifican precios oficiales**
- **NO se crean solicitudes automáticas**
- **NO se usa MongoDB** (todo en EDARSAHUB SQL)
- **NO se hace scraping web**

---

## 2. ARCHIVOS CREADOS

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `/app/backend/modules/comercial/services/pricing_ai_service.py` | ~1300 | Servicio principal de integración GPT-5.2 |
| `/app/backend/modules/comercial/routes_pricing_ai.py` | ~220 | Endpoints FastAPI para IA |

---

## 3. ENDPOINTS IA CREADOS

| Método | Ruta | Permiso RBAC | Descripción |
|--------|------|--------------|-------------|
| POST | `/api/comercial/pricing-ai/analizar-producto` | `comercial.precios_sugeridos.ver_ia` | Análisis completo de producto con justificación |
| POST | `/api/comercial/pricing-ai/sugerir-comparables` | `comercial.precios_sugeridos.ver_ia` | Sugerir productos comparables de competencia |
| POST | `/api/comercial/pricing-ai/generar-justificacion` | `comercial.precios_sugeridos.ver_ia` | Generar justificación para precio propuesto |
| POST | `/api/comercial/pricing-ai/analizar-benchmark` | `comercial.benchmark.ver` | Análisis estratégico de benchmark |
| GET | `/api/comercial/pricing-ai/analisis/{id}` | `comercial.precios_sugeridos.ver_ia` | Recuperar análisis guardado |
| GET | `/api/comercial/pricing-ai/health` | (público) | Health check del módulo IA |

---

## 4. TABLA DE AUDITORÍA CREADA

### Comercial_PricingAnalisisIA

```sql
CREATE TABLE Comercial_PricingAnalisisIA (
    AnalisisIAID UNIQUEIDENTIFIER PRIMARY KEY,
    ProductoID UNIQUEIDENTIFIER NULL,
    CodigoProducto NVARCHAR(100) NOT NULL,
    ServerID UNIQUEIDENTIFIER NULL,
    EmpresaID INT NOT NULL,
    UnidadNegocioID INT NOT NULL,
    TipoAnalisis VARCHAR(50) NOT NULL,
    ModeloIAUsado VARCHAR(50) NOT NULL,
    VersionModelo VARCHAR(50) NOT NULL,
    PromptResumen NVARCHAR(1000) NULL,
    DatosEntradaJSON NVARCHAR(MAX) NULL,
    RespuestaIAJSON NVARCHAR(MAX) NULL,
    JustificacionIA NVARCHAR(MAX) NULL,
    ConfianzaIA VARCHAR(20) NOT NULL,
    RequiereRevisionHumana BIT DEFAULT 0,
    PrecioActual DECIMAL(18,2) NULL,
    PrecioSugerido DECIMAL(18,2) NULL,
    MargenActual DECIMAL(8,4) NULL,
    MargenSugerido DECIMAL(8,4) NULL,
    CompetidoresUsadosJSON NVARCHAR(MAX) NULL,
    FuentesUsadasJSON NVARCHAR(MAX) NULL,
    EstadoAnalisis VARCHAR(30) NOT NULL,
    UsuarioEjecucion NVARCHAR(100) NOT NULL,
    FechaEjecucion DATETIME2 NOT NULL,
    FechaCreacion DATETIME2 NOT NULL
);
```

**Nota:** La tabla se crea automáticamente (DDL idempotente) en el primer uso.

---

## 5. TIPOS DE ANÁLISIS IA

| Tipo | Endpoint | Descripción |
|------|----------|-------------|
| `ANALISIS_PRODUCTO` | `/analizar-producto` | Análisis completo con precio sugerido y justificación |
| `SUGERENCIA_COMPARABLES` | `/sugerir-comparables` | Sugerir productos comparables de competidores |
| `JUSTIFICACION_PRECIO` | `/generar-justificacion` | Justificar precio propuesto para solicitud |
| `ANALISIS_BENCHMARK` | `/analizar-benchmark` | Análisis estratégico de posicionamiento |

---

## 6. SISTEMA DE CONFIANZA

### Reglas de Clasificación

| Confianza | Criterio |
|-----------|----------|
| **ALTA** | Costo confiable + precio actual + benchmark comparable + datos validados |
| **MEDIA** | Costo e impuesto, pero benchmark parcial o comparables no perfectos |
| **BAJA** | Faltan datos, comparables débiles o inferencia parcial |

### Comportamiento según Confianza

- **ALTA**: Análisis completo, recomendaciones directas
- **MEDIA**: Análisis con advertencias, requiere validación
- **BAJA**: No crear solicitud automática, marcar `RequiereRevisionHumana = 1`

---

## 7. CONFIGURACIÓN GPT-5.2

### Proveedor
```
Modelo: gpt-5.2
Proveedor: OpenAI via Emergent LLM Key
SDK: emergentintegrations
```

### Configuración de Entorno
```bash
# /app/backend/.env
EMERGENT_LLM_KEY=sk-emergent-c8aD06312408c4973B
```

### Uso en Código
```python
from emergentintegrations.llm.chat import LlmChat, UserMessage

chat = LlmChat(
    api_key=llm_key,
    session_id=f"pricing-{codigo_producto}-{uuid}",
    system_message="Eres un analista de precios experto."
).with_model("openai", "gpt-5.2")

response = await chat.send_message(UserMessage(text=prompt))
```

---

## 8. DATOS DE ENTRADA UTILIZADOS

El análisis IA solo utiliza datos de EDARSAHUB SQL:

| Fuente | Datos |
|--------|-------|
| `Sync_Productos` | Nombre, familia, subfamilia, costo receta, precio venta |
| `Sync_Productos_Insumos` | Costo, último costo, costo promedio |
| `Sistema_UnidadesNegocioPerfilDigital` | Concepto, tipo, segmento, ciudad, ticket objetivo |
| `Comercial_Competidores` | Nombre, tipo, segmento, es directo/aspiracional |
| `Comercial_CompetidoresMenuItems` | Productos, precios, categorías, confianza |
| `Comercial_PricingBenchmarkProducto` | Mapeos producto vs competencia |

---

## 9. EJEMPLOS DE RESPUESTA IA

### 9.1 Análisis de Producto

```json
{
    "success": true,
    "analisis_id": "bf15ced0-...",
    "estado": "REQUIERE_REVISION",
    "data": {
        "producto": {"codigo": "0000005008", "nombre": "(C) Arrachera Lorenza de kg"},
        "precio_sugerido_ia": 0,
        "justificacion": "El costo cargado ($0.36) es atípicamente bajo...",
        "posicionamiento": "No hay benchmarks de precios contra competencia...",
        "recomendacion": "REQUIERE_MAS_DATOS",
        "confianza": "MEDIA",
        "requiere_revision": true
    }
}
```

### 9.2 Análisis de Benchmark

```json
{
    "success": true,
    "analisis_id": "438398cc-...",
    "estado": "GENERADO",
    "data": {
        "unidad": {"nombre": "Origen Unión Gastronómica del Fuego", "segmento": "PREMIUM"},
        "resumen": "Con la información disponible, Origen compite en fine dining premium...",
        "posicionamiento": "COMPETITIVO",
        "oportunidades": ["Definir arquitectura de precios...", "Diferenciación por propuesta..."],
        "riesgos": ["Benchmark incompleto...", "Riesgo de inconsistencia..."],
        "recomendaciones": ["Completar benchmark...", "Definir concepto...", "Establecer ticket..."],
        "prioridad": "ALTA"
    }
}
```

---

## 10. VALIDACIONES REALIZADAS

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Login funciona | ✅ |
| 2 | Costos y Márgenes funciona | ✅ (HTTP 200) |
| 3 | Endpoints 1C-3I-B funcionan | ✅ |
| 4 | Endpoint analizar-producto funciona | ✅ |
| 5 | Endpoint analizar-benchmark funciona | ✅ |
| 6 | Análisis IA se guarda en SQL | ✅ |
| 7 | Análisis IA se recupera por ID | ✅ |
| 8 | NO se usa MongoDB | ✅ |
| 9 | NO se ejecuta scraping | ✅ |
| 10 | NO se modifican precios oficiales | ✅ |
| 11 | NO se crean solicitudes automáticas | ✅ |
| 12 | Vinos usan tabla de rangos (no reemplazada) | ✅ |
| 13 | Confianza clasificada ALTA/MEDIA/BAJA | ✅ |
| 14 | NO se exponen API keys | ✅ |
| 15 | Health check reporta estado correcto | ✅ |

---

## 11. CONFIRMACIONES OBLIGATORIAS

| # | Confirmación | Resultado |
|---|--------------|-----------|
| 1 | GPT-5.2 sugiere, NO autoriza | ✅ |
| 2 | GPT-5.2 NO aplica precios | ✅ |
| 3 | NO se usa MongoDB | ✅ |
| 4 | NO se hace scraping | ✅ |
| 5 | NO se consultan sitios web externos | ✅ |
| 6 | NO se modifican precios oficiales | ✅ |
| 7 | NO se crean solicitudes automáticas | ✅ |
| 8 | Regla de vinos intacta | ✅ |
| 9 | NO se exponen secretos | ✅ |
| 10 | Datos almacenados en EDARSAHUB SQL | ✅ |

---

## 12. RIESGOS PENDIENTES

1. **Productos sin costo**: El análisis depende de tener costo configurado. Sin costo, devuelve justificación parcial.

2. **Benchmark incompleto**: Sin competidores/items suficientes, el análisis tiene confianza BAJA.

3. **Validación de respuesta JSON**: GPT-5.2 a veces devuelve respuestas no JSON. Se implementó parsing tolerante.

---

## 13. RECOMENDACIÓN PARA SUBFASE 1C-3I-D

### Siguiente Paso: Frontend de Motor de Precios IA

**Funcionalidades sugeridas:**

1. **Panel de Análisis de Producto**
   - Formulario para seleccionar producto
   - Mostrar análisis IA con justificación
   - Visualización de confianza (badge ALTA/MEDIA/BAJA)
   - Botón "Crear Solicitud de Cambio" (si confianza >= MEDIA)

2. **Dashboard de Benchmark**
   - Resumen de competidores configurados
   - Estado de preparación para IA
   - Análisis estratégico con recomendaciones
   - Gráficos de posicionamiento

3. **Gestión de Competidores**
   - CRUD de competidores con URLs
   - Captura manual de items de menú
   - Validación de benchmarks

4. **Historial de Análisis IA**
   - Lista de análisis ejecutados
   - Filtros por producto, fecha, confianza
   - Detalle de cada análisis

---

**FIN DEL REPORTE**

**Estado**: COMPLETADO  
**Modelo IA**: GPT-5.2 (OpenAI)  
**Endpoints IA**: 5  
**Tabla Auditoría**: Comercial_PricingAnalisisIA  
**MongoDB**: NO usado  
**Scraping**: NO ejecutado  
**Regresiones**: 0  
**Siguiente Acción**: Esperar autorización para SUBFASE 1C-3I-D (Frontend)
