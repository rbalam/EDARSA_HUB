# FINANZAS-CXP-MPRO-COMBINE-01 - REPORTE

**Fecha**: 2025-12-28  
**Estado**: ✅ COMPLETADO  
**Autor**: E1 Agent

---

## 1. RESUMEN EJECUTIVO

Se corrigió el módulo de Cuentas por Pagar para combinar datos de SoftRestaurant + ManagementPro en lugar de usar MPRO como fallback.

**Antes**: Si SoftRestaurant retornaba datos, MPRO nunca se consultaba.  
**Después**: Ambas fuentes se consultan siempre y los resultados se combinan.

---

## 2. SEGURIDAD DE CREDENCIALES MPRO

### Tabla de verificación

| Punto | Resultado | Evidencia | Riesgo | Acción |
|-------|-----------|-----------|--------|--------|
| Fuente de credenciales | **MongoDB** (`db.servers`) | `repository_mpro.py:45-48` | BAJO | Servidor definido en MongoDB con ID fijo |
| EDARSAHUB/server_registry usado | NO directamente | MPRO usa MongoDB, no server_registry | BAJO | Documentado |
| Password impreso en logs | **NO** | Solo se loguea error genérico, nunca el valor | NINGUNO | OK |
| Connection string impreso | **NO** | No se construye connection string visible | NINGUNO | OK |
| Subprocess expone secretos | **SÍ - EN ARGUMENTOS** | `sql_subprocess_helper.py:78` | **MEDIO** | Ver mitigación abajo |
| Mecanismo de descifrado | `core/secret_manager.py` | Usa `SERVER_SECRET_KEY` (env var) | BAJO | Documentado |
| Rollback | **DOCUMENTADO** | Ver sección 7 | NINGUNO | OK |

### Detalle: Exposición en subprocess

**Hallazgo**: La contraseña se pasa como argumento de línea de comandos al subprocess:
```python
cmd = [PYTHON_PATH, WORKER_PATH, host, port, database, username, password, query_b64]
process = await asyncio.create_subprocess_exec(*cmd, ...)
```

**Riesgo**: La contraseña puede ser visible temporalmente en:
- `ps aux` o listado de procesos del sistema
- `/proc/[pid]/cmdline`

**Mitigación actual**:
1. El subprocess tiene vida corta (timeout 30s máximo)
2. El entorno de Kubernetes limita acceso a otros procesos
3. La contraseña está descifrada solo en memoria, no en disco

**Mitigación recomendada (futuro)**:
- Pasar credenciales via stdin en lugar de argumentos
- Usar variables de entorno del subprocess en lugar de argumentos

### Detalle: Mecanismo de descifrado

El descifrado usa `core/secret_manager.py`:
1. La contraseña en MongoDB está cifrada con formato `enc:v1:...`
2. Se descifra usando `decrypt_secret()` que requiere `SERVER_SECRET_KEY`
3. `SERVER_SECRET_KEY` es una variable de entorno (no hardcodeada)
4. Si `SERVER_SECRET_KEY` no está configurada, se usa la contraseña tal cual (fallback)

```python
# repository_mpro.py líneas 51-59
from core.secret_manager import decrypt_secret, is_encrypted_secret
if is_encrypted_secret(password):
    server['password'] = decrypt_secret(password)
```

### Detalle: Justificación del subprocess

**Razón**: El entorno de Supervisor de Kubernetes fuerza `LANG=C` que causa error de encoding en `pytds`:
```
'charmap' codec can't decode byte 0x81 in position X
```

**Solución**: El subprocess fuerza `PYTHONIOENCODING=utf-8` y `LANG=C.UTF-8` en su entorno, evadiendo el problema sin modificar el entorno global del servidor.

---

## 3. CAUSA RAÍZ

El módulo CxP usaba lógica de **fallback**:
```python
# ANTES (incorrecto)
if softrest_repo.get_datos():
    return datos_sr  # MPRO nunca se consulta
else:
    return mpro_repo.get_datos()  # Solo si SR falla
```

**Corrección aplicada**: Lógica de **combinación**:
```python
# DESPUÉS (correcto)
datos_sr = softrest_repo.get_datos()  # Siempre consultar SR
datos_mpro = mpro_repo.get_datos()    # Siempre consultar MPRO
return combinar(datos_sr, datos_mpro)  # Combinar ambos
```

---

## 4. ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/finanzas/cuentas_por_pagar.py` | Endpoint `/resumen` cambiado de fallback a combinación SR+MPRO |
| `/app/backend/modules/finanzas/cuentas_por_pagar.py` | Endpoint `/sucursales` cambiado de fallback a combinación SR+MPRO |
| `/app/backend/modules/finanzas/cuentas_por_pagar.py` | Endpoint de listado mejorado con mapeo de nombres MPRO |
| `/app/backend/modules/finanzas/repository_mpro.py` | Migrado de `execute_sql_query` a `execute_sql_subprocess` |
| `/app/backend/modules/finanzas/repository_mpro.py` | Agregado descifrado de contraseña (secret_manager) |
| `/app/backend/modules/finanzas/repository_mpro.py` | Aumentado limit de 500 a 2000 registros |

---

## 5. VALIDACIONES REALIZADAS

### 4.1 Resumen "Todas las fuentes"

| Métrica | Valor |
|---------|-------|
| Fuente | SOFTRESTAURANT+MANAGEMENTPRO |
| Facturas SR | 867 |
| Saldo SR | $18,514,378.63 |
| Facturas MPRO | 1,983 |
| Saldo MPRO | $30,382,371.95 |
| **Total Facturas** | **2,850** |
| **Total Saldo** | **$48,896,750.58** |

### 4.2 Filtros por sucursal MPRO

| Sucursal | Facturas | Saldo Esperado | Saldo Real | Estado |
|----------|----------|----------------|------------|--------|
| ORIGEN (0023) | 1,073 | $11,501,659.82 | $11,501,659.82 | ✅ EXACTO |
| 130° QRO (0021) | 524 | $8,984,825.24 | $8,984,825.24 | ✅ EXACTO |

### 4.3 Filtros SoftRestaurant (no regresión)

| Sucursal | Facturas | Saldo | Estado |
|----------|----------|-------|--------|
| CIENFUEGOS | 369 | $6,791,664.14 | ✅ OK |
| LA ESTELAR | 241 | $1,436,004.25 | ✅ OK |

### 4.4 Endpoint /sucursales

| Sucursal | Sistema | Facturas | Saldo |
|----------|---------|----------|-------|
| LA ESTELAR | SOFTRESTAURANT | 241 | $1,436,004.25 |
| ORIGEN | MANAGEMENTPRO | 1,073 | $11,501,659.82 |
| 130° QRO | MANAGEMENTPRO | 524 | $8,984,825.24 |
| 130° TULUM | MANAGEMENTPRO | 263 | $5,752,992.93 |

---

## 6. ESTRUCTURA DE RESPUESTA

### Endpoint `/resumen`
```json
{
  "fuente": "SOFTRESTAURANT+MANAGEMENTPRO",
  "fuentes_detalle": {
    "SOFTRESTAURANT": {"facturas": 867, "saldo": 18514378.63},
    "MANAGEMENTPRO": {"facturas": 1983, "saldo": 30382371.95}
  },
  "fuentes_fallidas": null,
  "resumen": {
    "total_facturas": 2850,
    "total_saldo": 48896750.58
  },
  "antiguedad": {...},
  "por_tipo": {...}
}
```

### Endpoint `/sucursales`
```json
{
  "fuente": "SOFTRESTAURANT+MANAGEMENTPRO",
  "sucursales": [
    {"SucursalID": "...", "Nombre_Sucursal": "ORIGEN", "Sistema": "MANAGEMENTPRO", ...},
    {"SucursalID": "...", "Nombre_Sucursal": "LA ESTELAR", "Sistema": "SOFTRESTAURANT", ...}
  ]
}
```

---

## 7. RIESGOS Y MITIGACIONES

| Riesgo | Mitigación |
|--------|------------|
| MPRO falla | Reporta `fuentes_fallidas` con error, continúa con SR |
| SR falla | Reporta `fuentes_fallidas` con error, continúa con MPRO |
| Ambos fallan | Retorna `fuente: ERROR_PARCIAL` con lista de errores |
| Duplicados | Cada factura tiene `factura_id` único con prefijo `MPRO_` |
| Encoding | Repositorio MPRO usa subprocess con UTF-8 forzado |

---

## 8. ROLLBACK

En caso de regresión, revertir los siguientes archivos a su versión anterior:
- `/app/backend/modules/finanzas/cuentas_por_pagar.py`
- `/app/backend/modules/finanzas/repository_mpro.py`

Comando:
```bash
git checkout HEAD~1 -- backend/modules/finanzas/cuentas_por_pagar.py backend/modules/finanzas/repository_mpro.py
sudo supervisorctl restart backend
```

---

## 9. PRÓXIMOS PASOS

1. ✅ Monitorear rendimiento del endpoint combinado
2. ⏸️ Evaluar si otros submódulos de Finanzas requieren lógica similar
3. ⏸️ Documentar en manual de usuario

---

*Generado automáticamente - 2025-12-28*

---

## 10. ACTUALIZACIÓN DE SEGURIDAD (2025-12-28)

### Subfase completada: FINANZAS-CXP-MPRO-CREDENTIALS-SECURITY-01

| Punto | Estado anterior | Estado actual |
|-------|-----------------|---------------|
| Fuente credenciales | MongoDB (db.servers) | ✅ EDARSAHUB SQL (server_registry.py) |
| config_origin | N/A | ✅ EDARSAHUB_SQL |
| Password en argv | SÍ (riesgo) | ✅ NO (usa stdin) |
| Worker | sql_query_worker.py | ✅ sql_query_worker_secure.py |

### Reporte completo
Ver `/app/docs/FINANZAS_CXP_MPRO_CREDENTIALS_SECURITY_01_REPORT.md`

