# Catálogo de Consultas para ManagementPro (MPRO)
# Estas consultas están probadas y listas para usar

CONSULTAS_MPRO = {
    # ============= VENTAS =============
    "ventas": {
        "nombre": "Ventas por Producto",
        "descripcion": "Obtiene las ventas de productos incluyendo kits y ventas directas",
        "parametros": ["@SUCURSAL", "@FECHA_INI", "@FECHA_FIN"],
        "sql": """
DECLARE @SUCURSAL VARCHAR(50) = '{sucursal}'
DECLARE @FECHA_INI VARCHAR(20) = '{fecha_ini}'
DECLARE @FECHA_FIN VARCHAR(20) = '{fecha_fin}'

SELECT Producto_Codigo, SUM(Cantidad) as Total_Ventas FROM (
    -- Ventas de productos KIT (componentes)
    SELECT 
        Producto_Kit.Pk_Producto as Producto_Codigo,
        SUM(venta.Vn_Cantidad_1 * Producto_Kit.Pk_Cantidad) as Cantidad
    FROM venta
    INNER JOIN producto_kit ON Producto_Kit.Pr_Cve_Producto = venta.Pr_Cve_Producto
    INNER JOIN producto ON producto.Pr_Cve_Producto = Producto_kit.Pk_Producto
    INNER JOIN sucursal ON sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
    WHERE sucursal.Sc_Descripcion LIKE '%' + @SUCURSAL + '%'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN @FECHA_INI AND @FECHA_FIN + ' 23:59:59'
        AND producto_kit.Pk_Producto IS NOT NULL
    GROUP BY Producto_Kit.Pk_Producto

    UNION ALL

    -- Ventas DIRECTAS
    SELECT 
        venta.Pr_Cve_Producto as Producto_Codigo,
        SUM(venta.Vn_Cantidad_Control_1) as Cantidad
    FROM venta
    INNER JOIN producto ON producto.Pr_Cve_Producto = venta.Pr_Cve_Producto
    INNER JOIN sucursal ON sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
    WHERE sucursal.Sc_Descripcion LIKE '%' + @SUCURSAL + '%'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN @FECHA_INI AND @FECHA_FIN + ' 23:59:59'
    GROUP BY venta.Pr_Cve_Producto
) AS VentasCombinadas
GROUP BY Producto_Codigo
"""
    },
    
    "ventas_detalle": {
        "nombre": "Detalle de Ventas",
        "descripcion": "Obtiene el detalle de ventas con información completa",
        "parametros": ["@SUCURSAL", "@FECHA_INI", "@FECHA_FIN"],
        "sql": """
SELECT 
    V.Vn_Folio as Folio,
    V.Vn_Fecha as Fecha,
    S.Sc_Descripcion as Sucursal,
    A.Al_Descripcion as Almacen,
    P.Pr_Cve_Producto as Codigo,
    P.Pr_Descripcion as Producto,
    V.Vn_Cantidad_1 as Cantidad,
    V.Vn_Cantidad_Control_1 as Cantidad_Control,
    V.Vn_Precio as Precio,
    V.Vn_Importe as Importe,
    V.Es_Cve_Estado as Estado
FROM Venta V
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
INNER JOIN Almacen A ON A.Al_Cve_Almacen = V.Al_Cve_Almacen
INNER JOIN Producto P ON P.Pr_Cve_Producto = V.Pr_Cve_Producto
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND V.Es_Cve_Estado <> 'CA'
    AND V.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
ORDER BY V.Vn_Fecha DESC
"""
    },

    # ============= COMPRAS =============
    "compras": {
        "nombre": "Compras por Producto",
        "descripcion": "Obtiene las compras agrupadas por producto",
        "parametros": ["@SUCURSAL", "@FECHA_INI", "@FECHA_FIN"],
        "sql": """
SELECT 
    C.Pr_Cve_Producto as Codigo,
    P.Pr_Descripcion as Producto,
    SUM(C.Co_Cantidad_1) as Cantidad,
    SUM(C.Co_Importe) as Importe_Total,
    AVG(C.Co_Costo) as Costo_Promedio
FROM Compra C
INNER JOIN Producto P ON P.Pr_Cve_Producto = C.Pr_Cve_Producto
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = C.Sc_Cve_Sucursal
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND C.Es_Cve_Estado <> 'CA'
    AND C.Co_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
GROUP BY C.Pr_Cve_Producto, P.Pr_Descripcion
ORDER BY P.Pr_Descripcion
"""
    },

    "compras_detalle": {
        "nombre": "Detalle de Compras",
        "descripcion": "Obtiene el detalle completo de compras",
        "parametros": ["@SUCURSAL", "@FECHA_INI", "@FECHA_FIN"],
        "sql": """
SELECT 
    C.Co_Folio as Folio,
    C.Co_Fecha as Fecha,
    S.Sc_Descripcion as Sucursal,
    PR.Pv_Nombre as Proveedor,
    P.Pr_Cve_Producto as Codigo,
    P.Pr_Descripcion as Producto,
    C.Co_Cantidad_1 as Cantidad,
    C.Co_Costo as Costo_Unitario,
    C.Co_Importe as Importe,
    C.Es_Cve_Estado as Estado
FROM Compra C
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = C.Sc_Cve_Sucursal
INNER JOIN Producto P ON P.Pr_Cve_Producto = C.Pr_Cve_Producto
LEFT JOIN Proveedor PR ON PR.Pv_Cve_Proveedor = C.Pv_Cve_Proveedor
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND C.Es_Cve_Estado <> 'CA'
    AND C.Co_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
ORDER BY C.Co_Fecha DESC
"""
    },

    # ============= MOVIMIENTOS =============
    "movimientos": {
        "nombre": "Movimientos de Inventario",
        "descripcion": "Obtiene los movimientos de inventario (entradas y salidas)",
        "parametros": ["@SUCURSAL", "@ALMACEN", "@FECHA_INI", "@FECHA_FIN", "@TIPOS_MOVIMIENTO"],
        "sql": """
SELECT 
    E.Pr_Cve_Producto as Codigo,
    P.Pr_Descripcion as Producto,
    SUM(E.Mv_Cantidad_Control_1) as Movimiento_Neto
FROM Movimiento E
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = E.Sc_Cve_Sucursal
INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = S.Sc_Cve_Sucursal
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = E.Tm_Cve_Tipo_Movimiento
INNER JOIN Producto P ON P.Pr_Cve_Producto = E.Pr_Cve_Producto
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND A.Al_Descripcion LIKE '%{almacen}%'
    AND E.Es_Cve_Estado <> 'CA'
    AND E.Tm_Cve_Tipo_Movimiento IN ({tipos_movimiento})
    AND E.Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
GROUP BY E.Pr_Cve_Producto, P.Pr_Descripcion
"""
    },

    "movimientos_detalle": {
        "nombre": "Detalle de Movimientos",
        "descripcion": "Obtiene el detalle completo de movimientos",
        "parametros": ["@SUCURSAL", "@FECHA_INI", "@FECHA_FIN"],
        "sql": """
SELECT 
    E.Mv_Folio as Folio,
    E.Mv_Fecha as Fecha,
    S.Sc_Descripcion as Sucursal,
    A.Al_Descripcion as Almacen,
    TM.Tm_Cve_Tipo_Movimiento as Tipo_Codigo,
    TM.Tm_Descripcion as Tipo_Movimiento,
    TM.Tm_Tipo as Signo,
    P.Pr_Cve_Producto as Codigo,
    P.Pr_Descripcion as Producto,
    E.Mv_Cantidad_Control_1 as Cantidad,
    E.Mv_Costo as Costo,
    E.Mv_Costo_Importe as Importe
FROM Movimiento E
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = E.Sc_Cve_Sucursal
INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = E.Tm_Cve_Tipo_Movimiento
INNER JOIN Producto P ON P.Pr_Cve_Producto = E.Pr_Cve_Producto
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND E.Es_Cve_Estado <> 'CA'
    AND E.Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
ORDER BY E.Mv_Fecha DESC
"""
    },

    # ============= PEDIDOS =============
    "pedidos": {
        "nombre": "Pedidos",
        "descripcion": "Obtiene los pedidos a proveedores",
        "parametros": ["@SUCURSAL", "@FECHA_INI", "@FECHA_FIN"],
        "sql": """
SELECT 
    PD.Pd_Folio as Folio,
    PD.Pd_Fecha as Fecha,
    S.Sc_Descripcion as Sucursal,
    PR.Pv_Nombre as Proveedor,
    PD.Pd_Observaciones as Observaciones,
    PD.Es_Cve_Estado as Estado,
    COUNT(PDD.Pr_Cve_Producto) as Total_Productos,
    SUM(PDD.Pd_Importe) as Importe_Total
FROM Pedido PD
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = PD.Sc_Cve_Sucursal
LEFT JOIN Proveedor PR ON PR.Pv_Cve_Proveedor = PD.Pv_Cve_Proveedor
LEFT JOIN Pedido_Detalle PDD ON PDD.Pd_Folio = PD.Pd_Folio
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND PD.Pd_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
GROUP BY PD.Pd_Folio, PD.Pd_Fecha, S.Sc_Descripcion, PR.Pv_Nombre, PD.Pd_Observaciones, PD.Es_Cve_Estado
ORDER BY PD.Pd_Fecha DESC
"""
    },

    # ============= ORDENES DE COMPRA =============
    "ordenes_compra": {
        "nombre": "Órdenes de Compra",
        "descripcion": "Obtiene las órdenes de compra",
        "parametros": ["@SUCURSAL", "@FECHA_INI", "@FECHA_FIN"],
        "sql": """
SELECT 
    OC.Oc_Folio as Folio,
    OC.Oc_Fecha as Fecha,
    S.Sc_Descripcion as Sucursal,
    PR.Pv_Nombre as Proveedor,
    OC.Oc_Observaciones as Observaciones,
    OC.Es_Cve_Estado as Estado,
    SUM(OCD.Oc_Cantidad) as Total_Cantidad,
    SUM(OCD.Oc_Importe) as Importe_Total
FROM Orden_Compra OC
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = OC.Sc_Cve_Sucursal
LEFT JOIN Proveedor PR ON PR.Pv_Cve_Proveedor = OC.Pv_Cve_Proveedor
LEFT JOIN Orden_Compra_Detalle OCD ON OCD.Oc_Folio = OC.Oc_Folio
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND OC.Oc_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
GROUP BY OC.Oc_Folio, OC.Oc_Fecha, S.Sc_Descripcion, PR.Pv_Nombre, OC.Oc_Observaciones, OC.Es_Cve_Estado
ORDER BY OC.Oc_Fecha DESC
"""
    },

    # ============= PROVEEDORES =============
    "proveedores": {
        "nombre": "Catálogo de Proveedores",
        "descripcion": "Obtiene el catálogo completo de proveedores",
        "parametros": [],
        "sql": """
SELECT 
    Pv_Cve_Proveedor as Codigo,
    Pv_Descripcion as Nombre,
    Pv_Razon_Social as Razon_Social,
    Pv_R_F_C as RFC,
    Pv_Direccion_1 as Direccion,
    Pv_Telefono_1 as Telefono,
    Pv_email_contacto_1 as Email,
    Pv_Contacto_1 as Contacto,
    Pv_Dias_Credito as Dias_Credito,
    Es_Cve_Estado as Estado
FROM Proveedor
WHERE Es_Cve_Estado <> 'BA'
ORDER BY Pv_Descripcion
"""
    },

    # ============= PRODUCTOS =============
    "productos": {
        "nombre": "Catálogo de Productos",
        "descripcion": "Obtiene el catálogo completo de productos",
        "parametros": [],
        "sql": """
SELECT 
    P.Pr_Cve_Producto as Codigo,
    P.Pr_Descripcion as Producto,
    F.Fm_Descripcion as Familia,
    SF.Sf_Descripcion as SubFamilia,
    C.Ct_Descripcion as Categoria,
    D.Dp_Descripcion as Departamento,
    P.Pr_Unidad_Control_1 as Unidad,
    P.Pr_ultimo_costo as Ultimo_Costo,
    P.Pr_Precio_1 as Precio_1,
    P.Pr_Precio_2 as Precio_2,
    P.Pr_Stock_Minimo as Stock_Minimo,
    P.Pr_Stock_Maximo as Stock_Maximo,
    P.Es_Cve_Estado as Estado
FROM Producto P
INNER JOIN Familia F ON F.Fm_Cve_Familia = P.Fm_Cve_Familia
INNER JOIN SubFamilia SF ON SF.Sf_Cve_SubFamilia = P.Sf_Cve_SubFamilia
INNER JOIN Categoria C ON C.Ct_Cve_Categoria = P.Ct_Cve_Categoria
INNER JOIN Departamento D ON D.Dp_Cve_Departamento = P.Dp_Cve_Departamento
WHERE P.Es_Cve_Estado <> 'BA'
ORDER BY F.Fm_Descripcion, SF.Sf_Descripcion, P.Pr_Descripcion
"""
    },

    # ============= FAMILIAS =============
    "familias": {
        "nombre": "Catálogo de Familias",
        "descripcion": "Obtiene el catálogo de familias de productos",
        "parametros": [],
        "sql": """
SELECT 
    Fm_Cve_Familia as Codigo,
    Fm_Descripcion as Descripcion,
    Es_Cve_Estado as Estado
FROM Familia
WHERE Es_Cve_Estado <> 'BA'
ORDER BY Fm_Descripcion
"""
    },

    "subfamilias": {
        "nombre": "Catálogo de SubFamilias",
        "descripcion": "Obtiene el catálogo de subfamilias de productos",
        "parametros": [],
        "sql": """
SELECT 
    SF.Sf_Cve_SubFamilia as Codigo,
    SF.Sf_Descripcion as Descripcion,
    F.Fm_Descripcion as Familia,
    SF.Es_Cve_Estado as Estado
FROM SubFamilia SF
INNER JOIN Familia F ON F.Fm_Cve_Familia = SF.Fm_Cve_Familia
WHERE SF.Es_Cve_Estado <> 'BA'
ORDER BY F.Fm_Descripcion, SF.Sf_Descripcion
"""
    },

    # ============= CATEGORÍAS =============
    "categorias": {
        "nombre": "Catálogo de Categorías",
        "descripcion": "Obtiene el catálogo de categorías",
        "parametros": [],
        "sql": """
SELECT 
    Ct_Cve_Categoria as Codigo,
    Ct_Descripcion as Descripcion,
    Es_Cve_Estado as Estado
FROM Categoria
WHERE Es_Cve_Estado <> 'BA'
ORDER BY Ct_Descripcion
"""
    },

    # ============= DEPARTAMENTOS =============
    "departamentos": {
        "nombre": "Catálogo de Departamentos",
        "descripcion": "Obtiene el catálogo de departamentos",
        "parametros": [],
        "sql": """
SELECT 
    Dp_Cve_Departamento as Codigo,
    Dp_Descripcion as Descripcion,
    Es_Cve_Estado as Estado
FROM Departamento
WHERE Es_Cve_Estado <> 'BA'
ORDER BY Dp_Descripcion
"""
    },

    # ============= GRUPOS =============
    "grupos": {
        "nombre": "Catálogo de Grupos",
        "descripcion": "Obtiene el catálogo de grupos de productos",
        "parametros": [],
        "sql": """
SELECT 
    Gp_Cve_Grupo as Codigo,
    Gp_Descripcion as Descripcion,
    Es_Cve_Estado as Estado
FROM Grupo
WHERE Es_Cve_Estado <> 'BA'
ORDER BY Gp_Descripcion
"""
    },

    # ============= SUCURSALES =============
    "sucursales": {
        "nombre": "Catálogo de Sucursales",
        "descripcion": "Obtiene el catálogo de sucursales",
        "parametros": [],
        "sql": """
SELECT 
    Sc_Cve_Sucursal as Codigo,
    Sc_Descripcion as Nombre,
    Sc_Direccion as Direccion,
    Sc_Telefono as Telefono,
    Es_Cve_Estado as Estado
FROM Sucursal
WHERE Es_Cve_Estado <> 'BA'
ORDER BY Sc_Descripcion
"""
    },

    # ============= ALMACENES =============
    "almacenes": {
        "nombre": "Catálogo de Almacenes",
        "descripcion": "Obtiene el catálogo de almacenes por sucursal",
        "parametros": ["@SUCURSAL"],
        "sql": """
SELECT 
    A.Al_Cve_Almacen as Codigo,
    A.Al_Descripcion as Nombre,
    S.Sc_Descripcion as Sucursal,
    A.Es_Cve_Estado as Estado
FROM Almacen A
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE A.Es_Cve_Estado <> 'BA'
    AND S.Sc_Descripcion LIKE '%{sucursal}%'
ORDER BY S.Sc_Descripcion, A.Al_Descripcion
"""
    },

    # ============= INVENTARIO FÍSICO =============
    "inventario_fisico": {
        "nombre": "Inventario Físico",
        "descripcion": "Obtiene el inventario físico por folio",
        "parametros": ["@FOLIO"],
        "sql": """
SELECT 
    F.Fi_Folio as Folio,
    F.Fi_Fecha as Fecha,
    A.Al_Descripcion as Almacen,
    P.Pr_Cve_Producto as Codigo,
    P.Pr_Descripcion as Producto,
    F.Fi_Cantidad_Control_1 as Cantidad,
    F.Fi_Costo as Costo,
    F.Fi_Costo_Importe as Importe
FROM Fisico F
INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen
INNER JOIN Producto P ON P.Pr_Cve_Producto = F.Pr_Cve_Producto
WHERE F.Fi_Folio = '{folio}'
ORDER BY P.Pr_Descripcion
"""
    },

    # ============= TIPOS DE MOVIMIENTO =============
    "tipos_movimiento": {
        "nombre": "Catálogo de Tipos de Movimiento",
        "descripcion": "Obtiene el catálogo de tipos de movimiento",
        "parametros": [],
        "sql": """
SELECT 
    Tm_Cve_Tipo_Movimiento as Codigo,
    Tm_Descripcion as Descripcion,
    Tm_Tipo as Tipo,
    CASE WHEN Tm_Tipo IN ('+', 'EN') THEN 'Entrada' ELSE 'Salida' END as Tipo_Descripcion,
    Es_Cve_Estado as Estado
FROM Tipo_Movimiento
WHERE Es_Cve_Estado <> 'BA'
ORDER BY Tm_Cve_Tipo_Movimiento
"""
    }
}

# Estructura de tablas principales de MPRO
ESTRUCTURA_TABLAS_MPRO = {
    "Producto": {
        "descripcion": "Catálogo de productos",
        "campos_principales": [
            "Pr_Cve_Producto (PK) - Código del producto",
            "Pr_Descripcion - Nombre del producto",
            "Fm_Cve_Familia - Código de familia",
            "Sf_Cve_SubFamilia - Código de subfamilia",
            "Ct_Cve_Categoria - Código de categoría",
            "Dp_Cve_Departamento - Código de departamento",
            "Pr_Unidad_Control_1 - Unidad de medida",
            "Pr_ultimo_costo - Último costo",
            "Pr_Precio_1, Pr_Precio_2 - Precios de venta",
            "Es_Cve_Estado - Estado (BA=Baja, AC=Activo)"
        ]
    },
    "Venta": {
        "descripcion": "Detalle de ventas",
        "campos_principales": [
            "Vn_Folio - Folio de venta",
            "Vn_Fecha - Fecha de venta",
            "Sc_Cve_Sucursal - Sucursal",
            "Al_Cve_Almacen - Almacén",
            "Pr_Cve_Producto - Producto",
            "Vn_Cantidad_1 - Cantidad vendida",
            "Vn_Cantidad_Control_1 - Cantidad en unidad de control",
            "Vn_Precio - Precio de venta",
            "Vn_Importe - Importe total",
            "Es_Cve_Estado - Estado (CA=Cancelado)"
        ]
    },
    "Compra": {
        "descripcion": "Detalle de compras",
        "campos_principales": [
            "Co_Folio - Folio de compra",
            "Co_Fecha - Fecha de compra",
            "Sc_Cve_Sucursal - Sucursal",
            "Pv_Cve_Proveedor - Proveedor",
            "Pr_Cve_Producto - Producto",
            "Co_Cantidad_1 - Cantidad comprada",
            "Co_Costo - Costo unitario",
            "Co_Importe - Importe total",
            "Es_Cve_Estado - Estado"
        ]
    },
    "Movimiento": {
        "descripcion": "Movimientos de inventario",
        "campos_principales": [
            "Mv_Folio - Folio de movimiento",
            "Mv_Fecha - Fecha de movimiento",
            "Sc_Cve_Sucursal - Sucursal",
            "Al_Cve_Almacen - Almacén",
            "Tm_Cve_Tipo_Movimiento - Tipo de movimiento",
            "Pr_Cve_Producto - Producto",
            "Mv_Cantidad_Control_1 - Cantidad (+ entrada, - salida)",
            "Mv_Costo - Costo",
            "Mv_Costo_Importe - Importe",
            "Es_Cve_Estado - Estado"
        ]
    },
    "Fisico": {
        "descripcion": "Inventario físico",
        "campos_principales": [
            "Fi_Folio - Folio de inventario",
            "Fi_Fecha - Fecha del inventario",
            "Al_Cve_Almacen - Almacén",
            "Pr_Cve_Producto - Producto",
            "Fi_Cantidad_Control_1 - Cantidad contada",
            "Fi_Costo - Costo",
            "Fi_Costo_Importe - Importe"
        ]
    },
    "Proveedor": {
        "descripcion": "Catálogo de proveedores",
        "campos_principales": [
            "Pv_Cve_Proveedor (PK) - Código del proveedor",
            "Pv_Nombre - Nombre",
            "Pv_Razon_Social - Razón social",
            "Pv_RFC - RFC",
            "Pv_Direccion - Dirección",
            "Pv_Telefono - Teléfono",
            "Pv_Email - Email",
            "Pv_Contacto - Contacto"
        ]
    },
    "Producto_Kit": {
        "descripcion": "Componentes de productos kit",
        "campos_principales": [
            "Pr_Cve_Producto - Producto padre (kit)",
            "Pk_Producto - Producto componente",
            "Pk_Cantidad - Cantidad del componente",
            "Un_Cve_Unidad - Unidad de medida"
        ]
    }
}
