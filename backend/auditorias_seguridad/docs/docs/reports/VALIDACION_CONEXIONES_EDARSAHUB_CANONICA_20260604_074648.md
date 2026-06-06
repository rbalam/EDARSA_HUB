# VALIDACIÓN CONEXIONES EDARSAHUB CANÓNICA
Fecha: Thu Jun  4 07:46:48 UTC 2026

## Objetivo
Determinar cuál conexión debe ser la canónica para EDARSAHUB SQL y eliminar hardcodeos.

## Variables disponibles relacionadas con SQL
```text
```

## Pruebas de conexión
```text
NO HAY CONNECTION STRINGS SQL COMPLETAS EN ENV.
```


## Configuración encontrada en backend/.env

```text
EDARSAHUB_HOST=<REDACTED_EDARSAHUB_SQL_HOST>
EDARSAHUB_PORT=1433
EDARSAHUB_DATABASE=EDARSAHUB
EDARSAHUB_USERNAME=<REDACTED_EDARSAHUB_SQL_USER>
EDARSAHUB_PASSWORD=<REDACTED_EDARSAHUB_SQL_PASSWORD>

# Duplicado con prefijo SQL_
EDARSAHUB_SQL_HOST=<REDACTED_EDARSAHUB_SQL_HOST>
EDARSAHUB_SQL_PORT=1433
EDARSAHUB_SQL_DATABASE=EDARSAHUB
EDARSAHUB_SQL_USER=<REDACTED_EDARSAHUB_SQL_USER>
EDARSAHUB_SQL_PASSWORD=<REDACTED_EDARSAHUB_SQL_PASSWORD>
```

## Análisis

| Parámetro | Valor Canónico (ENV) | sync_service.py | server.py admin |
|-----------|---------------------|-----------------|-----------------|
| Host | `<REDACTED_EDARSAHUB_SQL_HOST>` | ✅ `<REDACTED_EDARSAHUB_SQL_HOST>` | ❌ `4.255.36.175` |
| Port | `1433` | ✅ `1433` | ✅ `1433` |
| Database | `EDARSAHUB` | ✅ `EDARSAHUB` | ✅ `EDARSAHUB` |
| Username | `<REDACTED_EDARSAHUB_SQL_USER>` | ✅ `<REDACTED_EDARSAHUB_SQL_USER>` | ❌ `eloyk` |
| Password | `<REDACTED_EDARSAHUB_SQL_PASSWORD>` | ✅ `<REDACTED_EDARSAHUB_SQL_PASSWORD>` | ❌ `Tijuana2020$` |

## Inconsistencias Detectadas

### 🔴 server.py usa credenciales diferentes

Los endpoints admin en `server.py` usan:
- Host: `4.255.36.175` (diferente)
- Usuario: `eloyk` (diferente)
- Password: `Tijuana2020$` (diferente)

### ⚠️ sync_service.py tiene hardcoded

El archivo `sync_service.py` tiene los valores correctos pero **hardcodeados** en lugar de usar `os.environ.get()`.

## Recomendación

1. **Configuración canónica:** La del `.env` con prefijo `EDARSAHUB_`
2. **Host correcto:** `<REDACTED_EDARSAHUB_SQL_HOST>`
3. **Usuario correcto:** `<REDACTED_EDARSAHUB_SQL_USER>`
4. **Password correcto:** `<REDACTED_EDARSAHUB_SQL_PASSWORD>`

### Acciones requeridas:

1. ✅ `sync_service.py` - Cambiar hardcoded a `os.environ.get()`
2. ❌ `server.py` - Corregir host/usuario/password de `4.255.36.175/eloyk` a `<REDACTED_EDARSAHUB_SQL_HOST>/<REDACTED_EDARSAHUB_SQL_USER>`

---

*Reporte actualizado - E1 Agent*
