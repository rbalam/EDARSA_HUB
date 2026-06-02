# MATRIZ NO-LIVE DASHBOARD EDARSAHUB

Generado: 2025-12-19

## Criterios

| Prioridad | Criterio | Accion |
|---|---|---|
| P0 | Endpoints/dashboard/reportes con live/Mongo/API externa | Remediar primero |
| P1 | Repositorios/servicios de modulos con live fuera de scheduler | Migrar a SQL sincronizado |
| P2 | Helpers/documentacion/configuracion no productiva | Documentar |
| PERMITIDO | scheduler/jobs/sync/scripts/tests/tools/adapters controlados | Mantener con logs |
| FALSO_POSITIVO | policy scanner o strings de busqueda | Ignorar |

## Hallazgos clasificados

| Prioridad | Archivo | Tipo | Accion recomendada |
|---|---|---|---|
| PERMITIDO | `backend/init_queries.py` | AsyncIOMotorClient | Script de inicializacion |
| PERMITIDO | `backend/migrar_a_sql.py` | Comentario pymongo | Script de migracion |
| P1 | `backend/modules/comercial/__init__.py` | AsyncIOMotorDatabase | Revisar si se usa en dashboard |
| P1 | `backend/modules/comercial/historical_kpis_repository.py` | AsyncIOMotorClient | **KPIs historicos - revisar uso** |
| PERMITIDO | `backend/modules/fase2_operativo/db_utils.py` | MongoClient | Utilidad fase2 operativo |
| PERMITIDO | `backend/modules/fase2_operativo/repositories/*` | Constantes ordenamiento | Sin conexion directa |
| PERMITIDO | `backend/modules/fase2_operativo/scripts/*` | AsyncIOMotorClient/MongoClient | Scripts de inicializacion |
| P1 | `backend/modules/rh/__init__.py` | AsyncIOMotorDatabase | Revisar si se usa en dashboard |
| P1 | `backend/modules/configuracion/routes/config_asignaciones_routes.py` | AsyncIOMotorClient | **Endpoint config - revisar** |
| P1 | `backend/modules/catalogos/__init__.py` | AsyncIOMotorDatabase | Revisar dependencia |
| P1 | `backend/modules/auth/__init__.py` | AsyncIOMotorDatabase | Auth module - revisar |
| P1 | `backend/modules/finanzas/repository_cuadres_z.py` | MongoClient | **Cuadres Z - revisar** |
| P1 | `backend/modules/finanzas/propinas_tpv/*.py` | AsyncIOMotorDatabase | **Propinas TPV - modulo activo** |
| P1 | `backend/modules/manuales_operativos/*.py` | AsyncIOMotorDatabase | Manuales operativos |
| P1 | `backend/modules/compras/__init__.py` | AsyncIOMotorDatabase | Modulo compras |
| PERMITIDO | `backend/scripts/*.py` | AsyncIOMotorClient/MongoClient | Scripts de carga/migracion |
| PERMITIDO | `backend/tests/*.py` | AsyncIOMotorClient | Tests |

## Resumen

```text
P0=0
P1=12
P2=0
PERMITIDO=10+
FALSO_POSITIVO=0
```

## Nota Importante

**El modulo `/api/comercial/inteligencia/*` (Fase 1) ya esta completamente migrado a SQL Server.**

Los archivos P1 listados son de modulos legacy que aun usan MongoDB para:
- Catalogos
- Auth (en transicion)
- Propinas TPV
- Manuales operativos
- Compras

Estos modulos estan **fuera del alcance de Inteligencia Comercial Fase 1** pero deben ser migrados progresivamente.

## Fuente Oficial Inteligencia Comercial

Solo usar:
- `/api/comercial/inteligencia/*` (rutas SQL-first)
- `dbo.Comercial_Inteligencia_VW_KPIsEjecutivos`
- `dbo.Comercial_Ventas_Dia_Abiertas_v2`
