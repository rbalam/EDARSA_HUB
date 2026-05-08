# FASE 4C — Rotación Controlada de Claves de Cifrado

**Fecha:** 25 de Abril de 2026  
**Status:** COMPLETADA (Script preparado, dry-run validado)  
**Autor:** Sistema EDARSA HUB

---

## 1. Resumen Ejecutivo

La FASE 4C implementó un mecanismo seguro para rotar la clave de cifrado `SERVER_SECRET_KEY` sin perder acceso a los secretos existentes.

### Resultados

| Métrica | Valor |
|---------|-------|
| Script creado | `/app/backend/scripts/rotate_server_secret_key.py` |
| Funciones de rotación agregadas | 6 |
| Dry-run validado | ✓ |
| Servidores con secretos | 8 |
| Secretos rotables | 8 |
| Descifrado OK | 8/8 (100%) |

---

## 2. Motivo de la Fase

La rotación de claves es una práctica de seguridad esencial para:

1. Cumplir con políticas de seguridad corporativas
2. Responder a posibles compromisos de clave
3. Actualizar claves según ciclo de vida definido
4. Mantener acceso a secretos históricos durante transición

---

## 3. Estado Actual de Cifrado

| Métrica | Valor |
|---------|-------|
| Secretos cifrados | 8 |
| Secretos en texto plano | 0 |
| Formato | `enc:v1:<ciphertext>` |
| Algoritmo | Fernet (AES-128-CBC + HMAC) |
| Fingerprint clave actual | `d60eba8b` |

---

## 4. Variables de Entorno Requeridas

| Variable | Descripción | Obligatoria |
|----------|-------------|-------------|
| `SERVER_SECRET_KEY` | Clave de cifrado actual | Siempre |
| `SERVER_SECRET_KEY_NEW` | Nueva clave de cifrado | Solo apply |
| `SECRET_ROTATION_CONFIRM` | Debe ser "YES" para apply | Solo apply |

**Generar nueva clave:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 5. Procedimiento Dry-Run

```bash
# Ejecutar dry-run
python /app/backend/scripts/rotate_server_secret_key.py --dry-run

# Con clave nueva para validación completa
SERVER_SECRET_KEY_NEW="nueva_clave" python /app/backend/scripts/rotate_server_secret_key.py --dry-run
```

**El dry-run:**
1. Valida formato de clave actual
2. Valida formato de clave nueva (si existe)
3. Verifica que las claves son diferentes
4. Obtiene servidores con secretos
5. Intenta descifrar cada secreto con clave actual
6. Simula re-cifrado con clave nueva
7. Genera reporte sin modificar datos

---

## 6. Procedimiento Apply

```bash
# 1. Generar nueva clave
NEW_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# 2. Ejecutar dry-run primero
SERVER_SECRET_KEY_NEW="$NEW_KEY" python /app/backend/scripts/rotate_server_secret_key.py --dry-run

# 3. Si dry-run es SUCCESS, ejecutar apply
SERVER_SECRET_KEY_NEW="$NEW_KEY" SECRET_ROTATION_CONFIRM=YES python /app/backend/scripts/rotate_server_secret_key.py --apply

# 4. DESPUÉS de apply exitoso, actualizar .env
# Cambiar SERVER_SECRET_KEY al valor de $NEW_KEY

# 5. Reiniciar backend
sudo supervisorctl restart backend

# 6. Validar conectividad
python /app/backend/scripts/validate_encrypted_server_connectivity.py --run
```

**El apply requiere:**
- `SERVER_SECRET_KEY` configurada y válida
- `SERVER_SECRET_KEY_NEW` configurada y válida
- `SECRET_ROTATION_CONFIRM=YES`
- Dry-run previo exitoso (recomendado)

---

## 7. Manejo SQL

La rotación actualiza directamente la tabla `Servidores_Conexiones`:

```sql
UPDATE Servidores_Conexiones
SET password_encrypted = 'enc:v1:<nuevo_ciphertext>',
    api_key_encrypted = 'enc:v1:<nuevo_ciphertext>'
WHERE id = '<server_id>'
```

**Campos rotados:**
- `password_encrypted`
- `api_key_encrypted`

---

## 8. Manejo MongoDB Legacy

Si se usa `--include-mongo`:

1. Después de actualizar SQL, sincroniza a MongoDB
2. Mapea campos: `password_encrypted` → `password`
3. Si falla sync, marca `PARTIAL_SYNC` en reporte
4. SQL permanece como fuente de verdad

---

## 9. Rollback / Recuperación

### Si Apply Falla Parcialmente

1. **NO** cambiar `SERVER_SECRET_KEY` en producción
2. Revisar reporte para identificar servidores afectados
3. Los servidores no modificados siguen con clave anterior
4. Restaurar clave anterior si es necesario
5. Reintentar con dry-run para diagnosticar

### Si Apply es Exitoso

1. Cambiar `SERVER_SECRET_KEY` a la nueva clave
2. Reiniciar servicio
3. Validar con `validate_encrypted_server_connectivity.py`
4. Mantener clave anterior resguardada (no en repo)
5. Después de período de gracia, eliminar clave anterior

---

## 10. Validación Post-Rotación

```bash
# 1. Limpiar cache
python -c "from core.secret_manager import clear_secret_manager_cache; clear_secret_manager_cache()"

# 2. Validar configuración
python -c "from core.secret_manager import validate_secret_key_config; print(validate_secret_key_config())"

# 3. Validar conectividad
python /app/backend/scripts/validate_encrypted_server_connectivity.py --run

# 4. Validar endpoints
curl -X POST "$REACT_APP_BACKEND_URL/api/auth/login" -H "Content-Type: application/json" -d '{"email":"admin@edarsa.com","password":"EDARSA2025"}'
```

---

## 11. Funciones Agregadas a secret_manager.py

| Función | Descripción |
|---------|-------------|
| `validate_fernet_key(key)` | Valida si una clave es válida para Fernet |
| `get_key_fingerprint(key)` | Obtiene fingerprint sin exponer clave |
| `encrypt_secret_with_key(value, key)` | Cifra con clave específica |
| `decrypt_secret_with_key(value, key)` | Descifra con clave específica |
| `rotate_secret(value, old_key, new_key)` | Rota un secreto de clave a clave |
| `validate_rotation_keys(old, new)` | Valida par de claves para rotación |

---

## 12. Opciones del Script

| Opción | Descripción |
|--------|-------------|
| `--dry-run` | Solo verificar, no modificar (default) |
| `--apply` | Ejecutar rotación real |
| `--include-mongo` | Sincronizar MongoDB espejo |
| `--only-sql` | Solo SQL, ignorar MongoDB |
| `--only-active` | Solo servidores activos (default) |
| `--include-inactive` | Incluir servidores inactivos |
| `--include-core` | Incluir servidores CORE |
| `--output PATH` | Ruta del reporte JSON |

---

## 13. Reporte JSON

**Ubicación:** `/app/docs/reports/server_secret_key_rotation_report.json`

```json
{
  "timestamp": "2026-04-25T16:35:17.254017+00:00",
  "mode": "DRY_RUN",
  "status": "SUCCESS",
  "current_key_fingerprint": "d60eba8b",
  "new_key_fingerprint": "9a2a5301",
  "servers_checked": 8,
  "secrets_found": 8,
  "encrypted_secrets": 8,
  "plaintext_secrets": 0,
  "decrypt_ok": 8,
  "decrypt_failed": 0,
  "to_rotate": 8,
  "rotated": 0,
  "failed": 0,
  "skipped": 0,
  "mongo_synced": 0,
  "warnings": [],
  "errors": []
}
```

---

## 14. Logs Seguros

El script genera logs con tags:
- `[SECRET_ROTATION][APPLY_START]`
- `[SECRET_ROTATION][ROTATE_START]`
- `[SECRET_ROTATION][ROTATE_SUCCESS]`
- `[SECRET_ROTATION][ROTATE_ERROR]`
- `[SECRET_ROTATION][MONGO_SYNC_SUCCESS]`
- `[SECRET_ROTATION][PARTIAL_SYNC]`
- `[SECRET_ROTATION][COMPLETE]`

**NUNCA incluyen:**
- Claves de cifrado
- Valores de secretos
- Ciphertexts completos
- Connection strings

---

## 15. Riesgos Residuales

| Riesgo | Mitigación |
|--------|------------|
| Clave nueva perdida | Generar y resguardar antes de apply |
| Falla parcial durante apply | Reporte identifica servidores afectados |
| MongoDB desincronizado | Usar `--include-mongo` o sincronizar manual |
| Clave anterior comprometida | Rotar inmediatamente, no esperar |

---

## 16. Recomendaciones para Producción

1. **Siempre ejecutar dry-run primero**
2. **Resguardar clave nueva en vault seguro** antes de apply
3. **Mantener clave anterior** por período de gracia (7-30 días)
4. **Validar conectividad** después de cada rotación
5. **Documentar fecha de rotación** en políticas de seguridad
6. **NUNCA guardar claves en repositorio**
7. **Rotar regularmente** según política (ej: cada 90 días)

---

## 17. Archivos Creados/Modificados

| Archivo | Cambios |
|---------|---------|
| `/app/backend/core/secret_manager.py` | 6 funciones de rotación agregadas |
| `/app/backend/scripts/rotate_server_secret_key.py` | Script completo creado |
| `/app/docs/reports/server_secret_key_rotation_report.json` | Reporte generado |

---

## 18. Conclusión

La FASE 4C se completó exitosamente:

- ✅ Script de rotación creado y validado
- ✅ Dry-run funciona sin modificar datos
- ✅ Apply requiere confirmación explícita
- ✅ No se imprimen claves ni secretos
- ✅ Valida descifrado antes y después
- ✅ Genera reporte JSON detallado
- ✅ 8/8 secretos descifran correctamente
- ✅ Documentación completa

**Estado final:** EDARSA HUB está preparado para rotar claves de cifrado de forma segura cuando sea necesario.
