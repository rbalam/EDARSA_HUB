"""
Adapter MPRO → EDARSAHUB SQL

Este archivo separa nombres origen MPRO del modelo canónico EDARSAHUB.
Completar queries conforme diccionario real MPRO validado.
"""

ORIGEN = "MPRO"

TABLES = {
    "requisiciones": "Requisicion_Compra",
    "requisiciones_detalle": "Requisicion_Compra_Detalle",
    "pedidos_detalle": "Pedido_Detalle",
    "ordenes_detalle": "Orden_Compra_Detalle",
    "movimientos": "Movimiento",
    "almacenes": "Almacen",
    "productos": "Producto",
    "proveedores": "Proveedor",
}


def query_almacenes():
    return """
    SELECT
        Al_Cve_Almacen AS AlmacenOrigenID,
        Al_Descripcion AS NombreAlmacen
    FROM Almacen
    """


def query_requisiciones(dias_atras=30):
    return f"""
    SELECT *
    FROM Requisicion_Compra
    WHERE Rc_Fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
    """


def query_requisiciones_detalle(dias_atras=30):
    return f"""
    SELECT *
    FROM Requisicion_Compra_Detalle
    """
