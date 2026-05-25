# BUG FIX: Competidores - Campos No Guardados + Mejoras Redes Sociales

## Fecha: 25 Mayo 2026
## Autor: Agente E1

## Problema Reportado
El usuario reportó que al editar un competidor en el módulo "Pricing IA":
1. "Ubicación de Referencia" no se guardaba
2. "Nivel de Precio" no se guardaba
3. Solicitó agregar campos para redes sociales (Instagram, Facebook, TripAdvisor, OpenTable)

## Diagnóstico
El frontend usaba nombres de campos incorrectos que no coincidían con el backend:

| Frontend (incorrecto) | Backend (correcto) |
|-----------------------|-------------------|
| `tipo_negocio` | `tipo_restaurante` |
| `nivel_precio_percibido` | `segmento_precio` |
| `ubicacion_referencia` | `zona_comercial` |

Además, faltaban campos para Facebook y Notas en el modelo de Competidores.

## Solución Implementada

### 1. Backend - Schema (`pricing_schemas.py`)
- Agregado `url_facebook` a `CompetidorBase`
- Agregado `notas` a `CompetidorBase`
- Agregado `url_facebook` y `notas` a `CompetidorUpdate`

### 2. Backend - Service (`competidores_service.py`)
- Actualizado `_row_to_competidor()` para incluir `url_facebook` y `notas`
- Actualizadas queries SELECT para incluir nuevas columnas
- Actualizado INSERT para manejar `UrlFacebook` y `Notas`
- Actualizado UPDATE para manejar nuevos campos

### 3. Base de Datos SQL Server
- Ejecutado DDL para agregar columnas:
  - `UrlFacebook NVARCHAR(500) NULL`
  - `Notas NVARCHAR(1000) NULL`
- Script: `/app/backend/scripts/ddl_competidores_nuevos_campos.py`

### 4. Frontend - `PricingIA.jsx`
- Corregido mapeo de campos en `CompetidorModal`:
  - `tipo_negocio` → `tipo_restaurante`
  - `nivel_precio_percibido` → `segmento_precio`
  - `ubicacion_referencia` → `zona_comercial`
- Agregada sección "Redes Sociales y Monitoreo" con campos:
  - Google Maps
  - Instagram
  - Facebook (NUEVO)
  - TripAdvisor
  - OpenTable
- Ampliado modal de 500px a 700px para mejor UX
- Corregidos badges en tarjetas de competidores para usar nombres correctos

## Archivos Modificados
1. `/app/backend/modules/comercial/services/pricing_schemas.py`
2. `/app/backend/modules/comercial/services/competidores_service.py`
3. `/app/frontend/src/pages/comercial/PricingIA.jsx`

## Archivos Creados
1. `/app/backend/scripts/ddl_competidores_nuevos_campos.py`

## Pruebas Realizadas
1. **curl PUT** - Actualización de competidor con nuevos campos: ✅ OK
2. **curl GET** - Verificación de datos guardados: ✅ OK
3. **Screenshot** - Modal con todos los campos visibles: ✅ OK

## Estado
✅ BUG CORREGIDO
✅ MEJORA IMPLEMENTADA (Redes sociales)
