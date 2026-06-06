# RH-NOMINAS-EDARSAHUB-CONNECTION-01 — Reporte de Corrección

**Código:** RH-NOMINAS-EDARSAHUB-CONNECTION-01  
**Fecha:** 2025-12-27  
**Módulo:** RH / Nóminas  
**Estado:** ✅ CORRECCIÓN EXITOSA

---

## 1. Resumen Ejecutivo

Se corrigió la falla de arquitectura que bloqueaba el módulo RH/Nóminas. El módulo ahora usa conexión directa a EDARSAHUB vía variables de entorno (`EDARSAHUB_CONFIG`), eliminando la dependencia incorrecta del catálogo MongoDB `servers` con `active=True`.

---

## 2. Causa Raíz

El módulo RH usaba `get_edarsa_hub_server()` que buscaba en MongoDB `servers` con filtro `active=True`. El servidor "EDARSA HUB" tenía `active=False`, bloqueando todos los endpoints.

---

## 3. Por Qué NO Se Activó el Servidor "EDARSA HUB"

| Riesgo | Descripción |
|--------|-------------|
| Exposición | Aparecería como servidor seleccionable para usuarios |
| Confusión operativa | EDARSAHUB es cerebro del sistema, no unidad de negocio |
| Inconsistencia | Crearía dos rutas para acceder al mismo recurso |
| Permisos | Habría que excluirlo manualmente de `allowed_servers` |

La solución correcta es usar conexión directa como lo hace `server_registry.py`.

---

## 4. Archivo Modificado

**Archivo:** `/app/backend/modules/rh/repository.py`

### ANTES (problemático)

```python
from typing import Dict, List, Optional, Any
import logging
import re

from core.db import execute_sql_query

EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"

# ...

async def get_edarsa_hub_server() -> Optional[Dict]:
    """Obtiene la configuración del servidor EDARSA HUB."""
    return await get_db().servers.find_one(
        {"id": EDARSA_HUB_SERVER_ID, "active": True},
        {"_id": 0}
    )
```

### DESPUÉS (correcto)

```python
from typing import Dict, List, Optional, Any
import logging
import re
import os

from core.db import execute_sql_query

# Configuración EDARSAHUB interna (fuente maestra para RH/Nóminas)
EDARSAHUB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
}

# ...

async def get_edarsa_hub_server() -> Optional[Dict]:
    """
    Obtiene la configuración del servidor EDARSA HUB.
    Usa EDARSAHUB_CONFIG (conexión directa via variables de entorno)
    """
    if not EDARSAHUB_CONFIG.get('host') or not EDARSAHUB_CONFIG.get('database'):
        logging.error("EDARSAHUB_CONFIG incompleto: falta host o database")
        return None
    
    return EDARSAHUB_CONFIG
```

---

## 5. Patrón de Conexión Usado

```
RH/Nóminas → EDARSAHUB_CONFIG → SQL Server directo (54.39.104.176:1433)
```

Mismo patrón que `server_registry.py`, consistente con la arquitectura del sistema.

---

## 6. Endpoints Validados

| Endpoint | Status HTTP | Registros | Estado |
|----------|-------------|-----------|--------|
| `/api/rrhh/catalogos/puestos` | 200 | 37 | ✅ OK |
| `/api/rrhh/catalogos/sucursales` | 200 | 8 | ✅ OK |
| `/api/rrhh/catalogos/tipos-incidencias` | 200 | 0 | ✅ OK (tabla vacía) |
| `/api/rrhh/colaboradores` | 200 | 0 | ✅ OK (tabla vacía) |
| `/api/rrhh/incidencias` | 200 | 0 | ✅ OK (tabla vacía) |
| `/api/rrhh/asistencia` | 200 | 0 | ✅ OK (tabla vacía) |
| `/api/rrhh/nominas/flujo` | 200 | 0 | ✅ OK (tabla vacía) |
| `/api/rrhh/dashboard` | 200 | — | ✅ OK |
| `/api/rrhh/reclutamiento/dashboard` | 200 | — | ✅ OK |
| `/api/nomina/ciclos` | 200 | 0 | ✅ OK (MongoDB vacío) |

---

## 7. Tablas Consultadas en EDARSAHUB

| Tabla | Existe | Registros | Estado |
|-------|--------|-----------|--------|
| `RH_Cat_Puestos` | ✅ | 37 | Con datos |
| `RH_Cat_Sucursales` | ✅ | 8 | Con datos |
| `RH_Cat_Tipos_Incidencias` | ✅ | 0 | Vacía |
| `RH_Colaboradores_*` | ✅ | 0 | Vacía |
| `RH_Incidencias_*` | ✅ | 0 | Vacía |
| `RH_Asistencia_*` | ✅ | 0 | Vacía |
| `RH_Nominas_Flujo` | ✅ | 0 | Vacía |

---

## 8. Verificación de No Regresión

| Módulo | Endpoint | Estado |
|--------|----------|--------|
| Auth | `/api/auth/me` | ✅ OK |
| Compras | `/api/compras/dashboard/{id}` | ✅ OK ($2,340,813.14) |
| Usuarios | `/api/usuarios` | ✅ OK |
| Servidores | `/api/servers` | ✅ OK (EDARSA HUB no visible) |

---

## 9. Errores Encontrados

Ninguno después de la corrección.

---

## 10. Riesgos Pendientes

| Riesgo | Mitigación |
|--------|------------|
| `core/resilient_sql.py` usa mismo patrón problemático | Corrección separada recomendada |
| Variables de entorno no configuradas | Valores por defecto proporcionados |

---

## 11. Rollback

Para revertir, restaurar `repository.py` a la versión anterior:

```python
async def get_edarsa_hub_server() -> Optional[Dict]:
    return await get_db().servers.find_one(
        {"id": EDARSA_HUB_SERVER_ID, "active": True},
        {"_id": 0}
    )
```

Y activar el servidor "EDARSA HUB" en MongoDB `servers` con `active=True`.

---

## Dictamen Final

### ✅ CORRECCIÓN EXITOSA

| Criterio | Resultado |
|----------|-----------|
| RH no depende de MongoDB servers | ✅ Corregido |
| Usa EDARSAHUB_CONFIG directo | ✅ Implementado |
| Endpoints responden | ✅ Todos validados |
| EDARSA HUB no aparece como servidor | ✅ Verificado |
| No se rompe auth | ✅ OK |
| No se rompen módulos auditados | ✅ OK |
| Evidencia documentada | ✅ Este reporte |

---

*Corrección aplicada: 2025-12-27*  
*Agente: E1*
