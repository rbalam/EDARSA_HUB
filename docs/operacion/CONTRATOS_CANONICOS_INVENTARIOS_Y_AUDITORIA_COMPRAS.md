# EDARSAHUB — Contratos canónicos de Inventarios y Auditoría de Compras

## Inventarios físicos

Fuente publicada:
- `dbo.Compras_Inventarios_Fisicos_Sync`
- `dbo.Compras_Inventarios_Fisicos_Detalle_Sync`

Lectura:
- preferir ACTIVE;
- permitir recuperación REPLACED cuando corresponde;
- deduplicar por identidad física real.

## Alcance

Single-tenant:
- server puede ser suficiente.

Shared-server:
- requiere sucursal/unidad canónica.

Nunca decidirlo por strings hardcodeados de sistema.

## Movimientos

Fuente:
- `dbo.Inventario_Movimientos`
- `dbo.Inventario_MovimientosDetalle`
- catálogo `dbo.Inventario_TipoMovimiento`.

No usar queries POS LIVE para consumidores de reportes.

## Auditoría de Compras

Cruza fuentes canónicas; no las reemplaza.

Inventario inicial/final:
fuente física canónica.

Entradas/salidas:
movimientos canónicos.

Pedidos/recepciones:
Compras canónico.

Ventas/consumo:
dominio Comercial canónico según regla vigente.

## Consistencia

Para la misma unidad, periodo, almacén y filtro, dos reportes no deben
recalcular fuentes distintas y producir dos verdades.

## Atomicidad del snapshot

La fotografía nueva solo sustituye a la anterior después de completar:

1. lectura headers;
2. lectura detalles;
3. validación de correspondencia;
4. persistencia completa;
5. commit.

Cualquier fallo anterior conserva el snapshot previo.

## Presentaciones

Antes de comparar cantidades:
resolver unidad base y factor de conversión.

## RBAC

Backend authoritative.

Frontend solo refleja permisos efectivos.

## NO-LIVE

LIVE pertenece únicamente a jobs/sync autorizados.

No pertenece a dashboards, auditorías ni análisis de usuario.
