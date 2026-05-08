# DIAGNÓSTICO: Bypass del Server Registry
## CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE B

**Fecha:** 2026-04-27  
**Estado:** DIAGNÓSTICO COMPLETADO - BYPASS CRÍTICOS IDENTIFICADOS

---

## RESUMEN EJECUTIVO

Se identificaron **múltiples módulos que hacen bypass** del `server_registry.py` y acceden directamente a MongoDB para resolver configuración de servidores.

### Estadísticas:

| Categoría | Cantidad |
|-----------|----------|
| Archivos con bypass | 25+ |
| Bypass en server.py | 56 |
| Bypass en módulos | 15+ |
| Bypass en scripts | 8 |
| Módulos usando registry correctamente | ~5 |

---

## SERVER_REGISTRY.PY: CONFIRMACIÓN DE DISEÑO CORRECTO

```python
# /app/backend/core/server_registry.py

# Flag de control
USE_SQL_FOR_SERVERS = os.environ.get('USE_SQL_FOR_SERVERS', 'true').lower() == 'true'

# Fuentes en orden de prioridad:
# 1. EDARSAHUB SQL (fuente maestra)
# 2. MongoDB (fallback legacy)
```

**Estado: CORRECTO** - El registry está bien diseñado.

---

## BYPASS CRÍTICOS IDENTIFICADOS

### 1. SERVER.PY (56 bypass) - **CRÍTICO**

El archivo principal del backend tiene 56 accesos directos a `db.servers`:

| Líneas | Función | Patrón | Riesgo |
|--------|---------|--------|--------|
| 1315 | sync_server_data | `db.servers.find_one` | ALTO |
| 1531 | get_server_data | `db.servers.find_one` | ALTO |
| 1622-1782 | Múltiples endpoints | `db.servers.find_one` | ALTO |
| 1824-2019 | Endpoints comercial | `db.servers.find_one` | ALTO |
| 2091-2606 | Endpoints finanzas | `db.servers.find_one` | ALTO |
| 2821-3026 | Endpoints compras | `db.servers.find_one` | ALTO |
| 4309-4542 | Endpoints inventarios | `db.servers.find_one` | ALTO |

**Impacto:** Estos endpoints **NUNCA** usan EDARSAHUB como fuente, siempre van a MongoDB.

---

### 2. MÓDULO FINANZAS (9 bypass) - **CRÍTICO**

| Archivo | Función | Patrón |
|---------|---------|--------|
| `repository_real.py:47` | `__init__` | `db.servers.find_one` |
| `repository_mpro.py:42` | `_server_cache` | `db.servers.find_one` |
| `historical_kpis_repository.py:31` | búsqueda | `db.servers.find_one` |
| `propinas_tpv/service.py:79` | filtro | `db['servers'].find` |
| `propinas_tpv/routes_sql.py:408,440,516` | múltiples | `db.servers.find_one/find` |
| `propinas_tpv/routes.py:222,262,358` | múltiples | `db.servers.find_one/find` |
| `propinas_tpv/sql_repository.py:70` | búsqueda | `mongo_db.servers.find_one` |
| `propinas_tpv/service_sql.py:160` | filtro | `db['servers'].find` |

---

### 3. MÓDULO COMPRAS (2 bypass) - **CRÍTICO**

| Archivo | Función | Patrón |
|---------|---------|--------|
| `repository.py:111` | `get_server_by_id` | `db.servers.find_one` |
| `historical_kpis_repository.py:37` | búsqueda | `db.servers.find_one` |

---

### 4. MÓDULO COMERCIAL (3 bypass) - **PARCIAL**

| Archivo | Función | Patrón | Nota |
|---------|---------|--------|------|
| `repository.py:224` | `get_server_by_id` | `db.servers.find_one` | Es FALLBACK después de SQL |
| `repository.py:243` | `get_all_active_servers` | `db.servers.find` | Es FALLBACK |
| `adapters.py:273` | apis locales | `sync_db.servers.find` | BYPASS directo |

**Nota:** `repository.py` SÍ intenta EDARSAHUB primero (líneas 217-220) antes del fallback. Pero `adapters.py` hace bypass directo.

---

### 5. MÓDULO RH (2 bypass) - **CRÍTICO**

| Archivo | Función | Patrón |
|---------|---------|--------|
| `importador/repository.py:68` | búsqueda | `db.servers.find_one` |
| `repository.py:126` | búsqueda | `db.servers.find_one` |

---

### 6. MÓDULO CONFIGURACIÓN (2 bypass) - **CRÍTICO**

| Archivo | Función | Patrón |
|---------|---------|--------|
| `repositories/config_asignaciones_repository.py:249` | búsqueda | `db.servers.find_one` |
| `services/almacenes_sync_service.py:138` | búsqueda | `db.servers.find_one` |

---

### 7. MÓDULO CATÁLOGOS (1 bypass) - **CRÍTICO**

| Archivo | Función | Patrón |
|---------|---------|--------|
| `repository.py:31` | EDARSA HUB | `db.servers.find_one` |

---

### 8. PORTAL PROVEEDORES (2 bypass) - **CRÍTICO**

| Archivo | Función | Patrón |
|---------|---------|--------|
| `routes/portal_proveedores.py` | 2 accesos | `db.servers.find_one` |

---

### 9. SCHEDULER/JOBS (2 bypass) - **CRÍTICO**

| Archivo | Función | Patrón |
|---------|---------|--------|
| `core/scheduler/jobs/inventarios_detector_job.py` | 2 accesos | `db.servers` |

---

### 10. CONTEXT RESOLVER (2 bypass) - **CRÍTICO**

| Archivo | Función | Patrón |
|---------|---------|--------|
| `core/context_resolver.py` | 2 accesos | `db.servers` |

---

### 11. FASE2 OPERATIVO (1 bypass) - **CRÍTICO**

| Archivo | Función | Patrón |
|---------|---------|--------|
| `fase2_operativo/repositories/asignacion_repository.py:20` | collection | `db.server_sucursales_config` |

---

## MÓDULOS QUE SÍ USAN REGISTRY CORRECTAMENTE

| Archivo | Uso |
|---------|-----|
| `server.py` líneas 1099-1269 | CRUD de servidores |
| `scripts/reconcile_servers_sql_mongo.py` | Sincronización |
| `scripts/validate_encrypted_server_connectivity.py` | Validación |
| `scripts/encrypt_*.py` | Cifrado |
| `api/admin_core_connections.py` | Admin |

---

## USOS LEGÍTIMOS DE MONGODB (NO TOCAR)

| Archivo | Colección | Propósito |
|---------|-----------|-----------|
| `repository.py` | `server_status` | Cache de estado |
| `repository.py` | `comercial_dashboard_cache` | Cache de datos |
| Varios | `kpis_cache` | Cache de KPIs |
| Varios | `audit_log` | Logs de auditoría |
| Varios | `jobs_*` | Estado de jobs |

---

## PRIORIDAD DE CORRECCIÓN

| Prioridad | Módulo | Archivos | Bypass | Impacto |
|-----------|--------|----------|--------|---------|
| 🔴 P0 | server.py | 1 | 56 | CRÍTICO - Es el backend principal |
| 🔴 P1 | Finanzas | 9 | 9 | ALTO - Propinas, Dashboard |
| 🔴 P1 | Compras | 2 | 2 | ALTO - Pedidos, Autorización |
| 🟡 P2 | Comercial | 1 | 1 | MEDIO - Solo adapters.py |
| 🟡 P2 | RH | 2 | 2 | MEDIO - Importador |
| 🟡 P2 | Configuración | 2 | 2 | MEDIO |
| 🟡 P2 | Catálogos | 1 | 1 | BAJO |
| 🟡 P2 | Portal Proveedores | 1 | 2 | MEDIO |
| 🟢 P3 | Scheduler/Jobs | 1 | 2 | BAJO |
| 🟢 P3 | Context Resolver | 1 | 2 | BAJO |
| 🟢 P3 | Fase2 Operativo | 1 | 1 | BAJO |

---

## ACCIÓN RECOMENDADA POR ARCHIVO

### P0: server.py (56 bypass)

**Problema:** Casi todos los endpoints de datos hacen bypass directo.

**Solución propuesta:**
1. Crear función helper `async def get_server_config(server_id)` que use registry
2. Reemplazar todos los `db.servers.find_one({"id": server_id})` por `get_server_config(server_id)`
3. Registry se encarga de EDARSAHUB → MongoDB fallback

**Riesgo:** ALTO - Archivo crítico, requiere testing exhaustivo.

---

### P1: Módulo Finanzas (9 bypass)

**Solución propuesta:**
1. Importar `get_server_by_id` de `server_registry`
2. Reemplazar accesos directos

**Archivos a modificar:**
- `repository_real.py`
- `repository_mpro.py`
- `historical_kpis_repository.py`
- `propinas_tpv/service.py`
- `propinas_tpv/routes_sql.py`
- `propinas_tpv/routes.py`
- `propinas_tpv/sql_repository.py`
- `propinas_tpv/service_sql.py`

---

### P1: Módulo Compras (2 bypass)

**Solución propuesta:**
1. `repository.py:111` ya tiene fallback, pero debe priorizar SQL
2. `historical_kpis_repository.py` debe usar registry

---

## SUBFASE C PROPUESTA (CORRECCIÓN)

**Alcance:** Corregir bypass críticos en orden de prioridad.

**Entregables:**
1. Helper unificado en server.py
2. Migración de Finanzas a registry
3. Migración de Compras a registry
4. Validaciones por módulo

**Pruebas requeridas:**
- Tablero Ejecutivo
- Dashboard Comercial
- Finanzas Dashboard
- Propinas TPV
- Compras/Autorización
- Portal Proveedores

---

## DICTAMEN

**DESVIACIONES CONFIRMADAS:**
- 56 bypass en server.py
- 15+ bypass en módulos
- Solo ~5 lugares usan registry correctamente

**IMPACTO:**
Los módulos que hacen bypass NUNCA consultan EDARSAHUB como fuente primaria. Siempre usan MongoDB directamente, violando la arquitectura definida.

**RECOMENDACIÓN:**
Aprobar SUBFASE C para corrección quirúrgica, priorizando server.py y módulos críticos.

---

---

## SUBFASE B.1 - CLASIFICACIÓN COMPLETADA

**Estado:** Ver documento completo en:  
`/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md`

**Resumen de clasificación:**
- 45 bypasses categoría A (MIGRAR)
- 5 bypasses categoría B (NO MIGRAR - uso legítimo)
- 3 bypasses categoría C (REVISAR)
- 3 bypasses categoría D (LEGACY)

**Lote 1 propuesto:** 5 cambios priorizados listos para SUBFASE C.

---

## SUBFASE C - PROGRESO DE MIGRACIÓN (Actualizado 2025-12-19)

### Estado por Lote:

| Lote | Bypasses | Dictamen Migración | Dictamen Arquitectura |
|------|----------|-------------------|----------------------|
| Lote 1 | 5 | OK con observación | Brecha: usa MongoDB fallback |
| Lote 2 | 5 | OK con observación | Brecha: usa MongoDB fallback |
| Lote 3 | 5 | OK con observación | Brecha: usa MongoDB fallback |
| **Total** | 15/56 | | |

### Brechas de Catálogo Maestro Detectadas:

| Server ID | Servidor | Existe en EDARSAHUB | Existe en MongoDB | Acción |
|-----------|----------|---------------------|-------------------|--------|
| a5547321-1139-4d2b-9d53-182ca737b6b6 | 130° MERIDA | No | Sí | MIGRAR A EDARSAHUB |
| b5175237-5e57-41f3-ab6d-b5ae2f5e780b | HR2020 ESCRITURA | No | Sí | MIGRAR A EDARSAHUB |

### Interpretación:

**CAPA A - Migración técnica:** Los 15 endpoints migrados usan `server_registry.py` y ya no hacen bypass directo a `db.servers.find_one()`. Migración técnica completa.

**CAPA B - SQL Externo:** Conexión SQL externa NO VERIFICABLE en entorno de prueba. No es regresión del código.

**CAPA C - Arquitectura:** BRECHA DE CATÁLOGO MAESTRO. Todos los servidores se resuelven vía MongoDB fallback porque no existen en EDARSAHUB. El fallback funciona como tolerancia legacy temporal, pero no es arquitectura final correcta.

---

**Última actualización:** 2025-12-19

---

## SUBFASE D - REGULARIZACIÓN CATÁLOGO MAESTRO (2025-12-19)

### Estado: DIAGNÓSTICO COMPLETADO - SIN HALLAZGOS PENDIENTES

### Hallazgo Principal:
**LA BRECHA DE CATÁLOGO MAESTRO YA NO EXISTE**

| Fuente | Servidores | Estado |
|--------|------------|--------|
| EDARSAHUB | 13 | Fuente primaria activa con datos completos |
| MongoDB | 0 | Colección vacía |

### Conclusiones:
1. EDARSAHUB ya es el catálogo maestro funcional
2. MongoDB `db.servers` está vacío
3. Los servidores 130° MERIDA y HR2020 ESCRITURA SÍ existen en EDARSAHUB
4. El registry funciona con `config_origin: EDARSAHUB_SQL`
5. **NO hay datos que migrar de MongoDB a EDARSAHUB**

### Issue Identificado (separado de migración):
- `SERVER_SECRET_KEY` no configurada impide descifrar passwords
- No bloquea la migración de código

### Documentación:
- `/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md`
- `/app/docs/sql/VALIDACION_SERVIDORES_EDARSAHUB.sql`

### Dictamen:
**BRECHA DE CATÁLOGO MAESTRO CERRADA - Proceder con Lote 4**

---

## ISSUE SEPARADO: CONFIG-SECURITY-01 — SERVER_SECRET_KEY PENDIENTE

### Clasificación
| Campo | Valor |
|-------|-------|
| **ID** | CONFIG-SECURITY-01 |
| **Tipo** | Configuración / Seguridad |
| **Estado** | PENDIENTE CONFIGURACIÓN |
| **Prioridad** | P1 (no bloquea código, sí bloquea validación real) |

### Descripción
`SERVER_SECRET_KEY` no está configurada en el entorno. Esta variable es requerida por `core/secret_manager.py` para descifrar los passwords cifrados (Fernet) almacenados en `Servidores_Conexiones.password_encrypted`.

### Síntoma
```
WARNING: [SECRET_MANAGER] SERVER_SECRET_KEY no configurada. Cifrado deshabilitado.
ERROR: [SECRET_MANAGER] No se puede descifrar: SERVER_SECRET_KEY no configurada
ERROR: [SERVER_REGISTRY][DECRYPT_ERROR] Error descifrando password: SecretManagerError
```

### Impacto
| Área | Impacto |
|------|---------|
| Migración de bypasses | ❌ **NO BLOQUEA** — El código migrado funciona, solo falla el descifrado |
| Catálogo maestro | ❌ **NO AFECTA** — EDARSAHUB sigue siendo fuente primaria |
| Conexión SQL externa | ✅ **SÍ BLOQUEA** — No puede conectar a servidores SQL externos |
| Pruebas funcionales | ✅ **SÍ BLOQUEA** — Las validaciones de conexión real fallan |

### Causa Raíz
La variable `SERVER_SECRET_KEY` no está definida en `/app/backend/.env`.

### Solución Requerida
1. Generar o recuperar la clave Fernet usada para cifrar los passwords en EDARSAHUB
2. Agregar a `/app/backend/.env`:
   ```
   SERVER_SECRET_KEY=<clave_fernet_base64>
   ```
3. Reiniciar backend

### Dependencias
- Requiere conocer la clave Fernet original con la que se cifraron los passwords en EDARSAHUB
- Si se perdió la clave, los passwords deben re-cifrarse con una nueva clave

### No es:
- ❌ Bug de código
- ❌ Brecha de catálogo maestro
- ❌ Problema de migración de bypasses
- ❌ Regresión de Lotes 1-3

---

## ACTUALIZACIÓN: CREDENCIALES MPRO EN CxP (2025-12-28)

### Contexto
Durante FINANZAS-CXP-MPRO-COMBINE-01, se modificó `repository_mpro.py` para usar subprocess y descifrar contraseñas.

### Fuente de credenciales MPRO
- **Origen**: MongoDB (`db.servers`)
- **Server ID**: `1b230a06-ffaf-4c70-bd27-b1be3579dea6`
- **No usa**: server_registry.py directamente para MPRO

### Mecanismo de descifrado
- Usa `core/secret_manager.py`
- Requiere `SERVER_SECRET_KEY` (env var)
- Formato cifrado: `enc:v1:...`

### Riesgo identificado
- Password se pasa como argumento al subprocess
- Visible temporalmente en `ps aux` / `/proc/[pid]/cmdline`
- Mitigación: subprocess de vida corta, entorno Kubernetes aislado

### Recomendación futura
- Pasar credenciales via stdin al subprocess
- Usar env vars del subprocess en lugar de argumentos


---

## CORRECCIÓN: FINANZAS-CXP-MPRO-CREDENTIALS-SECURITY-01 (2025-12-28)

### Problema corregido
El repositorio MPRO (`repository_mpro.py`) leía credenciales desde MongoDB en lugar de EDARSAHUB SQL.

### Solución implementada
1. Credenciales ahora vienen de `server_registry.py` con `prefer_sql=True`
2. `config_origin = EDARSAHUB_SQL` confirmado
3. Subprocess usa stdin para credenciales (no argv)
4. Nuevo worker: `sql_query_worker_secure.py`

### Verificación
```
Server encontrado: ManagmentPro
config_origin: EDARSAHUB_SQL  ✅
```

### Reporte
`/app/docs/FINANZAS_CXP_MPRO_CREDENTIALS_SECURITY_01_REPORT.md`

