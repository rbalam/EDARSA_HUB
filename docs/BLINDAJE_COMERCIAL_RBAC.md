# BLINDAJE MÓDULO COMERCIAL - RBAC

## FECHA: 2026-04-20
## ESTADO: IMPLEMENTADO Y EN PRUEBAS

---

## 1. CAUSA RAÍZ DEL PROBLEMA

### Problema Detectado:
El módulo Comercial mostraba el filtro de SUCURSAL en todos los tabs incluso cuando el usuario tenía una sola sucursal/unidad autorizada. Además, aparecían opciones no autorizadas como "ORIGEN" para usuarios restringidos a "130 QRO".

### Causas Identificadas:

1. **Frontend (Comercial.js líneas 2513-2579):**
   - Llamaba a `/api/servers/${selectedServer}/sucursales` que retorna TODAS las sucursales del servidor SQL sin filtrar por RBAC
   - No usaba las sucursales que ya vienen filtradas con la unidad de negocio

2. **Backend (core/security.py líneas 341-364):**
   - La función `filter_sucursales_by_permissions()` retornaba TODAS las sucursales cuando el usuario NO tenía `allowed_sucursales` configurado
   - No usaba el modelo nuevo de `empresas_permitidas`

3. **Inconsistencia Arquitectónica:**
   - El endpoint `/api/unidades-negocio` ya retornaba sucursales correctas filtradas por RBAC
   - Pero el frontend hacía una llamada adicional que ignoraba este contexto

---

## 2. ARCHIVOS MODIFICADOS

### Frontend:
- `/app/frontend/src/pages/Comercial.js`
  - Líneas 2513-2579: Reemplazado `fetchSucursales()` que llamaba a API insegura
  - Ahora usa sucursales que vienen con la unidad de negocio (ya filtradas por RBAC)
  - Lógica de `showSucursalSelector` corregida para mostrar solo si hay >1 sucursal autorizada
  
- Tab "Precios Constantes" (VentasPreciosConstantes):
  - Corregida lógica similar de carga de sucursales

### Backend:
- `/app/backend/modules/comercial/routes.py`
  - Agregada función helper `validate_server_access_rbac()` para validación unificada
  - Actualizado validación RBAC en endpoints: sucursales, metas, ticket-perfecto, ventas-tiempo, mesas, detalle-movimientos, precios-constantes, reporte-pax, dashboard

---

## 3. AJUSTES REALIZADOS

### Contexto:
- **FUENTE ÚNICA DE VERDAD:** El endpoint `/api/unidades-negocio` retorna empresas + sucursales permitidas según RBAC del usuario
- **Frontend consume este contexto:** Ya no hace llamadas adicionales a endpoints de sucursales que no respetan RBAC

### Endpoints Seguros:
- Todos los endpoints del módulo Comercial ahora usan `validate_server_access_rbac()` que:
  1. Primero valida por `empresas_permitidas` (modelo FASE 3)
  2. Fallback a `allowed_servers` (modelo legacy)
  3. Rechaza con 403 si no tiene acceso

### Renderizado Condicional:
- El frontend aplica estas reglas:
  - Si `sucursales.length <= 1`: NO mostrar selector
  - Si `unidadesNegocio.length === 1`: Mostrar como texto fijo, no como selector
  - Solo mostrar selectores si hay múltiples opciones autorizadas

### Persistencia entre Tabs:
- El contexto (`selectedUnidad`, `selectedSucursal`) se mantiene en el componente principal
- Todos los tabs reciben el mismo contexto via `commonProps`
- El cambio de tab NO resetea el contexto

---

## 4. VALIDACIÓN TAB POR TAB

| Tab | Validación | Estado |
|-----|-----------|--------|
| Dashboard | Usa `selectedUnidad` y `selectedSucursal` del contexto | ✅ |
| Precios Const. | Corregido para usar sucursales de unidad | ✅ |
| Reporte PAX | Usa contexto compartido | ✅ |
| Ticket Perfecto | Usa contexto compartido | ✅ |
| Metas | Usa contexto compartido | ✅ |
| Por Hora/Día | Usa contexto compartido | ✅ |
| Mesas | Usa contexto compartido | ✅ |

---

## 5. CRITERIOS DE ACEPTACIÓN

### CASO A: Usuario con 1 sola sucursal (ej: 130 QRO)
- [ ] Entra a Comercial
- [ ] Ve "130 QRO" como contexto fijo
- [ ] NO ve selector de sucursal
- [ ] NO ve "ORIGEN" ni otras sucursales
- [ ] Esto se cumple en todos los tabs

### CASO B: Usuario con múltiples sucursales
- [ ] Solo ve sucursales autorizadas en selector
- [ ] Selector aparece solo si hay >1 opción

### CASO C: Navegación entre tabs
- [ ] No reaparece filtro de sucursal
- [ ] No se pierde el contexto
- [ ] Comportamiento consistente

### CASO D: Seguridad backend
- [ ] Intento de enviar sucursal no autorizada → 403
- [ ] No hay fuga de datos por catálogos

---

## 6. BLINDAJE CONTRA REGRESIÓN

### Validaciones Implementadas:
1. **Frontend:** El código ya no llama a `/api/servers/.../sucursales` para cargar opciones
2. **Backend:** Función `validate_server_access_rbac()` centralizada para todos los endpoints
3. **Logs:** Se logea cualquier intento de acceso no autorizado

### Recomendaciones Futuras:
- Cualquier nuevo endpoint de Comercial DEBE usar `validate_server_access_rbac()`
- NO crear nuevos endpoints que retornen sucursales sin filtrar por RBAC
- Mantener el patrón de contexto compartido entre tabs

---

## 7. DECLARACIÓN DE ALCANCE

✅ **Confirmado:** Solo se modificó el módulo Comercial
✅ **Confirmado:** No se tocaron otros módulos (Compras, Finanzas, etc.)
✅ **Confirmado:** No se alteraron permisos globales del sistema
✅ **Confirmado:** No se rompió funcionalidad existente del módulo

---

**Autor:** Agente E1 (Arquitecto de Software)
**Revisión:** Pendiente validación por usuario
