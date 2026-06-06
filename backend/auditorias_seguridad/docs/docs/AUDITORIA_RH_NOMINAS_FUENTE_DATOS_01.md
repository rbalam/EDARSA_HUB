# AUDITORIA-RH-NOMINAS-01 / SUBFASE A — VALIDACIÓN DE FUENTE Y BLOQUEO

**Código:** AUDITORIA-RH-NOMINAS-FUENTE-DATOS-01  
**Fecha:** 2025-12-27  
**Módulo:** RH / Nóminas  
**Estado:** ⚠️ FALLA DE ARQUITECTURA DETECTADA

---

## Resumen Ejecutivo

El módulo RH/Nóminas está bloqueado porque depende de un registro de servidor en MongoDB (`servers`) con `active=True`, cuando debería usar la **conexión interna directa** a EDARSAHUB como lo hace `server_registry.py`.

### Arquitectura Actual (Incorrecta)

```
RH Repository → MongoDB.servers.find_one({id: X, active: True}) → FALLA (active=False)
```

### Arquitectura Correcta (como server_registry.py)

```
server_registry.py → EDARSAHUB_CONFIG (conexión directa) → FUNCIONA
```

---

## Diagnóstico por Endpoint

| Endpoint | Archivo | Función | Servicio | Repository | Fuente Esperada | Fuente Real | Usa server_registry | Depende de active | Estado | Dictamen |
|----------|---------|---------|----------|------------|-----------------|-------------|---------------------|-------------------|--------|----------|
| `/rrhh/catalogos/puestos` | routes.py:158 | `rrhh_listar_puestos` | `RHCatalogosService.listar_puestos` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
| `/rrhh/catalogos/sucursales` | routes.py:215 | `rrhh_listar_sucursales` | `RHCatalogosService.listar_sucursales` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
| `/rrhh/catalogos/tipos-incidencias` | routes.py:232 | `rrhh_listar_tipos_incidencias` | `RHCatalogosService.listar_tipos_incidencias` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
| `/rrhh/colaboradores` | routes.py:306 | `rrhh_listar_colaboradores` | `RHColaboradoresService.listar` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
| `/rrhh/incidencias` | routes.py:431 | `rrhh_listar_incidencias` | `RHIncidenciasService.listar` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
| `/rrhh/asistencia` | routes.py:568 | `rrhh_listar_asistencia` | `RHAsistenciaService.listar` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
| `/rrhh/nominas/flujo` | routes.py:674 | `rrhh_listar_flujos` | `RHNominasService.listar_flujos` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
| `/rrhh/dashboard` | routes.py:824+ | `rrhh_dashboard` | `RHDashboardService.obtener` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
| `/rrhh/reclutamiento/*` | routes.py:880+ | varios | `RHReclutamientoService` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
| `/nomina/ciclos` | server.py:13901 | `listar_ciclos_nomina` | — | — | MongoDB `nomina_ciclos` | MongoDB | N/A | NO | ⚠️ SIN DATOS | OK (diferente fuente) |

---

## Análisis de Conexiones a EDARSAHUB

### 1. Conexión Interna Directa (CORRECTA)

**Archivo:** `/app/backend/core/server_registry.py`

```python
EDARSAHUB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
}
```

**Uso:** Consulta `Servidores_Conexiones` para listar servidores externos.  
**NO depende de:** MongoDB `servers` ni de `active=True/False`  
**Estado:** ✅ FUNCIONA

### 2. Conexión vía MongoDB servers (PROBLEMÁTICA)

**Archivos:**
- `/app/backend/modules/rh/repository.py`
- `/app/backend/core/resilient_sql.py`

```python
EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"

async def get_edarsa_hub_server():
    return await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})
```

**Depende de:** Registro en MongoDB `servers` con `active: True`  
**Estado:** ⛔ FALLA porque el registro tiene `active: False`

---

## Análisis del Servidor "EDARSA HUB"

```json
{
  "id": "bea40259-35f1-4693-bda2-d2d10e13e56a",
  "name": "EDARSA HUB",
  "host": "54.39.104.176",
  "port": "1433",
  "database": "EDARSAHUB",
  "system_type": "Otro",
  "active": false   // ← PROBLEMA
}
```

### ¿Es este registro necesario?

| Pregunta | Respuesta |
|----------|-----------|
| ¿Representa una conexión externa operativa? | NO — Es el cerebro del sistema |
| ¿Debe aparecer en filtros de usuario? | NO — No es unidad de negocio |
| ¿Debe ser seleccionable en módulos? | NO — Es infraestructura interna |
| ¿Otros módulos dependen de este registro? | SÍ — `resilient_sql.py` lo usa |
| ¿Activarlo expondría EDARSAHUB como servidor operativo? | SÍ — Riesgo de seguridad |

---

## Comparación de Arquitecturas

| Aspecto | server_registry.py | modules/rh/repository.py |
|---------|-------------------|--------------------------|
| Fuente de conexión | `EDARSAHUB_CONFIG` (variables de entorno) | MongoDB `servers` |
| Depende de `active` | NO | SÍ |
| Configurable por .env | SÍ | NO |
| Requiere registro en DB | NO | SÍ |
| Riesgo de exposición | Bajo | Alto |

---

## Módulos Afectados por el Mismo Patrón

| Módulo | Archivo | Usa `get_edarsa_hub_server` | Estado |
|--------|---------|----------------------------|--------|
| RH/Nóminas | `modules/rh/repository.py` | SÍ | ⛔ BLOQUEADO |
| resilient_sql | `core/resilient_sql.py` | SÍ | ⛔ POTENCIALMENTE AFECTADO |
| server_registry | `core/server_registry.py` | NO (usa `EDARSAHUB_CONFIG`) | ✅ OK |

---

## Dictamen

### ⚠️ FALLA DE ARQUITECTURA: RH DEPENDE DE SERVIDOR EXTERNO

El módulo RH/Nóminas está usando un patrón de conexión incorrecto:

1. **Debería usar:** Conexión directa vía `EDARSAHUB_CONFIG` (como `server_registry.py`)
2. **Está usando:** Búsqueda en MongoDB `servers` con `active=True`

### Riesgos de Activar el Servidor como Solución

1. **Exposición:** "EDARSA HUB" aparecería como servidor seleccionable para usuarios
2. **Confusión:** Los usuarios podrían intentar usarlo como fuente de datos operativos
3. **Permisos:** Habría que excluirlo de `allowed_servers` de todos los usuarios
4. **Inconsistencia:** Dos rutas para acceder al mismo recurso interno

---

## Propuesta de Corrección

### Opción A: Refactorizar RH para usar conexión directa (RECOMENDADA)

Modificar `modules/rh/repository.py`:

```python
# ANTES (problemático)
async def get_edarsa_hub_server() -> Optional[Dict]:
    return await get_db().servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})

# DESPUÉS (correcto)
def get_edarsa_hub_config() -> Dict:
    """Obtiene configuración EDARSAHUB desde variables de entorno."""
    return {
        'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
        'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
        'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
        'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
        'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
    }
```

**Impacto:** Bajo — Solo cambia la fuente de configuración, no la lógica de negocio.

### Opción B: Activar servidor con protecciones (NO RECOMENDADA)

1. Activar registro en MongoDB
2. Agregar flag `visible_en_listado: false`
3. Excluir de `allowed_servers` de todos los usuarios
4. Filtrar en API de servidores

**Impacto:** Alto — Requiere múltiples cambios y validaciones.

---

## Acción Requerida

**Decisión del Usuario:**

- [ ] **A)** Autorizar corrección arquitectónica para que RH use `EDARSAHUB_CONFIG` directamente
- [ ] **B)** Activar el servidor "EDARSA HUB" con protecciones adicionales
- [ ] **C)** Documentar como limitación conocida y no corregir

---

*Diagnóstico: 2025-12-27*  
*Agente: E1*  
*Requiere decisión de arquitectura antes de proceder*
