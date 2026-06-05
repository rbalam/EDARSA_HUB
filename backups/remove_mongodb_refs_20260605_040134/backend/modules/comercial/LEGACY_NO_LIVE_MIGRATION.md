# Comercial Legacy - Migracion No-Live

## Estado

Este modulo contiene componentes legacy que pueden consultar fuentes externas, MongoDB, adaptadores MPRO/SoftRestaurant o configuracion de servidores.

## Regla

Ningun dashboard ejecutivo nuevo debe usar estos archivos como fuente directa:

- `backend/modules/comercial/routes.py`
- `backend/modules/comercial/service.py`
- `backend/modules/comercial/repository.py`

## Fuente oficial para Inteligencia Comercial

Usar exclusivamente:

- `/api/comercial/inteligencia/*`
- `dbo.Comercial_Inteligencia_VW_KPIsEjecutivos`
- `dbo.Comercial_Ventas_Dia_Abiertas_v2`
- `dbo.Sync_PAX_Detalle`
- `dbo.Sync_Sales`
- `dbo.Unidades_Negocio`

## Permitido

Las conexiones live solo se permiten dentro de:

- scheduler
- jobs
- procesos sync
- adapters controlados

## Prohibido

- Consultas live desde dashboards.
- MongoDB como fuente comercial.
- APIs SoftRestaurant/MPRO desde endpoints ejecutivos.
