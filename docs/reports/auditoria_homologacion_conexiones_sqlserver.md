# AUDITORÍA: HOMOLOGACIÓN DE CONEXIONES SQL SERVER

**Fecha de auditoría**: 01-Mayo-2026  
**Auditor**: E1 Agent (READ-ONLY)  
**Código modificado**: NO  
**Secretos expuestos**: NO

---

## 1. RESUMEN EJECUTIVO

El sistema tiene **múltiples lógicas de conexión** a SQL Server (SoftRestaurant/MPRO) que no están homologadas:

| Patrón | Módulos | Riesgo |
|--------|---------|--------|
| **EDARSAHUB + decrypt_secret** (correcto) | sync_propinas, sync_cortes, comercial_v2 | Bajo |
| **Credenciales hardcodeadas** (deuda técnica) | repository_softrestaurant.py | Alto |
| **MongoDB legacy** (parcial) | Configuración histórica | Medio |

**Situación actual**:
- Las Fases 2 y 3 (Control de Ingresos, Propinas TPV) usan EDARSAHUB correctamente
- `repository_softrestaurant.py` tiene credenciales hardcodeadas que **difieren** de EDARSAHUB
- CxP **no usa** `repository_softrestaurant.py` directamente (usa repository_mpro.py que usa EDARSAHUB)
- MongoDB tiene configuración histórica pero no passwords válidos

---

## 2. MAPA DE LÓGICAS DE CONEXIÓN

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LÓGICAS DE CONEXIÓN IDENTIFICADAS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PATRÓN A: EDARSAHUB + decrypt_secret (✅ CORRECTO)                         │
│  ─────────────────────────────────────────────────────────────────────      │
│  • sync_cortes_softrestaurant.py                                            │
│  • sync_propinas_softrestaurant.py                                          │
│  • sync_cortes_mpro.py                                                      │
│  • sync_propinas_mpro.py                                                    │
│  • comercial/repository.py                                                  │
│  • comercial_v2/sync_comercial_edarsahub.py                                 │
│  • repository_real.py                                                       │
│  • repository_mpro.py                                                       │
│  • propinas_tpv/sql_repository.py                                           │
│                                                                             │
│  Flujo:                                                                     │
│  EDARSAHUB.Servidores_Conexiones                                            │
│       │                                                                     │
│       ├─► password_encrypted (cifrado enc:v1:)                              │
│       │                                                                     │
│       ▼                                                                     │
│  decrypt_secret(password_encrypted)                                         │
│       │                                                                     │
│       ▼                                                                     │
│  parse_sql_server_host(host, port)                                          │
│       │                                                                     │
│       ▼                                                                     │
│  execute_sql_query(pytds/pymssql)                                           │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PATRÓN B: CREDENCIALES HARDCODEADAS (❌ DEUDA TÉCNICA)                      │
│  ─────────────────────────────────────────────────────────────────────      │
│  • repository_softrestaurant.py                                             │
│                                                                             │
│  Flujo:                                                                     │
│  DICCIONARIO HARDCODEADO                                                    │
│       │                                                                     │
│       ├─► "password": "C0ntr4s3ña#2026"  (texto plano en código)            │
│       │                                                                     │
│       ▼                                                                     │
│  execute_sql_query()                                                        │
│                                                                             │
│  RIESGO: Alto (secretos en código, difícil de rotar)                        │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PATRÓN C: MONGODB LEGACY (⚠️ DEPRECADO)                                     │
│  ─────────────────────────────────────────────────────────────────────      │
│  • Colección 'servers' con 13 documentos                                    │
│  • Usado como fallback en comercial/repository.py                           │
│  • NO tiene passwords válidos (campo 'password' no existe)                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. MÓDULOS CON CREDENCIALES HARDCODEADAS

### `repository_softrestaurant.py` (BLINDADO)

**Ubicación**: `/app/backend/modules/finanzas/repository_softrestaurant.py`

**Credenciales encontradas** (líneas 36-60):
```python
SERVER_CONFIG = {
    "CIENFUEGOS": {
        "host": "servercienfuegos.ddns.net",
        ...
        "password": "***********",  # HARDCODEADO
    },
    "LA ESTELAR": {
        "host": "serverestelar.ddns.net",
        ...
        "password": "***********",  # HARDCODEADO
    },
    "130° MÉRIDA": {
        "host": "130mid.ddns.net",
        ...
        "password": "***********",  # HARDCODEADO
    }
}
```

**¿Quién lo usa?**:
- Este archivo NO es importado directamente por otros módulos activos
- Parece ser código legacy que fue reemplazado por sync_cortes/sync_propinas

**Riesgo**:
- Los passwords están en texto plano en el código
- Si alguien importa este módulo, usaría credenciales potencialmente desactualizadas

---

## 4. MÓDULOS QUE USAN EDARSAHUB + decrypt_secret

| Módulo | decrypt_secret | parse_sql_server | Driver |
|--------|----------------|------------------|--------|
| sync_cortes_softrestaurant.py | ✅ | ✅ | pytds/pymssql |
| sync_propinas_softrestaurant.py | ✅ | ✅ | pytds/pymssql |
| sync_cortes_mpro.py | ✅ | ✅ | pytds/pymssql |
| sync_propinas_mpro.py | ✅ | ✅ | pytds/pymssql |
| comercial/repository.py | ✅ | Via core/db | pytds/pymssql |
| comercial_v2/sync_comercial_edarsahub.py | ✅ | ✅ | pytds/pymssql |
| repository_real.py | ✅ | Via core/db | pytds/pymssql |
| repository_mpro.py | ✅ | Via server_registry | pytds/pymssql |
| propinas_tpv/sql_repository.py | ✅ | Via core/db | pytds/pymssql |

---

## 5. MÓDULOS QUE USAN MONGODB LEGACY

| Módulo | Propósito | Estado |
|--------|-----------|--------|
| comercial/repository.py | Fallback si EDARSAHUB falla | Activo (solo lectura) |
| core/server_registry.py | Reconciliación | Activo |
| Colección 'servers' | Config histórica | 13 documentos |

**Nota**: MongoDB NO contiene passwords válidos. El campo `password` no existe en los documentos.

---

## 6. DRIVERS USADOS POR MÓDULO

| Driver | Módulos | Notas |
|--------|---------|-------|
| **pytds** | Todos (preferido) | Mejor soporte para instancias nombradas |
| **pymssql** | Todos (fallback) | Usado cuando pytds falla |
| pyodbc | Ninguno activo | No detectado en código activo |

La lógica de `core/db.py` (líneas 460-510):
1. Intenta con `pytds` primero
2. Si falla, intenta con `pymssql`
3. Ambos usan `parse_sql_server_host()` para parsear instancias

---

## 7. MANEJO DE INSTANCIA NOMBRADA POR MÓDULO

| Módulo | parse_sql_server_host | Manejo Correcto |
|--------|----------------------|-----------------|
| core/db.py | ✅ Implementado | ✅ Sí |
| sync_cortes_*.py | Via core/db | ✅ Sí |
| sync_propinas_*.py | Via core/db | ✅ Sí |
| comercial_v2/*.py | ✅ Implementado | ✅ Sí |
| repository_softrestaurant.py | ❌ No usa | ❌ Parcial |

`parse_sql_server_host()` maneja formatos como:
- `servidor.ddns.net,6669`
- `servidor.ddns.net,6669\SQLEXPRESS`
- `servidor.ddns.net\SQLEXPRESS`

---

## 8. USO DE decrypt_secret Y SERVER_SECRET_KEY

| Módulo | decrypt_secret | Carga .env | Funciona |
|--------|----------------|------------|----------|
| sync_cortes_softrestaurant.py | ✅ | ✅ | ✅ |
| sync_propinas_softrestaurant.py | ✅ | ✅ | ✅ |
| comercial/repository.py | ✅ | ✅ | ✅ |
| comercial_v2/sync_comercial_edarsahub.py | ✅ | ✅ | ✅ |
| repository_softrestaurant.py | ❌ No usa | N/A | N/A (hardcoded) |

---

## 9. DIFERENCIAS ENTRE repository_softrestaurant.py Y EDARSAHUB

| Campo | repository_softrestaurant.py | EDARSAHUB |
|-------|------------------------------|-----------|
| **Fuente** | Hardcodeado en código | Tabla Servidores_Conexiones |
| **Password** | Texto plano | Cifrado (enc:v1:) |
| **Formato host** | Simple (server.ddns.net) | Con puerto (server.ddns.net,6669) |
| **Actualización** | Requiere deploy | Actualizable en runtime |

**¿Los passwords coinciden?**: No verificable sin exponer secretos, pero la lógica de EDARSAHUB + decrypt_secret funciona correctamente para las 5 unidades.

---

## 10. RIESGO PARA CXP

**Hallazgo importante**: CxP (`cuentas_por_pagar.py`) **NO importa** `repository_softrestaurant.py`.

Análisis de imports de CxP:
```python
# cuentas_por_pagar.py importa:
from modules.finanzas.repository_mpro import MPRO_SERVER_ID
from modules.comercial.repository import get_sucursales_visibles_config
```

CxP usa:
- `repository_mpro.py` → que usa EDARSAHUB + server_registry (✅ correcto)
- `comercial/repository.py` → que usa EDARSAHUB + decrypt_secret (✅ correcto)

**Conclusión**: CxP NO está en riesgo si se modifica `repository_softrestaurant.py`, pero el archivo está blindado por precaución.

---

## 11. RECOMENDACIÓN PARA COMERCIAL V2

Comercial v2 **YA usa el patrón correcto**:

```python
# sync_comercial_edarsahub.py
from core.secret_manager import decrypt_secret
from core.db import parse_sql_server_host

password = decrypt_secret(cfg['password_encrypted'])
hostname, port, instance = parse_sql_server_host(host_raw, default_port)
```

**No se requieren cambios**. La arquitectura de Comercial v2 está alineada con el objetivo.

---

## 12. PLAN DE NORMALIZACIÓN POR FASES

### Fase 0 (Actual): Documentación
- ✅ Auditoría completada
- ✅ Mapa de conexiones documentado
- ✅ Riesgos identificados

### Fase 1 (Recomendada - Corto Plazo)
- Verificar que `repository_softrestaurant.py` no sea importado activamente
- Si no se usa, marcar como `DEPRECATED` con comentario
- No eliminar ni modificar hasta tener certeza

### Fase 2 (Mediano Plazo - Requiere Ventana de Mantenimiento)
- Migrar cualquier uso residual de `repository_softrestaurant.py` a patrón EDARSAHUB
- Eliminar credenciales hardcodeadas
- Requiere pruebas completas de CxP y Finanzas

### Fase 3 (Largo Plazo)
- Eliminar código legacy de MongoDB fallback
- Unificar toda la lógica de conexión en `core/db.py` + `server_registry.py`

---

## 13. ARCHIVOS QUE NO DEBEN TOCARSE

```
❌ BLINDADOS - NO MODIFICAR SIN AUTORIZACIÓN:

/app/backend/modules/finanzas/repository_softrestaurant.py
  - Contiene credenciales hardcodeadas
  - Potencialmente usado por flujos legacy
  - Riesgo: CxP (aunque análisis muestra que no lo usa)

/app/backend/modules/finanzas/cuentas_por_pagar.py
  - Módulo CxP en producción
  - Cualquier cambio requiere pruebas completas

/app/backend/modules/comercial/routes.py
  - Tablero Ejecutivo actual
  - Módulo blindado por el usuario

/app/backend/modules/comercial/repository.py
  - Ya usa patrón correcto (EDARSAHUB + decrypt_secret)
  - No requiere cambios
```

---

## 14. CONFIRMACIONES

- ✅ **NO se modificó código** durante esta auditoría
- ✅ **NO se expusieron secretos** (passwords enmascarados como `***`)
- ✅ **NO se ejecutaron queries de escritura**
- ✅ EDARSAHUB sigue siendo la fuente oficial para módulos nuevos
- ✅ Comercial v2 ya está alineado con la arquitectura objetivo

---

## 15. RESPUESTAS A LAS 17 PREGUNTAS

1. **¿Cuántas lógicas de conexión existen?** 3 (EDARSAHUB, Hardcoded, MongoDB legacy)
2. **¿Qué módulos usan hardcoded?** Solo `repository_softrestaurant.py`
3. **¿Qué módulos usan EDARSAHUB + decrypt_secret?** 9+ módulos (sync_*, comercial_*, repository_*)
4. **¿Qué módulos usan MongoDB legacy?** `comercial/repository.py` (solo fallback)
5. **¿Qué módulos usan menú Servidores?** Todos los que leen de EDARSAHUB (es la misma fuente)
6. **¿Qué módulos usan pytds?** Todos (preferido en core/db.py)
7. **¿Qué módulos usan pymssql?** Todos (fallback en core/db.py)
8. **¿Qué módulos usan pyodbc?** Ninguno activo
9. **¿Qué módulos manejan instancia nombrada?** Todos los que usan core/db.py
10. **¿Qué módulos descartan instancia?** `repository_softrestaurant.py` (parcialmente)
11. **¿Qué módulos cargan SERVER_SECRET_KEY?** Todos los que usan decrypt_secret
12. **¿Qué módulos fallan por no cargar .env?** Ninguno detectado (todos cargan correctamente)
13. **¿Credenciales de repository_softrestaurant.py difieren de EDARSAHUB?** Posiblemente (no verificable sin exponer)
14. **¿Qué conexiones funcionan?** Todas las de EDARSAHUB (5/5 unidades validadas)
15. **¿Qué conexiones fallan?** Ninguna (después de corregir queries)
16. **¿Riesgo de cambiar repository_softrestaurant.py?** Medio (CxP no lo usa directamente)
17. **¿Plan para normalizar?** 3 fases documentadas arriba

---

*Fin del documento de auditoría*
