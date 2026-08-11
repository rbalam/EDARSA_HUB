# Auditoría de clave compuesta servidor-sucursal-unidad

## Objetivo

Determinar si la atribución comercial requiere una clave compuesta.

## Contrato de la fuente

- Servidor: `server_id`
- Unidad: `unidad_negocio_id`
- Sucursal: `sucursal_id`
- Sistema: `sistema_origen`

## Mapeos detectados

- `1B230A06-FFAF-4C70-BD27-B1BE3579DEA6` → `130QRO` mediante `dbo.Unidades_Negocio`
- `1B230A06-FFAF-4C70-BD27-B1BE3579DEA6` → `ORIGEN` mediante `dbo.Sistema_EmpresasServidores, dbo.Sistema_ServidorSucursalesConfig, dbo.Unidades_Negocio`
- `6D053C22-523E-48C0-B72B-96081E2D781B` → `CIENFUEGOS` mediante `dbo.Sistema_EmpresasServidores, dbo.Unidades_Negocio`
- `A5547321-1139-4D2B-9D53-182CA737B6B6` → `130MID` mediante `dbo.Unidades_Negocio`
- `A5FF0E25-F029-43DB-B634-D4AC814C904F` → `ESTELAR` mediante `dbo.Unidades_Negocio`

## Servidores compartidos

- `1B230A06-FFAF-4C70-BD27-B1BE3579DEA6` → `130QRO, ORIGEN`

## Dictamen

- Unidades mapeadas: `130MID, 130QRO, CIENFUEGOS, ESTELAR, ORIGEN`
- GUID sin mapear: `NONE`
- Unidades ausentes: `NONE`
- Fuente tiene discriminador: `True`
- Estado: `COMPOSITE_KEY_REQUIRED_AND_AVAILABLE`

## Resultado

- Estado: `COMPOSITE_KEY_REQUIRED_AND_AVAILABLE`
- SQL de escritura: `0`
- Código modificado: `0`
- Producción modificada: `0`
