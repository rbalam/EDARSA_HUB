# REPORTE FASE A - Backend Refresh Tokens
## P1-REFRESH-TOKENS: Implementación Backend

**Proyecto:** EDARSA HUB  
**Fase:** A - Backend Refresh Tokens  
**Fecha de inicio:** 2025-04-27  
**Estado:** EN PROGRESO - Bloqueado por ejecución SQL pendiente

---

## 1. RESUMEN EJECUTIVO

La Fase A implementa la infraestructura backend para el sistema de refresh tokens con rotación y detección de replay. El código está completo y verificado, pero las **pruebas de integración están bloqueadas** hasta que se ejecute manualmente el script SQL en EDARSAHUB.

### Estado por Componente

| Componente | Estado | Notas |
|------------|--------|-------|
| Script SQL | LISTO | Pendiente ejecución manual |
| `core/refresh_tokens.py` | COMPLETADO | 868 líneas |
| `core/security.py` | MODIFICADO | Nueva función `create_access_token` |
| `modules/auth/routes.py` | MODIFICADO | Endpoints refresh/logout-all |
| `modules/auth/service.py` | MODIFICADO | Nueva función `get_user_by_id` |
| Backend startup | VERIFICADO | FastAPI inicia sin errores |
| Pruebas integración | BLOQUEADAS | Requiere tablas SQL |

---

## 2. ARCHIVOS CREADOS/MODIFICADOS

### 2.1 Nuevo: `/app/docs/sql/CREATE_SESIONES_REFRESH_TOKENS.sql` (283 líneas)

Script SQL para creación manual de infraestructura:

**Tablas:**
- `Sesiones` - Sesiones activas con refresh token hasheado
- `SesionesHistorico` - Auditoría inmutable de acciones

**Índices (8 total):**
- `IX_Sesiones_TokenHash_Activo` - Búsqueda por hash (único, filtrado)
- `IX_Sesiones_Usuario` - Listar sesiones por usuario
- `IX_Sesiones_Familia` - Detección de replay
- `IX_Sesiones_Expiracion` - Limpieza de expirados
- `IX_SesionesHist_Usuario` - Historial por usuario
- `IX_SesionesHist_Sesion` - Historial por sesión
- `IX_SesionesHist_Seguridad` - Alertas de seguridad

**Procedimiento:**
- `sp_LimpiarSesionesExpiradas` - Job de limpieza (opcional)

### 2.2 Nuevo: `/app/backend/core/refresh_tokens.py` (868 líneas)

Módulo central de gestión de refresh tokens:

**Funciones de generación:**
- `generate_refresh_token()` - Token opaco criptográfico
- `hash_refresh_token()` - SHA256 para almacenamiento
- `verify_refresh_token_hash()` - Comparación segura

**Funciones de cookies:**
- `set_refresh_cookie()` - httpOnly, secure, strict
- `clear_refresh_cookie()` - Limpieza
- `get_refresh_token_from_request()` - Extracción

**Operaciones de sesión:**
- `create_session()` - Nueva sesión en SQL
- `validate_and_get_session()` - Validar token
- `rotate_refresh_token()` - Rotación segura
- `detect_and_handle_replay()` - Detectar robo de tokens
- `revoke_session()` - Revocar una sesión
- `revoke_session_family()` - Revocar familia completa
- `revoke_all_user_sessions()` - Logout-all
- `get_user_active_sessions()` - Listar sesiones

### 2.3 Modificado: `/app/backend/core/security.py`

**Nuevas constantes:**
```python
ACCESS_TOKEN_MINUTES = 15  # Configurable vía .env
```

**Nueva función:**
```python
def create_access_token(user_id, email, role, token_type="internal") -> str:
    """Crea access token de corta duración (15 min)"""
```

### 2.4 Modificado: `/app/backend/modules/auth/routes.py`

**Nuevos endpoints:**
- `POST /api/auth/refresh` - Renovar tokens
- `POST /api/auth/logout-all` - Cerrar todas las sesiones

**Endpoints modificados:**
- `POST /api/auth/login` - Ahora crea sesión SQL + emite refresh token
- `POST /api/auth/logout` - Ahora revoca sesión en SQL

### 2.5 Modificado: `/app/backend/modules/auth/service.py`

**Nueva función:**
```python
async def get_user_by_id(user_id) -> Dict[str, Any]:
    """Obtiene usuario por ID para refresh token"""
```

---

## 3. VERIFICACIONES REALIZADAS

### 3.1 Backend inicia correctamente

```
INFO:     Started server process [39934]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3.2 No hay auto-creación de tablas

```bash
$ grep -rn "CREATE TABLE\|create_all\|Base.metadata" /app/backend/core/refresh_tokens.py
No se encontró creación automática de tablas
```

El código **NO** intenta crear tablas automáticamente. Solo ejecuta INSERTs/UPDATEs/SELECTs contra tablas existentes.

### 3.3 Imports válidos

Todos los módulos importan correctamente sin errores de sintaxis o dependencias faltantes.

### 3.4 Login legacy funciona

```
INFO: POST /api/auth/login HTTP/1.1" 200 OK
```

El login actual sigue funcionando. Si falla la creación de sesión SQL (porque las tablas no existen), el sistema continúa con el flujo legacy:

```python
except Exception as e:
    logging.warning(f"No se pudo crear sesión en EDARSAHUB (continuando con login legacy): {e}")
    session_info = None
```

---

## 4. PRUEBAS BLOQUEADAS

Las siguientes pruebas no se pueden ejecutar hasta que existan las tablas en EDARSAHUB:

### 4.1 Crear sesión SQL

```bash
# Prueba pendiente
curl -c cookies.txt -X POST \
  https://erp-crm-enterprise-1.preview.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@inventario.com","password":"xxx"}'

# Verificar en SQL:
# SELECT * FROM Sesiones WHERE UsuarioID = [id]
```

### 4.2 Refresh token

```bash
# Prueba pendiente
curl -b cookies.txt -X POST \
  https://erp-crm-enterprise-1.preview.emergentagent.com/api/auth/refresh
```

**Comportamiento esperado con tablas:**
- 200 OK
- Nuevas cookies seteadas
- Sesión anterior revocada
- Nueva sesión creada con misma FamiliaTokenID

**Comportamiento actual sin tablas:**
- 401 "No refresh token" o 500 error interno

### 4.3 Logout-all

```bash
# Prueba pendiente
curl -b cookies.txt -X POST \
  https://erp-crm-enterprise-1.preview.emergentagent.com/api/auth/logout-all
```

### 4.4 Detección de replay

```bash
# Prueba pendiente (requiere simular ataque)
# 1. Login → guardar refresh token
# 2. Refresh → token rotado
# 3. Usar token antiguo → debe detectar replay y revocar familia
```

---

## 5. ARQUITECTURA IMPLEMENTADA

### 5.1 Flujo de Login

```
Cliente                  Backend                     SQL Server
   |                        |                            |
   |-- POST /login -------->|                            |
   |                        |-- Validar credenciales --->|
   |                        |                            |
   |                        |-- Generar access token     |
   |                        |-- Generar refresh token    |
   |                        |-- hash(refresh_token) ---->|
   |                        |                            | INSERT Sesiones
   |                        |<-- session_id -------------|
   |<-- 200 + cookies ------|                            |
```

### 5.2 Flujo de Refresh

```
Cliente                  Backend                     SQL Server
   |                        |                            |
   |-- POST /refresh ------>|                            |
   |   (cookie refresh)     |                            |
   |                        |-- Verificar replay ------->|
   |                        |   (buscar token revocado)  |
   |                        |                            |
   |                        |-- Validar sesión --------->|
   |                        |   (buscar token activo)    |
   |                        |                            |
   |                        |-- Rotar token ------------>|
   |                        |   UPDATE sesión anterior   |
   |                        |   INSERT nueva sesión      |
   |                        |<---------------------------|
   |<-- 200 + nuevas cookies|                            |
```

### 5.3 Flujo de Detección de Replay

```
Atacante                 Backend                     SQL Server
   |                        |                            |
   |-- POST /refresh ------>|                            |
   |   (token robado)       |                            |
   |                        |-- Buscar token ----------->|
   |                        |   en sesiones inactivas    |
   |                        |                            |
   |                        |<-- Encontrado (rotated) ---|
   |                        |                            |
   |                        |-- REVOCAR FAMILIA -------->|
   |                        |   UPDATE todas con         |
   |                        |   mismo FamiliaTokenID     |
   |                        |<---------------------------|
   |<-- 401 REPLAY ----------|                            |
```

---

## 6. CONFIGURACIÓN DE SEGURIDAD

### 6.1 Cookies

| Cookie | Atributo | Valor |
|--------|----------|-------|
| Access Token | httpOnly | true |
| Access Token | secure | true (producción) |
| Access Token | samesite | lax |
| Access Token | path | / |
| Access Token | max_age | 15 min |
| Refresh Token | httpOnly | true |
| Refresh Token | secure | true (producción) |
| Refresh Token | samesite | strict |
| Refresh Token | path | /api/auth |
| Refresh Token | max_age | 7 días |

### 6.2 Tokens

| Token | Tipo | Duración | Almacenamiento |
|-------|------|----------|----------------|
| Access | JWT | 15 min | Cookie cliente |
| Refresh | Opaco | 7 días | Hash en SQL |

### 6.3 Protecciones

- **CSRF:** SameSite=strict en refresh cookie
- **XSS:** httpOnly en todas las cookies
- **Timing attacks:** `secrets.compare_digest` para hash
- **Token theft:** Rotación + detección de replay
- **Session hijacking:** IP y User-Agent registrados

---

## 7. PRÓXIMOS PASOS

### Inmediatos (Usuario)

1. Ejecutar `/app/docs/sql/CREATE_SESIONES_REFRESH_TOKENS.sql` en SSMS
2. Verificar con las queries de validación
3. Confirmar al agente

### Tras ejecución SQL (Agente)

1. Ejecutar pruebas de integración con curl
2. Verificar inserción en tablas SQL
3. Probar flujo de refresh completo
4. Documentar resultados finales
5. Marcar Fase A como COMPLETADA

### Fase B (Pendiente aprobación)

- Interceptor Axios para refresh silencioso
- NO iniciar hasta aprobar Fase A

---

## 8. CRITERIOS DE ACEPTACIÓN

| Criterio | Estado |
|----------|--------|
| Script SQL listo para ejecución manual | CUMPLIDO |
| Backend no crea tablas automáticamente | CUMPLIDO |
| Login sigue funcionando sin tablas | CUMPLIDO |
| Endpoints refresh implementados | CUMPLIDO |
| Hash de tokens (nunca plano) | CUMPLIDO |
| Rotación de tokens | CUMPLIDO (pendiente prueba) |
| Detección de replay | CUMPLIDO (pendiente prueba) |
| Frontend NO modificado | CUMPLIDO |

---

## 9. DICTAMEN

**La Fase A no se puede cerrar completamente hasta que:**

1. El script SQL sea ejecutado manualmente en EDARSAHUB
2. Se verifique la creación correcta de tablas e índices
3. Se ejecuten las pruebas de integración (login, refresh, logout-all)
4. Se documente el resultado de las pruebas

**Estado actual: IMPLEMENTACIÓN COMPLETA - PRUEBAS BLOQUEADAS**

---

**Documento generado por Agente E1 - EDARSA HUB**  
**Última actualización:** 2025-04-27
