# FASE 3C.3 — Cifrado Controlado de Secretos en Servidores CORE

**Fecha:** 25 de Abril de 2026  
**Status:** COMPLETADA  
**Autor:** Sistema EDARSA HUB

---

## 1. Resumen Ejecutivo

La FASE 3C.3 implementó el cifrado controlado de secretos (passwords) en los 2 servidores de tipo CORE que aún tenían credenciales en texto plano en la base de datos SQL.

Este proceso fue necesario porque:
- Los endpoints normales `/api/servers` (POST/PUT/DELETE) **rechazan por diseño** la modificación de servidores CORE
- La migración de secretos de FASE 3C solo cubrió servidores DATA_SOURCE
- Los servidores CORE requieren un método especial de cifrado

**Resultado:** 2 servidores CORE cifrados exitosamente con validación de descifrado interno.

---

## 2. Inventario de Servidores CORE

| ID | Nombre | Estado | Password Status |
|---|---|---|---|
| F8A9049A-96E8-4210-84AE-595FFA2822FA | EDARSA HUB | ACTIVO | CIFRADO enc:v1:... |
| BEA40259-35F1-4693-BDA2-D2D10E13E56A | EDARSA HUB | INACTIVO | CIFRADO enc:v1:... |

---

## 3. Por qué CORE Requiere Script Especial

Los servidores CORE tienen protección especial en la API:

```python
# En server_registry.py - update_server()
if existing.get('tipo_conexion') == 'CORE':
    return {
        'success': False,
        'error': 'No se puede modificar conexión tipo CORE desde API estándar',
        'sync_status': 'PROTECTED'
    }
```

Esta protección existe porque:
1. CORE contiene la conexión principal a EDARSAHUB SQL
2. Modificar CORE incorrectamente podría romper toda la aplicación
3. Solo scripts administrativos autorizados deben modificar CORE

---

## 4. Script de Cifrado

**Ubicación:** `/app/backend/scripts/encrypt_core_server_secrets.py`

### Uso

```bash
# Modo dry-run (solo reporta, no modifica)
python encrypt_core_server_secrets.py --dry-run

# Modo apply (ejecuta cifrado real)
python encrypt_core_server_secrets.py --apply
```

### Funciones Principales

| Función | Descripción |
|---|---|
| `check_prerequisites()` | Valida SERVER_SECRET_KEY disponible |
| `get_core_servers_sql()` | Obtiene servidores CORE desde SQL |
| `analyze_core_secrets()` | Analiza estado de cifrado de cada servidor |
| `encrypt_core_server_sql()` | Cifra secretos en SQL con validación |
| `sync_core_to_mongo()` | Sincroniza cambios a MongoDB |
| `run_encryption()` | Orquesta el proceso completo |

---

## 5. Resultado Dry-Run

```
============================================================
EDARSA HUB - Cifrado Controlado de Secretos CORE
Modo: DRY-RUN (solo reporta)
============================================================
✓ Sistema de cifrado disponible (fingerprint: d60eba8b)

Obteniendo servidores CORE...
  → 2 servidores CORE encontrados

Analizando secretos CORE...
  → CORE activos: 1
  → CORE inactivos: 1
  → Passwords: 2 total, 2 en texto plano
  → API Keys: 0 total, 0 en texto plano
  → Servidores CORE a cifrar: 2

[DRY-RUN] No se aplicarán cambios
```

---

## 6. Resultado Apply

```
============================================================
EDARSA HUB - Cifrado Controlado de Secretos CORE
Modo: APPLY (cifrará secretos CORE)
============================================================
✓ Sistema de cifrado disponible (fingerprint: d60eba8b)

  → Cifrando CORE: EDARSA HUB (ACTIVO)...
    ✓ SQL cifrado OK, descifrado validado
    ✓ MongoDB sincronizado

  → Cifrando CORE: EDARSA HUB (INACTIVO)...
    ✓ SQL cifrado OK, descifrado validado
    ✓ MongoDB sincronizado

Status: SUCCESS
Cifrados en esta ejecución: 2
Descifrado validado OK: 2
MongoDB sincronizado: 2
```

---

## 7. Validación de Descifrado Interno

```
=== VALIDACIÓN DE DESCIFRADO INTERNO ===
Servidor: EDARSA HUB (ID: f8a9049a-96e8-4210-84ae-595ffa2822fa)
Host: <REDACTED_EDARSAHUB_SQL_HOST>
Port: 1433
Database: EDARSAHUB
Username: <REDACTED_EDARSAHUB_SQL_USER>
Password descifrado OK: YES
Was encrypted: True
Password length (descifrado): 11
✓ Descifrado interno FUNCIONA correctamente
```

---

## 8. Validación de Login

```bash
curl -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@edarsa.com","password":"EDARSA2025"}'

# Resultado: LOGIN OK, Token generado
```

---

## 9. Validación de /api/servers

```
GET /api/servers:
  Total servidores: 8
  Servidores CORE en respuesta: 0
  PROTECCIÓN CORE EN GET: OK (excluidos por default)
```

---

## 10. Validación de Protección CORE

### PUT Rechazado
```json
{
  "detail": "Esta conexión es del sistema central (CORE) y no puede ser modificada desde la interfaz"
}
```

### DELETE Rechazado
```json
{
  "detail": "Esta conexión es del sistema central (CORE) y no puede ser eliminada desde la interfaz"
}
```

**Resultado:** Protección CORE sigue activa después del cifrado.

---

## 11. Confirmación de No Exposición de Secretos

- El script **NUNCA** imprime passwords ni api_keys en consola
- Los logs solo muestran status (CIFRADO_OK, longitud)
- El reporte JSON no contiene valores de secretos
- La API `/api/servers` devuelve `password_configured: true` en lugar del valor

---

## 12. Riesgos Residuales

| Riesgo | Mitigación |
|---|---|
| Pérdida de SERVER_SECRET_KEY | Documentar clave en vault seguro fuera del repo |
| Corrupción de datos cifrados | Backups regulares de SQL con secretos cifrados |
| Acceso no autorizado a script | Script solo ejecutable por administradores del servidor |

---

## 13. Pendientes

- P3: Implementar rotación de claves de cifrado
- P3: Endpoint `/api/admin/core-connections` para gestión segura desde UI
- P3: Alertas automáticas si se detectan secretos en texto plano

---

## 14. Archivos Relacionados

| Archivo | Propósito |
|---|---|
| `/app/backend/scripts/encrypt_core_server_secrets.py` | Script de cifrado CORE |
| `/app/backend/core/secret_manager.py` | Servicio central de cifrado |
| `/app/backend/core/server_registry.py` | Registry con protección CORE |
| `/app/docs/reports/core_secrets_encryption_report.json` | Reporte de ejecución |

---

## 15. Conclusión

La FASE 3C.3 se completó exitosamente:

- ✅ 2 servidores CORE cifrados
- ✅ Descifrado interno validado
- ✅ Login funciona correctamente
- ✅ API /api/servers funciona correctamente
- ✅ Protección CORE sigue activa
- ✅ No se expusieron secretos en logs/responses
- ✅ Backend compilado y ejecutándose

**Estado final:** Todos los servidores de EDARSA HUB (CORE + DATA_SOURCE) tienen sus secretos cifrados con Fernet usando `enc:v1:` prefix.
