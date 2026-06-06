# PROPUESTA FORMAL: Recuperar Contraseña (TEMPORAL - SOLO PREVIEW)

**ID:** PROP-001  
**Fecha:** 04-Mayo-2026  
**Estado:** PENDIENTE APROBACIÓN  
**Autor:** Agente E1  
**Clasificación:** SOLUCIÓN OPERATIVA TEMPORAL

---

## ⚠️ DECLARACIÓN ARQUITECTÓNICA OBLIGATORIA

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                     ACLARACIÓN DE ALCANCE Y TEMPORALIDAD                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Esta propuesta es una SOLUCIÓN OPERATIVA TEMPORAL para el ambiente          ║
║  PREVIEW únicamente.                                                         ║
║                                                                              ║
║  NO REDEFINE la arquitectura oficial del sistema.                            ║
║  NO CONVIERTE a MongoDB en la fuente maestra definitiva de identidad.        ║
║  NO APLICA automáticamente a producción.                                     ║
║  NO CONSTITUYE una decisión final sobre la fuente de usuarios/password.      ║
║                                                                              ║
║  El "cerebro" oficial del sistema sigue siendo la BD EDARSAHUB.              ║
║                                                                              ║
║  Esta implementación se considera un MECANISMO PROVISIONAL mientras se       ║
║  define y ejecuta la consolidación final de identidad en EDARSAHUB.          ║
║                                                                              ║
║  Cualquier extensión a producción o cambio arquitectónico requiere           ║
║  APROBACIÓN SEPARADA Y EXPLÍCITA.                                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. OBJETIVO

Implementar funcionalidad **TEMPORAL** de "Recuperar Contraseña" para usuarios internos del sistema EDARSA HUB **EXCLUSIVAMENTE en el ambiente PREVIEW**, permitiendo a los usuarios con password desconocido restablecer su acceso de forma segura y autónoma.

**Naturaleza:** Solución operativa provisional para desbloquear usuarios en PREVIEW mientras se consolida la arquitectura definitiva de identidad en EDARSAHUB.

---

## 2. MÁXIMAS OBLIGATORIAS DEL PROYECTO

| # | Máxima | Cómo se cumple |
|---|--------|----------------|
| 1 | EDARSA HUB es el cerebro | Los tokens de reset se almacenarán en MongoDB (fuente de usuarios). Futuro: migrar a EDARSAHUB SQL |
| 2 | Backend manda | Toda la lógica de generación, validación y cambio de password está en backend |
| 3 | No romper nada de lo existente | Login actual intacto. Solo se AGREGAN endpoints nuevos |
| 4 | Cambios transversales requieren análisis previo | Esta propuesta ES el análisis previo |
| 5 | Primero diagnosticar, luego ejecutar | Diagnóstico completado (8 usuarios sin acceso) |
| 6 | Implementación por fases | Fase 1: Solo PREVIEW. Fase 2: Producción (requiere aprobación separada) |
| 7 | Mantener compatibilidad temporal con legacy | Se mantiene login existente sin cambios |
| 8 | Mínimo impacto posible | 2 endpoints nuevos, 2 páginas nuevas, 0 modificaciones a código existente crítico |
| 9 | Toda ejecución debe dejar evidencia | Auditoría en MongoDB + logs de backend |
| 10 | Si aparece riesgo transversal, detenerse | Definido checklist de rollback |

---

## 3. ALCANCE EXACTO

### 3.1 RESTRICCIONES DE ALCANCE (OBLIGATORIAS)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LÍMITES EXPLÍCITOS                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ✅ INCLUIDO                          │  ❌ EXCLUIDO                    │
├───────────────────────────────────────┼─────────────────────────────────┤
│  Ambiente PREVIEW únicamente          │  Producción                     │
│  Usuarios internos (MongoDB users)    │  Portal proveedores             │
│  Solución temporal/provisional        │  Arquitectura definitiva        │
│  Desbloqueo operativo                 │  Redefinición de fuente maestra │
└───────────────────────────────────────┴─────────────────────────────────┘
```

### 3.2 Incluido (Temporal)

| Elemento | Detalle | Naturaleza |
|----------|---------|------------|
| Ambiente | **SOLO PREVIEW** (`stock-tracker-990.preview.emergentagent.com`) | OBLIGATORIO |
| Usuarios | **SOLO usuarios internos** (colección `users` de MongoDB) | TEMPORAL |
| Flujo | Solicitud de reset → Email con token → Nueva contraseña | PROVISIONAL |
| Email | Via SMTP existente (`mail.edarsa.com.mx`) | EXISTENTE |

### 3.3 Excluido explícitamente

| Elemento | Razón | Requiere para cambiar |
|----------|-------|----------------------|
| **Producción** | Fuera de alcance temporal | Aprobación separada |
| **Decisión arquitectónica** | No es objetivo de esta propuesta | Propuesta arquitectónica separada |
| **Fuente maestra definitiva** | EDARSAHUB sigue siendo el cerebro | Migración de identidad a EDARSAHUB |
| Usuarios del portal proveedores | Flujo diferente ya existente | N/A |
| OAuth/Google Auth | Fuera de alcance | N/A |
| SMS/WhatsApp | Solo email | N/A |
| Cambio de password estando logueado | Ya existe (fuera de alcance) | N/A |

### 3.4 Condiciones de expiración de esta solución temporal

Esta implementación temporal deberá ser **revisada o reemplazada** cuando:

1. Se implemente la consolidación de identidad en EDARSAHUB
2. Se decida arquitectónicamente la fuente maestra definitiva de usuarios
3. Se prepare el despliegue a producción (requiere nueva propuesta)
4. Pase más de 6 meses sin definición arquitectónica (requiere revisión)

---


## 4. FUENTE DE DATOS DE PASSWORD (CONTEXTO TEMPORAL)

### 4.1 Declaracion arquitectonica

**ARQUITECTURA OFICIAL DEL SISTEMA:**

| Elemento | Definicion |
|----------|------------|
| **Fuente maestra oficial** | BD EDARSAHUB (SQL Server) |
| **Esta propuesta cambia eso?** | **NO** |

Esta propuesta NO redefine la arquitectura oficial.

### 4.2 Situacion actual de usuarios (estado transitorio)

| Componente | Ubicacion actual | Estado |
|------------|------------------|--------|
| Usuarios internos | MongoDB `edarsa_hub.users` | **LEGACY/TRANSITORIO** |
| Sesiones/Refresh tokens | EDARSAHUB SQL `Sesiones` | IMPLEMENTADO |
| Password hash | MongoDB `users.password` | **LEGACY/TRANSITORIO** |

**Nota:** La ubicacion actual de usuarios en MongoDB es un estado **transitorio heredado**. La consolidacion de identidad en EDARSAHUB es una tarea pendiente separada de esta propuesta.

### 4.3 Alcance de esta propuesta (temporal)

Esta propuesta opera sobre el estado actual transitorio (MongoDB users) SIN REDEFINIR la arquitectura oficial.

**Estado actual (Transitorio/Legacy):**
- MongoDB localhost:27017
- Database: edarsa_hub
- Collection: users
- Campo password: Hash bcrypt
- **UBICACION LEGACY/TRANSITORIA - NO ES FUENTE MAESTRA OFICIAL**
- **PENDIENTE MIGRACION A EDARSAHUB**

**Cerebro oficial del sistema:**
- EDARSAHUB SQL Server
- Tabla Sesiones: ya implementado
- Tabla Usuarios: PENDIENTE (futura migracion)
- **FUENTE MAESTRA OFICIAL DEL SISTEMA**

### 4.4 Operacion de actualizacion (temporal)

```python
# El password se actualiza en MongoDB (ubicacion TRANSITORIA actual)
# Esta operacion es TEMPORAL mientras los usuarios vivan en MongoDB
db.users.update_one(
    {"email": email},
    {"$set": {"password": hash_bcrypt_nuevo}}
)

# NOTA: Cuando se migre identidad a EDARSAHUB, esta logica debera actualizarse
```

### 4.5 Compromisos explicitos

| Compromiso | Descripcion |
|------------|-------------|
| **No redefine arquitectura** | Esta propuesta NO convierte a MongoDB en fuente maestra oficial |
| **Transitorio** | Opera sobre el estado actual heredado mientras exista |
| **Sin precedente** | No establece precedente para produccion |
| **Requiere migracion** | Cuando se migre identidad a EDARSAHUB, esta funcionalidad debera adaptarse |


## 5. DISEÑO DEL TOKEN

### 5.1 Generación

| Atributo | Valor |
|----------|-------|
| Algoritmo | `secrets.token_urlsafe(32)` — 256 bits de entropía |
| Formato | String URL-safe de 43 caracteres |
| Ejemplo | `Ks7Yx3QnP9vB2mL5wR8tA1zC6fH4jD0eG-xNkMpWqYr` |

### 5.2 Almacenamiento

| Atributo | Valor |
|----------|-------|
| Colección MongoDB | `password_reset_tokens` |
| Se almacena | **HASH del token** (SHA-256), no el token en texto plano |
| Razón | Si la DB se compromete, los tokens no son usables |

### 5.3 Estructura del documento

```javascript
{
    "_id": ObjectId("..."),
    "token_hash": "sha256_del_token",           // Hash SHA-256
    "user_id": "uuid_del_usuario",              // Referencia a users.id
    "email": "carlosruz@edarsa.com.mx",         // Para auditoría
    "created_at": ISODate("2026-05-04T..."),    // Timestamp UTC
    "expires_at": ISODate("2026-05-04T..."),    // created_at + 1 hora
    "used": false,                               // Marca de uso único
    "used_at": null,                            // Timestamp si se usó
    "ip_request": "192.168.1.1",                // IP de solicitud
    "ip_reset": null,                           // IP de uso (si se usó)
    "user_agent_request": "Mozilla/5.0...",     // UA de solicitud
    "invalidated": false,                       // Si fue invalidado manualmente
    "invalidated_reason": null                  // Razón de invalidación
}
```

### 5.4 TTL (Time To Live)

| Parámetro | Valor |
|-----------|-------|
| Duración | **1 hora** (3600 segundos) |
| Índice TTL MongoDB | `expires_at` con `expireAfterSeconds: 0` |
| Limpieza automática | MongoDB elimina documentos expirados |

### 5.5 Comportamiento de tokens

| Escenario | Comportamiento |
|-----------|----------------|
| Token usado una vez | `used: true`, no puede usarse de nuevo |
| Token expirado | MongoDB lo elimina automáticamente |
| Usuario solicita dos veces | Token anterior se **invalida**, solo el último es válido |
| Usuario cambia password por otra vía | Todos los tokens pendientes se **invalidan** |
| Token inválido/inexistente | Error genérico: "Token inválido o expirado" |

### 5.6 Invalidación

```python
# Al solicitar nuevo token, invalidar anteriores
db.password_reset_tokens.update_many(
    {"user_id": user_id, "used": False, "invalidated": False},
    {"$set": {"invalidated": True, "invalidated_reason": "new_request"}}
)

# Al cambiar password por otra vía
db.password_reset_tokens.update_many(
    {"user_id": user_id, "used": False, "invalidated": False},
    {"$set": {"invalidated": True, "invalidated_reason": "password_changed_directly"}}
)
```

---

## 6. SEGURIDAD

### 6.1 No revelar existencia de email

```python
# SIEMPRE responder con mensaje genérico
return {"message": "Si el email existe, recibirás instrucciones de recuperación"}

# Internamente:
# - Si email existe: enviar email
# - Si email no existe: NO enviar email, pero dar misma respuesta
```

### 6.2 Rate limiting / Throttling

| Control | Valor |
|---------|-------|
| Por IP | Máximo 5 solicitudes por hora |
| Por email | Máximo 3 solicitudes por hora |
| Implementación | Colección `rate_limit_password_reset` con TTL |

```javascript
// Estructura rate limit
{
    "key": "ip:192.168.1.1" | "email:user@example.com",
    "count": 3,
    "window_start": ISODate("..."),
    "expires_at": ISODate("...") // +1 hora
}
```

### 6.3 Auditoría

| Evento | Campos registrados |
|--------|-------------------|
| Solicitud de reset | email, ip, user_agent, timestamp, success |
| Uso de token | token_id, ip, user_agent, timestamp, success |
| Token inválido | token_hash_parcial, ip, user_agent, timestamp |
| Rate limit alcanzado | key, ip, timestamp |

Colección: `audit_password_reset`

### 6.4 Hashing del password nuevo

```python
# Usar función existente de core/security.py
from core.security import hash_password

new_hash = hash_password(new_password)  # bcrypt con salt automático
```

### 6.5 Política de complejidad mínima

| Requisito | Valor |
|-----------|-------|
| Longitud mínima | 8 caracteres |
| Longitud máxima | 128 caracteres |
| Requiere mayúscula | SÍ (al menos 1) |
| Requiere minúscula | SÍ (al menos 1) |
| Requiere número | SÍ (al menos 1) |
| Requiere especial | NO (recomendado pero no obligatorio) |

```python
import re

def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if len(password) > 128:
        return False, "La contraseña no puede exceder 128 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe incluir al menos una mayúscula"
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe incluir al menos una minúscula"
    if not re.search(r'[0-9]', password):
        return False, "La contraseña debe incluir al menos un número"
    return True, "OK"
```

### 6.6 Invalidación de sesiones previas

| Opción | Implementación |
|--------|----------------|
| **Opción A (Recomendada)** | Al cambiar password, invalidar TODAS las sesiones en EDARSAHUB.Sesiones |
| Opción B | No invalidar sesiones (menos seguro) |

```sql
-- Invalidar sesiones al cambiar password
UPDATE Sesiones 
SET EstaActiva = 0, FechaModificacion = GETUTCDATE()
WHERE UsuarioID = @user_id AND EstaActiva = 1
```

---

## 7. EMAIL

### 7.1 Configuración

| Parámetro | Valor |
|-----------|-------|
| Host SMTP | `mail.edarsa.com.mx` |
| Puerto | `587` |
| TLS | Sí |
| Remitente | `notificaciones@edarsa.com.mx` |
| Nombre remitente | `EDARSA HUB` |

### 7.2 Asunto del email

```
Recuperación de contraseña - EDARSA HUB
```

### 7.3 Plantilla del email (HTML)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Recuperación de contraseña</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #1a365d; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">EDARSA HUB</h1>
    </div>
    
    <div style="padding: 30px; background: #f7fafc; border: 1px solid #e2e8f0;">
        <h2 style="color: #2d3748;">Recuperación de contraseña</h2>
        
        <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.</p>
        
        <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{RESET_URL}}" 
               style="background: #3182ce; color: white; padding: 15px 30px; 
                      text-decoration: none; border-radius: 5px; font-weight: bold;">
                Restablecer contraseña
            </a>
        </div>
        
        <p style="color: #718096; font-size: 14px;">
            Este enlace expirará en <strong>1 hora</strong>.
        </p>
        
        <p style="color: #718096; font-size: 14px;">
            Si no solicitaste este cambio, puedes ignorar este correo. 
            Tu contraseña actual seguirá siendo válida.
        </p>
        
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
        
        <p style="color: #a0aec0; font-size: 12px;">
            Si el botón no funciona, copia y pega esta URL en tu navegador:<br>
            <span style="word-break: break-all;">{{RESET_URL}}</span>
        </p>
    </div>
    
    <div style="padding: 20px; text-align: center; color: #a0aec0; font-size: 12px;">
        <p>Este es un correo automático de EDARSA HUB. Por favor no respondas.</p>
        <p>© 2026 EDARSA. Todos los derechos reservados.</p>
    </div>
</body>
</html>
```

### 7.4 URL de reset

```
https://stock-tracker-990.preview.emergentagent.com/reset-password?token={{TOKEN}}
```

**Nota:** El token va en la URL (query param), NO en el path.

### 7.5 Comportamiento si falla SMTP

| Escenario | Comportamiento |
|-----------|----------------|
| SMTP no disponible | Loguear error, responder mensaje genérico al usuario |
| Timeout | Reintentar 1 vez, si falla loguear y responder genérico |
| Email rechazado | Loguear, responder mensaje genérico |

**Importante:** NUNCA revelar al usuario que el envío falló (podría confirmar existencia de email).

---

## 8. ENDPOINTS EXACTOS

### 8.1 POST /api/auth/forgot-password

**Propósito:** Solicitar recuperación de contraseña

**Request:**
```json
{
    "email": "carlosruz@edarsa.com.mx"
}
```

**Response (siempre 200):**
```json
{
    "message": "Si el email está registrado, recibirás instrucciones de recuperación"
}
```

**Lógica interna:**
1. Validar formato de email
2. Verificar rate limit (IP y email)
3. Buscar usuario en MongoDB
4. Si existe:
   - Invalidar tokens anteriores
   - Generar nuevo token
   - Almacenar hash del token
   - Enviar email
5. Si no existe: no hacer nada
6. Registrar en auditoría
7. Retornar mensaje genérico

### 8.2 POST /api/auth/reset-password

**Propósito:** Cambiar contraseña con token válido

**Request:**
```json
{
    "token": "Ks7Yx3QnP9vB2mL5wR8tA1zC6fH4jD0eG-xNkMpWqYr",
    "new_password": "NuevaPassword123"
}
```

**Response (éxito):**
```json
{
    "message": "Contraseña actualizada correctamente"
}
```

**Response (error):**
```json
{
    "detail": "Token inválido o expirado"
}
```

**Lógica interna:**
1. Calcular hash SHA-256 del token
2. Buscar en `password_reset_tokens` donde:
   - `token_hash` coincide
   - `used: false`
   - `invalidated: false`
   - `expires_at > now`
3. Si no encuentra: error 400 "Token inválido o expirado"
4. Validar complejidad del nuevo password
5. Hashear nuevo password con bcrypt
6. Actualizar en MongoDB `users.password`
7. Marcar token como usado
8. Invalidar sesiones en EDARSAHUB (opcional)
9. Registrar en auditoría
10. Retornar éxito

---

## 9. COLECCIONES/TABLAS EXACTAS

### 9.1 MongoDB: password_reset_tokens

```javascript
// Crear colección con índices
db.createCollection("password_reset_tokens")

// Índice TTL para expiración automática
db.password_reset_tokens.createIndex(
    { "expires_at": 1 },
    { expireAfterSeconds: 0 }
)

// Índice para búsqueda por hash
db.password_reset_tokens.createIndex(
    { "token_hash": 1 },
    { unique: true }
)

// Índice para búsqueda por usuario
db.password_reset_tokens.createIndex(
    { "user_id": 1, "used": 1, "invalidated": 1 }
)
```

### 9.2 MongoDB: rate_limit_password_reset

```javascript
db.createCollection("rate_limit_password_reset")

// Índice TTL para limpieza automática
db.rate_limit_password_reset.createIndex(
    { "expires_at": 1 },
    { expireAfterSeconds: 0 }
)

// Índice para búsqueda por key
db.rate_limit_password_reset.createIndex(
    { "key": 1 },
    { unique: true }
)
```

### 9.3 MongoDB: audit_password_reset

```javascript
db.createCollection("audit_password_reset")

// Índice por fecha para consultas
db.audit_password_reset.createIndex(
    { "timestamp": -1 }
)

// Índice por email
db.audit_password_reset.createIndex(
    { "email": 1, "timestamp": -1 }
)
```

---

## 10. ARCHIVOS A TOCAR

### 10.1 Backend (modificar)

| Archivo | Cambio | Riesgo |
|---------|--------|--------|
| `/app/backend/modules/auth/routes.py` | Agregar 2 endpoints al final | BAJO |
| `/app/backend/modules/auth/service.py` | Agregar funciones de reset | BAJO |

### 10.2 Backend (crear)

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/modules/auth/password_reset.py` | Lógica de tokens y validación |

### 10.3 Frontend (crear)

| Archivo | Propósito |
|---------|-----------|
| `/app/frontend/src/pages/ForgotPassword.js` | Página "Olvidé mi contraseña" |
| `/app/frontend/src/pages/ResetPassword.js` | Página "Nueva contraseña" |

### 10.4 Frontend (modificar)

| Archivo | Cambio | Riesgo |
|---------|--------|--------|
| `/app/frontend/src/pages/Login.js` | Agregar enlace "¿Olvidaste tu contraseña?" | MÍNIMO |
| `/app/frontend/src/App.js` | Agregar 2 rutas públicas | BAJO |

---

## 11. QUÉ NO SE TOCARÁ

| Elemento | Razón |
|----------|-------|
| Login actual (`/api/auth/login`) | Solo se agrega funcionalidad |
| MongoDB `users` estructura | Solo se actualiza campo `password` |
| EDARSAHUB.Sesiones estructura | Solo se ejecuta UPDATE para invalidar |
| Comercial V1/V2 | Fuera de alcance |
| Módulos blindados | Fuera de alcance |
| Finanzas, CxP, Tesorería | Fuera de alcance |
| RBAC | Fuera de alcance |
| Layout global | Solo se agregan páginas aisladas |
| Rutas protegidas | Solo se agregan rutas públicas |

---

## 12. RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| SMTP falla y no envía email | BAJA | MEDIO | Reintentos + logs + mensaje genérico |
| Token interceptado | MUY BAJA | ALTO | Token de un solo uso + TTL corto + HTTPS |
| Abuso de endpoint (spam) | MEDIA | BAJO | Rate limiting estricto |
| Fuga de información (email existe) | BAJA | MEDIO | Mensaje genérico siempre |
| Regresión en login | MUY BAJA | ALTO | Tests automatizados + checklist |
| Token almacenado sin hash | NINGUNA | - | Diseño especifica hash SHA-256 |

---

## 13. ROLLBACK

### 13.1 Si falla en backend

```bash
# Revertir cambios en routes.py y service.py
git checkout HEAD -- /app/backend/modules/auth/routes.py
git checkout HEAD -- /app/backend/modules/auth/service.py

# Eliminar archivo nuevo
rm /app/backend/modules/auth/password_reset.py

# Reiniciar
sudo supervisorctl restart backend
```

### 13.2 Si falla en frontend

```bash
# Revertir cambios
git checkout HEAD -- /app/frontend/src/pages/Login.js
git checkout HEAD -- /app/frontend/src/App.js

# Eliminar archivos nuevos
rm /app/frontend/src/pages/ForgotPassword.js
rm /app/frontend/src/pages/ResetPassword.js

# Reiniciar
sudo supervisorctl restart frontend
```

### 13.3 Limpiar MongoDB

```javascript
// Solo si es necesario
db.password_reset_tokens.drop()
db.rate_limit_password_reset.drop()
db.audit_password_reset.drop()
```

---

## 14. CHECKLIST DE NO REGRESIÓN

### 14.1 Login actual

| Test | Esperado | Verificar |
|------|----------|-----------|
| Login `admin@inventario.com` / `admin123` | ✅ Éxito, token válido | [ ] |
| Login email inexistente | ❌ "Credenciales inválidas" | [ ] |
| Login password incorrecto | ❌ "Credenciales inválidas" | [ ] |
| Login usuario inactivo | ❌ "Usuario inactivo" | [ ] |

### 14.2 Recuperación de contraseña

| Test | Esperado | Verificar |
|------|----------|-----------|
| Solicitar con email existente | ✅ Mensaje genérico, email enviado | [ ] |
| Solicitar con email inexistente | ✅ Mensaje genérico, NO email | [ ] |
| Solicitar 6 veces mismo email (rate limit) | ❌ "Demasiadas solicitudes" | [ ] |
| Usar token válido | ✅ Password cambiado | [ ] |
| Usar token expirado | ❌ "Token inválido o expirado" | [ ] |
| Usar token ya usado | ❌ "Token inválido o expirado" | [ ] |
| Usar token después de solicitar nuevo | ❌ "Token inválido o expirado" | [ ] |
| Password muy corto (< 8) | ❌ Error de validación | [ ] |
| Password sin mayúscula | ❌ Error de validación | [ ] |
| Password sin número | ❌ Error de validación | [ ] |

### 14.3 SMTP

| Test | Esperado | Verificar |
|------|----------|-----------|
| Email se envía correctamente | ✅ Email recibido | [ ] |
| SMTP caído (simular) | ✅ Error logueado, respuesta genérica | [ ] |

### 14.4 Usuarios existentes

| Test | Esperado | Verificar |
|------|----------|-----------|
| `admin@inventario.com` sigue funcionando | ✅ | [ ] |
| Usuarios con password conocido siguen OK | ✅ | [ ] |
| Usuario recupera password exitosamente | ✅ Puede hacer login | [ ] |

### 14.5 Frontend

| Test | Esperado | Verificar |
|------|----------|-----------|
| Enlace visible en login | ✅ | [ ] |
| Formulario forgot-password funciona | ✅ | [ ] |
| Formulario reset-password funciona | ✅ | [ ] |
| Token inválido muestra error | ✅ | [ ] |
| Token expirado muestra error | ✅ | [ ] |
| Password actualizado muestra éxito | ✅ | [ ] |

---

## 15. APROBACIÓN REQUERIDA

### 15.1 Decisiones pendientes

| Decisión | Opciones | Recomendación |
|----------|----------|---------------|
| ¿Invalidar sesiones al cambiar password? | A) Sí B) No | A) Sí |
| ¿TTL de token? | A) 1 hora B) 30 min C) 2 horas | A) 1 hora |
| ¿Rate limit por email? | A) 3/hora B) 5/hora C) Sin límite | A) 3/hora |

### 15.2 Autorización solicitada

```
[ ] Apruebo la implementacion de "Recuperar Contrasena" TEMPORAL para PREVIEW segun esta propuesta
[ ] Confirmo que esta implementacion NO redefine la arquitectura oficial (EDARSAHUB es el cerebro)
[ ] Confirmo que esta implementacion NO aplica a produccion sin aprobacion separada
[ ] Confirmo que esta es una solucion PROVISIONAL mientras se consolida identidad en EDARSAHUB
[ ] Apruebo invalidar sesiones al cambiar password (Opcion A)
[ ] Apruebo TTL de 1 hora para tokens (Opcion A)
[ ] Apruebo rate limit de 3 solicitudes por hora por email (Opcion A)

Autorizado por: ________________
Fecha: ________________
```

---

## 16. CRONOGRAMA PROPUESTO

| Fase | Descripcion | Estimacion |
|------|-------------|------------|
| 1 | Crear colecciones MongoDB con indices | 10 min |
| 2 | Implementar `password_reset.py` (logica de tokens) | 30 min |
| 3 | Agregar endpoints en `routes.py` | 20 min |
| 4 | Implementar paginas frontend | 40 min |
| 5 | Testing manual completo | 30 min |
| 6 | Documentacion | 15 min |

**Total estimado:** ~2.5 horas

---

## 17. REFERENCIAS

| Documento | Ubicacion |
|-----------|-----------|
| Arquitectura auth actual | `/app/backend/core/security.py` |
| Servicio de email | `/app/backend/core/communications/providers/email_smtp_provider.py` |
| Sesiones EDARSAHUB | `/app/backend/core/refresh_tokens.py` |

---

## 18. RESUMEN DE ACLARACIONES ARQUITECTONICAS

| Punto | Aclaracion |
|-------|------------|
| Fuente maestra oficial | BD EDARSAHUB (no cambia) |
| Esta propuesta redefine arquitectura? | **NO** |
| Alcance | **SOLO PREVIEW** |
| Naturaleza | **TEMPORAL/PROVISIONAL** |
| Aplica a produccion? | **NO** sin aprobacion separada |
| MongoDB es fuente definitiva? | **NO** - es ubicacion transitoria/legacy |
| Cuando expira esta solucion? | Al migrar identidad a EDARSAHUB o por decision explicita |

---

*Propuesta elaborada el 04-Mayo-2026*  
*Version 2: Con aclaraciones arquitectonicas*  
*Pendiente aprobacion antes de implementacion*
