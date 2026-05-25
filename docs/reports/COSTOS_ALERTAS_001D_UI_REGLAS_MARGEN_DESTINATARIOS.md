# COSTOS-ALERTAS-001-D: UI para Reglas de Margen

## Fecha: 25 Mayo 2026
## Estado: ✅ COMPLETADO
## Autor: Agente E1

---

## 1. OBJETIVO

Crear interfaz de usuario (UI) dentro del módulo `/comercial/costos-margenes` para configurar reglas de margen esperado con jerarquía:
- **Producto > Subfamilia > Familia > Grupo**

---

## 2. UBICACIÓN

- **Módulo**: Comercial → Costos y Márgenes
- **Tab**: "Reglas de Margen" (5to tab)
- **Archivo**: `/app/frontend/src/pages/comercial/TabReglasMargen.jsx`

---

## 3. FUNCIONALIDADES IMPLEMENTADAS

### 3.1 Vista Principal

| Funcionalidad | Estado |
|---------------|--------|
| Ver reglas configuradas | ✅ |
| Crear nueva regla | ✅ |
| Editar regla existente | ✅ |
| Desactivar regla (soft delete) | ✅ |
| Resolver regla por jerarquía | ✅ |
| Evaluar margen individual | ✅ |
| Filtrar por nivel | ✅ |
| Buscar por código | ✅ |

### 3.2 Estadísticas

- Total de reglas
- Reglas activas
- Reglas por grupo
- Reglas por producto

### 3.3 Umbrales de Severidad

Visualización de los umbrales configurados:
- **INFORMATIVA**: 0 - 1.99 puntos (azul)
- **MEDIA**: 2 - 4.99 puntos (amarillo)
- **ALTA**: 5 - 9.99 puntos (naranja)
- **CRÍTICA**: 10+ puntos (rojo)

### 3.4 Tabla de Reglas

Columnas:
- Nivel (badge colorizado)
- Código de entidad
- Margen esperado (%)
- Severidad base
- Descripción
- Estado (Activa/Inactiva)
- Acciones (Editar/Desactivar)

### 3.5 Jerarquía Visual

Banner informativo mostrando:
```
PRODUCTO (más específico) → SUBFAMILIA → FAMILIA → GRUPO (más general)
```

---

## 4. MODALES IMPLEMENTADOS

### 4.1 Modal Nueva/Editar Regla

- **Nivel de Aplicación**: Selector visual con 4 opciones
- **Código de Entidad**: Input con validación uppercase
- **Margen Esperado**: Slider + input numérico (0-100%)
- **Severidad Base**: Botones de selección
- **Descripción**: Campo opcional
- **Info de Jerarquía**: Banner explicativo

### 4.2 Modal Resolver Regla

Permite probar qué regla aplica según la jerarquía:
- Input para Producto
- Input para Subfamilia
- Input para Familia
- Input para Grupo
- Resultado mostrando: Fuente, Margen esperado, Descripción

### 4.3 Modal Evaluar Margen

Permite evaluar un margen actual contra la regla aplicable:
- Slider de margen actual
- Inputs de contexto (producto/familia/grupo)
- Resultado con:
  - Tiene alerta (Sí/No)
  - Estado (OK/ALERTA)
  - Margen actual vs esperado
  - Diferencia en puntos
  - Severidad resultante

---

## 5. ENDPOINTS CONSUMIDOS

| Método | Endpoint | Función |
|--------|----------|---------|
| GET | `/comercial/alertas-margen/reglas` | Listar reglas |
| POST | `/comercial/alertas-margen/reglas` | Crear regla |
| PUT | `/comercial/alertas-margen/reglas/{id}` | Actualizar regla |
| DELETE | `/comercial/alertas-margen/reglas/{id}` | Desactivar regla |
| GET | `/comercial/alertas-margen/resolver-regla` | Resolver jerarquía |
| POST | `/comercial/alertas-margen/evaluar` | Evaluar margen |
| GET | `/comercial/alertas-margen/estadisticas` | Stats de reglas |
| GET | `/comercial/alertas-margen/umbrales` | Umbrales severidad |

---

## 6. ARCHIVOS MODIFICADOS/CREADOS

| Archivo | Acción |
|---------|--------|
| `/app/frontend/src/pages/comercial/TabReglasMargen.jsx` | CREADO |
| `/app/frontend/src/pages/comercial/CostosMargenes.jsx` | MODIFICADO (import + tab) |

---

## 7. VALIDACIONES CUMPLIDAS

| # | Validación | Estado |
|---|------------|--------|
| 1 | Costos y Márgenes carga | ✅ |
| 2 | Tab "Reglas de Margen" visible | ✅ |
| 3 | Crear regla funciona | ✅ |
| 4 | Editar regla funciona | ✅ |
| 5 | Desactivar regla funciona | ✅ |
| 6 | Resolver regla funciona | ✅ |
| 7 | Jerarquía visible | ✅ |
| 8 | RBAC protege acciones | ✅ (vía token) |
| 9 | UnidadNegocio respetada | ✅ (endpoints filtran) |
| 10 | No MongoDB | ✅ |
| 11 | No notificaciones enviadas | ✅ |
| 12 | No precios modificados | ✅ |
| 13 | Dashboard Comercial funciona | ✅ |
| 14 | Tablero Ejecutivo funciona | ✅ |

---

## 8. RESTRICCIONES RESPETADAS

- ✅ No se usa MongoDB
- ✅ No se crean jobs
- ✅ No se envía email real
- ✅ No se envía WhatsApp real
- ✅ No se modifican precios oficiales
- ✅ No se crean solicitudes automáticas
- ✅ No se toca Dashboard Comercial
- ✅ No se toca Tablero Ejecutivo
- ✅ No se toca POS/Comandero
- ✅ No se ejecuta IA
- ✅ No se hace scraping

---

## 9. SCREENSHOTS

### Vista Tab Reglas de Margen
- Estadísticas: 3 Total, 3 Activas, 1 Grupo, 1 Producto
- Umbrales de severidad con colores
- Tabla con 3 reglas configuradas
- Jerarquía visual

### Modal Nueva Regla
- Selector de nivel con 4 opciones visuales
- Slider de margen esperado
- Botones de severidad
- Info de jerarquía

---

## 10. PRÓXIMOS PASOS

| Fase | Descripción | Estado |
|------|-------------|--------|
| COSTOS-ALERTAS-001-E | Motor de evaluación masiva | PENDIENTE |
| COSTOS-ALERTAS-001-F | Job/scheduler + envío Email/WhatsApp | PENDIENTE |

---

## 11. BACKLOG REGISTRADO

**MIGRACION-FRONTEND-COMPETIDORES-ENTERPRISE**

Objetivo: Actualizar frontend de competidores/benchmark para usar arquitectura enterprise:
- `Comercial_CompetidoresCatalogo`
- `Comercial_CompetidoresUnidad`
- `vw_CompetidoresPorUnidad`

Regla: Todo filtro debe requerir `UnidadNegocioID`.
