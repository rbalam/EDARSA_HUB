# FIX AUTOMÁTICO SERVIDORES NUEVOS: CATÁLOGO SQL Y EXPLORADOR BD

**Fecha:** 2026-05-18  
**Estado:** ✅ COMPLETADO  
**Prioridad:** P0  

---

## 1. Diagnóstico Raíz

### Estado Inicial de CHAPUR NORTE y CHAPUR NORTE BACKOFICE en BD

```sql
-- ANTES de corrección
CHAPUR NORTE:
  id: d8b2d1eb-2e1f-4e43-b7d9-822bf671e315
  tipo_conexion: API_LOCAL
  activo: True ✅
  visible_en_operaciones: False ⚠️ (UI mostraba True pero no se guardaba)
  
CHAPUR NORTE BACKOFICE:
  id: 8cbdcc89-6495-49c3-be9c-a965db82c77f
  tipo_conexion: API_LOCAL
  activo: True ✅
  visible_en_operaciones: False ✅ (correcto para back office)
```

### Estado Final DESPUÉS de Corrección

```sql
-- DESPUÉS de corrección
CHAPUR NORTE:
  visible_en_operaciones: True ✅ (AHORA PERSISTE CORRECTAMENTE)
  
CHAPUR NORTE BACKOFICE:
  visible_en_operaciones: False ✅ (sin cambio, correcto)
```

---

## 2. Causa Exacta: `visible_en_operaciones` No Se Guardaba

**Archivo:** `/app/frontend/src/pages/Servidores.js`

**Problema (líneas 1784-1790):**
```javascript
// ANTES - Solo actualizaba estado local, NO llamaba al backend
onClick={() => {
  setApiConnections(prev => prev.map(a => 
    a.id === apiConn.id 
      ? {...a, visible_en_operaciones: !a.visible_en_operaciones} 
      : a
  ));
  toast.success(apiConn.visible_en_operaciones ? 'Oculto en operaciones' : 'Visible en operaciones');
}}
```

**Solución:**
```javascript
// DESPUÉS - Llama al backend y actualiza estado local solo si éxito
onClick={async () => {
  const newValue = !apiConn.visible_en_operaciones;
  try {
    await api.put(`/api-connections/${apiConn.id}`, {
      visible_en_operaciones: newValue
    });
    setApiConnections(prev => prev.map(a => 
      a.id === apiConn.id 
        ? {...a, visible_en_operaciones: newValue} 
        : a
    ));
    toast.success(newValue ? 'Visible en operaciones' : 'Oculto en operaciones');
  } catch (error) {
    toast.error('Error al guardar cambio');
  }
}}
```

---

## 3. Causa Exacta: No Aparecían en Catálogo SQL

**Archivo:** `/app/frontend/src/components/catalogo-consultas/useCatalogoConsultasData.js`

**Problema (línea 92):**
```javascript
// ANTES - Usaba fetchServersOperativos que FILTRA por visible_en_operaciones
const serversOperativos = await fetchServersOperativos();
```

**Solución:**
```javascript
// DESPUÉS - Usa fetchConexionesExplorables que NO filtra por visible_en_operaciones
import { fetchConexionesExplorables } from '../../services/exploradorService';
const conexionesExplorables = await fetchConexionesExplorables();
```

---

## 4. Causa Exacta: No Aparecían en Explorador BD

**Resultado del diagnóstico:** Explorador BD ya funcionaba correctamente.

El endpoint `/api/explorador/conexiones-explorables` ya usaba la lógica técnica correcta:
- Filtra por `activo = 1`
- NO filtra por `visible_en_operaciones`
- Devuelve CHAPUR NORTE y CHAPUR NORTE BACKOFICE

El problema era únicamente en Catálogo SQL.

---

## 5. Endpoints Auditados

| Endpoint | Estado | Filtra visible_ops |
|----------|--------|-------------------|
| `/api/explorador/conexiones-explorables` | ✅ Correcto | NO |
| `/api/api-connections` | ✅ Correcto | NO |
| `/api/comercial/tablero-ejecutivo` | ✅ Correcto | SÍ (correcto) |
| `/api/servers` | ✅ Correcto | Usa `visible_listado` |

---

## 6. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/frontend/src/pages/Servidores.js` | Toggle visible_en_operaciones ahora persiste en backend |
| `/app/frontend/src/components/catalogo-consultas/useCatalogoConsultasData.js` | Usa `fetchConexionesExplorables` en lugar de `fetchServersOperativos` |

---

## 7. Regla Final Automática para Servidores Nuevos

### A) CATÁLOGO SQL y EXPLORADOR BD

Muestran AUTOMÁTICAMENTE cualquier servidor que cumpla:
- `activo = 1`
- Conexión configurada
- Usuario autorizado

**NO filtran por:**
- `visible_en_operaciones`
- Nombre hardcodeado
- Listas manuales

### B) TABLEROS y KPIs

Muestran solo servidores que cumplan:
- `activo = 1`
- `visible_en_operaciones = 1`
- `unidad_negocio_id` asignada (si el módulo requiere unidad)
- Usuario autorizado RBAC

---

## 8. Evidencia SQL Antes/Después

### ANTES
```
CHAPUR NORTE: visible_en_operaciones=False
CHAPUR NORTE BACKOFICE: visible_en_operaciones=False
```

### DESPUÉS
```
CHAPUR NORTE: visible_en_operaciones=True ✅
CHAPUR NORTE BACKOFICE: visible_en_operaciones=False (sin cambio)
```

---

## 9. Evidencia de Endpoints

### Explorador BD (conexiones-explorables)
```
Total conexiones explorables: 12
SERVIDORES CHAPUR EN EXPLORADOR BD:
  - CHAPUR NORTE: explorable=True ✅
  - CHAPUR NORTE BACKOFICE: explorable=True ✅
```

### Tablero Ejecutivo
```
CHAPUR NO aparece en Tablero Ejecutivo
(correcto - no tiene unidad_negocio_id asignada)
```

---

## 10. Validación No Regresión

| Endpoint | Antes | Después |
|----------|-------|---------|
| Login | ✅ OK | ✅ OK |
| Tablero Ejecutivo | ✅ HTTP 200 | ✅ HTTP 200 |
| /api/users | ✅ HTTP 200 | ✅ HTTP 200 |
| /api/servers | ✅ HTTP 200 | ✅ HTTP 200 |
| /api/api-connections | ✅ HTTP 200 | ✅ HTTP 200 |
| /api/explorador/conexiones-explorables | ✅ HTTP 200 | ✅ HTTP 200 |

---

## 11. Confirmaciones

- ✅ NO hay lógica hardcodeada por nombre "Chapur"
- ✅ NO hay listas manuales de servidores
- ✅ Catálogo SQL NO filtra por `visible_en_operaciones`
- ✅ Explorador BD NO filtra por `visible_en_operaciones`
- ✅ `visible_en_operaciones` se guarda correctamente en EDARSAHUB SQL
- ✅ Servidores futuros se clasifican automáticamente
- ✅ RBAC se respeta
- ✅ No hay regresión en módulos existentes

---

## 12. Backout Plan

Si hay regresión:

1. En `useCatalogoConsultasData.js`:
   - Revertir a `fetchServersOperativos` si causa problemas

2. En `Servidores.js`:
   - Revertir toggle a solo estado local (sin persistencia)

---

**Fin del Reporte**
