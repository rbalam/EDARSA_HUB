# FASE 3 - PROPUESTA DE PILOTO FUNCIONAL
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1 ✅ cerrada | FASE 2 ✅ cerrada

---

## 1. RESUMEN EJECUTIVO

Este documento propone 3 opciones de piloto funcional para la FASE 3 del nuevo sistema de seguridad RBAC, ordenadas de menor a mayor riesgo. El objetivo es activar el **primer permiso real** del nuevo esquema `sec_*` en un caso de uso controlado, validando la coexistencia con el sistema legacy sin afectar módulos productivos.

### Estado actual de colecciones `sec_*`:

| Colección | Documentos | Estado |
|-----------|------------|--------|
| `sec_empresas` | 1 | ✅ Poblada |
| `sec_unidades_negocio` | 7 | ✅ Poblada |
| `sec_sucursales` | 7 | ✅ Poblada |
| `sec_permisos_catalogo` | 89 | ✅ Poblada (catálogo completo) |
| `sec_modulos_sistema` | 10 | ✅ Poblada |
| `sec_mapeo_servidor_sucursal` | 7 | ✅ Poblada |
| `sec_bitacora_acceso` | 11 | ✅ Activa (logs) |

### Roles legacy activos:

| Rol | Usuarios | Permisos |
|-----|----------|----------|
| SuperAdministrador | 1 | 13 módulos |
| Administrador | 2 | 14 módulos |
| Supervisor | 7 | 7 módulos |
| Usuario | 5 | 4 módulos |

---

## 2. DIAGNÓSTICO DEL PUNTO DE ENTRADA

### 2.1 Criterios de selección del piloto

| # | Criterio | Peso |
|---|----------|------|
| 1 | Bajo impacto en operaciones críticas | ALTO |
| 2 | No afecta finanzas, ventas, nóminas | ALTO |
| 3 | Fácil rollback | ALTO |
| 4 | Permite probar flujo completo (permiso → validación → respuesta) | MEDIO |
| 5 | Usa colecciones `sec_*` existentes | MEDIO |
| 6 | Mínimo número de archivos a tocar | MEDIO |
| 7 | No requiere migración de usuarios | ALTO |

### 2.2 Módulos descartados para piloto

| Módulo | Razón de exclusión |
|--------|-------------------|
| **Comercial** | Crítico - dashboards de ventas en uso diario |
| **Compras** | Crítico - detector y autorizaciones activas |
| **Finanzas** | Ya tiene RBAC v2 parcial - riesgo de conflicto |
| **RH/Nóminas** | Alta criticidad - flujos de pago activos |
| **Inventarios** | Crítico - análisis operativos frecuentes |
| **Tablero Ejecutivo** | Visible a dirección - alto impacto de falla |

### 2.3 Módulos candidatos para piloto

| Módulo | Ventaja | Riesgo actual |
|--------|---------|---------------|
| **Sistema → Alertas** | Bajo impacto, CRUD simple | Sin validación backend |
| **Sistema → Catálogo SQL** | Solo lectura, técnico | Sin validación backend |
| **Tab Estructura (nuevo)** | Aislado, ya existe UI | Sin permisos granulares |

---

## 3. OPCIÓN A: PILOTO EN TAB "ESTRUCTURA" (MENOR RIESGO)

### 3.1 Descripción

Agregar validación de permiso real al **tab "Estructura"** que ya fue creado en FASE 2. Actualmente cualquier usuario con rol Administrador/SuperAdministrador puede ver el tab, pero no hay validación de permiso granular en backend.

### 3.2 Alcance exacto

| Elemento | Valor |
|----------|-------|
| **Módulo** | Sistema |
| **Pantalla** | `/usuarios` |
| **Tab** | Estructura |
| **Endpoint** | `GET /api/sistema/estructura-organizacional` |
| **Permiso nuevo** | `SISTEMA_ESTRUCTURA_VER` |
| **Roles afectados** | Solo SuperAdministrador (piloto restrictivo) |

### 3.3 Comportamiento esperado

```
ANTES (actual):
- Cualquier Administrador ve el tab Estructura
- Backend no valida permisos específicos
- Solo valida que el usuario esté autenticado

DESPUÉS (piloto):
- Solo usuarios con permiso SISTEMA_ESTRUCTURA_VER ven el tab
- Backend valida permiso en endpoint
- Se registra en bitácora sec_bitacora_acceso
- Si no tiene permiso: HTTP 403 + tab oculto en frontend
```

### 3.4 Archivos a modificar

| Archivo | Cambio | Líneas aprox. |
|---------|--------|---------------|
| `/app/backend/server.py` | Agregar validación de permiso al endpoint | ~5-10 líneas |
| `/app/frontend/src/pages/Usuarios.js` | Condicionar visibilidad del tab | ~5 líneas |

### 3.5 Colecciones a leer/escribir

| Colección | Operación | Propósito |
|-----------|-----------|-----------|
| `sec_permisos_catalogo` | READ | Verificar si permiso existe |
| `sec_bitacora_acceso` | WRITE | Registrar intento de acceso |
| `users` | READ | Obtener permisos del usuario (campo nuevo opcional) |

### 3.6 Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Tab desaparece para usuarios autorizados | BAJA | BAJO | Validación previa de asignación |
| Error 403 inesperado | BAJA | BAJO | Fallback a legacy si falla nuevo |
| Bitácora llena disco | MUY BAJA | BAJO | TTL de 90 días ya configurado |

### 3.7 Lo que NO se tocará

- ❌ `get_current_user()` en security.py
- ❌ `Layout.js`
- ❌ Router global
- ❌ Otros tabs de Usuarios (Usuarios, Roles, Permisos Catálogos)
- ❌ Ningún módulo productivo
- ❌ Colección `roles` legacy
- ❌ Colección `users` (solo lectura)

### 3.8 Estrategia de compatibilidad legacy

```python
# Pseudocódigo de validación híbrida
async def verificar_acceso_estructura(user):
    # 1. PRIMERO: Verificar legacy (rol permite acceso a /usuarios)
    if user['role'] not in ['SuperAdministrador', 'Administrador']:
        return False  # Legacy niega
    
    # 2. SEGUNDO: Verificar permiso granular nuevo (solo si legacy permite)
    # Si no existe asignación nueva, usar fallback por rol
    tiene_permiso_nuevo = await verificar_permiso_sec(user, 'SISTEMA_ESTRUCTURA_VER')
    
    # 3. FALLBACK: Si es SuperAdmin y no tiene asignación explícita, permitir
    if user['role'] == 'SuperAdministrador' and not tiene_permiso_nuevo:
        return True  # Fallback legacy
    
    return tiene_permiso_nuevo
```

### 3.9 Rollback

```
TIEMPO ESTIMADO: 2 minutos

1. Revertir endpoint a versión sin validación de permiso
2. Revertir frontend a mostrar tab sin condición
3. NO es necesario eliminar colecciones
4. NO es necesario restaurar datos

IMPACTO: CERO en funcionalidades productivas
```

### 3.10 Validaciones de no regresión

| Validación | Criterio |
|------------|----------|
| Login SuperAdmin | Funciona igual |
| Login Admin | Funciona igual |
| Tab Usuarios visible | Sí (legacy) |
| Tab Roles visible | Sí (legacy) |
| Tab Permisos Catálogos visible | Sí (legacy) |
| Tab Estructura visible para SuperAdmin | Sí (piloto) |
| Tab Estructura oculto para Admin (si no tiene permiso) | Sí (piloto) |
| Endpoint estructura responde 200 para autorizado | Sí |
| Endpoint estructura responde 403 para no autorizado | Sí |
| Bitácora registra acceso | Sí |
| Dashboards funcionan | Sin cambios |

### 3.11 Evidencia esperada

1. Screenshot: SuperAdmin ve tab Estructura
2. Screenshot: Admin sin permiso NO ve tab Estructura
3. Curl: Endpoint retorna 200 para autorizado
4. Curl: Endpoint retorna 403 para no autorizado
5. Consulta: Bitácora tiene registros de acceso

---

## 4. OPCIÓN B: PILOTO EN ALERTAS (RIESGO MEDIO)

### 4.1 Descripción

Agregar validación de permisos al módulo **Alertas**, que actualmente no tiene validación backend. Es un módulo de configuración que no afecta operaciones críticas.

### 4.2 Alcance exacto

| Elemento | Valor |
|----------|-------|
| **Módulo** | Sistema |
| **Pantalla** | `/centro-control` (tab Alertas) |
| **Endpoints** | CRUD de alertas |
| **Permisos nuevos** | `SISTEMA_ALERTAS_VER`, `SISTEMA_ALERTAS_CREAR`, `SISTEMA_ALERTAS_EDITAR`, `SISTEMA_ALERTAS_ELIMINAR` |
| **Roles afectados** | Administrador, SuperAdministrador |

### 4.3 Comportamiento esperado

```
ANTES:
- Cualquiera con acceso a Centro de Control puede crear/editar/eliminar alertas
- Sin validación granular

DESPUÉS:
- VER: Requiere SISTEMA_ALERTAS_VER
- CREAR: Requiere SISTEMA_ALERTAS_CREAR
- EDITAR: Requiere SISTEMA_ALERTAS_EDITAR
- ELIMINAR: Requiere SISTEMA_ALERTAS_ELIMINAR
- Bitácora registra todas las acciones
```

### 4.4 Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `/app/backend/server.py` o `routes/alerts.py` | Agregar validaciones |
| `/app/frontend/src/pages/CentroControl.js` | Condicionar botones |

### 4.5 Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Usuario no puede crear alertas necesarias | MEDIA | MEDIO | Asignar permisos antes de activar |
| UI muestra botones pero backend rechaza | BAJA | BAJO | Sincronizar frontend con backend |
| Afecta flujo de notificaciones | BAJA | MEDIO | Alertas existentes no se modifican |

### 4.6 Lo que NO se tocará

- ❌ Alertas ya creadas
- ❌ Sistema de notificaciones
- ❌ Otros tabs de Centro de Control
- ❌ Módulos productivos

### 4.7 Rollback

```
TIEMPO: 5 minutos
- Revertir validaciones en endpoints
- Revertir condiciones en frontend
```

### 4.8 Validaciones de no regresión

- Login funciona
- Alertas existentes visibles
- Notificaciones funcionan
- Centro de Control carga

---

## 5. OPCIÓN C: PILOTO EN CATÁLOGO SQL (RIESGO MEDIO-ALTO)

### 5.1 Descripción

Agregar validación de permisos al módulo **Catálogo SQL**, que permite configurar queries SQL para los servidores. Es técnico pero tiene impacto si se bloquea incorrectamente.

### 5.2 Alcance exacto

| Elemento | Valor |
|----------|-------|
| **Módulo** | Sistema |
| **Pantalla** | `/catalogo-sql` |
| **Endpoints** | Validación/guardado de queries |
| **Permisos nuevos** | `SISTEMA_CATALOGO_SQL_VER`, `SISTEMA_CATALOGO_SQL_EDITAR`, `SISTEMA_CATALOGO_SQL_VALIDAR` |
| **Roles afectados** | Administrador, SuperAdministrador |

### 5.3 Riesgos

| Riesgo | Probabilidad | Impacto |
|--------|--------------|---------|
| Bloquear configuración de servidores | MEDIA | ALTO |
| Afectar integraciones SQL | BAJA | ALTO |
| Romper dashboards que dependen de queries | BAJA | ALTO |

### 5.4 Por qué NO es recomendado como primer piloto

- Alto impacto si falla
- Afecta configuración técnica crítica
- Requiere más validaciones de no regresión

---

## 6. RECOMENDACIÓN

### 6.1 Opción recomendada: **OPCIÓN A - Tab Estructura**

| Criterio | Evaluación |
|----------|------------|
| Mínimo riesgo | ✅ Tab aislado, sin impacto en legacy |
| Fácil rollback | ✅ 2 minutos |
| Prueba flujo completo | ✅ Permiso → Backend → Frontend |
| Usa colecciones existentes | ✅ sec_permisos_catalogo, sec_bitacora_acceso |
| Mínimos archivos | ✅ Solo 2 archivos |
| No requiere migración | ✅ Fallback por rol |
| Permite validar coexistencia | ✅ Legacy + nuevo simultáneo |

### 6.2 Justificación

1. **El tab Estructura ya existe** - No se crea funcionalidad nueva, solo se protege
2. **Es informativo** - Si se bloquea incorrectamente, no afecta operaciones
3. **Prueba el modelo completo** - Permiso en catálogo → validación backend → visibilidad frontend → bitácora
4. **Rollback trivial** - Quitar validación y volver al estado FASE 2
5. **Permite iterar** - Si funciona, expandir a más permisos gradualmente

---

## 7. ALCANCE EXACTO RECOMENDADO

### 7.1 Cambios en Backend

**Archivo:** `/app/backend/server.py` (o crear helper en `/app/backend/core/permissions_v3.py`)

```python
# Nuevo helper de validación FASE 3
async def verificar_permiso_v3(user: dict, codigo_permiso: str) -> bool:
    """
    Verifica si usuario tiene permiso usando nuevo sistema sec_*.
    FASE 3: Coexiste con legacy, no lo reemplaza.
    
    Estrategia:
    1. Si usuario tiene asignación explícita en nuevo sistema, usar esa
    2. Si no, usar fallback basado en rol legacy
    """
    db = get_db()
    
    # Verificar si existe asignación explícita (campo nuevo en users)
    permisos_nuevos = user.get('sec_permisos', [])
    if permisos_nuevos:
        return codigo_permiso in permisos_nuevos
    
    # Fallback: Mapeo rol legacy → permisos
    FALLBACK_ROL_PERMISOS = {
        'SuperAdministrador': ['SISTEMA_ESTRUCTURA_VER'],
        # Otros roles no tienen este permiso por defecto
    }
    
    rol = user.get('role', '')
    permisos_por_rol = FALLBACK_ROL_PERMISOS.get(rol, [])
    
    return codigo_permiso in permisos_por_rol
```

**Cambio en endpoint estructura:**

```python
@api_router.get("/sistema/estructura-organizacional")
async def get_estructura_organizacional(
    current_user: dict = Depends(get_current_user)
):
    # FASE 3: Validación de permiso granular
    tiene_permiso = await verificar_permiso_v3(current_user, 'SISTEMA_ESTRUCTURA_VER')
    
    if not tiene_permiso:
        # Registrar intento denegado
        await registrar_bitacora_v3(
            current_user, 'ACCESO_DENEGADO', 
            '/api/sistema/estructura-organizacional',
            'Sin permiso SISTEMA_ESTRUCTURA_VER'
        )
        raise HTTPException(status_code=403, detail="Permiso requerido: SISTEMA_ESTRUCTURA_VER")
    
    # Registrar acceso permitido
    await registrar_bitacora_v3(
        current_user, 'ACCESO_PERMITIDO',
        '/api/sistema/estructura-organizacional'
    )
    
    # Lógica existente...
    service = get_estructura_service(db)
    return await service.get_estructura_organizacional()
```

### 7.2 Cambios en Frontend

**Archivo:** `/app/frontend/src/pages/Usuarios.js`

```javascript
// Agregar estado para permisos
const [userPermissions, setUserPermissions] = useState([]);

// En useEffect, cargar permisos del usuario actual
useEffect(() => {
    const userData = JSON.parse(localStorage.getItem('user') || '{}');
    // FASE 3: Verificar permisos nuevos o fallback por rol
    const permisos = userData.sec_permisos || [];
    const rol = userData.role || '';
    
    // Fallback: SuperAdmin siempre puede ver estructura
    if (rol === 'SuperAdministrador' && !permisos.includes('SISTEMA_ESTRUCTURA_VER')) {
        permisos.push('SISTEMA_ESTRUCTURA_VER');
    }
    
    setUserPermissions(permisos);
}, []);

// Condicionar visibilidad del tab
const canViewEstructura = userPermissions.includes('SISTEMA_ESTRUCTURA_VER');

// En el render del TabsList:
{canViewEstructura && (
    <TabsTrigger value="estructura" ...>
        <Building2 className="h-4 w-4" />
        Estructura
    </TabsTrigger>
)}
```

### 7.3 Función de bitácora

```python
async def registrar_bitacora_v3(
    user: dict,
    accion: str,
    recurso: str,
    detalles: str = None
):
    """Registra en bitácora FASE 3 de forma desacoplada."""
    try:
        db = get_db()
        await db.sec_bitacora_acceso.insert_one({
            "timestamp": datetime.now(timezone.utc),
            "usuario_id": user.get('id'),
            "usuario_email": user.get('email'),
            "rol": user.get('role'),
            "accion": accion,
            "recurso": recurso,
            "resultado": "OK" if "PERMITIDO" in accion else "DENEGADO",
            "detalles": detalles,
            "fase": "FASE_3",
            "sistema_verificacion": "NUEVO"
        })
    except Exception as e:
        logging.warning(f"Bitácora FASE3 falló (no crítico): {e}")
```

---

## 8. ARCHIVOS Y ENDPOINTS A TOCAR

### 8.1 Archivos a modificar

| Archivo | Tipo de cambio | Líneas estimadas |
|---------|----------------|------------------|
| `/app/backend/server.py` | Agregar validación en endpoint | +15 líneas |
| `/app/frontend/src/pages/Usuarios.js` | Condicionar tab | +10 líneas |

### 8.2 Archivos a crear (opcional)

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/core/permissions_v3.py` | Helper de validación FASE 3 (opcional, puede ir en server.py) |

### 8.3 Endpoints afectados

| Endpoint | Cambio |
|----------|--------|
| `GET /api/sistema/estructura-organizacional` | Agregar validación de permiso |
| `GET /api/sistema/mapeo-servidores` | Agregar validación de permiso (mismo permiso) |

### 8.4 Colecciones afectadas

| Colección | Operación | Propósito |
|-----------|-----------|-----------|
| `sec_permisos_catalogo` | READ | Verificar que permiso existe |
| `sec_bitacora_acceso` | WRITE | Registrar accesos |
| `users` | READ (futuro: UPDATE) | Leer permisos asignados |

---

## 9. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Tab desaparece para SuperAdmin | MUY BAJA | BAJO | Fallback hardcodeado por rol |
| 2 | Error 403 inesperado | BAJA | BAJO | Verificación previa con curl |
| 3 | Frontend y backend desincronizados | BAJA | BAJO | Desplegar juntos |
| 4 | Bitácora falla | BAJA | CERO | try/catch desacoplado |
| 5 | Impacto en rendimiento | MUY BAJA | BAJO | Consulta simple sin joins |

---

## 10. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Router global | ❌ NO SE MODIFICA |
| Menú lateral | ❌ NO SE MODIFICA |
| Otros tabs de /usuarios | ❌ NO SE MODIFICAN |
| Colección `roles` | ❌ NO SE MODIFICA |
| Colección `users` (estructura) | ❌ NO SE MODIFICA |
| Módulo Comercial | ❌ NO SE TOCA |
| Módulo Compras | ❌ NO SE TOCA |
| Módulo Finanzas | ❌ NO SE TOCA |
| Módulo RH | ❌ NO SE TOCA |
| Dashboards | ❌ NO SE TOCAN |
| Filtros existentes | ❌ NO SE TOCAN |
| Integraciones SQL | ❌ NO SE TOCAN |

---

## 11. ESTRATEGIA DE ROLLBACK

### 11.1 Pasos de rollback

```
TIEMPO TOTAL: 2-3 minutos

Paso 1: Revertir endpoint (1 minuto)
- Quitar validación verificar_permiso_v3
- Endpoint vuelve a solo requerir autenticación

Paso 2: Revertir frontend (1 minuto)
- Quitar condición canViewEstructura
- Tab Estructura visible para todos los que tengan acceso a /usuarios

Paso 3: Opcional - limpiar bitácora
- No necesario, pero puede eliminarse con:
  db.sec_bitacora_acceso.deleteMany({fase: "FASE_3"})
```

### 11.2 Criterios de rollback automático

Si cualquiera de estos ocurre, hacer rollback inmediato:

1. ❌ SuperAdmin no puede ver tab Estructura
2. ❌ Endpoint retorna 500
3. ❌ Login deja de funcionar
4. ❌ Otros tabs de /usuarios afectados

---

## 12. CHECKLIST DE NO REGRESIÓN

### 12.1 Pre-cambio

- [ ] Verificar que SuperAdmin puede ver tab Estructura (estado actual)
- [ ] Verificar que endpoint responde 200 (estado actual)
- [ ] Verificar login funciona
- [ ] Verificar otros tabs de /usuarios funcionan

### 12.2 Post-cambio

| Verificación | Resultado esperado |
|--------------|-------------------|
| Login SuperAdmin | ✅ Funciona |
| Login Admin | ✅ Funciona |
| Login Supervisor | ✅ Funciona |
| Login Usuario | ✅ Funciona |
| Tab Usuarios visible | ✅ Sin cambios |
| Tab Roles visible | ✅ Sin cambios |
| Tab Permisos Catálogos visible | ✅ Sin cambios |
| Tab Estructura visible (SuperAdmin) | ✅ Visible |
| Tab Estructura oculto (Admin sin permiso) | ✅ Oculto |
| Endpoint estructura 200 (SuperAdmin) | ✅ OK |
| Endpoint estructura 403 (sin permiso) | ✅ Forbidden |
| Bitácora tiene registro | ✅ Existe |
| Dashboard Comercial | ✅ Sin cambios |
| Dashboard Compras | ✅ Sin cambios |
| Dashboard Finanzas | ✅ Sin cambios |

---

## 13. SOLICITUD DE APROBACIÓN

### 13.1 Resumen de lo que se solicita aprobar

| # | Elemento | Descripción |
|---|----------|-------------|
| 1 | Agregar validación de permiso `SISTEMA_ESTRUCTURA_VER` al endpoint `/api/sistema/estructura-organizacional` | Backend |
| 2 | Agregar validación de permiso al endpoint `/api/sistema/mapeo-servidores` | Backend |
| 3 | Condicionar visibilidad del tab Estructura según permiso | Frontend |
| 4 | Crear función helper `verificar_permiso_v3` (puede ir en server.py) | Backend |
| 5 | Registrar accesos en `sec_bitacora_acceso` | Backend |
| 6 | Fallback: SuperAdmin siempre tiene permiso por defecto | Compatibilidad |

### 13.2 Lo que NO se hará en esta fase

| Elemento | Confirmación |
|----------|--------------|
| Migrar usuarios | ❌ NO |
| Modificar `get_current_user` | ❌ NO |
| Modificar `Layout.js` | ❌ NO |
| Crear nuevas colecciones | ❌ NO |
| Tocar módulos productivos | ❌ NO |
| Activar permisos en otros endpoints | ❌ NO |
| Reemplazar sistema legacy | ❌ NO |

### 13.3 Decisión solicitada

**¿Aprueba la ejecución de FASE 3 OPCIÓN A bajo las condiciones descritas?**

- [ ] SÍ, proceder con OPCIÓN A (Tab Estructura)
- [ ] NO, requiere ajustes (especificar)
- [ ] PREFERIR OPCIÓN B (Alertas)
- [ ] DIFERIR esta fase

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 3**

*Esperando aprobación explícita antes de implementar.*
