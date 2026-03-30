# Catálogo de Consultas para SoftRestaurant
# Estas consultas están adaptadas para la estructura de SoftRestaurant

CONSULTAS_SOFTRESTAURANT = {
    # ============= VENTAS =============
    "ventas": {
        "nombre": "Ventas por Producto",
        "descripcion": "Obtiene las ventas de productos",
        "parametros": ["@FECHA_INI", "@FECHA_FIN"],
        "sql": """
SELECT 
    D.idproducto as Codigo,
    P.descripcion as Producto,
    SUM(D.cantidad) as Cantidad,
    SUM(D.precio * D.cantidad) as Importe_Total
FROM cheqdet D
INNER JOIN productos P ON P.idproducto = D.idproducto
INNER JOIN cheques C ON C.folio = D.folio
WHERE C.fecha BETWEEN '{fecha_ini}' AND '{fecha_fin}'
    AND C.cancelado = 0
GROUP BY D.idproducto, P.descripcion
ORDER BY P.descripcion
"""
    },

    "ventas_detalle": {
        "nombre": "Detalle de Ventas",
        "descripcion": "Obtiene el detalle completo de ventas",
        "parametros": ["@FECHA_INI", "@FECHA_FIN"],
        "sql": """
SELECT 
    C.folio as Folio,
    C.fecha as Fecha,
    C.hora as Hora,
    P.idproducto as Codigo,
    P.descripcion as Producto,
    D.cantidad as Cantidad,
    D.precio as Precio,
    D.cantidad * D.precio as Importe,
    C.total as Total_Cheque
FROM cheqdet D
INNER JOIN productos P ON P.idproducto = D.idproducto
INNER JOIN cheques C ON C.folio = D.folio
WHERE C.fecha BETWEEN '{fecha_ini}' AND '{fecha_fin}'
    AND C.cancelado = 0
ORDER BY C.fecha DESC, C.hora DESC
"""
    },

    # ============= COMPRAS =============
    "compras": {
        "nombre": "Compras por Producto",
        "descripcion": "Obtiene las compras agrupadas por producto",
        "parametros": ["@FECHA_INI", "@FECHA_FIN"],
        "sql": """
SELECT 
    CM.idinsumo as Codigo,
    I.descripcion as Producto,
    SUM(CM.cantidad) as Cantidad,
    SUM(CM.costo * CM.cantidad) as Importe_Total,
    AVG(CM.costo) as Costo_Promedio
FROM comprasmovtos CM
INNER JOIN insumos I ON I.idinsumo = CM.idinsumo
INNER JOIN compras C ON C.idcompra = CM.idcompra
WHERE C.fechaaplicacion BETWEEN '{fecha_ini}' AND '{fecha_fin}'
    AND C.cancelado = 0
GROUP BY CM.idinsumo, I.descripcion
ORDER BY I.descripcion
"""
    },

    # ============= MOVIMIENTOS =============
    "movimientos": {
        "nombre": "Movimientos de Inventario",
        "descripcion": "Obtiene los movimientos de inventario",
        "parametros": ["@FECHA_INI", "@FECHA_FIN"],
        "sql": """
SELECT 
    M.idproducto as Codigo,
    P.descripcion as Producto,
    TM.descripcion as Tipo_Movimiento,
    SUM(CASE WHEN TM.tipo = 'E' THEN M.cantidad ELSE -M.cantidad END) as Movimiento_Neto
FROM movtos M
INNER JOIN productos P ON P.idproducto = M.idproducto
INNER JOIN tipomovto TM ON TM.idtipomovto = M.idtipomovto
WHERE M.fecha BETWEEN '{fecha_ini}' AND '{fecha_fin}'
GROUP BY M.idproducto, P.descripcion, TM.descripcion
ORDER BY P.descripcion
"""
    },

    # ============= PRODUCTOS =============
    "productos": {
        "nombre": "Catálogo de Productos",
        "descripcion": "Obtiene el catálogo completo de productos",
        "parametros": [],
        "sql": """
SELECT 
    P.idproducto as Codigo,
    P.descripcion as Producto,
    G.descripcion as Grupo,
    P.unidad as Unidad,
    P.costo as Costo,
    P.precio1 as Precio_1,
    P.precio2 as Precio_2,
    P.existencia as Existencia,
    P.activo as Activo
FROM productos P
LEFT JOIN grupos G ON G.idgrupo = P.idgrupo
WHERE P.activo = 1
ORDER BY G.descripcion, P.descripcion
"""
    },

    # ============= PROVEEDORES =============
    "proveedores": {
        "nombre": "Catálogo de Proveedores",
        "descripcion": "Obtiene el catálogo completo de proveedores",
        "parametros": [],
        "sql": """
SELECT 
    idproveedor as Codigo,
    nombre as Nombre,
    rfc as RFC,
    direccion as Direccion,
    telefono as Telefono,
    email as Email,
    contacto as Contacto,
    diascredito as Dias_Credito
FROM proveedores
ORDER BY nombre
"""
    },

    # ============= GRUPOS =============
    "grupos": {
        "nombre": "Catálogo de Grupos",
        "descripcion": "Obtiene el catálogo de grupos de productos",
        "parametros": [],
        "sql": """
SELECT 
    idgrupo as Codigo,
    descripcion as Descripcion
FROM grupos
ORDER BY descripcion
"""
    },

    # ============= TIPOS DE MOVIMIENTO =============
    "tipos_movimiento": {
        "nombre": "Catálogo de Tipos de Movimiento",
        "descripcion": "Obtiene el catálogo de tipos de movimiento",
        "parametros": [],
        "sql": """
SELECT 
    idtipomovto as Codigo,
    descripcion as Descripcion,
    tipo as Tipo,
    CASE WHEN tipo = 'E' THEN 'Entrada' ELSE 'Salida' END as Tipo_Descripcion
FROM tipomovto
ORDER BY idtipomovto
"""
    }
}

# Estructura de tablas principales de SoftRestaurant
ESTRUCTURA_TABLAS_SOFTRESTAURANT = {
    "productos": {
        "descripcion": "Catálogo de productos",
        "campos_principales": [
            "idproducto (PK) - Código del producto",
            "descripcion - Nombre del producto",
            "idgrupo - Código de grupo",
            "unidad - Unidad de medida",
            "costo - Costo",
            "precio1, precio2 - Precios de venta",
            "existencia - Existencia actual",
            "activo - Estado (1=Activo, 0=Inactivo)"
        ]
    },
    "cheques": {
        "descripcion": "Encabezado de ventas/tickets",
        "campos_principales": [
            "folio (PK) - Folio del ticket",
            "fecha - Fecha de venta",
            "hora - Hora de venta",
            "total - Total del ticket",
            "cancelado - Estado (0=Activo, 1=Cancelado)",
            "idmesero - Mesero",
            "nopersonas - Número de personas"
        ]
    },
    "cheqdet": {
        "descripcion": "Detalle de ventas/tickets",
        "campos_principales": [
            "folio - Folio del ticket",
            "idproducto - Producto",
            "cantidad - Cantidad vendida",
            "precio - Precio de venta",
            "descuento - Descuento aplicado"
        ]
    },
    "compras": {
        "descripcion": "Encabezado de compras",
        "campos_principales": [
            "idcompra (PK) - ID de compra",
            "fecha - Fecha de compra",
            "idproveedor - Proveedor",
            "total - Total de la compra"
        ]
    },
    "comprasmovtos": {
        "descripcion": "Detalle de compras (movimientos de compra)",
        "campos_principales": [
            "idcompra - ID de compra",
            "idinsumo - Producto/Insumo",
            "cantidad - Cantidad comprada",
            "costo - Costo unitario",
            "importeconimpuestos - Total con impuestos"
        ]
    },
    "movtos": {
        "descripcion": "Movimientos de inventario",
        "campos_principales": [
            "idmovto (PK) - ID de movimiento",
            "fecha - Fecha del movimiento",
            "idtipomovto - Tipo de movimiento",
            "idproducto - Producto",
            "cantidad - Cantidad"
        ]
    },
    "proveedores": {
        "descripcion": "Catálogo de proveedores",
        "campos_principales": [
            "idproveedor (PK) - Código del proveedor",
            "nombre - Nombre",
            "rfc - RFC",
            "direccion - Dirección",
            "telefono - Teléfono"
        ]
    },
    "grupos": {
        "descripcion": "Catálogo de grupos de productos",
        "campos_principales": [
            "idgrupo (PK) - Código del grupo",
            "descripcion - Nombre del grupo"
        ]
    }
}
