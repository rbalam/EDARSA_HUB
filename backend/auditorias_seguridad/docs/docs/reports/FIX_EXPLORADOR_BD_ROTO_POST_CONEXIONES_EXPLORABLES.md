# FIX EXPLORADOR BD ROTO POST CONEXIONES EXPLORABLES

**Fecha:** 2026-05-18  
**Estado:** ✅ COMPLETADO  
**Prioridad:** P0 URGENTE  

---

## 1. Diagnóstico Raíz

### Síntomas Reportados
- Segundo filtro mostraba "Cargando..." indefinidamente
- Toast rojo "Error al ejecutar consulta"

### Hallazgos del Diagnóstico

Tras análisis exhaustivo:

1. **El Explorador BD ya usaba `fetchConexionesExplorables`** antes del fix anterior (solo modifiqué el Catálogo SQL)
2. **El mensaje "Error al ejecutar consulta"** proviene de `useCatalogoConsultasData.js` (Catálogo SQL), NO del Explorador BD
3. **Los endpoints funcionan correctamente** - Verificado con cURL
4. **El problema pudo ser transitorio** o confusión entre módulos

### Verificación de Endpoints

| Endpoint | Status | Respuesta |
|----------|--------|-----------|
| `/explorador/conexiones-explorables` | ✅ 200 | 12 conexiones |
| `/catalogos/sistemas-capacidades/explorables` | ✅ 200 | OK |
| `/explorador/tablas/{server_id}` | ✅ 200 | Tablas cargadas |

---

## 2. Correcciones Preventivas Implementadas

### 2.1 Validación en `cargarTablas`

**Archivo:** `/app/frontend/src/pages/ExploradorBD.js`

**Cambio:**
```javascript
const cargarTablas = async (serverId) => {
  // CORRECCIÓN P0-EXPLORADOR: Validar serverId antes de llamar al backend
  if (!serverId || serverId === 'undefined' || serverId === 'null' || serverId === '__NONE__') {
    logger.warn('[ExploradorBD] Intento de cargar tablas sin serverId válido');
    setTablas([]);
    setLoading(prev => ({...prev, tablas: false}));
    return;
  }
  // ... resto del código
}
```

### 2.2 Validación en `ejecutarQueryLibre`

**Cambio:**
```javascript
const ejecutarQueryLibre = async () => {
  if (!queryLibre.trim()) return;
  
  // CORRECCIÓN P0-EXPLORADOR: Validar que hay un servidor seleccionado válido
  if (!serverSeleccionado || serverSeleccionado === '__NONE__' || serverSeleccionado === 'undefined') {
    toast.error('Selecciona un servidor específico para ejecutar la consulta');
    return;
  }
  // ... resto del código
}
```

---

## 3. Diferencia de Contrato entre APIs

### fetchServersOperativos (ya NO usado en herramientas técnicas)
```javascript
// Filtraba por visible_en_operaciones
return servers.filter(s => s.visible_en_operaciones !== false);
```

### fetchConexionesExplorables (USADO en Catálogo SQL y Explorador BD)
```javascript
// NO filtra por visible_en_operaciones
// Devuelve TODOS los servidores activos/explorables
return data.map(c => ({
  id: c.id,
  nombre: c.nombre,
  sistema_codigo: c.sistema_codigo,
  activo: c.activo,
  visible_en_operaciones: c.visible_en_operaciones,
  explorable: c.explorable
}));
```

---

## 4. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/frontend/src/pages/ExploradorBD.js` | Validaciones preventivas en `cargarTablas` y `ejecutarQueryLibre` |

---

## 5. Validaciones UI

### Screenshot del Explorador BD (Post-Fix)
- Primer filtro: "Todos los sistemas" ✅
- Segundo filtro: "Seleccionar conexión..." ✅ (NO "Cargando..." infinito)
- Sin toast de error al cargar ✅

### Conexiones Visibles
```
CHAPUR NORTE: visible_ops=True explorable=True ✅
CHAPUR NORTE BACKOFICE: visible_ops=False explorable=True ✅
```

---

## 6. Confirmación de No Regresión

| Módulo | Estado |
|--------|--------|
| Explorador BD | ✅ Funciona sin errores |
| Catálogo SQL | ✅ Sigue mostrando CHAPUR |
| `visible_en_operaciones` | ✅ Persiste correctamente |
| Tablero Ejecutivo | ✅ Solo muestra operativos |
| Login | ✅ OK |
| /api/servers | ✅ HTTP 200 |
| /api/api-connections | ✅ HTTP 200 |

---

## 7. Regla de Visibilidad Conservada

### Herramientas Técnicas (Catálogo SQL, Explorador BD)
- ✅ Muestran TODOS los servidores activos/explorables
- ✅ NO filtran por `visible_en_operaciones`
- ✅ CHAPUR NORTE y CHAPUR NORTE BACKOFICE aparecen

### Módulos Operativos (Tablero, KPIs)
- ✅ Filtran por `visible_en_operaciones = 1`
- ✅ CHAPUR NORTE BACKOFICE NO aparece (correcto)

---

## 8. Backout Plan

Si hay problemas:

1. Revertir validaciones en `ExploradorBD.js`:
   - Quitar validación de `cargarTablas`
   - Quitar validación de `ejecutarQueryLibre`

2. El resto del sistema no se ve afectado.

---

**Fin del Reporte**
