"""
Adapter SOFTRESTAURANT_PRO → EDARSAHUB SQL

Este archivo contiene únicamente queries de extracción del origen SoftRestaurant PRO.
El destino SIEMPRE debe ser el modelo canónico EDARSAHUB:

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
"""

ORIGEN = "SOFTRESTAURANT_PRO"

TABLES = {
    "almacenes": "almacen",
    "compras": "compras",
    "compras_detalle": "comprasmovtos",
    "ordenes": "ordenescompra",
    "ordenes_detalle": "ordenescompramov",
    "pedidos": "pedidos",
    "pedidos_detalle": "pedidosdetalle",
    "inventarios_fisicos": "invfisico",
    "inventarios_fisicos_detalle": "invfisicomovtos",
    "movimientos": "movtosalmacen",
    "proveedores": "proveedores",
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


def query_movimientos(dias_atras=30):
    return f"""
    SELECT
        m.idmovtoalmacen AS MovimientoOrigenID,
        m.fecha AS FechaMovimiento,
        m.movto AS TipoMovimiento,
        m.idalmacen AS AlmacenOrigenID,
        m.idcompra AS DocumentoOrigenID,
        m.traspaso AS Traspaso
    FROM movtosalmacen m
    WHERE m.fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
    """


def query_inventarios_fisicos(dias_atras=30):
    return f"""
    SELECT
        i.folio AS FolioInventario,
        i.fecha AS FechaInventario,
        i.idalmacen1 AS AlmacenOrigenID,
        i.inventariofisico1 AS EstatusOrigen
    FROM invfisico i
    WHERE i.fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
    """
