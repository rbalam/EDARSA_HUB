# Migración FASE 3.2: Selector "Servidor" → "Unidad de Negocio"

**Fecha:** 2026-04-19  
**Módulo:** Compras  
**Estado:** COMPLETADO ✅

## Resumen

Se implementó el cambio de filtro visible de "Servidor" a "Unidad de Negocio" en el módulo de Compras, siguiendo las reglas de arquitectura donde **EDARSA HUB es el cerebro del sistema**.

## Cambios Implementados

### Backend

1. **Nuevo endpoint** `GET /api/unidades-negocio` (`server.py` líneas 1943-2040)
   - Filtra por RBAC/empresas_permitidas del usuario
   - Devuelve: `id`, `nombre`, `server_id` (interno), `system_type`, `sucursal_origen_id`
   - Ordena por nombre
   - Admin ve las 5 unidades, usuario restringido solo la suya

### Frontend

1. **Nuevo servicio** `/services/unidadesNegocioService.js`
   - `fetchUnidadesNegocio()`: Obtiene unidades según RBAC
   - `getServerIdFromUnidad()`: Traduce unidad → server_id
   - `getSucursalOrigenIdFromUnidad()`: Para MPRO

2. **Componente principal** `Compras.js`
   - Estado `selectedUnidad` reemplaza concepto de `selectedServer`
   - `useMemo` deriva `selectedServer` internamente desde unidad
   - Auto-selección cuando usuario tiene solo 1 unidad
   - Compatibilidad con componentes hijos mediante transformación

3. **Componentes actualizados**
   - `DashboardCompras`
   - `AutorizacionComprasTab`
   - `AnalisisCompras`
   - `AuditoriaOperativaTab`

## Validaciones Realizadas

| Test | Resultado |
|------|-----------|
| Admin ve 5 unidades | ✅ 130 MID, 130 QRO, CIENFUEGOS, LA ESTELAR, ORIGEN |
| Usuario restringido ve 1 unidad | ✅ CIENFUEGOS (auto-seleccionada y bloqueada) |
| Label cambiado | ✅ "Unidad de Negocio" visible en todos los tabs |
| server_id interno | ✅ No visible en UI, solo usado para llamadas API |
| RBAC backend | ✅ Endpoint filtra por empresas_permitidas |

## No Tocado

- [x] `.env` - Sin cambios
- [x] `DB_NAME` - Sin cambios  
- [x] `URI` - Sin cambios
- [x] Conexión principal - Sin cambios
- [x] RBAC base - Sin cambios
- [x] Otros módulos (Comercial, Operaciones, Finanzas) - Pendiente

## Hallazgo durante implementación

El endpoint `/api/servers/{server_id}/sucursales` devuelve vacío para MPRO aunque las sucursales existen en SQL y la configuración en `server_sucursales_config` es correcta. Esto parece ser un issue preexistente con el connection pooling. Las requisiciones directas al endpoint `/api/compras/pedidos-vigentes` funcionan correctamente cuando se pasa la sucursal correcta.

## Próximos Pasos

1. **P1**: Propagar cambio a Comercial, Operaciones, Finanzas
2. **P2**: Deprecar selector "Servidor" en configuración de sistema
3. **P2**: Investigar y corregir endpoint sucursales MPRO

## Screenshots

- Dashboard: Selector "Unidad de Negocio" visible
- Dropdown: Muestra las 5 unidades (ORIGEN, 130 QRO, etc.)
- Usuario restringido: Unidad auto-seleccionada y bloqueada
