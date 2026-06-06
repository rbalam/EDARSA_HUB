# P2-12 — Validación /api/unidades-negocio

## Estado

CERRADO.

## Resultado

El endpoint `/api/unidades-negocio` retorna correctamente 5 unidades desde EDARSAHUB SQL.

## Unidades validadas

| Código | Nombre | Sistema | Servidor |
|---|---|---|---|
| 130MID | 130° MERIDA | SoftRestaurant | 130° MERIDA |
| CIENFUEGOS | CIENFUEGOS | SoftRestaurant | CIENFUEGOS |
| ESTELAR | LA ESTELAR | SoftRestaurant | LA ESTELAR |
| 130QRO | 130° QUERETARO | MPRO | ManagmentPro |
| ORIGEN | ORIGEN | MPRO | ManagmentPro |

## Dictamen

La relación canónica queda confirmada:

`Unidades_Negocio.server_id → Servidores_Conexiones.id`

El issue de array vacío no está activo.
