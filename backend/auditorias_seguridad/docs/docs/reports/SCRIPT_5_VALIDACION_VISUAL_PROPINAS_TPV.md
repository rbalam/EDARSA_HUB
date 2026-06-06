# Script 5 - Validación visual pendiente PropinasTPV

## Estado técnico

PropinasTPV fue migrado técnicamente a Corporate Filters.

## Validaciones técnicas cumplidas

- ✅ `CorporateFiltersProvider` integrado.
- ✅ `useCorporateFilters` integrado.
- ✅ Scope usado: `finanzas.propinas_tpv`.
- ✅ Fetch directo a `/api/servers` eliminado.
- ✅ Fetch directo a `/api/sucursales` eliminado.
- ✅ Endpoints propios de propinas conservados.
- ✅ Build frontend exitoso.
- ✅ Corporate Filters carga desde EDARSAHUB SQL.
- ✅ `remote_connections_required = false`.

## Validación visual requerida

Abrir en navegador:

```text
Finanzas → Propinas TPV
```

### Checklist visual

| # | Validación | OK/FALLA |
|---|------------|----------|
| 1 | Pantalla carga sin errores | |
| 2 | Selector de Unidad de Negocio muestra opciones | |
| 3 | Selector de Unidad de Negocio se puede cambiar | |
| 4 | Tablero de propinas carga datos | |
| 5 | No hay errores en consola del navegador | |
| 6 | No hay requests a `/api/servers` en Network tab | |
| 7 | No hay requests a `/api/sucursales` en Network tab | |

### Instrucciones para validar Network tab

1. Abrir DevTools (F12).
2. Ir a pestaña Network.
3. Filtrar por "servers" y "sucursales".
4. Verificar que no aparezcan requests a esos endpoints.

## Siguiente paso

Si validación visual pasa, marcar este archivo como COMPLETADO y proceder a migrar otro tablero.

Si falla algún punto, documentar error exacto y corregir.

## Firma validación

- Fecha validación visual: ________________
- Validado por: ________________
- Resultado: ________________
