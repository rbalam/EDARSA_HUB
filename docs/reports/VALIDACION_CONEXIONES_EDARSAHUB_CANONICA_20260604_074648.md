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
EDARSAHUB_HOST=54.39.104.176
EDARSAHUB_PORT=1433
EDARSAHUB_DATABASE=EDARSAHUB
EDARSAHUB_USERNAME=HRLectura
EDARSAHUB_PASSWORD=National09$

# Duplicado con prefijo SQL_
EDARSAHUB_SQL_HOST=54.39.104.176
EDARSAHUB_SQL_PORT=1433
EDARSAHUB_SQL_DATABASE=EDARSAHUB
EDARSAHUB_SQL_USER=HRLectura
EDARSAHUB_SQL_PASSWORD=National09$
```

## Análisis

| Parámetro | Valor Canónico (ENV) | sync_service.py | server.py admin |
|-----------|---------------------|-----------------|-----------------|
| Host | `54.39.104.176` | ✅ `54.39.104.176` | ❌ `4.255.36.175` |
| Port | `1433` | ✅ `1433` | ✅ `1433` |
| Database | `EDARSAHUB` | ✅ `EDARSAHUB` | ✅ `EDARSAHUB` |
| Username | `HRLectura` | ✅ `HRLectura` | ❌ `eloyk` |
| Password | `National09$` | ✅ `National09$` | ❌ `Tijuana2020$` |

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
2. **Host correcto:** `54.39.104.176`
3. **Usuario correcto:** `HRLectura`
4. **Password correcto:** `National09$`

### Acciones requeridas:

1. ✅ `sync_service.py` - Cambiar hardcoded a `os.environ.get()`
2. ❌ `server.py` - Corregir host/usuario/password de `4.255.36.175/eloyk` a `54.39.104.176/HRLectura`

---

*Reporte actualizado - E1 Agent*
