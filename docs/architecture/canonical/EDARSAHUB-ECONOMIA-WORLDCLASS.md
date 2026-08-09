# EDARSAHUB Economia WorldClass

## Estado

Diseño V1.0 del núcleo canónico de series económicas.

La auditoría de 550 tablas EDARSAHUB confirmó:

- `STRICT_MACRO_TIMESERIES_CANDIDATES=0`
- no existe una fuente canónica actual de series macroeconómicas;
- inflación, PIB, desempleo, tasas de interés y energía tienen gap estructural;
- las columnas de `TipoCambio` existentes son datos transaccionales y no constituyen una serie macroeconómica FX.

## Principios

1. SQL-First.
2. MongoDB prohibido como fuente.
3. Dashboards sin conexión LIVE.
4. Una sola fuente económica canónica.
5. Indicadores nuevos son datos/configuración y no cambios de schema.
6. Reutilizar catálogos y plataforma existentes.
7. No almacenar secretos en tablas Economía.
8. RBAC obligatorio para toda funcionalidad Economía.
9. Histórico/versionado de revisiones oficiales.
10. No sobrescribir observaciones anteriores cuando un proveedor revise un dato.

## Reutilización

Se reutilizan:

- `dbo.Proveedor_Monedas`
- `dbo.Sistema_Empresas`
- `dbo.Unidades_Negocio`
- `dbo.Servidores_Conexiones`
- `dbo.Sys_Scheduler_Jobs`
- `dbo.Sys_Scheduler_JobConfig`
- `dbo.Sistema_RBAC_Permisos`
- `dbo.Sistema_RBAC_Roles`
- `dbo.Sistema_RBAC_RolesPermisos`

## Núcleo nuevo

El diseño agrega:

- `Economia_Paises`
- `Economia_Proveedores`
- `Economia_CategoriasIndicador`
- `Economia_Series`
- `Economia_Valores`
- `Economia_ContextoOperativo`

## Indicadores

El schema debe admitir, sin nuevas columnas:

- INPC
- inflación subyacente
- inflación sectorial
- CPI
- PPI / INPP
- FX
- tasas de interés
- salarios
- PIB / actividad económica
- desempleo
- energía
- cualquier indicador futuro compatible con el modelo de serie temporal.

## FX

El tipo de cambio de una compra, venta o asiento es un valor transaccional aplicado.

Una serie FX macroeconómica es una observación histórica publicada por una fuente económica.

No son la misma fuente de verdad.

## RBAC

Economía no podrá quedar disponible únicamente por rol ADMIN.

Debe utilizar permisos explícitos del RBAC canónico.

Capacidades previstas:

- leer indicadores;
- leer series;
- administrar series;
- administrar proveedores;
- sincronizar datos;
- ejecutar backfill;
- configurar contexto económico;
- exportar información;
- administrar configuración.

Los códigos exactos se incorporarán usando las convenciones reales de `Sistema_RBAC_*`; no se hardcodearán IDs.

## Scheduler

No se crea scheduler paralelo.

Los jobs de Economía deberán registrarse en el scheduler central.

Los proveedores externos deberán configurarse por catálogo/conexión, con secretos administrados por la infraestructura existente.

## Motor de Proyección de Ventas

Economía WorldClass es una fuente potencial de variables explicativas para el futuro Motor de Proyección de Ventas con objetivo de error aproximado de ±5%.

El modelo de forecast no debe depender obligatoriamente de todos los indicadores económicos. Cada variable debe demostrar valor predictivo mediante backtesting.

## Fechas especiales

Las fechas especiales y periodos especiales son otro conjunto de variables para el motor de proyección y para comparativos ejecutivos.

No deben hardcodearse por país.
