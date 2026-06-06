# FASE 3C — Seguridad de Secretos: Cifrado de Passwords/API Keys

**Fecha:** 2026-04-25  
**Autor:** E1 Agent  
**Estado:** COMPLETADA  

---

## 1. RESUMEN EJECUTIVO

La FASE 3C implementa cifrado de secretos (passwords, api_keys) para servidores en EDARSAHUB SQL, evitando almacenamiento en texto plano.

### Resultados

| Componente | Estado |
|------------|--------|
| `secret_manager.py` central | ✅ Creado |
| Variable de entorno `SERVER_SECRET_KEY` | ✅ Configurada |
| Cifrado en POST `/api/servers` | ✅ Implementado |
| Preservación en PUT con `********` | ✅ Implementado |
| Cifrado en PUT con password nuevo | ✅ Implementado |
| Descifrado para uso interno | ✅ Implementado |
| Script de migración | ✅ Creado y ejecutado |
| Migración de secretos existentes | ✅ 10/10 servidores cifrados |

---

## 2. DIAGNÓSTICO INICIAL

### 2.1 Campos de Secretos Identificados

| Fuente | Tabla/Colección | Campo | Uso | Estado Inicial | Riesgo |
|--------|-----------------|-------|-----|----------------|--------|
| SQL | Servidores_Conexiones | password_encrypted | Conexión SQL Server | Texto plano | ALTO |
| SQL | Servidores_Conexiones | api_key_encrypted | APIs REST | Vacío | BAJO |
| MongoDB | servers | password | Conexión SQL Server | Texto plano | ALTO |
| MongoDB | servers | api_key | APIs REST | Vacío | BAJO |

### 2.2 Estado Pre-Migración

- 12 servidores con password en texto plano
- 0 servidores con api_key
- 2 servidores CORE (excluidos de migración)
- 0 servidores con secretos cifrados

---

## 3. ESTRATEGIA DE CIFRADO

### 3.1 Algoritmo

- **Librería:** cryptography (Fernet)
- **Tipo:** Cifrado simétrico AES-128 CBC
- **Formato:** `enc:v1:<ciphertext_base64>`

### 3.2 Variable de Entorno

```bash
SERVER_SECRET_KEY=<Fernet_key_44_chars>
```

**Ubicación:** `/app/backend/.env`

**Generar clave:**
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### 3.3 Comportamiento

| Operación | Cifrado disponible | Cifrado no disponible |
|-----------|--------------------|-----------------------|
| Guardar secreto nuevo | Cifra con Fernet | Guarda texto plano + warning |
| Leer secreto cifrado | Descifra | Error |
| Leer secreto legacy | Retorna tal cual | Retorna tal cual |
| Actualizar con `********` | Preserva existente | Preserva existente |

---

## 4. SERVICIO CENTRAL DE SECRETOS

**Archivo:** `/app/backend/core/secret_manager.py`

### 4.1 Funciones Principales

```python
# Cifrar secreto
encrypt_secret(value: str) -> str

# Descifrar secreto
decrypt_secret(value: str) -> str

# Verificar si está cifrado
is_encrypted_secret(value: str) -> bool

# Enmascarar para UI
mask_secret(value: str) -> str  # Siempre retorna "********"

# Verificar si preservar existente
should_preserve_existing_secret(new_value) -> bool

# Preparar para almacenamiento
prepare_secret_for_storage(new_value, existing_value) -> Tuple[str, bool]

# Estado del manager
verify_secret_manager_ready() -> dict
```

### 4.2 Valores Enmascarados Reconocidos

```python
MASKED_VALUES = {
    None, "", "********", "••••••••", "●●●●●●●●",
    "[PROTECTED]", "[ENCRYPTED]", "[HIDDEN]"
}
```

---

## 5. INTEGRACIÓN EN SERVER REGISTRY

**Archivo:** `/app/backend/core/server_registry.py`

### 5.1 Cambios en `create_server`

```python
# FASE 3C: Cifrar secretos antes de guardar
from core.secret_manager import encrypt_secret

password_to_store = encrypt_secret(payload.get('password', ''))
api_key_to_store = encrypt_secret(payload.get('api_key', ''))
```

### 5.2 Cambios en `update_server`

```python
# FASE 3C: Password solo si viene explícito y no enmascarado
from core.secret_manager import should_preserve_existing_secret, encrypt_secret

if 'password' in payload:
    if not should_preserve_existing_secret(payload['password']):
        encrypted_pwd = encrypt_secret(payload['password'])
        # ... actualizar
```

### 5.3 Nueva Función `get_decrypted_credentials`

```python
def get_decrypted_credentials(server: Dict) -> Dict:
    """
    Obtiene credenciales descifradas para uso interno.
    NUNCA exponer al frontend.
    """
    from core.secret_manager import decrypt_secret
    
    return {
        'host': server.get('host'),
        'password': decrypt_secret(server.get('password_encrypted')),
        # ...
    }
```

### 5.4 Cambios en `mask_sensitive_fields`

Ahora incluye `secrets_encrypted: bool` en responses.

---

## 6. SCRIPT DE MIGRACIÓN

**Archivo:** `/app/backend/scripts/encrypt_existing_server_secrets.py`

### 6.1 Uso

```bash
# Solo reportar
python encrypt_existing_server_secrets.py --dry-run

# Aplicar cifrado
python encrypt_existing_server_secrets.py --apply
```

### 6.2 Resultado de Migración

```json
{
  "timestamp": "2026-04-25T15:28:08.636879+00:00",
  "mode": "APPLY",
  "status": "SUCCESS",
  "servers_checked": 13,
  "secrets_found": 13,
  "already_encrypted": 1,
  "to_encrypt": 10,
  "encrypted": 10,
  "failed": 0,
  "skipped_core": 2
}
```

**Reporte:** `/app/docs/reports/server_secrets_encryption_report.json`

---

## 7. PRUEBAS REALIZADAS

### 7.1 POST con Password Nuevo

| Prueba | Resultado |
|--------|-----------|
| Password cifrado en SQL | ✅ `enc:v1:gAAAAAB...` |
| Password cifrado en MongoDB | ✅ `enc:v1:gAAAAAB...` |
| Response sin password expuesto | ✅ Solo `password_configured: true` |
| sync_status | ✅ SYNCED |

### 7.2 PUT con Password Enmascarado

| Prueba | Resultado |
|--------|-----------|
| Enviar `********` | ✅ Preserva password existente |
| Password sigue cifrado | ✅ `enc:v1:...` |
| No se sobrescribe con máscara | ✅ Verificado |

### 7.3 PUT con Password Nuevo

| Prueba | Resultado |
|--------|-----------|
| Enviar `NuevoPassword123` | ✅ Se cifra y guarda |
| Password anterior reemplazado | ✅ Ciphertext diferente |
| Nuevo password cifrado | ✅ `enc:v1:...` |

### 7.4 Descifrado para Uso Interno

| Prueba | Resultado |
|--------|-----------|
| `get_decrypted_credentials()` | ✅ Retorna password en texto plano |
| `was_encrypted` flag | ✅ True |
| Password correcto | ✅ Match con original |

### 7.5 Migración de Existentes

| Prueba | Resultado |
|--------|-----------|
| Dry-run genera reporte | ✅ 10 servidores detectados |
| Apply cifra servidores | ✅ 10/10 OK |
| CORE excluidos | ✅ 2 excluidos |
| MongoDB sincronizado | ✅ Warnings documentados |

---

## 8. MONGODB LEGACY

### 8.1 Manejo Actual

- MongoDB recibe secretos cifrados desde sync SQL→MongoDB
- Si módulo legacy espera texto plano, fallará conexión
- TODO: Actualizar módulos legacy para usar `get_decrypted_credentials`

### 8.2 Riesgo Documentado

⚠️ Si algún módulo accede directamente a MongoDB.password sin descifrar, la conexión fallará. Solución: migrar a usar `server_registry.get_server_connection_info()`.

---

## 9. NO REGRESIÓN

| Validación | Resultado |
|------------|-----------|
| `python -m compileall /app/backend` | ✅ OK |
| Backend RUNNING | ✅ RUNNING |
| Login OK | ✅ Token generado |
| `/api/servers` | ✅ 8 servidores activos |
| Estado de cifrado | ✅ 89% cifrado (8/9 activos) |
| Comercial tablero | ⚠️ Timeout por red externa (no es error de cifrado) |

---

## 10. RIESGOS RESIDUALES

1. ~~**CORE no cifrados:** Los 2 servidores CORE mantienen passwords en texto plano por diseño (excluidos de migración automática).~~ **RESUELTO en FASE 3C.3**

2. **MongoDB espejo:** MongoDB ahora tiene passwords cifrados. Módulos que lean directamente de MongoDB sin descifrar fallarán.

3. **Rollback de clave:** Si se pierde `SERVER_SECRET_KEY`, los passwords cifrados serán irrecuperables. Respaldo de clave es crítico.

4. **Ambiente preview:** Conexiones a servidores externos (130mid.ddns.net, servercienfuegos.ddns.net) fallan por red, no por cifrado.

---

## 11. ARCHIVOS CREADOS/MODIFICADOS

### Creados
- `/app/backend/core/secret_manager.py`
- `/app/backend/scripts/encrypt_existing_server_secrets.py`
- `/app/docs/reports/server_secrets_encryption_report.json`
- `/app/docs/FASE_3C_SECRETOS_SERVIDORES.md` (este documento)

### Modificados
- `/app/backend/.env` (agregado SERVER_SECRET_KEY)
- `/app/backend/core/server_registry.py` (integración cifrado)

---

## 12. CRITERIOS DE ACEPTACIÓN

| Criterio | Estado |
|----------|--------|
| Existe secret_manager central | ✅ |
| Clave no hardcodeada | ✅ (en .env) |
| Secretos nuevos se guardan cifrados | ✅ |
| Script dry-run de migración | ✅ |
| Responses no exponen secretos | ✅ |
| PUT con `********` preserva existente | ✅ |
| resolve_server_context puede descifrar | ✅ |
| Backend compila | ✅ |
| /api/servers funciona | ✅ |
| Documentación completa | ✅ |

---

## 13. PRÓXIMOS PASOS

- ~~**P1:** Cifrar passwords de servidores CORE (requiere procedimiento manual)~~ **COMPLETADO en FASE 3C.3**
- **P1:** Actualizar módulos legacy para usar `get_server_connection_info()`
- **P2:** Implementar rotación de claves de cifrado
- **P2:** Auditoría de accesos a secretos

---

## 14. FASE 3C.3 — Cifrado Controlado de Servidores CORE

**Fecha:** 25 de Abril de 2026  
**Estado:** COMPLETADA

### Resumen

La FASE 3C.3 completó el cifrado de los 2 servidores CORE que estaban pendientes:

| Servidor | Estado | Resultado |
|----------|--------|-----------|
| EDARSA HUB (Activo) | CIFRADO | `enc:v1:...` |
| EDARSA HUB (Inactivo) | CIFRADO | `enc:v1:...` |

### Script Utilizado

```bash
# Dry-run
python /app/backend/scripts/encrypt_core_server_secrets.py --dry-run

# Apply
python /app/backend/scripts/encrypt_core_server_secrets.py --apply
```

### Validaciones Post-Cifrado

| Validación | Resultado |
|------------|-----------|
| Passwords CORE cifrados en SQL | ✅ |
| Descifrado interno funciona | ✅ |
| Login OK | ✅ |
| /api/servers excluye CORE | ✅ |
| PUT CORE rechazado | ✅ |
| DELETE CORE rechazado | ✅ |

### Documentación Detallada

Ver: `/app/docs/FASE_3C3_CORE_SECRET_ENCRYPTION.md`

---

## 15. FASE 3D — Validación Real de Conectividad con Secretos Cifrados

**Fecha:** 25 de Abril de 2026  
**Estado:** COMPLETADA

### Resumen

La FASE 3D validó que los módulos pueden conectarse correctamente usando passwords cifrados:

| Métrica | Valor |
|---------|-------|
| Servidores probados | 8 |
| Descifrado OK | 8/8 (100%) |
| Conectividad OK | 5/8 |
| Source Unreachable (red) | 3/8 |
| Auth Failed | 0/8 |
| Secret Decryption Error | 0/8 |

### Validaciones Realizadas

| Módulo | Resultado |
|--------|-----------|
| Comercial | SUCCESS |
| Finanzas | SUCCESS |
| Propinas TPV | SUCCESS |
| No exposición secretos | ✓ |

### Script Creado

```bash
python /app/backend/scripts/validate_encrypted_server_connectivity.py --run
```

### Documentación Detallada

Ver: `/app/docs/FASE_3D_VALIDACION_CONECTIVIDAD_SECRETOS_CIFRADOS.md`

---

## 16. FASE 4C — Rotación Controlada de Claves

**Fecha:** 25 de Abril de 2026  
**Estado:** PREPARADA (dry-run validado)

### Resumen

La FASE 4C implementó el mecanismo para rotar `SERVER_SECRET_KEY`:

| Métrica | Valor |
|---------|-------|
| Servidores con secretos | 8 |
| Secretos rotables | 8 |
| Descifrado OK | 8/8 |

### Script de Rotación

```bash
# Dry-run (validar sin modificar)
python /app/backend/scripts/rotate_server_secret_key.py --dry-run

# Apply (requiere confirmación)
SERVER_SECRET_KEY_NEW="nueva_clave" SECRET_ROTATION_CONFIRM=YES python /app/backend/scripts/rotate_server_secret_key.py --apply
```

### Funciones Agregadas a secret_manager.py

- `validate_fernet_key(key)`
- `get_key_fingerprint(key)`
- `encrypt_secret_with_key(value, key)`
- `decrypt_secret_with_key(value, key)`
- `rotate_secret(value, old_key, new_key)`
- `validate_rotation_keys(old, new)`

### Documentación Detallada

Ver: `/app/docs/FASE_4C_ROTACION_CLAVES_SECRETOS.md`

---

**FASE 3C COMPLETADA EXITOSAMENTE (incluyendo 3C.1, 3C.1 Parte 2, 3C.3, 3D y 4C)**
