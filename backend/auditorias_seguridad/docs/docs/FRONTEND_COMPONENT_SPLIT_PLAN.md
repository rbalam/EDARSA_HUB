# FRONTEND COMPONENT SPLIT PLAN
## EDARSA HUB - Plan de División de Componentes Grandes

**Fecha:** 2025-12-XX  
**Estado:** DOCUMENTACIÓN PARA FASES FUTURAS  
**Prioridad:** MEDIA (no urgente para estabilización)

---

## 1. RESUMEN

Este documento describe el plan de división de componentes grandes identificados en el reporte de calidad. **NO SE EJECUTARÁ EN LA FASE DE ESTABILIZACIÓN** para evitar romper módulos funcionales.

---

## 2. ESTADO ACTUAL DE COMPONENTES

| Componente | Líneas | Hooks Extraídos | Subcomponentes | Estado |
|------------|--------|-----------------|----------------|--------|
| CentroControl.jsx | 1,305 | ✅ useCentroControlData | ✅ CentroControlComponents | **YA REFACTORIZADO** |
| AuditoriasProgramadas.jsx | 913 | ✅ useAuditoriasData | ✅ AuditoriasComponents | **YA REFACTORIZADO** |
| Comercial.js | 2,926 | ❌ | ❌ | **BLINDADO - NO TOCAR** |
| FinanzasCuentasPorPagar.jsx | 732 | ❌ | ❌ | Presentacional |
| TabOperativasCompras.jsx | 558 | ❌ | ✅ 8 subcomponentes | **YA REFACTORIZADO** |

---

## 3. COMPONENTES YA REFACTORIZADOS

### 3.1 CentroControl.jsx (1,305 líneas)
**Estado:** ✅ YA REFACTORIZADO

**Hooks extraídos:**
- `/components/centro-control/useCentroControlData.js` (5,524 bytes)
- `/components/centro-control/useWebSocketNotifications.js` (5,191 bytes)

**Subcomponentes:**
- `/components/centro-control/CentroControlComponents.jsx`

**Acción futura:** NINGUNA URGENTE

---

### 3.2 AuditoriasProgramadas.jsx (913 líneas)
**Estado:** ✅ YA REFACTORIZADO

**Hooks extraídos:**
- `/components/auditorias/useAuditoriasData.js` (3,830 bytes)

**Subcomponentes:**
- `/components/auditorias/AuditoriasComponents.jsx`

**Acción futura:** NINGUNA URGENTE

---

### 3.3 TabOperativasCompras.jsx (558 líneas)
**Estado:** ✅ YA REFACTORIZADO

**Subcomponentes extraídos (8):**
- `AccionesGerenciaCard.jsx`
- `AccionesTesoreriaCard.jsx`
- `AutomatizacionesTable.jsx`
- `BitacoraList.jsx`
- `EstadoFinalCard.jsx`
- `PronosticoCard.jsx`
- `ResumenEjecutivoCard.jsx`
- `SeguimientoComprasCard.jsx`

**Acción futura:** NINGUNA URGENTE

---

## 4. COMPONENTES PROTEGIDOS (NO TOCAR)

### 4.1 Comercial.js (2,926 líneas) ⚠️ BLINDADO
**Estado:** PROTEGIDO - NO MODIFICAR

**Razón de protección:**
- Archivo marcado como BLINDADO en código fuente
- Contiene lógica crítica de ventas y KPIs
- Alto riesgo de romper funcionalidad existente
- Múltiples dependencias con filtros y permisos

**Dependencias críticas:**
- Permisos por rol
- Filtros por sucursal/empresa
- Cálculos de KPIs
- Integración con servidores SQL externos

**Plan futuro (FASE POSTERIOR):**
1. Crear rama dedicada: `refactor/comercial-split`
2. Extraer hook: `useComercialData.js`
3. Extraer subcomponentes:
   - `ComercialKPIs.jsx`
   - `ComercialVentas.jsx`
   - `ComercialFilters.jsx`
   - `ComercialCharts.jsx`
4. Testing exhaustivo antes de merge
5. Rollback plan documentado

---

### 4.2 FinanzasCuentasPorPagar.jsx (732 líneas)
**Estado:** EVALUADO - MAYORMENTE PRESENTACIONAL

**Análisis:**
- Ya tiene useMemo para optimizaciones
- Componentes internos bien estructurados
- No requiere extracción urgente

**Plan futuro (OPCIONAL):**
1. Extraer hook si crece más
2. Considerar split solo si se agregan features

---

## 5. ORDEN RECOMENDADO PARA REFACTORS FUTUROS

| Prioridad | Componente | Riesgo | Esfuerzo | Beneficio |
|-----------|------------|--------|----------|-----------|
| 1 | FinanzasCuentasPorPagar | Bajo | 1 día | Medio |
| 2 | Comercial.js | ALTO | 3-5 días | Alto |

---

## 6. PRUEBAS NECESARIAS ANTES DE REFACTOR

### Para cualquier componente grande:

1. **Funcionalidad básica:**
   - Carga inicial de datos
   - Filtros funcionan
   - Permisos respetados

2. **Filtros por contexto:**
   - Empresa
   - Sucursal
   - Servidor
   - Almacén
   - Usuario

3. **Acciones CRUD:**
   - Crear (si aplica)
   - Leer
   - Actualizar (si aplica)
   - Eliminar (si aplica)

4. **Exportaciones:**
   - Excel
   - PDF
   - CSV

5. **Permisos:**
   - SuperAdministrador
   - Administrador
   - Usuario normal
   - Solo lectura

---

## 7. DEPENDENCIAS CON ENDPOINTS

| Componente | Endpoints Críticos |
|------------|-------------------|
| CentroControl | /api/centro-control/*, /api/alertas/* |
| AuditoriasProgramadas | /api/v2/auditorias-programadas/* |
| Comercial | /api/comercial/*, /api/servers/* |
| FinanzasCuentasPorPagar | /api/finanzas/cxp/* |
| TabOperativasCompras | /api/compras/operativas/* |

---

## 8. CONCLUSIÓN

**Estado de esta fase:** ✅ DOCUMENTADO

Los componentes más críticos (CentroControl, AuditoriasProgramadas, TabOperativasCompras) **ya fueron refactorizados** en sesiones anteriores.

El componente Comercial.js está **BLINDADO** y no debe tocarse sin una fase dedicada con testing exhaustivo.

**NO SE REQUIEREN CAMBIOS EN ESTA FASE DE ESTABILIZACIÓN.**
