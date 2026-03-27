# Catálogo Maestro de Consultas - Edarsa Hub
# Rich puede agregar/modificar consultas aquí sin programador
# Formato: nombre amigable, descripción, parámetros, SQL

CATALOGO_CONSULTAS = {
    # ==========================================
    # VENTAS - SoftRestaurant
    # ==========================================
    "SR_VENTAS_DIA": {
        "nombre": "Ventas del Día",
        "descripcion": "Total de ventas, cheques y comensales del día seleccionado",
        "sistema": "SoftRestaurant",
        "categoria": "Ventas",
        "parametros": ["fecha"],
        "sql": """
SELECT 
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta_Total,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX,
    ISNULL(AVG(cheques.total), 0) as Cheque_Promedio,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 0) as PAX_Promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(date, turnos.apertura) = '{fecha}'
  AND cheques.cancelado = 0
"""
    },
    
    "SR_VENTAS_PERIODO": {
        "nombre": "Ventas por Período",
        "descripcion": "Total de ventas entre dos fechas",
        "sistema": "SoftRestaurant",
        "categoria": "Ventas",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta_Total,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX,
    ISNULL(AVG(cheques.total), 0) as Cheque_Promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
"""
    },
    
    "SR_VENTAS_POR_DIA": {
        "nombre": "Ventas Desglosadas por Día",
        "descripcion": "Ventas día a día en un período",
        "sistema": "SoftRestaurant",
        "categoria": "Ventas",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    CONVERT(date, turnos.apertura) as Fecha,
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY CONVERT(date, turnos.apertura)
ORDER BY CONVERT(date, turnos.apertura)
"""
    },
    
    "SR_VENTAS_POR_HORA": {
        "nombre": "Ventas por Hora",
        "descripcion": "Distribución de ventas por hora del día",
        "sistema": "SoftRestaurant",
        "categoria": "Ventas",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    DATEPART(HOUR, turnos.apertura) as Hora,
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY DATEPART(HOUR, turnos.apertura)
ORDER BY DATEPART(HOUR, turnos.apertura)
"""
    },
    
    "SR_VENTAS_POR_MESERO": {
        "nombre": "Ventas por Mesero",
        "descripcion": "Ranking de ventas por mesero/vendedor",
        "sistema": "SoftRestaurant",
        "categoria": "Ventas",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    ISNULL(m.nombre, 'Sin asignar') as Mesero,
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX,
    ISNULL(AVG(cheques.total), 0) as Cheque_Promedio
FROM cheques
LEFT JOIN meseros m ON m.idmesero = cheques.idmesero
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY m.nombre
ORDER BY SUM(cheques.total) DESC
"""
    },
    
    "SR_VENTAS_POR_PRODUCTO": {
        "nombre": "Ventas por Producto",
        "descripcion": "Top productos más vendidos",
        "sistema": "SoftRestaurant",
        "categoria": "Ventas",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT TOP 50
    p.idproducto as Codigo,
    p.descripcion as Producto,
    SUM(cd.cantidad) as Cantidad,
    SUM(cd.cantidad * cd.precio) as Venta
FROM cheqdet cd
INNER JOIN cheques ON cheques.folio = cd.foliodet
INNER JOIN productos p ON p.idproducto = cd.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY p.idproducto, p.descripcion
ORDER BY SUM(cd.cantidad * cd.precio) DESC
"""
    },
    
    "SR_CORTESIAS": {
        "nombre": "Cortesías y Descuentos",
        "descripcion": "Detalle de cortesías aplicadas",
        "sistema": "SoftRestaurant",
        "categoria": "Ventas",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    CONVERT(date, turnos.apertura) as Fecha,
    cheques.folio as Folio,
    ISNULL(m.nombre, 'N/A') as Mesero,
    cheques.subtotal as Subtotal,
    cheques.descuento as Descuento,
    cheques.total as Total,
    cheques.razondescuento as Razon
FROM cheques
LEFT JOIN meseros m ON m.idmesero = cheques.idmesero
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.descuento > 0
ORDER BY turnos.apertura DESC
"""
    },
    
    "SR_CANCELACIONES": {
        "nombre": "Cancelaciones",
        "descripcion": "Cheques cancelados en el período",
        "sistema": "SoftRestaurant",
        "categoria": "Ventas",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    CONVERT(date, turnos.apertura) as Fecha,
    cheques.folio as Folio,
    ISNULL(m.nombre, 'N/A') as Mesero,
    cheques.total as Monto,
    cheques.razoncancelado as Razon
FROM cheques
LEFT JOIN meseros m ON m.idmesero = cheques.idmesero
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 1
ORDER BY turnos.apertura DESC
"""
    },

    # ==========================================
    # COMPRAS - SoftRestaurant
    # ==========================================
    "SR_COMPRAS_PERIODO": {
        "nombre": "Compras por Período",
        "descripcion": "Total de compras entre dos fechas",
        "sistema": "SoftRestaurant",
        "categoria": "Compras",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
WHERE c.fecha >= '{fecha_ini}'
  AND c.fecha <= '{fecha_fin} 23:59:59'
"""
    },
    
    "SR_COMPRAS_POR_PROVEEDOR": {
        "nombre": "Compras por Proveedor",
        "descripcion": "Desglose de compras por proveedor",
        "sistema": "SoftRestaurant",
        "categoria": "Compras",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    ISNULL(p.nombre, 'Sin proveedor') as Proveedor,
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
LEFT JOIN proveedores p ON p.idproveedor = c.idproveedor
WHERE c.fecha >= '{fecha_ini}'
  AND c.fecha <= '{fecha_fin} 23:59:59'
GROUP BY p.nombre
ORDER BY SUM(c.total) DESC
"""
    },
    
    "SR_COMPRAS_POR_PRODUCTO": {
        "nombre": "Compras por Producto",
        "descripcion": "Detalle de productos comprados",
        "sistema": "SoftRestaurant",
        "categoria": "Compras",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT TOP 50
    i.idinsumo as Codigo,
    i.descripcion as Producto,
    SUM(cd.cantidad) as Cantidad,
    AVG(cd.costo) as Costo_Promedio,
    SUM(cd.cantidad * cd.costo) as Compra_Total
FROM comprasdet cd
INNER JOIN compras c ON c.idcompra = cd.idcompra
INNER JOIN insumos i ON i.idinsumo = cd.idproducto
WHERE c.fecha >= '{fecha_ini}'
  AND c.fecha <= '{fecha_fin} 23:59:59'
GROUP BY i.idinsumo, i.descripcion
ORDER BY SUM(cd.cantidad * cd.costo) DESC
"""
    },

    # ==========================================
    # INVENTARIOS - SoftRestaurant
    # ==========================================
    "SR_INVENTARIO_ACTUAL": {
        "nombre": "Inventario Actual",
        "descripcion": "Existencias actuales por almacén",
        "sistema": "SoftRestaurant",
        "categoria": "Inventarios",
        "parametros": ["almacen"],
        "sql": """
SELECT 
    i.idinsumo as Codigo,
    i.descripcion as Producto,
    ISNULL(e.existencia, 0) as Existencia,
    i.unidadcompra as Unidad,
    ISNULL(i.costo, 0) as Costo,
    ISNULL(e.existencia * i.costo, 0) as Valor
FROM insumos i
LEFT JOIN existenciasalmacen e ON e.idinsumo = i.idinsumo
LEFT JOIN almacen a ON a.idalmacen = e.idalmacen
WHERE a.nombre LIKE '%{almacen}%'
  AND ISNULL(e.existencia, 0) > 0
ORDER BY i.descripcion
"""
    },

    # ==========================================
    # VENTAS - MPRO
    # ==========================================
    "MPRO_VENTAS_PERIODO": {
        "nombre": "Ventas por Período",
        "descripcion": "Total de ventas MPRO entre dos fechas",
        "sistema": "MPRO",
        "categoria": "Ventas",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    COUNT(DISTINCT Vn_Folio) as Tickets,
    ISNULL(SUM(Vn_Importe), 0) as Venta_Total
FROM Venta
WHERE Vn_Fecha >= '{fecha_ini}' 
  AND Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    },
    
    "MPRO_VENTAS_POR_DIA": {
        "nombre": "Ventas por Día",
        "descripcion": "Ventas MPRO desglosadas por día",
        "sistema": "MPRO",
        "categoria": "Ventas",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    CONVERT(date, Vn_Fecha) as Fecha,
    COUNT(DISTINCT Vn_Folio) as Tickets,
    ISNULL(SUM(Vn_Importe), 0) as Venta
FROM Venta
WHERE Vn_Fecha >= '{fecha_ini}' 
  AND Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND ISNULL(Es_Cve_Estado, '') <> 'CA'
GROUP BY CONVERT(date, Vn_Fecha)
ORDER BY CONVERT(date, Vn_Fecha)
"""
    },
    
    "MPRO_VENTAS_POR_SUCURSAL": {
        "nombre": "Ventas por Sucursal",
        "descripcion": "Ventas MPRO por sucursal/almacén",
        "sistema": "MPRO",
        "categoria": "Ventas",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    ISNULL(A.Al_Descripcion, 'Sin sucursal') as Sucursal,
    COUNT(DISTINCT V.Vn_Folio) as Tickets,
    ISNULL(SUM(V.Vn_Importe), 0) as Venta
FROM Venta V
LEFT JOIN Almacen A ON A.Al_Cve_Almacen = V.Al_Cve_Almacen
WHERE V.Vn_Fecha >= '{fecha_ini}' 
  AND V.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND ISNULL(V.Es_Cve_Estado, '') <> 'CA'
GROUP BY A.Al_Descripcion
ORDER BY SUM(V.Vn_Importe) DESC
"""
    },
    
    "MPRO_VENTAS_POR_PRODUCTO": {
        "nombre": "Ventas por Producto",
        "descripcion": "Top productos MPRO más vendidos",
        "sistema": "MPRO",
        "categoria": "Ventas",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT TOP 50
    P.Pd_Cve_Producto as Codigo,
    P.Pd_Descripcion as Producto,
    SUM(V.Vn_Cantidad_1) as Cantidad,
    SUM(V.Vn_Importe) as Venta
FROM Venta V
INNER JOIN Producto P ON P.Pd_Cve_Producto = V.Pd_Cve_Producto
WHERE V.Vn_Fecha >= '{fecha_ini}' 
  AND V.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND ISNULL(V.Es_Cve_Estado, '') <> 'CA'
GROUP BY P.Pd_Cve_Producto, P.Pd_Descripcion
ORDER BY SUM(V.Vn_Importe) DESC
"""
    },

    # ==========================================
    # COMPRAS - MPRO
    # ==========================================
    "MPRO_COMPRAS_PERIODO": {
        "nombre": "Compras por Período",
        "descripcion": "Total de compras MPRO",
        "sistema": "MPRO",
        "categoria": "Compras",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    COUNT(DISTINCT RC.Rc_Folio) as Facturas,
    ISNULL(SUM(RCD.Rd_Cantidad * RCD.Rd_Costo), 0) as Compra_Total
FROM REQUISICION_COMPRA RC
INNER JOIN REQUISICION_COMPRA_DETALLE RCD ON RCD.Rc_Folio = RC.Rc_Folio
WHERE RC.Rc_FechaCaptura >= '{fecha_ini}' 
  AND RC.Rc_FechaCaptura <= '{fecha_fin} 23:59:59'
"""
    },
    
    "MPRO_COMPRAS_POR_PROVEEDOR": {
        "nombre": "Compras por Proveedor",
        "descripcion": "Compras MPRO por proveedor",
        "sistema": "MPRO",
        "categoria": "Compras",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    ISNULL(P.Pv_Descripcion, 'Sin proveedor') as Proveedor,
    COUNT(DISTINCT RC.Rc_Folio) as Facturas,
    ISNULL(SUM(RCD.Rd_Cantidad * RCD.Rd_Costo), 0) as Compra_Total
FROM REQUISICION_COMPRA RC
INNER JOIN REQUISICION_COMPRA_DETALLE RCD ON RCD.Rc_Folio = RC.Rc_Folio
LEFT JOIN Proveedor P ON P.Pv_Cve_Proveedor = RC.Pv_Cve_Proveedor
WHERE RC.Rc_FechaCaptura >= '{fecha_ini}' 
  AND RC.Rc_FechaCaptura <= '{fecha_fin} 23:59:59'
GROUP BY P.Pv_Descripcion
ORDER BY SUM(RCD.Rd_Cantidad * RCD.Rd_Costo) DESC
"""
    },

    # ==========================================
    # PAGOS - SoftRestaurant
    # ==========================================
    "SR_FORMAS_PAGO": {
        "nombre": "Formas de Pago",
        "descripcion": "Desglose por forma de pago (efectivo, tarjeta, etc.)",
        "sistema": "SoftRestaurant",
        "categoria": "Pagos",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    ISNULL(fp.descripcion, 'Efectivo') as Forma_Pago,
    COUNT(*) as Operaciones,
    ISNULL(SUM(cp.importe), 0) as Monto
FROM chequespagos cp
INNER JOIN cheques c ON c.folio = cp.folio
INNER JOIN turnos t ON t.idturno = c.idturno
LEFT JOIN formaspago fp ON fp.idformapago = cp.idformapago
WHERE t.apertura >= '{fecha_ini} 00:00:00'
  AND t.apertura <= '{fecha_fin} 23:59:59'
  AND c.cancelado = 0
GROUP BY fp.descripcion
ORDER BY SUM(cp.importe) DESC
"""
    },
    
    "SR_PROPINAS": {
        "nombre": "Propinas",
        "descripcion": "Total de propinas por mesero",
        "sistema": "SoftRestaurant",
        "categoria": "Pagos",
        "parametros": ["fecha_ini", "fecha_fin"],
        "sql": """
SELECT 
    ISNULL(m.nombre, 'Sin asignar') as Mesero,
    COUNT(DISTINCT c.folio) as Cheques,
    ISNULL(SUM(c.propina), 0) as Propinas,
    ISNULL(SUM(c.total), 0) as Ventas
FROM cheques c
LEFT JOIN meseros m ON m.idmesero = c.idmesero
INNER JOIN turnos t ON t.idturno = c.idturno
WHERE t.apertura >= '{fecha_ini} 00:00:00'
  AND t.apertura <= '{fecha_fin} 23:59:59'
  AND c.cancelado = 0
  AND c.propina > 0
GROUP BY m.nombre
ORDER BY SUM(c.propina) DESC
"""
    },
}

# Función para obtener consultas por categoría
def get_consultas_por_categoria(sistema=None, categoria=None):
    """Filtra consultas por sistema y/o categoría"""
    resultado = {}
    for key, consulta in CATALOGO_CONSULTAS.items():
        if sistema and consulta['sistema'] != sistema:
            continue
        if categoria and consulta['categoria'] != categoria:
            continue
        resultado[key] = consulta
    return resultado

# Función para obtener categorías disponibles
def get_categorias():
    """Retorna lista de categorías únicas"""
    categorias = set()
    for consulta in CATALOGO_CONSULTAS.values():
        categorias.add(consulta['categoria'])
    return sorted(list(categorias))

# Función para ejecutar consulta con parámetros
def preparar_sql(key, parametros):
    """Prepara el SQL reemplazando parámetros"""
    if key not in CATALOGO_CONSULTAS:
        return None
    
    sql = CATALOGO_CONSULTAS[key]['sql']
    for param, valor in parametros.items():
        sql = sql.replace('{' + param + '}', str(valor))
    return sql
