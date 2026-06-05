"""
Adapter SOFTRESTAURANT_PRO → EDARSAHUB SQL

Este archivo contiene únicamente queries de extracción del origen SoftRestaurant PRO.
El destino SIEMPRE debe ser el modelo canónico EDARSAHUB.

MAPEO ORIGEN → DESTINO:
========================
| Tabla Origen SR      | Tabla Destino EDARSAHUB              |
|----------------------|--------------------------------------|
| almacen              | Inventario_Almacenes                 |
| invfisico            | Compras_Inventarios_Fisicos_Sync     |
| invfisicomovtos      | Compras_Inventarios_Fisicos_Sync (detalle) |
| movtosalmacen        | Inventario_Movimientos + Inventario_MovimientosDetalle |
| pedidos              | Compras_Pedidos                      |
| pedidosdetalle       | Compras_PedidosDetalle               |
| ordenescompra        | Compras_Ordenes                      |
| ordenescompramov     | Compras_OrdenesDetalle               |
| compras              | Compras_Recepciones                  |
| comprasmovtos        | Compras_RecepcionesDetalle           |
| proveedores          | (catálogo auxiliar)                  |
"""

ORIGEN = "SOFTRESTAURANT_PRO"

# Mapeo: clave canónica → tabla origen SoftRestaurant
TABLES_ORIGEN = {
    "almacenes": "almacen",
    "inventarios_fisicos": "invfisico",
    "inventarios_fisicos_detalle": "invfisicomovtos",
    "movimientos": "movtosalmacen",
    "pedidos": "pedidos",
    "pedidos_detalle": "pedidosdetalle",
    "ordenes": "ordenescompra",
    "ordenes_detalle": "ordenescompramov",
    "recepciones": "compras",
    "recepciones_detalle": "comprasmovtos",
    "proveedores": "proveedores",
}

# Mapeo: clave canónica → tabla destino EDARSAHUB
TABLES_DESTINO = {
    "almacenes": "Inventario_Almacenes",
    "inventarios_fisicos": "Compras_Inventarios_Fisicos_Sync",
    "inventarios_fisicos_detalle": "Compras_Inventarios_Fisicos_Sync",
    "movimientos": "Inventario_Movimientos",
    "movimientos_detalle": "Inventario_MovimientosDetalle",
    "pedidos": "Compras_Pedidos",
    "pedidos_detalle": "Compras_PedidosDetalle",
    "ordenes": "Compras_Ordenes",
    "ordenes_detalle": "Compras_OrdenesDetalle",
    "recepciones": "Compras_Recepciones",
    "recepciones_detalle": "Compras_RecepcionesDetalle",
}


def query_almacenes():
    return """
    SELECT
        idalmacen AS AlmacenOrigenID,
        nombre AS NombreAlmacen,
        tipo AS TipoAlmacen
    FROM almacen
    """


def query_pedidos(dias_atras=30):
    return f"""
    SELECT
        p.idpedido AS PedidoOrigenID,
        p.folio AS FolioPedido,
        p.fechacaptura AS FechaPedido,
        p.fecharecepcion AS FechaRecepcion,
        p.idproveedor AS ProveedorOrigenID
    FROM pedidos p
    WHERE p.fechacaptura >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
    """


def query_pedidos_detalle(dias_atras=30):
    return f"""
    SELECT
        p.idpedido AS PedidoOrigenID,
        p.folio AS FolioPedido,
        d.idinsumo AS CodigoProducto,
        d.cantidad AS Cantidad,
        d.costo AS CostoUnitario
    FROM pedidos p
    INNER JOIN pedidosdetalle d ON d.idpedido = p.idpedido
    WHERE p.fechacaptura >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
    """


def query_ordenes(dias_atras=30):
    return f"""
    SELECT
        o.idordencompra AS OrdenOrigenID,
        o.folio AS FolioOrden,
        o.fechacaptura AS FechaOrden,
        o.idproveedor AS ProveedorOrigenID
    FROM ordenescompra o
    WHERE o.fechacaptura >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
    """


def query_ordenes_detalle(dias_atras=30):
    return f"""
    SELECT
        o.idordencompra AS OrdenOrigenID,
        o.folio AS FolioOrden,
        d.idinsumo AS CodigoProducto,
        d.cantidad AS Cantidad,
        d.costo AS CostoUnitario
    FROM ordenescompra o
    INNER JOIN ordenescompramov d ON d.idordencompra = o.idordencompra
    WHERE o.fechacaptura >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
    """


def query_recepciones(dias_atras=30):
    return f"""
    SELECT
        c.idcompra AS RecepcionOrigenID,
        c.folio AS FolioRecepcion,
        c.fechaaplicacion AS FechaRecepcion,
        c.idproveedor AS ProveedorOrigenID,
        c.total AS Total
    FROM compras c
    WHERE c.fechaaplicacion >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
    """


def query_recepciones_detalle(dias_atras=30):
    return f"""
    SELECT
        c.idcompra AS RecepcionOrigenID,
        c.folio AS FolioRecepcion,
        d.idinsumo AS CodigoProducto,
        d.cantidad AS Cantidad,
        d.costo AS CostoUnitario,
        d.descuento AS Descuento
    FROM compras c
    INNER JOIN comprasmovtos d ON d.idcompra = c.idcompra
    WHERE c.fechaaplicacion >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
    """


def query_inventarios_fisicos(dias_atras=30):
    """
    Inventarios físicos → Compras_Inventarios_Fisicos_Sync
    """
    return f"""
    SELECT
        i.folio AS FolioInventario,
        i.fecha AS FechaInventario,
        i.idalmacen1 AS AlmacenOrigenID,
        i.idalmacen2 AS AlmacenDestinoID,
        i.inventarioteorico1 AS InventarioTeorico,
        i.inventariofisico1 AS InventarioFisico,
        i.diferencia1 AS Diferencia,
        i.cancelado AS Cancelado
    FROM invfisico i
    WHERE i.fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
    """


def query_inventarios_fisicos_detalle(dias_atras=30):
    """
    Detalle inventarios físicos → Compras_Inventarios_Fisicos_Sync (según lógica existente)
    """
    return f"""
    SELECT
        d.folio AS FolioInventario,
        d.idinsumo AS CodigoProducto,
        d.idpresentacion AS PresentacionID,
        d.existenciaalmacen1 AS ExistenciaTeorica,
        d.fisicoalmacen1 AS ExistenciaFisica,
        d.costo AS CostoUnitario
    FROM invfisicomovtos d
    INNER JOIN invfisico i ON i.folio = d.folio
    WHERE i.fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
    """


def query_movimientos_almacen(dias_atras=30):
    """
    Movimientos de almacén → Inventario_Movimientos + Inventario_MovimientosDetalle
    
    Esta tabla contiene todos los movimientos: entradas, salidas, traspasos, etc.
    """
    return f"""
    SELECT
        m.fecha AS FechaMovimiento,
        m.movto AS TipoMovimiento,
        m.idcompra AS CompraOrigenID,
        m.traspaso AS TraspasoOrigenID,
        m.invfisico AS InvFisicoOrigenID,
        m.idconcepto AS ConceptoID,
        m.idinsumo AS CodigoProducto,
        m.idpresentacion AS PresentacionID,
        m.idalmacen AS AlmacenOrigenID,
        m.cantidad AS Cantidad,
        m.costo AS CostoUnitario,
        m.cancelado AS Cancelado,
        m.usuario AS UsuarioOrigen
    FROM movtosalmacen m
    WHERE m.fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
      AND m.cancelado = 0
    """
