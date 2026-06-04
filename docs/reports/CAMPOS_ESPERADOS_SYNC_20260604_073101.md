# CAMPOS ESPERADOS EN TABLAS DE SINCRONIZACIÓN

Extraídos de: `/app/backend/modules/compras/sync_service.py`

## Inventario_Movimientos (Encabezado)
| Campo | Requerido | Descripción |
|-------|-----------|-------------|
| ServerID | ✅ | FK servidor origen |
| OrigenSistema | ✅ | 'SOFTRESTAURANT' / 'MPRO' |
| DocumentoID | ✅ | ID documento en origen |
| Folio | - | Número folio |
| TipoMovimiento | - | Tipo de movimiento |
| FechaMovimiento | - | Fecha del movimiento |
| AlmacenOrigenID | - | ID almacén origen |
| AlmacenDestinoID | - | ID almacén destino |
| Observaciones | - | Notas |
| UsuarioID | - | Usuario que creó |
| FechaSync | ✅ | Timestamp sincronización |

## Inventario_MovimientosDetalle
| Campo | Requerido | Descripción |
|-------|-----------|-------------|
| MovimientoID | ✅ | FK a Inventario_Movimientos |
| ServerID | ✅ | FK servidor |
| OrigenSistema | ✅ | Sistema origen |
| ProductoID | ✅ | ID producto |
| CodigoProducto | - | Código SKU |
| Cantidad | - | Cantidad movida |
| CostoUnitario | - | Costo por unidad |
| Lote | - | Número de lote |
| FechaCaducidad | - | Fecha expiración |
| FechaSync | ✅ | Timestamp |

## Compras_Pedidos (Encabezado)
| Campo | Requerido | Descripción |
|-------|-----------|-------------|
| ServerID | ✅ | FK servidor |
| OrigenSistema | ✅ | Sistema origen |
| PedidoID | ✅ | ID pedido en origen |
| Folio | - | Número folio |
| FechaPedido | - | Fecha pedido |
| ProveedorID | - | ID proveedor |
| SucursalID | - | ID sucursal |
| Estatus | - | Estado del pedido |
| Total | - | Monto total |
| FechaSync | ✅ | Timestamp |

## Compras_PedidosDetalle
| Campo | Requerido | Descripción |
|-------|-----------|-------------|
| PedidoID | ✅ | FK a Compras_Pedidos |
| ServerID | ✅ | FK servidor |
| OrigenSistema | ✅ | Sistema origen |
| ProductoID | ✅ | ID producto |
| CodigoProducto | - | Código SKU |
| Cantidad | - | Cantidad pedida |
| PrecioUnitario | - | Precio por unidad |
| Subtotal | - | Subtotal línea |
| FechaSync | ✅ | Timestamp |

## Compras_Ordenes (Encabezado)
| Campo | Requerido | Descripción |
|-------|-----------|-------------|
| ServerID | ✅ | FK servidor |
| OrigenSistema | ✅ | Sistema origen |
| OrdenID | ✅ | ID orden en origen |
| Folio | - | Número folio |
| FechaOrden | - | Fecha orden |
| ProveedorID | - | ID proveedor |
| SucursalID | - | ID sucursal |
| Estatus | - | Estado |
| Total | - | Monto total |
| FechaSync | ✅ | Timestamp |

## Compras_OrdenesDetalle
| Campo | Requerido | Descripción |
|-------|-----------|-------------|
| OrdenID | ✅ | FK a Compras_Ordenes |
| ServerID | ✅ | FK servidor |
| OrigenSistema | ✅ | Sistema origen |
| ProductoID | ✅ | ID producto |
| CodigoProducto | - | Código SKU |
| Cantidad | - | Cantidad ordenada |
| PrecioUnitario | - | Precio |
| Subtotal | - | Subtotal |
| FechaSync | ✅ | Timestamp |

## Compras_Recepciones (Encabezado)
| Campo | Requerido | Descripción |
|-------|-----------|-------------|
| ServerID | ✅ | FK servidor |
| OrigenSistema | ✅ | Sistema origen |
| RecepcionID | ✅ | ID recepción en origen |
| Folio | - | Número folio |
| FechaRecepcion | - | Fecha recepción |
| ProveedorID | - | ID proveedor |
| OrdenCompraID | - | FK orden de compra |
| SucursalID | - | ID sucursal |
| Estatus | - | Estado |
| Total | - | Monto total |
| FechaSync | ✅ | Timestamp |

## Compras_RecepcionesDetalle
| Campo | Requerido | Descripción |
|-------|-----------|-------------|
| RecepcionID | ✅ | FK a Compras_Recepciones |
| ServerID | ✅ | FK servidor |
| OrigenSistema | ✅ | Sistema origen |
| ProductoID | ✅ | ID producto |
| CodigoProducto | - | Código SKU |
| CantidadRecibida | - | Cantidad recibida |
| PrecioUnitario | - | Precio |
| Subtotal | - | Subtotal |
| Lote | - | Número lote |
| FechaCaducidad | - | Fecha expiración |
| FechaSync | ✅ | Timestamp |

---

## Llaves Naturales Compuestas (para MERGE)

| Tabla | Llave Natural |
|-------|---------------|
| Inventario_Movimientos | ServerID + OrigenSistema + DocumentoID |
| Inventario_MovimientosDetalle | MovimientoID + ServerID + OrigenSistema + ProductoID |
| Compras_Pedidos | ServerID + OrigenSistema + PedidoID |
| Compras_PedidosDetalle | PedidoID + ServerID + OrigenSistema + ProductoID |
| Compras_Ordenes | ServerID + OrigenSistema + OrdenID |
| Compras_OrdenesDetalle | OrdenID + ServerID + OrigenSistema + ProductoID |
| Compras_Recepciones | ServerID + OrigenSistema + RecepcionID |
| Compras_RecepcionesDetalle | RecepcionID + ServerID + OrigenSistema + ProductoID |
