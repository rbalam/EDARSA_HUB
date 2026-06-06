# AUTH STORAGE SECURITY AUDIT
## EDARSA HUB - Auditoría de Almacenamiento de Autenticación

**Fecha:** 2025-12-XX  
**Auditor:** Arquitecto Senior FullStack  
**Archivo Principal:** `/app/frontend/src/services/authStorage.js`

---

## 1. RESUMEN EJECUTIVO

El servicio `authStorage.js` centraliza el acceso a credenciales y sesión en EDARSA HUB. La implementación actual utiliza **sessionStorage como almacenamiento primario** (más seguro que localStorage), con fallback a localStorage para compatibilidad con código legacy.

### Estado de Seguridad: ✅ ACEPTABLE (con reservas documentadas)

---

## 2. DATOS ALMACENADOS

| Dato | Storage | Sensibilidad | Riesgo XSS | Estado |
|------|---------|--------------|------------|--------|
| `token` (JWT) | sessionStorage | ALTA | Medio | ⚠️ Documentado |
| `user` (datos usuario) | sessionStorage | MEDIA | Bajo | ⚠️ Documentado |
| `refresh_token` | sessionStorage | ALTA | Medio | ⚠️ Documentado |
| Preferencias UI | localStorage | BAJA | Nulo | ✅ OK |

### Detalle de qué se guarda:

1. **Token JWT (líneas 27-42, 48-54)**
   - Almacenado en: sessionStorage (primario) + localStorage (legacy)
   - Riesgo: Vulnerable a XSS, pero sessionStorage limita exposición a tab actual
   - Mitigación actual: sessionStorage, CSP headers recomendados

2. **Datos de Usuario (líneas 60-91)**
   - Almacenado en: sessionStorage (primario) + localStorage (legacy)
   - Contenido: email, rol, permisos, empresa_id, sucursal_id
   - Riesgo: Bajo (no son secretos, solo identificadores)

3. **Preferencias (líneas 135-151)**
   - Almacenado en: localStorage
   - Contenido: Configuración de UI, filtros guardados
   - Riesgo: Nulo (datos no sensibles)

---

## 3. ANÁLISIS DE ARCHIVOS ADICIONALES

### `src/pages/Compras.js` (líneas 3290, 3359)
```javascript
// Uso: Guardar parámetros de filtro de compras
localStorage.setItem(STORAGE_KEY, JSON.stringify({...}))
```
**Clasificación:** NO SENSIBLE (parámetros de UI)
**Acción:** ✅ No requiere cambio

### `src/pages/AutorizacionCompras.js` (líneas 40, 47)
```javascript
// Uso: Guardar parámetros de filtro
localStorage.setItem(STORAGE_KEY, JSON.stringify({...}))
localStorage.getItem(STORAGE_KEY)
```
**Clasificación:** NO SENSIBLE (parámetros de UI)
**Acción:** ✅ No requiere cambio

### `src/portal/App.jsx`
**Estado:** No encontrado uso de localStorage para datos sensibles
**Acción:** ✅ No requiere cambio

---

## 4. RIESGOS IDENTIFICADOS

### Riesgo 1: Token JWT en Storage del Navegador
- **Severidad:** MEDIA
- **Descripción:** El token JWT está expuesto a ataques XSS
- **Mitigación actual:** 
  - sessionStorage limita acceso a tab actual
  - El token tiene expiración corta
  - CSP headers deben implementarse en backend
- **Mitigación futura recomendada:**
  - Migrar a httpOnly cookies (requiere cambios en backend)
  - Implementar refresh token rotation

### Riesgo 2: Compatibilidad Legacy con localStorage
- **Severidad:** BAJA
- **Descripción:** Se mantiene copia en localStorage para compatibilidad
- **Mitigación actual:** Migración gradual a sessionStorage
- **Acción futura:** Eliminar fallback a localStorage cuando toda la app use authStorage

---

## 5. CAMBIOS APLICADOS EN ESTA FASE

**NINGUNO** - El archivo ya está correctamente implementado:
- ✅ sessionStorage como almacenamiento primario
- ✅ Centralización de acceso a credenciales
- ✅ Funciones de limpieza de sesión
- ✅ Separación de preferencias (no sensibles) en localStorage
- ✅ Headers de autorización centralizados

---

## 6. RECOMENDACIONES FUTURAS (NO PARA ESTA FASE)

### Prioridad ALTA (Requiere Backend):
1. **Migrar a httpOnly cookies**
   - Backend debe setear cookie en response de login
   - Backend debe leer cookie en cada request
   - Eliminar almacenamiento de token en frontend
   - Implementar endpoint de refresh

### Prioridad MEDIA:
2. **Content Security Policy (CSP)**
   - Agregar headers CSP en backend/nginx
   - Prevenir ejecución de scripts externos

3. **Eliminar fallback a localStorage**
   - Una vez migrada toda la app, remover líneas 33-38, 53, 67-71, 90

### Prioridad BAJA:
4. **Cifrado de datos de usuario**
   - No prioritario ya que no son secretos
   - Solo considerar si se agregan datos más sensibles

---

## 7. VERIFICACIÓN DE ACCESOS DISPERSOS

### Búsqueda de `localStorage.getItem('token')` directo:
```
Resultado: 0 instancias fuera de authStorage.js
```

### Búsqueda de `sessionStorage` directo:
```
Resultado: Solo en authStorage.js (centralizado)
```

---

## 8. CONCLUSIÓN

El almacenamiento de autenticación en EDARSA HUB:

1. **ESTÁ CORRECTAMENTE CENTRALIZADO** en `authStorage.js`
2. **USA sessionStorage** como almacenamiento primario (mejor práctica sin httpOnly cookies)
3. **SEPARA CORRECTAMENTE** datos sensibles de preferencias
4. **NO REQUIERE CAMBIOS URGENTES** para esta fase de estabilización
5. **TIENE RUTA DE MIGRACIÓN** documentada para httpOnly cookies

### Estado Final: ✅ ACEPTABLE

---

## 9. PENDIENTES PARA FASES FUTURAS

| Ítem | Prioridad | Requiere Backend | Estimación |
|------|-----------|------------------|------------|
| httpOnly cookies | ALTA | SÍ | 2-3 días |
| CSP headers | MEDIA | SÍ | 1 día |
| Eliminar localStorage fallback | BAJA | NO | 1 hora |
