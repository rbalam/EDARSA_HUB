# INCIDENTE: EDARSAHUB SQL Desaparecido del Menú de Servidores

**Fecha**: 2026-05-20  
**Estado**: DIAGNÓSTICO COMPLETADO  
**Severidad**: CRÍTICA  

---

## RESUMEN EJECUTIVO

EDARSAHUB SQL **SÍ EXISTE** en la base de datos `Servidores_Conexiones` con `activo=True` y `visible_en_listado=True`, pero está siendo **EXCLUIDO INTENCIONALMENTE** por la lógica del backend.

---

## CAUSA RAÍZ

### Código Responsable

**Archivo**: `/app/backend/server.py`  
**Línea**: 1222-1246  
**Endpoint**: `GET /api/servers`

```python
@api_router.get("/servers", response_model=List[Server])
async def get_servers(current_user: Dict = Depends(get_current_user)):
    servers = await registry_list_servers(
        ...
        exclude_core=True,  # <-- CAUSA RAÍZ
        ...
    )
```

### Filtro SQL Aplicado

**Archivo**: `/app/backend/core/server_registry.py`  
**Función**: `_get_servers_from_sql`

Cuando `exclude_core=True`, se aplica:
```sql
WHERE (tipo_conexion != 'CORE' OR tipo_conexion IS NULL)
```

Esto **EXCLUYE** a EDARSA HUB porque su `tipo_conexion = 'CORE'`.

---

## ESTADO DEL REGISTRO EN BD

### Registro Activo (el que debería aparecer)

| Campo | Valor |
|-------|-------|
| id | `f8a9049a-96e8-4210-84ae-595ffa2822fa` |
| nombre | EDARSA HUB |
| system_type | **EDARSA_HUB** |
| tipo_conexion | **CORE** |
| host | 54.39.104.176 |
| port | 1433 |
| database_name | EDARSAHUB |
| username | HRLectura |
| **activo** | **True** ✅ |
| **visible_en_operaciones** | **True** ✅ |
| **visible_en_listado** | **True** ✅ |

### Registro Duplicado Inactivo

| Campo | Valor |
|-------|-------|
| id | `bea40259-35f1-4693-bda2-d2d10e13e56a` |
| nombre | EDARSA HUB |
| system_type | Otro |
| tipo_conexion | CORE |
| activo | **False** |
| visible_en_listado | **False** |

---

## HIPÓTESIS VALIDADAS

| # | Hipótesis | Resultado |
|---|-----------|-----------|
| 1 | Filtrado por activo=0 | ❌ No es el problema (activo=True) |
| 2 | Filtrado por visible_en_operaciones=0 | ❌ No es el problema (visible=True) |
| 3 | Filtrado por visible_en_listado=0 | ❌ No es el problema (visible=True) |
| 4 | system_type no mapeado | ❌ No es el problema |
| 5 | **tipo_conexion='CORE' excluido** | ✅ **CONFIRMADO** |
| 6 | Registro eliminado | ❌ No, sí existe |
| 7 | MongoDB como fuente | ❌ No, usa SQL |
| 8 | Filtro por familia POS | ❌ No aplica |

---

## ARCHIVOS INVOLUCRADOS

### Backend
- `/app/backend/server.py` (línea 1222-1246) - Endpoint GET /api/servers
- `/app/backend/core/server_registry.py` - Función `_get_servers_from_sql` y `list_servers`

### Frontend
- `/app/frontend/src/pages/Servidores.js` (línea 662) - Llama a `api.get('/servers')`

---

## PLAN DE CORRECCIÓN

### Opción A: Agregar Parámetro `include_core` al Endpoint

Modificar el endpoint para aceptar un query parameter opcional:

```python
@api_router.get("/servers", response_model=List[Server])
async def get_servers(
    current_user: Dict = Depends(get_current_user),
    include_core: bool = False  # Nuevo parámetro
):
    servers = await registry_list_servers(
        ...
        exclude_core=not include_core,  # Invertir la lógica
        ...
    )
```

### Opción B: Cambiar Lógica por Defecto (RECOMENDADO)

Cambiar `exclude_core=True` a `exclude_core=False` en el endpoint principal para que EDARSAHUB siempre aparezca:

```python
exclude_core=False  # Ahora incluye servidores CORE
```

### Opción C: Crear Endpoint Separado

Crear un endpoint `/api/servers/all` que incluya servidores CORE.

---

## RIESGOS

| Cambio | Riesgo |
|--------|--------|
| Cambiar `exclude_core=False` | BAJO - Solo agrega EDARSAHUB a la lista |
| Otros servidores | NINGUNO - No se afectan |
| Secretos | NINGUNO - Se enmascaran con `mask_secrets=True` |

---

## RECOMENDACIÓN

**Proceder con Opción B**: Cambiar `exclude_core=True` a `exclude_core=False` en el endpoint `GET /api/servers`.

Esto permitirá que EDARSAHUB aparezca en el menú de servidores sin afectar otros servidores ni exponer secretos.

---

*Documento generado: 2026-05-20 04:10 UTC*
