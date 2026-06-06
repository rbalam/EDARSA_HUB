# FASE 12 - PROPUESTA: PANEL DE BITÁCORA RBAC DE SOLO LECTURA
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1-11 ✅

---

## 1. RESUMEN EJECUTIVO

Esta propuesta define la implementación de un **panel de auditoría visual RBAC** para consultar la colección `sec_bitacora_admin` existente.

### Características:
- **Solo lectura** - No hay edición, borrado ni modificación
- **Acceso restringido** - Solo SuperAdministrador
- **Reutiliza datos existentes** - Consume `sec_bitacora_admin` ya poblada
- **UI mínima** - Nueva pestaña en `/usuarios`

### Fuera de alcance:
- Dashboard ejecutivo
- Métricas/KPIs agregados
- Gráficos
- Edición de eventos
- Perfiles
- Expansión de whitelist
- Cambios transversales

---

## 2. DIAGNÓSTICO DEL PUNTO DE ENTRADA UI

### 2.1 Colección sec_bitacora_admin (Existente)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | string | UUID del evento |
| `timestamp` | datetime | Fecha y hora del evento |
| `tipo` | string | ASIGNAR_PERMISO, ASIGNAR_ROL_MULTIPLE |
| `administrador` | object | {id, email, role} |
| `usuario_afectado` | object | {id, email} |
| `permiso` | string | Código del permiso (si aplica) |
| `rol` | string | Código del rol (si aplica) |
| `accion` | string | ASIGNAR, RETIRAR |
| `resultado` | string | OK, RECHAZADO, SIN_CAMBIO |
| `mensaje` | string | Descripción del evento |
| `fase` | string | FASE_4, FASE_5, FASE_6 |
| `estado_anterior` | array | Permisos/roles antes |
| `estado_nuevo` | array | Permisos/roles después |

**Total actual:** 45 registros

### 2.2 Endpoints Existentes

**NO EXISTE** endpoint para consultar `sec_bitacora_admin`. Las funciones actuales solo insertan:

```python
# server.py líneas 13851-13867
async def registrar_auditoria_admin_fase4(...)
async def registrar_auditoria_rol_fase6(...)
```

### 2.3 Página Usuarios.js (Punto de entrada propuesto)

Tabs actuales:
1. `usuarios` - Lista y gestión de usuarios
2. `roles` - Gestión de roles
3. `permisos-catalogos` - Permisos de catálogos RH
4. `estructura` - Estructura RBAC (solo SuperAdmin)

**Propuesta:** Agregar tab `bitacora` después de `estructura`, visible solo para SuperAdmin.

---

## 3. OPCIONES DE IMPLEMENTACIÓN

### 3.1 OPCIÓN A: SOLO FRONTEND (Menor riesgo)

**Descripción:** Crear un endpoint mínimo en backend y pestaña nueva en frontend.

| Elemento | Cambio |
|----------|--------|
| Backend | 1 endpoint GET nuevo |
| Frontend | 1 tab nuevo + componente |
| Archivos tocados | 2 |
| Riesgo | MÍNIMO |
| Rollback | 3 minutos |

**Endpoint propuesto:**
```
GET /api/admin/bitacora
Query params: 
  - fecha_inicio (opcional)
  - fecha_fin (opcional)
  - email (opcional)
  - resultado (opcional)
  - limite (default 100)
```

**UI propuesta:**
- Tabla simple con filtros básicos
- Columnas: Fecha, Tipo, Administrador, Usuario, Acción, Resultado
- Click en fila → Modal con detalle completo
- Sin paginación compleja (límite fijo)

### 3.2 OPCIÓN B: FRONTEND + PAGINACIÓN (Riesgo bajo)

**Descripción:** Como Opción A, pero con paginación server-side.

| Elemento | Cambio |
|----------|--------|
| Backend | 1 endpoint GET con skip/limit |
| Frontend | 1 tab + componente + paginación |
| Archivos tocados | 2 |
| Riesgo | BAJO |
| Rollback | 4 minutos |

**Endpoint propuesto:**
```
GET /api/admin/bitacora
Query params: 
  - fecha_inicio, fecha_fin, email, resultado (filtros)
  - skip (default 0)
  - limit (default 50)
Response: { total, pagina, eventos }
```

**UI propuesta:**
- Como Opción A + controles de paginación
- Botones "Anterior" / "Siguiente"

### 3.3 OPCIÓN C: COMPONENTE DEDICADO (Riesgo bajo-medio)

**Descripción:** Crear archivo de componente separado para mejor mantenibilidad.

| Elemento | Cambio |
|----------|--------|
| Backend | 1 endpoint GET con paginación |
| Frontend | 1 archivo componente nuevo + import en Usuarios.js |
| Archivos tocados | 3 |
| Riesgo | BAJO-MEDIO |
| Rollback | 5 minutos |

**Estructura propuesta:**
```
frontend/src/components/admin/BitacoraRBAC.jsx  (NUEVO)
frontend/src/pages/Usuarios.js                  (import + tab)
backend/server.py                               (endpoint)
```

**Ventajas:**
- Componente aislado y reutilizable
- Más fácil de testear
- Menor impacto en Usuarios.js

---

## 4. RECOMENDACIÓN

### Opción recomendada: **OPCIÓN C - COMPONENTE DEDICADO**

| Criterio | Evaluación |
|----------|------------|
| Mínimo impacto en Usuarios.js | ✅ Solo import + tab |
| Mantenibilidad | ✅ Componente aislado |
| Testabilidad | ✅ Fácil de probar independiente |
| Riesgo controlado | ✅ Rollback simple |
| Cumple alcance | ✅ Solo lectura, solo SuperAdmin |

### Justificación

1. **Aislamiento**: El componente `BitacoraRBAC.jsx` encapsula toda la lógica
2. **Mínimo cambio en Usuarios.js**: Solo agregar import y un TabTrigger/TabsContent
3. **Escalabilidad controlada**: Si en futuro se requiere más funcionalidad, está aislado
4. **Rollback simple**: Eliminar archivo + revertir 2 líneas en Usuarios.js

---

## 5. ALCANCE EXACTO

### 5.1 Funcionalidad

| # | Funcionalidad | Estado |
|---|---------------|--------|
| 1 | Consultar sec_bitacora_admin | ✅ |
| 2 | Filtrar por fecha | ✅ |
| 3 | Filtrar por usuario afectado | ✅ |
| 4 | Filtrar por resultado | ✅ |
| 5 | Ver detalle de evento | ✅ |
| 6 | Paginación | ✅ |
| 7 | Acceso solo SuperAdmin | ✅ |

### 5.2 Restricciones

| # | Restricción | Confirmación |
|---|-------------|--------------|
| 1 | No edición | ❌ NO |
| 2 | No borrado | ❌ NO |
| 3 | No métricas | ❌ NO |
| 4 | No gráficos | ❌ NO |
| 5 | No KPIs | ❌ NO |
| 6 | No dashboards | ❌ NO |

---

## 6. ARCHIVOS A TOCAR

| Archivo | Cambio | Líneas estimadas |
|---------|--------|------------------|
| `/app/backend/server.py` | Agregar endpoint GET | +40 |
| `/app/frontend/src/components/admin/BitacoraRBAC.jsx` | NUEVO componente | +200 |
| `/app/frontend/src/pages/Usuarios.js` | Import + tab | +15 |

**Total:** 3 archivos, ~255 líneas nuevas

---

## 7. ENDPOINTS

### 7.1 Endpoint Nuevo (Único)

```
GET /api/admin/bitacora

Headers:
  Authorization: Bearer <token>

Query Params:
  fecha_inicio: string (YYYY-MM-DD, opcional)
  fecha_fin: string (YYYY-MM-DD, opcional)
  email: string (email usuario afectado, opcional)
  resultado: string (OK|RECHAZADO|SIN_CAMBIO, opcional)
  tipo: string (ASIGNAR_PERMISO|ASIGNAR_ROL_MULTIPLE, opcional)
  skip: int (default 0)
  limit: int (default 50, max 100)

Response 200:
{
  "total": 45,
  "pagina": 1,
  "paginas_total": 1,
  "eventos": [
    {
      "id": "uuid",
      "timestamp": "2026-04-21T08:49:29",
      "tipo": "ASIGNAR_PERMISO",
      "administrador_email": "ricardo@edarsa.com.mx",
      "usuario_email": "test@edarsa.com",
      "permiso_o_rol": "SISTEMA_USUARIOS_VER",
      "accion": "ASIGNAR",
      "resultado": "OK",
      "mensaje": "...",
      "fase": "FASE_4"
    }
  ]
}

Response 403:
{"detail": "Solo SuperAdministrador puede acceder a la bitácora"}
```

### 7.2 Endpoint Detalle (Opcional)

```
GET /api/admin/bitacora/{evento_id}

Response 200:
{
  // Documento completo incluyendo estado_anterior, estado_nuevo, etc.
}
```

**Nota:** Este endpoint puede omitirse si el detalle se muestra en modal con datos ya cargados.

---

## 8. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Carga lenta con muchos registros | BAJA | BAJO | Paginación + límite 100 |
| 2 | Exposición de datos sensibles | BAJA | MEDIO | Solo SuperAdmin + sin passwords |
| 3 | Regresión en Usuarios.js | BAJA | MEDIO | Cambio mínimo (import + tab) |
| 4 | Conflicto con tabs existentes | MUY BAJA | BAJO | Tab nuevo al final |

---

## 9. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `POST /auth/register` | ❌ NO SE MODIFICA |
| `POST /auth/login` | ❌ NO SE MODIFICA |
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Router global | ❌ NO SE MODIFICA |
| Middleware global | ❌ NO SE MODIFICA |
| Auth global | ❌ NO SE MODIFICA |
| Tabs existentes de Usuarios.js | ❌ NO SE MODIFICAN |
| Endpoints FASE 1-11 | ❌ NO SE MODIFICAN |
| Dashboards | ❌ NO SE MODIFICAN |
| Módulos operativos | ❌ NO SE MODIFICAN |

---

## 10. COMPATIBILIDAD LEGACY

| Elemento | Compatibilidad |
|----------|---------------|
| `sec_bitacora_admin` | ✅ Se consume sin modificar |
| Funciones `registrar_auditoria_*` | ✅ Sin cambios |
| Modelo de usuarios | ✅ Sin cambios |
| Modelo RBAC | ✅ Sin cambios |
| Whitelists | ✅ Sin cambios |

---

## 11. ROLLBACK

### Procedimiento

```bash
# 1. Eliminar componente nuevo
rm /app/frontend/src/components/admin/BitacoraRBAC.jsx

# 2. Revertir import y tab en Usuarios.js (2 líneas)
# - Eliminar import BitacoraRBAC
# - Eliminar TabsTrigger y TabsContent de bitacora

# 3. Eliminar endpoint en server.py (~40 líneas)
# - Eliminar función get_bitacora_admin
# - Eliminar route /admin/bitacora
```

### Tiempo Estimado

**5 minutos**

---

## 12. CHECKLIST DE NO REGRESIÓN

| # | Verificación | Resultado esperado |
|---|--------------|-------------------|
| 1 | Login funciona | ✅ |
| 2 | Tab usuarios funciona | ✅ |
| 3 | Tab roles funciona | ✅ |
| 4 | Tab permisos-catalogos funciona | ✅ |
| 5 | Tab estructura funciona | ✅ |
| 6 | CRUD usuarios FASE 9-11 | ✅ |
| 7 | CRUD roles FASE 9-11 | ✅ |
| 8 | Dashboards Comercial | ✅ |
| 9 | Layout.js no modificado | ✅ |
| 10 | get_current_user() no modificado | ✅ |
| 11 | Nueva pestaña bitácora visible solo para SuperAdmin | ✅ |
| 12 | Filtros funcionan | ✅ |
| 13 | Detalle de evento muestra información completa | ✅ |
| 14 | Usuario no-SuperAdmin no ve pestaña bitácora | ✅ |

---

## 13. SOLICITUD DE APROBACIÓN

### 13.1 Resumen de la propuesta

| # | Elemento |
|---|----------|
| 1 | Crear componente `BitacoraRBAC.jsx` |
| 2 | Agregar endpoint `GET /api/admin/bitacora` |
| 3 | Agregar tab "Bitácora" en `/usuarios` (solo SuperAdmin) |
| 4 | Implementar filtros básicos (fecha, email, resultado) |
| 5 | Implementar paginación |
| 6 | Implementar modal de detalle |

### 13.2 Archivos a modificar

1. `/app/backend/server.py` - Endpoint nuevo
2. `/app/frontend/src/components/admin/BitacoraRBAC.jsx` - Componente NUEVO
3. `/app/frontend/src/pages/Usuarios.js` - Import + tab

### 13.3 Decisión solicitada

**¿Aprueba FASE 12 con OPCIÓN C (Componente Dedicado)?**

- [ ] SÍ, proceder con OPCIÓN C
- [ ] NO, requiere ajustes
- [ ] PREFERIR OPCIÓN A (solo frontend sin componente separado)
- [ ] PREFERIR OPCIÓN B (con paginación pero sin componente separado)
- [ ] DIFERIR

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 12**
