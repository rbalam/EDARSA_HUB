# MATRIZ ADAPTERS SYNC COMPRAS / INVENTARIOS

## Regla

La sincronización no debe depender únicamente del `system_type`.

Debe resolver adapter por:

- ServidorID
- NombreServidor
- UnidadNegocio
- SystemType
- BaseDatosOrigen
- Esquema detectado
- Tablas disponibles
- Versión funcional del origen

## Matriz esperada inicial

| Servidor | Unidad | Sistema | Base compartida | Adapter recomendado | Observación |
|---|---|---|---|---|---|
| 130° MERIDA | 130MID | SOFTRESTAURANT_PRO | No | softrestaurant_pro_adapter | Validado con tablas compras, comprasmovtos, pedidos, ordenescompra, invfisico, movtosalmacen |
| CIENFUEGOS | CIENFUEGOS | SOFTRESTAURANT_PRO | No | softrestaurant_pro_adapter + validación por esquema | Puede tener diferencias de columnas/tablas |
| LA ESTELAR | ESTELAR | SOFTRESTAURANT_PRO | No | softrestaurant_pro_adapter + validación por esquema | Puede tener diferencias de columnas/tablas |
| ManagmentPro | ORIGEN | MPRO | Sí | mpro_adapter | Comparte base con 130QRO |
| ManagmentPro | 130QRO | MPRO | Sí | mpro_adapter | Comparte base con ORIGEN |
| MPRO TABLAJERIA | N/A | MPRO | Por validar | mpro_adapter o adapter específico | Validar esquema |
| Futuro sistema | N/A | OTRO | N/A | nuevo adapter | No contaminar EDARSAHUB |

## Decisión

No crear tablas EDARSAHUB con nombres de SoftRestaurant, MPRO ni futuros sistemas.

Cada adapter debe devolver datos canónicos para:

- Inventario_Almacenes
- Inventario_Existencias
- Inventario_Movimientos
- Inventario_MovimientosDetalle
- Compras_Pedidos
- Compras_PedidosDetalle
- Compras_Ordenes
- Compras_OrdenesDetalle
- Compras_Recepciones
- Compras_RecepcionesDetalle
- Compras_Inventarios_Fisicos_Sync
- Compras_Requisiciones_Sync

## Pendiente técnico

Antes de `dry_run=false` definitivo, validar esquema por servidor SoftRestaurant:

- 130° MERIDA
- CIENFUEGOS
- LA ESTELAR

y no asumir que los tres tienen exactamente las mismas columnas.
