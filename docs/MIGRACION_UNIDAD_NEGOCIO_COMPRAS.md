# Migración FASE 3.2: Selector "Servidor" → "Unidad de Negocio"

**Fecha:** 2026-04-19  
**Módulo:** Compras  
**Estado:** COMPLETADO ✅

## Resumen

Se eliminó la dependencia funcional del frontend hacia `fetchServersOperativos` en el módulo de Compras y se reemplazó por un modelo basado en "Unidad de Negocio", donde **EDARSA HUB es el cerebro del sistema**.

## Flujo Anterior (ELIMINADO en Compras)

```
Frontend → fetchServersOperativos() → Muestra "Servidor" → Envía server_id
```

## Flujo Nuevo (IMPLEMENTADO)

```
Frontend → fetchUnidadesNegocio() → Muestra "Unidad de Negocio" → Envía unidad_id
Backend → Valida RBAC → Traduce unidad → server_id → Ejecuta query
```

## Cambios Implementados

### Backend

**Endpoint** `GET /api/unidades-negocio` (`server.py` líneas 1943-2040)

```json
// Respuesta
[
  {
    "id": "uuid-empresa",
    "codigo": "ORIGEN",
    "nombre": "ORIGEN",
    "server_id": "uuid-interno",  // No visible en UI
    "system_type": "MPRO",
    "sucursal_origen_id": "0023"
  }
]
```

- Filtra por `empresas_permitidas` del usuario (RBAC)
- `server_id` es dato interno, nunca expuesto al usuario
- Ordena por nombre

### Frontend

**Servicio** `/services/unidadesNegocioService.js`
- `fetchUnidadesNegocio()`: Obtiene unidades según RBAC
- `getServerIdFromUnidad()`: Traduce unidad → server_id internamente
- `getSucursalOrigenIdFromUnidad()`: Para sistemas MPRO

**Componente** `Compras.js`
- Reemplazado `fetchServersOperativos` por `fetchUnidadesNegocio`
- Label cambiado de "Servidor" a "Unidad de Negocio"
- Auto-selección cuando usuario tiene solo 1 unidad
- `selectedServer` derivado internamente via `useMemo`

## Validaciones Realizadas

| Test | Resultado |
|------|-----------|
| Admin ve 5 unidades | ✅ 130 MID, 130 QRO, CIENFUEGOS, LA ESTELAR, ORIGEN |
| Usuario restringido ve 1 unidad | ✅ CIENFUEGOS auto-seleccionada y bloqueada |
| Label "Unidad de Negocio" | ✅ Visible en Dashboard, Autorización, Análisis, Auditoría |
| server_id interno | ✅ No visible en UI, solo usado internamente |
| RBAC backend | ✅ Endpoint filtra por empresas_permitidas |
| Sucursales funcionan | ✅ Se cargan al seleccionar unidad |
| Íconos Building2 | ✅ Representa empresa, no servidor técnico |

## Capturas de Pantalla

1. **Admin**: Dropdown muestra 5 unidades de negocio (ORIGEN, 130 QRO, etc.)
2. **Usuario restringido**: Unidad auto-seleccionada como texto fijo (CIENFUEGOS)
3. **Auditoría**: Selector "Unidad de Negocio" funcional

## No Tocado

- [x] `.env` - Sin cambios
- [x] `DB_NAME` - Sin cambios
- [x] `URI` - Sin cambios
- [x] Conexión principal - Sin cambios
- [x] RBAC base - Sin cambios
- [x] Módulo técnico "Servidores" - Sin cambios
- [x] Otros módulos (Comercial, Operaciones, Finanzas) - Pendiente migración

## Módulos que aún usan fetchServersOperativos (FUERA DE ALCANCE)

- `Comercial.js`
- `Reportes.js`
- `ExploradorBD.js`
- `CatalogoConsultas.js`

Estos se migrarán en fases posteriores.

## Próximos Pasos

1. **P1**: Propagar cambio a Comercial, Operaciones, Finanzas
2. **P2**: Deprecar `fetchServersOperativos` completamente
3. **P2**: Eliminar selector "Servidor" de UI de administración en módulos de negocio
