# INCIDENTE P0-CACHE-PREVIEW - DIAGNÓSTICO

**Fecha:** 2026-05-26  
**Severidad:** P0 (Crítico)  
**Estado:** RESUELTO

---

## 1. DESCRIPCIÓN DEL PROBLEMA

Los endpoints principales de EDARSAHUB funcionan correctamente:
- `/api/servers`: 9 servidores desde SQL
- `/api/unidades-negocio`: 5 unidades desde SQL
- `/api/v2/comercial/dashboard`: 5 unidades con datos de ventas

Sin embargo, en el frontend los filtros de Unidad de Negocio, Servidores, Comercial, Finanzas, Operaciones y Catálogo de Consultas podían quedar "rotos" por:
- Estado temporal corrupto
- Caché previa en localStorage/sessionStorage
- Memoria de React (query cache, stores)
- Service worker cache
- Cooldowns de conexiones fallidas

---

## 2. EVIDENCIA

### 2.1 Endpoints Funcionando (Backend)
```
GET /api/servers              → 9 servidores
GET /api/unidades-negocio     → 5 unidades
GET /api/v2/comercial/dashboard → 5 unidades con datos
Sistema_Empresas              → 5 empresas activas
Servidores_Conexiones         → 13 servidores activos
```

### 2.2 Problema Frontend (Reportado)
- Filtros mostraban "0 servidores" o "Selecciona unidad"
- Dashboards no cargaban datos
- Estado inconsistente entre recargas

---

## 3. CAUSA RAÍZ

El frontend y backend pueden mantener estados en caché que no se actualizan al:
1. Reiniciar el backend
2. Cambiar datos en SQL
3. Fallar conexiones temporalmente (cooldown)
4. Cambiar de ambiente (producción → preview)

### Cachés Identificados

**Frontend:**
| Tipo | Ubicación | Riesgo |
|------|-----------|--------|
| localStorage | selectedServer, selectedUnidadNegocio, filtros | ALTO |
| sessionStorage | user, token, dashboard_cache | MEDIO |
| React Query | servers, unidades, dashboard | ALTO |
| Browser Cache API | Service worker, assets | MEDIO |

**Backend:**
| Tipo | Ubicación | Riesgo |
|------|-----------|--------|
| _server_status_cache | core/db.py | ALTO |
| LRU caches | Funciones decoradas | BAJO |
| Pool connections | Connection pools | MEDIO |

---

## 4. RIESGO

| Escenario | Impacto | Probabilidad |
|-----------|---------|--------------|
| Usuario ve datos obsoletos | ALTO | ALTA |
| Filtros rotos post-reinicio | CRÍTICO | MEDIA |
| Estados inconsistentes | ALTO | ALTA |
| Loop infinito de login | CRÍTICO | BAJA |

---

## 5. PLAN DE CORRECCIÓN

### 5.1 Detección de Modo Preview
Implementar función `isPreviewMode()` que detecta ambiente:
- URL contiene `preview.emergentagent.com`
- URL contiene `staging`
- `localhost` / `127.0.0.1`
- Variable `REACT_APP_PREVIEW_MODE=true`

### 5.2 Limpieza Automática Frontend
Al iniciar app en modo preview:
1. Limpiar localStorage (llaves EDARSA)
2. Limpiar sessionStorage (excepto marcador)
3. Limpiar Browser Caches
4. Invalidar React Query cache

### 5.3 Limpieza Automática Backend
Endpoint administrativo:
```
POST /api/admin/cache/clear-preview
```
Limpia:
- server_status_cache
- context_resolver_cache
- db_pool_cooldowns
- lru_caches registrados

### 5.4 Protecciones
- Marcador de sesión para evitar loop de limpieza
- Solo ejecuta en modo preview
- No afecta producción
- No borra datos SQL
- No expone secretos

---

**Firmado:** E1 Agent  
**Estado:** DIAGNÓSTICO COMPLETADO
