# EDARSA — Inventarios / Operaciones / Compras — reglas obligatorias

Antes de tocar estos dominios leer:

- `docs/operacion/MEMORIA_ERRORES_CORREGIDOS_INVENTARIOS_COMPRAS_OPERACIONES.md`
- `docs/operacion/CONTRATOS_CANONICOS_INVENTARIOS_Y_AUDITORIA_COMPRAS.md`

## Invariantes

- SQL EDARSAHUB es fuente productiva.
- No Mongo productivo.
- No LIVE en reportes/auditorías.
- No hardcodes de sistemas/unidades/sucursales.
- Shared-server se resuelve desde configuración canónica.
- MPRO requiere scope de sucursal/unidad.
- SoftRestaurant no debe recibir filtro de sucursal ficticio.
- Snapshot físico es atómico.
- ACTIVE/REPLACED no debe ocultar último dato válido.
- Cantidad cero no elimina un SKU existente.
- Movimientos usan resolver/mapeo canónico.
- IDs no resolubles no se inventan.
- Presentación e insumo no son equivalentes sin conversión.
- Auditoría de Compras cruza fuentes canónicas existentes.
- RBAC obligatorio backend.
- SUPERADMIN >= ADMINISTRADOR.
- No crear menús/acciones sin permiso.
- No crear fuentes paralelas para resolver un bug.

## Antes del patch

Demostrar:

1. endpoint/ruta real;
2. tabla/vista real;
3. filtro real;
4. alcance unidad/sucursal/almacén;
5. sistema origen;
6. causa;
7. test de regresión.

## Bloqueo

Si falta evidencia, AUDITAR. No improvisar.
