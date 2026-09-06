# EKS CAVAS 003 - Gate de auditoría canónica SQL

## Objetivo
Este gate impide crear o duplicar esquema de Cavas sin inspeccionar primero la SQL canónica real de EDARSAHUB.

## Alcance
- Cliente canónico / CRM.
- Unidad de negocio / empresa.
- Tablas Cava legacy existentes.
- Producto/catálogo e inventario relacionado.
- Catálogo extendido si existe.
- Configuraciones, zonas horarias, monedas y horarios operativos reutilizables.

## Regla
No se autoriza DDL de Cavas hasta que el resultado READ_ONLY_SQL determine qué entidades deben reutilizarse y cuáles, en su caso, deben convertirse en canónicas y atómicas.

## Resultado esperado
El resultado del Worker asociado a `CAVAS-BOS-V1-CANONICAL-AUDIT-01` es la evidencia vinculante para el siguiente slice de implementación.
