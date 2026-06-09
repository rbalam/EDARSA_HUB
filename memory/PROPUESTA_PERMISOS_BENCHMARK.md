# PROPUESTA — Permisos RBAC de Benchmark (NO SEMBRADO)
Fecha: 2026-06-09 · Decisión usuario: **2b = solo proponer, no sembrar todavía**
Régimen: SQL-First, sin tablas nuevas (los permisos son FILAS en tablas RBAC ya existentes).

## Cómo se materializarían (cuando se autorice sembrar)
El RBAC ya modela permisos como `MODULO_ACCION`:
- `Usuario_Modulos` (módulos, soportan jerarquía con punto: `crm.clientes`)
- `Usuario_Acciones` (16 acciones; usaremos las EXISTENTES: `VER`, `EXPORTAR`)
- `Usuario_PermisosRolModulo` (asigna rol → módulo → acción, con flags
  `RestriccionPropietario`/`RestriccionSucursal` que ya existen)

> Por tanto NO se crean tablas. Solo se insertarían: 1 módulo nuevo
> `COMERCIAL_BENCHMARK` (+ submódulos por punto) y filas de asignación a roles.

## Listado propuesto (código = MODULO_ACCION)

### Acceso general (ya cubierto por módulo existente `INTELIGENCIA_COMERCIAL`)
| Código propuesto | Equivalente existente | Notas |
|---|---|---|
| `INTELIGENCIA_COMERCIAL_VER` | ✅ existe (módulo INTELIGENCIA_COMERCIAL) | Reutilizar |
| `INTELIGENCIA_COMERCIAL_EXPORTAR` | derivable (acción EXPORTAR existe) | Sembrar fila |

### Benchmark interno (grupo) — submódulos de `COMERCIAL_BENCHMARK`
| Código | Acción base | Descripción |
|---|---|---|
| `COMERCIAL_BENCHMARK.GRUPO_VER` | VER | Ver benchmark interno del grupo (anónimo) |
| `COMERCIAL_BENCHMARK.GRUPO_NOMBRES_VER` | VER | Ver nombres reales de unidades hermanas |
| `COMERCIAL_BENCHMARK.GRUPO_TICKET_VER` | VER | Ver ticket promedio comparado |
| `COMERCIAL_BENCHMARK.GRUPO_MARGEN_VER` | VER | Ver costo/margen comparado |
| `COMERCIAL_BENCHMARK.GRUPO_EXPORTAR` | EXPORTAR | Exportar benchmark de grupo |

### Benchmark sectorial (DIFERIDO — decisión 5a)
| Código | Acción | Estado |
|---|---|---|
| `COMERCIAL_BENCHMARK.SECTOR_VER` | VER | DIFERIDO (sin datos externos hoy) |
| `COMERCIAL_BENCHMARK.SECTOR_AGREGADO_VER` | VER | DIFERIDO |
| `COMERCIAL_BENCHMARK.SECTOR_PRODUCTO_VER` | VER | DIFERIDO |
| `COMERCIAL_BENCHMARK.SECTOR_CATEGORIA_VER` | VER | DIFERIDO |
| `COMERCIAL_BENCHMARK.SECTOR_MARGEN_VER` | VER | DIFERIDO |
| `COMERCIAL_BENCHMARK.SECTOR_EXPORTAR` | EXPORTAR | DIFERIDO |

### Prohibidos por defecto (solo con autorización contractual documentada)
- `COMERCIAL_BENCHMARK.SECTOR_NOMBRES_EMPRESAS_VER`
- `COMERCIAL_BENCHMARK.SECTOR_NOMBRES_UNIDADES_VER`
- `COMERCIAL_BENCHMARK.SECTOR_TICKET_TERCEROS_VER`
- `COMERCIAL_BENCHMARK.SECTOR_VENDEDORES_TERCEROS_VER`
- `COMERCIAL_BENCHMARK.SECTOR_DATOS_TECNICOS_TERCEROS_VER`

## Mapa propuesto rol → nivel de confidencialidad (mientras NO se siembran permisos)
Hoy el `AnonymizerService` deriva el nivel del **rol canónico** (sin permisos sembrados):

| Rol canónico | Nivel AnonymizerService | Nombres propios | Nombres grupo | Técnicos |
|---|---|---|---|---|
| SUPERADMIN | COMPLETO | ✅ | ✅ | ✅ |
| ADMIN / ADMIN_COMERCIAL / DIRECCION / CRM_ADMIN | GRUPO_NOMBRES | ✅ | ✅ | ⛔ |
| GERENTE / GERENTE_OPS / GERENTE_UNIDAD / SUPERVISOR / AUDITOR | PROPIO_NOMBRES | ✅ | ⛔ (anónimo) | ⛔ |
| ANALISTA_COMERCIAL / VISOR_COMERCIAL / VISOR / USUARIO / resto | ANONIMO | ⛔ | ⛔ | ⛔ |
| Usuario Portal externo (EsUsuarioPortal=1) | AGREGADO | ⛔ | ⛔ | ⛔ |

> Cuando se autorice sembrar permisos, `AnonymizerService.build_context` migrará a
> consultar `COMERCIAL_BENCHMARK.GRUPO_NOMBRES_VER` etc. en lugar del rol, sin
> cambiar la firma ni a los consumidores (endpoints).
