# Resolver Corporativo Global EDARSAHUB

Fecha: Thu Jun  4 19:00:02 UTC 2026

## Objetivo

Crear un resolver corporativo global para evitar que cada módulo interprete por separado nombres, códigos o aliases de:

- Empresa
- Unidad de Negocio
- Sucursal
- Almacén
- Proveedor
- Producto
- Servidor
- system_type

## Regla

Los repositories deben consultar usando IDs canónicos.

Los endpoints pueden recibir valores flexibles por compatibilidad, pero antes de consultar datos deben resolverlos usando este helper central.

## Prohibido

- Hardcodear CIENFUEGOS, ESTELAR, 130MID, ORIGEN, etc. dentro de repositories.
- Crear resolvers por módulo.
- Crear listas locales de system_type.
- Interpretar unidad/empresa/sucursal dentro de cada query.
Backups en: /app/backups/corporate_identity_resolver_global_20260604_190002
