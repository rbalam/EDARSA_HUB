# MANIFEST — Backup Auth/RBAC MongoDB

**Fecha:** 2026-05-08T19:34:21 UTC  
**Base de datos:** edarsa_hub  
**Total documentos:** 749  
**Estado:** ✅ VALIDADO

---

## Colecciones Exportadas

| Colección | Documentos | Archivo | Tamaño | SHA256 | Validación |
|-----------|------------|---------|--------|--------|------------|
| `users` | 15 | users.json | 17,409 bytes | `b2b8628a41f65d84...` | ✅ OK |
| `roles` | 4 | roles.json | 2,102 bytes | `14341fecf6f44e0c...` | ✅ OK |
| `rbac_roles` | 6 | rbac_roles.json | 5,695 bytes | `a8c3892bde9bc7fd...` | ✅ OK |
| `rbac_permisos` | 43 | rbac_permisos.json | 13,830 bytes | `6b46bf09e7993ae5...` | ✅ OK |
| `rbac_usuarios_roles` | 72 | rbac_usuarios_roles.json | 28,442 bytes | `600520678ca28bd4...` | ✅ OK |
| `rbac_audit_log` | 584 | rbac_audit_log.json | 373,842 bytes | `afd81fca51236665...` | ✅ OK |
| `password_reset_tokens` | 0 | password_reset_tokens.json | 2 bytes | `4f53cda18c2baa0c...` | ✅ OK |
| `sec_bitacora_acceso` | 25 | sec_bitacora_acceso.json | 9,675 bytes | `5823bb8a2c3c3dd6...` | ✅ OK |

---

## Comandos Utilizados

```python
# Exportación
from pymongo import MongoClient
client = MongoClient(os.environ.get('MONGO_URL'))
db = client['edarsa_hub']
docs = list(db[collection_name].find({}))
json.dump(docs, file, indent=2, ensure_ascii=False, default=str)

# Checksum
hashlib.sha256(file_content).hexdigest()
```

---

## Validación de Lectura

Todos los archivos fueron releídos y parseados exitosamente como JSON válido.
El conteo de documentos coincide con la exportación original.

---

## Ubicación del Backup

```
/app/backups/20260508_1934_auth_rbac_mongodb/
├── users.json
├── roles.json
├── rbac_roles.json
├── rbac_permisos.json
├── rbac_usuarios_roles.json
├── rbac_audit_log.json
├── password_reset_tokens.json
├── sec_bitacora_acceso.json
├── MANIFEST.json
└── MANIFEST.md (este archivo)
```

---

## Restauración (si fuera necesaria)

```python
# NO EJECUTAR SIN AUTORIZACIÓN
import json
from pymongo import MongoClient

client = MongoClient(os.environ.get('MONGO_URL'))
db = client['edarsa_hub']

with open('users.json', 'r') as f:
    docs = json.load(f)
    # db.users.delete_many({})  # PELIGRO
    # db.users.insert_many(docs)  # PELIGRO
```

---

**Backup realizado por:** Sistema de Arquitectura  
**Motivo:** FASE A0 - Preparación para migración Auth/RBAC a EDARSAHUB  
**Estado de implementación:** NO AUTORIZADA - Solo backup preventivo
