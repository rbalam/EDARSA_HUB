"""Snapshot de detalle operativo de Ventas del Dia para Comercial.

Este modulo solo define consultas del sincronizador autorizado de Ventas del Dia
y serializa su resultado para persistirlo dentro del snapshot EDARSAHUB.
Los endpoints de Comercial nunca consultan el POS directamente.

Compatibilidad:
- La columna persistida conserva el nombre legacy ``detalle_abiertas_json``.
- Para MPRO el payload contiene abiertas y cerradas del dia, porque el encabezado
  tambien combina ambos grupos desde la API local. Asi el drill-down puede
  conciliar con el total del encabezado sin leer CENTRAL2020 ni otro POS.
"""

from __future__ import annotations

import json
from modules.comercial_v2.ticket_contract import fields_from
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List


QUERY_SOFTRESTAURANT_DETALLE_ABIERTAS = """
SELECT
    MAX(CAST(CONVERT(nvarchar(100), d.movimiento) AS nvarchar(100))) AS partida_origen_id,
    MAX(CAST(NULL AS nvarchar(100))) AS partida_key,
    MAX(CAST(ch.idcliente AS nvarchar(100))) AS cliente_id,
    MAX(CAST(cl.nombre AS nvarchar(max))) AS cliente_nombre,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_razon_social,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_descripcion,
    MAX(CAST(NULL AS nvarchar(100))) AS cliente_maestro_id,
    MAX(CAST(NULL AS nvarchar(50))) AS cliente_sucursal_origen,
    MAX(CAST(cl.contacto AS nvarchar(max))) AS cliente_contacto,
    MAX(CAST(cl.rfc AS nvarchar(50))) AS cliente_rfc,
    MAX(CAST(cl.direccion AS nvarchar(max))) AS cliente_direccion_1,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_direccion_2,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_direccion_3,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_calle,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_numero_exterior,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_numero_interior,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_colonia,
    MAX(CAST(cl.poblacion AS nvarchar(max))) AS cliente_ciudad,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_municipio,
    MAX(CAST(cl.estado AS nvarchar(max))) AS cliente_estado,
    MAX(CAST(cl.pais AS nvarchar(max))) AS cliente_pais,
    MAX(CAST(cl.codigopostal AS nvarchar(max))) AS cliente_codigo_postal,
    MAX(CAST(ch.fecha AS datetime2)) AS ticket_fecha,
    MAX(CAST(ch.cierre AS datetime2)) AS ticket_fecha_cierre,
    MAX(CAST(ch.pagado AS tinyint)) AS ticket_pagado,
    MAX(CAST(ch.impreso AS tinyint)) AS ticket_impreso,
    MAX(CAST(ch.impresiones AS int)) AS ticket_impresiones,
    MAX(CAST(NULL AS nvarchar(max))) AS ticket_comentario,
    MAX(CAST(ch.comentariodescuento AS nvarchar(max))) AS ticket_comentario_descuento,
    MAX(CAST(NULL AS datetime2)) AS ticket_fecha_alta,
    MAX(CAST(NULL AS nvarchar(100))) AS ticket_oper_ult_modif,
    MAX(CAST(NULL AS nvarchar(100))) AS ticket_oper_baja,
    MAX(CAST(ch.fechacancelado AS datetime2)) AS ticket_fecha_baja,
    MAX(CAST(d.comentario AS nvarchar(max))) AS partida_comentario,
    MAX(CAST(d.comentariodescuento AS nvarchar(max))) AS partida_comentario_descuento,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario_cancelacion,
    MAX(CAST(NULL AS nvarchar(100))) AS partida_oper_baja,
    MAX(CAST(NULL AS datetime2)) AS partida_fecha_baja,
    MAX(CAST(d.idtipodescuento AS nvarchar(100))) AS tipo_descuento_id,
    MAX(CAST(td.desc_tipodescuento AS nvarchar(max))) AS tipo_descuento_descripcion,
    MAX(CAST(td.descuento AS decimal(18,6))) AS tipo_descuento_valor,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_cruzamiento_1,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_cruzamiento_2,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_entrega_direccion_1,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_entrega_direccion_2,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_entrega_direccion_3,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_entrega_ciudad,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_entrega_estado,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_entrega_pais,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_entrega_codigo_postal,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_colonia_origen_id,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_ciudad_origen_id,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_municipio_origen_id,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_estado_origen_id,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_pais_origen_id,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_codigo_postal_origen_id,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_latitud,
    MAX(CAST(NULL AS nvarchar(max))) AS cliente_longitud,
    COALESCE(
        NULLIF(MAX(LTRIM(RTRIM(CONVERT(varchar(64), ch.numcheque)))), ''),
        CONVERT(varchar(64), ch.folio)
    ) AS folio,
    CONVERT(varchar(64), ch.folio) AS folio_origen,
    'ABIERTA' AS estado_ticket,
    'SOFTRESTAURANT' AS sistema_origen,
    MIN(ch.fecha) AS fecha_hora,
    MAX(ISNULL(ch.nopersonas, 0)) AS pax,
    MAX(ISNULL(ch.propina, 0)) AS propina,
    MAX(CONVERT(varchar(50), ch.idmesero)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), m.nombre))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), ch.mesa))), '')) AS mesa,
    MAX(ISNULL(ch.total, 0)) AS total_ticket,
    MAX(ISNULL(ch.descuentoimporte, 0)) AS descuento_encabezado_reportado,
    MAX(ISNULL(ch.totaldescuentos, 0)) AS descuento_total_reportado,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.idproducto), ''),
        'SIN_CODIGO'
    ) AS producto_codigo,
    COALESCE(
        MAX(CONVERT(varchar(300), p.descripcion)),
        'VENTA SIN DETALLE DE PRODUCTO'
    ) AS producto_nombre,
    SUM(CAST(ISNULL(d.cantidad, 0) AS decimal(18,4))) AS cantidad,
    CASE
        WHEN SUM(CAST(ISNULL(d.cantidad, 0) AS decimal(18,4))) <> 0
        THEN
            SUM(
                CAST(
                    ISNULL(d.cantidad, 0) * ISNULL(d.precio, 0)
                    AS decimal(18,4)
                )
            )
            / SUM(CAST(ISNULL(d.cantidad, 0) AS decimal(18,4)))
        ELSE MAX(CAST(ISNULL(d.precio, 0) AS decimal(18,4)))
    END AS precio_unitario,
    SUM(
        CAST(
            ISNULL(d.cantidad, 0) * ISNULL(d.precio, 0)
            AS decimal(18,4)
        )
    ) AS importe_bruto,
    MAX(CAST(ISNULL(d.descuento, 0) AS decimal(18,4))) AS descuento_pct,
    SUM(
        CAST(
            ISNULL(d.cantidad, 0)
            * ISNULL(d.precio, 0)
            * (ISNULL(d.descuento, 0) / 100.0)
            AS decimal(18,4)
        )
    ) AS descuento_producto,
    SUM(
        CAST(
            ISNULL(d.cantidad, 0)
            * ISNULL(d.precio, 0)
            * (1 - (ISNULL(d.descuento, 0) / 100.0))
            AS decimal(18,4)
        )
    ) AS importe_neto_producto
FROM tempcheques ch
LEFT JOIN tempcheqdet d
    ON d.foliodet = ch.folio
LEFT JOIN clientes cl ON cl.idcliente=ch.idcliente
LEFT JOIN tipodescuento td ON td.idtipodescuento=d.idtipodescuento
LEFT JOIN meseros m
    ON m.idmesero = ch.idmesero
LEFT JOIN productos p
    ON p.idproducto = d.idproducto
WHERE ISNULL(ch.cancelado, 0) = 0
  AND ISNULL(ch.total, 0) >= 0
  AND ch.fecha >= CONVERT(
        DATETIME,
        REPLACE('{fecha_operacion}', '-', ''),
        112
    )
  AND ch.fecha < DATEADD(
        DAY,
        1,
        CONVERT(
            DATETIME,
            REPLACE('{fecha_operacion}', '-', ''),
            112
        )
    )
GROUP BY
    d.movimiento,
    ch.folio,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.idproducto), ''),
        'SIN_CODIGO'
    ),
    CAST(ISNULL(d.descuento, 0) AS decimal(18,4))
ORDER BY ch.folio, producto_codigo
"""


QUERY_MPRO_DETALLE_ABIERTAS = """
SELECT
    MAX(CAST(CONVERT(nvarchar(100), d.Cd_Id) AS nvarchar(100))) AS partida_origen_id,
    MAX(CAST(d.Cd_Key AS nvarchar(100))) AS partida_key,
    MAX(CAST(c.Cl_Cve_Cliente AS nvarchar(100))) AS cliente_id,
    MAX(CAST(COALESCE(NULLIF(cl.Cl_Razon_Social,''),NULLIF(cl.Cl_Descripcion,'')) AS nvarchar(max))) AS cliente_nombre,
    MAX(CAST(cl.Cl_Razon_Social AS nvarchar(max))) AS cliente_razon_social,
    MAX(CAST(cl.Cl_Descripcion AS nvarchar(max))) AS cliente_descripcion,
    MAX(CAST(cl.Cl_Cve_Maestro AS nvarchar(100))) AS cliente_maestro_id,
    MAX(CAST(cl.Sc_Cve_Sucursal AS nvarchar(50))) AS cliente_sucursal_origen,
    MAX(CAST(cl.Cl_Contacto_1 AS nvarchar(max))) AS cliente_contacto,
    MAX(CAST(cl.Cl_R_F_C AS nvarchar(50))) AS cliente_rfc,
    MAX(CAST(cl.Cl_Direccion_1 AS nvarchar(max))) AS cliente_direccion_1,
    MAX(CAST(cl.Cl_Direccion_2 AS nvarchar(max))) AS cliente_direccion_2,
    MAX(CAST(cl.Cl_Direccion_3 AS nvarchar(max))) AS cliente_direccion_3,
    MAX(CAST(cl.Cl_Calle AS nvarchar(max))) AS cliente_calle,
    MAX(CAST(cl.Cl_Numero_Exterior AS nvarchar(max))) AS cliente_numero_exterior,
    MAX(CAST(cl.Cl_Numero_Interior AS nvarchar(max))) AS cliente_numero_interior,
    MAX(CAST(cl.Cl_Colonia AS nvarchar(max))) AS cliente_colonia,
    MAX(CAST(cl.Cl_Ciudad AS nvarchar(max))) AS cliente_ciudad,
    MAX(CAST(cl.Cl_Municipio AS nvarchar(max))) AS cliente_municipio,
    MAX(CAST(cl.Cl_Estado AS nvarchar(max))) AS cliente_estado,
    MAX(CAST(cl.Cl_Pais AS nvarchar(max))) AS cliente_pais,
    MAX(CAST(cl.Cl_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal,
    MAX(CAST(c.Co_Fecha AS datetime2)) AS ticket_fecha,
    MAX(CAST(NULL AS datetime2)) AS ticket_fecha_cierre,
    MAX(CAST(NULL AS tinyint)) AS ticket_pagado,
    MAX(CAST(NULL AS tinyint)) AS ticket_impreso,
    MAX(CAST(NULL AS int)) AS ticket_impresiones,
    MAX(CAST(c.Co_Comentario AS nvarchar(max))) AS ticket_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS ticket_comentario_descuento,
    MAX(CAST(c.Fecha_Alta AS datetime2)) AS ticket_fecha_alta,
    MAX(CAST(c.Oper_Ult_Modif AS nvarchar(100))) AS ticket_oper_ult_modif,
    MAX(CAST(c.Oper_Baja AS nvarchar(100))) AS ticket_oper_baja,
    MAX(CAST(c.Fecha_Baja AS datetime2)) AS ticket_fecha_baja,
    MAX(CAST(d.Cd_Comentario AS nvarchar(max))) AS partida_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario_descuento,
    MAX(CAST(d.Cd_Comentario_Cancelacion AS nvarchar(max))) AS partida_comentario_cancelacion,
    MAX(CAST(d.Oper_Baja AS nvarchar(100))) AS partida_oper_baja,
    MAX(CAST(d.Fecha_Baja AS datetime2)) AS partida_fecha_baja,
    MAX(CAST(d.Cd_Tipo_Descuento AS nvarchar(100))) AS tipo_descuento_id,
    MAX(CAST(td.Td_Descripcion AS nvarchar(max))) AS tipo_descuento_descripcion,
    MAX(CAST(td.Td_Porcentaje AS decimal(18,6))) AS tipo_descuento_valor,
    MAX(CAST(cl.Cl_Cruzamiento_1 AS nvarchar(max))) AS cliente_cruzamiento_1,
    MAX(CAST(cl.Cl_Cruzamiento_2 AS nvarchar(max))) AS cliente_cruzamiento_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_1 AS nvarchar(max))) AS cliente_entrega_direccion_1,
    MAX(CAST(cl.Cl_Direccion_Entrega_2 AS nvarchar(max))) AS cliente_entrega_direccion_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_3 AS nvarchar(max))) AS cliente_entrega_direccion_3,
    MAX(CAST(cl.Cl_Ciudad_Entrega AS nvarchar(max))) AS cliente_entrega_ciudad,
    MAX(CAST(cl.Cl_Estado_Entrega AS nvarchar(max))) AS cliente_entrega_estado,
    MAX(CAST(cl.Cl_Pais_Entrega AS nvarchar(max))) AS cliente_entrega_pais,
    MAX(CAST(cl.Cl_Codigo_Postal_Entrega AS nvarchar(max))) AS cliente_entrega_codigo_postal,
    MAX(CAST(cl.Cl_Cve_Colonia AS nvarchar(max))) AS cliente_colonia_origen_id,
    MAX(CAST(cl.Cl_Cve_Ciudad AS nvarchar(max))) AS cliente_ciudad_origen_id,
    MAX(CAST(cl.Cl_Cve_Municipio AS nvarchar(max))) AS cliente_municipio_origen_id,
    MAX(CAST(cl.Cl_Cve_Estado AS nvarchar(max))) AS cliente_estado_origen_id,
    MAX(CAST(cl.Cl_Cve_Pais AS nvarchar(max))) AS cliente_pais_origen_id,
    MAX(CAST(cl.Cl_Cve_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal_origen_id,
    MAX(CAST(cl.Cl_Latitud AS nvarchar(max))) AS cliente_latitud,
    MAX(CAST(cl.Cl_Longitud AS nvarchar(max))) AS cliente_longitud,
    CONVERT(varchar(64), c.Co_Folio) AS folio,
    CONVERT(varchar(64), c.Co_Folio) AS folio_origen,
    'ABIERTA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(c.Co_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), c.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))))
        OVER (PARTITION BY c.Co_Folio) AS total_ticket,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    ) AS producto_codigo,
    COALESCE(
        MAX(CONVERT(varchar(300), d.Cd_Concepto)),
        'VENTA SIN DETALLE DE PRODUCTO'
    ) AS producto_nombre,
    SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) AS cantidad,
    CASE
        WHEN SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) <> 0
        THEN
            SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4)))
            / SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4)))
        ELSE MAX(CAST(ISNULL(d.Cd_Precio, 0) AS decimal(18,4)))
    END AS precio_unitario,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_bruto
FROM Comanda c
LEFT JOIN Comanda_Detalle d
    ON d.Co_Folio = c.Co_Folio
   AND ISNULL(d.Es_Cve_Estado, '') = 'AC'
   AND d.Fecha_Baja IS NULL
LEFT JOIN Cliente cl ON cl.Cl_Cve_Cliente=c.Cl_Cve_Cliente
LEFT JOIN Tipo_Descuento td ON td.Td_Cve_Tipo_Descuento=d.Cd_Tipo_Descuento
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = c.Vn_Cve_Vendedor
WHERE CAST(c.Co_Fecha AS date) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND c.Es_Cve_Estado IN ('AC', 'IM')
GROUP BY
    d.Cd_Id,
    c.Co_Folio,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    )
ORDER BY c.Co_Folio, producto_codigo
"""


# MPRO: detalle de tickets cerrados desde la MISMA API local del encabezado.
#
# La selección de cuál consulta usar se hace en sync_comercial_abiertas_v2_job.py
# con el mismo closed_sales_source que decide el total del encabezado:
# - CANONICAL_VENTA_ENCABEZADO -> esta consulta.
# - PROVISIONAL_COMANDA -> QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES.
QUERY_MPRO_DETALLE_CERRADAS_CANONICAS = """
WITH h AS (
    SELECT
        ve.Vn_Folio,
        ve.Vn_Documento,
        ve.Vn_Fecha,
        ve.Sc_Cve_Sucursal,
        ve.Vn_Cve_Vendedor,
        CAST(
            ISNULL(ve.Vn_Precio_Neto_Importe, 0)
            AS decimal(18,4)
        ) AS total_header,
        ISNULL(c.Co_Personas, 0) AS pax,
        ISNULL(c.Co_Propina, 0) AS propina,
        NULLIF(
            LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))),
            ''
        ) AS mesa,
        NULLIF(
            LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))),
            ''
        ) AS vendedor_nombre
    FROM Venta_Encabezado ve
    LEFT JOIN Comanda c
        ON c.Co_Folio = ve.Vn_Documento
       AND c.Sc_Cve_Sucursal = ve.Sc_Cve_Sucursal
    LEFT JOIN Vendedor vnd
        ON vnd.Vn_Cve_Vendedor = ve.Vn_Cve_Vendedor
    WHERE CAST(ve.Vn_Fecha AS date) = '{fecha_operacion}'
      AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
      AND ve.Es_Cve_Estado IN ('AC', 'FA')
      AND ve.Fecha_Baja IS NULL
),
t AS (
    SELECT
        Vn_Documento,
        MIN(Vn_Fecha) AS fecha_hora,
        MAX(pax) AS pax,
        MAX(propina) AS propina,
        MAX(CONVERT(varchar(100), Vn_Cve_Vendedor)) AS vendedor_id,
        MAX(vendedor_nombre) AS vendedor_nombre,
        MAX(mesa) AS mesa,
        SUM(total_header) AS total_ticket
    FROM h
    GROUP BY Vn_Documento
),
l AS (
    SELECT
        h.Vn_Documento,
        h.Vn_Folio AS venta_folio,
        d.Vn_ID AS venta_partida_id,
        MAX(CONVERT(varchar(64), h.Vn_Folio)) AS folio_origen,
        COALESCE(
            NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
            'SIN_CODIGO'
        ) AS producto_codigo,
        COALESCE(
            MAX(CONVERT(varchar(300), d.Vn_Concepto)),
            'VENTA SIN DETALLE DE PRODUCTO'
        ) AS producto_nombre,
        MAX(CASE WHEN d.Vn_Folio IS NULL THEN 0 ELSE 1 END) AS tiene_detalle,
        SUM(
            CAST(ISNULL(d.Vn_Cantidad_1, 0) AS decimal(18,4))
        ) AS cantidad,
        SUM(
            CAST(ISNULL(d.Vn_Precio_Lista_Importe, 0) AS decimal(18,4))
        ) AS importe_bruto,
        SUM(
            CAST(ISNULL(d.Vn_Descuento_Importe, 0) AS decimal(18,4))
        ) AS descuento_producto
    FROM h
    LEFT JOIN Venta d
        ON d.Vn_Folio = h.Vn_Folio
       AND d.Sc_Cve_Sucursal = h.Sc_Cve_Sucursal
    GROUP BY
        h.Vn_Documento,
        h.Vn_Folio,
        d.Vn_ID,
        COALESCE(
            NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
            'SIN_CODIGO'
        )
)
SELECT
    CONCAT(l.venta_folio,':',l.venta_partida_id) AS partida_origen_id,
    cd2.Cd_Key AS partida_key,
    c2.Cl_Cve_Cliente AS cliente_id,
    COALESCE(NULLIF(cl.Cl_Razon_Social,''),NULLIF(cl.Cl_Descripcion,'')) AS cliente_nombre,
    cl.Cl_Razon_Social AS cliente_razon_social,
    cl.Cl_Descripcion AS cliente_descripcion,
    cl.Cl_Cve_Maestro AS cliente_maestro_id,
    cl.Sc_Cve_Sucursal AS cliente_sucursal_origen,
    cl.Cl_Contacto_1 AS cliente_contacto,
    cl.Cl_R_F_C AS cliente_rfc,
    cl.Cl_Direccion_1 AS cliente_direccion_1,
    cl.Cl_Direccion_2 AS cliente_direccion_2,
    cl.Cl_Direccion_3 AS cliente_direccion_3,
    cl.Cl_Calle AS cliente_calle,
    cl.Cl_Numero_Exterior AS cliente_numero_exterior,
    cl.Cl_Numero_Interior AS cliente_numero_interior,
    cl.Cl_Colonia AS cliente_colonia,
    cl.Cl_Ciudad AS cliente_ciudad,
    cl.Cl_Municipio AS cliente_municipio,
    cl.Cl_Estado AS cliente_estado,
    cl.Cl_Pais AS cliente_pais,
    cl.Cl_Codigo_Postal AS cliente_codigo_postal,
    c2.Co_Fecha AS ticket_fecha,
    NULL AS ticket_fecha_cierre,
    NULL AS ticket_pagado,
    NULL AS ticket_impreso,
    NULL AS ticket_impresiones,
    c2.Co_Comentario AS ticket_comentario,
    NULL AS ticket_comentario_descuento,
    c2.Fecha_Alta AS ticket_fecha_alta,
    c2.Oper_Ult_Modif AS ticket_oper_ult_modif,
    c2.Oper_Baja AS ticket_oper_baja,
    c2.Fecha_Baja AS ticket_fecha_baja,
    cd2.Cd_Comentario AS partida_comentario,
    NULL AS partida_comentario_descuento,
    cd2.Cd_Comentario_Cancelacion AS partida_comentario_cancelacion,
    cd2.Oper_Baja AS partida_oper_baja,
    cd2.Fecha_Baja AS partida_fecha_baja,
    cd2.Cd_Tipo_Descuento AS tipo_descuento_id,
    td.Td_Descripcion AS tipo_descuento_descripcion,
    td.Td_Porcentaje AS tipo_descuento_valor,
    cl.Cl_Cruzamiento_1 AS cliente_cruzamiento_1,
    cl.Cl_Cruzamiento_2 AS cliente_cruzamiento_2,
    cl.Cl_Direccion_Entrega_1 AS cliente_entrega_direccion_1,
    cl.Cl_Direccion_Entrega_2 AS cliente_entrega_direccion_2,
    cl.Cl_Direccion_Entrega_3 AS cliente_entrega_direccion_3,
    cl.Cl_Ciudad_Entrega AS cliente_entrega_ciudad,
    cl.Cl_Estado_Entrega AS cliente_entrega_estado,
    cl.Cl_Pais_Entrega AS cliente_entrega_pais,
    cl.Cl_Codigo_Postal_Entrega AS cliente_entrega_codigo_postal,
    cl.Cl_Cve_Colonia AS cliente_colonia_origen_id,
    cl.Cl_Cve_Ciudad AS cliente_ciudad_origen_id,
    cl.Cl_Cve_Municipio AS cliente_municipio_origen_id,
    cl.Cl_Cve_Estado AS cliente_estado_origen_id,
    cl.Cl_Cve_Pais AS cliente_pais_origen_id,
    cl.Cl_Cve_Codigo_Postal AS cliente_codigo_postal_origen_id,
    cl.Cl_Latitud AS cliente_latitud,
    cl.Cl_Longitud AS cliente_longitud,
    CONVERT(varchar(64), t.Vn_Documento) AS folio,
    l.folio_origen,
    'CERRADA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    t.fecha_hora,
    t.pax,
    t.propina,
    t.vendedor_id,
    t.vendedor_nombre,
    t.mesa,
    t.total_ticket,
    l.producto_codigo,
    l.producto_nombre,
    CASE
        WHEN l.tiene_detalle = 0
        THEN CAST(1 AS decimal(18,4))
        ELSE l.cantidad
    END AS cantidad,
    CASE
        WHEN l.tiene_detalle = 0
        THEN t.total_ticket
        WHEN l.cantidad <> 0
        THEN l.importe_bruto / l.cantidad
        ELSE CAST(0 AS decimal(18,4))
    END AS precio_unitario,
    CASE
        WHEN l.tiene_detalle = 0
        THEN t.total_ticket
        ELSE l.importe_bruto
    END AS importe_bruto,
    CASE
        WHEN l.importe_bruto > 0
        THEN CAST(
            (l.descuento_producto * 100.0) / l.importe_bruto
            AS decimal(9,4)
        )
        ELSE CAST(0 AS decimal(9,4))
    END AS descuento_pct,
    CASE
        WHEN l.tiene_detalle = 0
        THEN CAST(0 AS decimal(18,4))
        ELSE l.descuento_producto
    END AS descuento_producto,
    CASE
        WHEN l.tiene_detalle = 0
        THEN t.total_ticket
        ELSE l.importe_bruto - l.descuento_producto
    END AS importe_neto_producto,
    CAST(0 AS decimal(18,4)) AS descuento_encabezado_reportado,
    CAST(0 AS decimal(18,4)) AS descuento_total_reportado
FROM t
INNER JOIN l
    ON l.Vn_Documento = t.Vn_Documento
LEFT JOIN Comanda c2 ON c2.Co_Folio=t.Vn_Documento
LEFT JOIN Cliente cl ON cl.Cl_Cve_Cliente=c2.Cl_Cve_Cliente
LEFT JOIN Venta vd2 ON vd2.Vn_Folio=l.venta_folio AND vd2.Vn_ID=l.venta_partida_id
LEFT JOIN Comanda_Detalle cd2 ON cd2.Co_Folio=vd2.Vn_Documento AND cd2.Cd_Id=vd2.Vn_Documento_ID AND vd2.Vn_Tabla='Comanda'
LEFT JOIN Tipo_Descuento td ON td.Td_Cve_Tipo_Descuento=cd2.Cd_Tipo_Descuento
ORDER BY t.Vn_Documento, l.producto_codigo
"""


QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_COMANDA = """
SELECT
    MAX(CAST(CONVERT(nvarchar(100), d.Cd_Id) AS nvarchar(100))) AS partida_origen_id,
    MAX(CAST(d.Cd_Key AS nvarchar(100))) AS partida_key,
    MAX(CAST(c.Cl_Cve_Cliente AS nvarchar(100))) AS cliente_id,
    MAX(CAST(COALESCE(NULLIF(cl.Cl_Razon_Social,''),NULLIF(cl.Cl_Descripcion,'')) AS nvarchar(max))) AS cliente_nombre,
    MAX(CAST(cl.Cl_Razon_Social AS nvarchar(max))) AS cliente_razon_social,
    MAX(CAST(cl.Cl_Descripcion AS nvarchar(max))) AS cliente_descripcion,
    MAX(CAST(cl.Cl_Cve_Maestro AS nvarchar(100))) AS cliente_maestro_id,
    MAX(CAST(cl.Sc_Cve_Sucursal AS nvarchar(50))) AS cliente_sucursal_origen,
    MAX(CAST(cl.Cl_Contacto_1 AS nvarchar(max))) AS cliente_contacto,
    MAX(CAST(cl.Cl_R_F_C AS nvarchar(50))) AS cliente_rfc,
    MAX(CAST(cl.Cl_Direccion_1 AS nvarchar(max))) AS cliente_direccion_1,
    MAX(CAST(cl.Cl_Direccion_2 AS nvarchar(max))) AS cliente_direccion_2,
    MAX(CAST(cl.Cl_Direccion_3 AS nvarchar(max))) AS cliente_direccion_3,
    MAX(CAST(cl.Cl_Calle AS nvarchar(max))) AS cliente_calle,
    MAX(CAST(cl.Cl_Numero_Exterior AS nvarchar(max))) AS cliente_numero_exterior,
    MAX(CAST(cl.Cl_Numero_Interior AS nvarchar(max))) AS cliente_numero_interior,
    MAX(CAST(cl.Cl_Colonia AS nvarchar(max))) AS cliente_colonia,
    MAX(CAST(cl.Cl_Ciudad AS nvarchar(max))) AS cliente_ciudad,
    MAX(CAST(cl.Cl_Municipio AS nvarchar(max))) AS cliente_municipio,
    MAX(CAST(cl.Cl_Estado AS nvarchar(max))) AS cliente_estado,
    MAX(CAST(cl.Cl_Pais AS nvarchar(max))) AS cliente_pais,
    MAX(CAST(cl.Cl_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal,
    MAX(CAST(c.Co_Fecha AS datetime2)) AS ticket_fecha,
    MAX(CAST(NULL AS datetime2)) AS ticket_fecha_cierre,
    MAX(CAST(NULL AS tinyint)) AS ticket_pagado,
    MAX(CAST(NULL AS tinyint)) AS ticket_impreso,
    MAX(CAST(NULL AS int)) AS ticket_impresiones,
    MAX(CAST(c.Co_Comentario AS nvarchar(max))) AS ticket_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS ticket_comentario_descuento,
    MAX(CAST(c.Fecha_Alta AS datetime2)) AS ticket_fecha_alta,
    MAX(CAST(c.Oper_Ult_Modif AS nvarchar(100))) AS ticket_oper_ult_modif,
    MAX(CAST(c.Oper_Baja AS nvarchar(100))) AS ticket_oper_baja,
    MAX(CAST(c.Fecha_Baja AS datetime2)) AS ticket_fecha_baja,
    MAX(CAST(d.Cd_Comentario AS nvarchar(max))) AS partida_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario_descuento,
    MAX(CAST(d.Cd_Comentario_Cancelacion AS nvarchar(max))) AS partida_comentario_cancelacion,
    MAX(CAST(d.Oper_Baja AS nvarchar(100))) AS partida_oper_baja,
    MAX(CAST(d.Fecha_Baja AS datetime2)) AS partida_fecha_baja,
    MAX(CAST(d.Cd_Tipo_Descuento AS nvarchar(100))) AS tipo_descuento_id,
    MAX(CAST(td.Td_Descripcion AS nvarchar(max))) AS tipo_descuento_descripcion,
    MAX(CAST(td.Td_Porcentaje AS decimal(18,6))) AS tipo_descuento_valor,
    MAX(CAST(cl.Cl_Cruzamiento_1 AS nvarchar(max))) AS cliente_cruzamiento_1,
    MAX(CAST(cl.Cl_Cruzamiento_2 AS nvarchar(max))) AS cliente_cruzamiento_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_1 AS nvarchar(max))) AS cliente_entrega_direccion_1,
    MAX(CAST(cl.Cl_Direccion_Entrega_2 AS nvarchar(max))) AS cliente_entrega_direccion_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_3 AS nvarchar(max))) AS cliente_entrega_direccion_3,
    MAX(CAST(cl.Cl_Ciudad_Entrega AS nvarchar(max))) AS cliente_entrega_ciudad,
    MAX(CAST(cl.Cl_Estado_Entrega AS nvarchar(max))) AS cliente_entrega_estado,
    MAX(CAST(cl.Cl_Pais_Entrega AS nvarchar(max))) AS cliente_entrega_pais,
    MAX(CAST(cl.Cl_Codigo_Postal_Entrega AS nvarchar(max))) AS cliente_entrega_codigo_postal,
    MAX(CAST(cl.Cl_Cve_Colonia AS nvarchar(max))) AS cliente_colonia_origen_id,
    MAX(CAST(cl.Cl_Cve_Ciudad AS nvarchar(max))) AS cliente_ciudad_origen_id,
    MAX(CAST(cl.Cl_Cve_Municipio AS nvarchar(max))) AS cliente_municipio_origen_id,
    MAX(CAST(cl.Cl_Cve_Estado AS nvarchar(max))) AS cliente_estado_origen_id,
    MAX(CAST(cl.Cl_Cve_Pais AS nvarchar(max))) AS cliente_pais_origen_id,
    MAX(CAST(cl.Cl_Cve_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal_origen_id,
    MAX(CAST(cl.Cl_Latitud AS nvarchar(max))) AS cliente_latitud,
    MAX(CAST(cl.Cl_Longitud AS nvarchar(max))) AS cliente_longitud,
    CONVERT(varchar(64), c.Co_Folio) AS folio,
    CONVERT(varchar(64), c.Co_Folio) AS folio_origen,
    'CERRADA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(c.Co_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), c.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))))
        OVER (PARTITION BY c.Co_Folio) AS total_ticket,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    ) AS producto_codigo,
    COALESCE(
        MAX(CONVERT(varchar(300), d.Cd_Concepto)),
        'VENTA SIN DETALLE DE PRODUCTO'
    ) AS producto_nombre,
    SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) AS cantidad,
    CASE
        WHEN SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) <> 0
        THEN
            SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4)))
            / SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4)))
        ELSE MAX(CAST(ISNULL(d.Cd_Precio, 0) AS decimal(18,4)))
    END AS precio_unitario,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_bruto,
    CAST(0 AS decimal(9,4)) AS descuento_pct,
    CAST(0 AS decimal(18,4)) AS descuento_producto,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_neto_producto,
    CAST(0 AS decimal(18,4)) AS descuento_encabezado_reportado,
    CAST(0 AS decimal(18,4)) AS descuento_total_reportado
FROM Comanda c
INNER JOIN Comanda_Detalle d
    ON d.Co_Folio = c.Co_Folio
   AND d.Es_Cve_Estado = 'AC'
   AND d.Fecha_Baja IS NULL
LEFT JOIN Cliente cl ON cl.Cl_Cve_Cliente=c.Cl_Cve_Cliente
LEFT JOIN Tipo_Descuento td ON td.Td_Cve_Tipo_Descuento=d.Cd_Tipo_Descuento
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = c.Vn_Cve_Vendedor
WHERE CAST(c.Co_Fecha AS date) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND EXISTS (
      SELECT 1
      FROM Venta_Encabezado ve
      WHERE ve.Vn_Documento = c.Co_Folio
        AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
        AND CAST(ve.Vn_Fecha AS date) = '{fecha_operacion}'
        AND ve.Es_Cve_Estado IN ('AC', 'FA')
        AND ve.Fecha_Baja IS NULL
  )
GROUP BY
    d.Cd_Id,
    c.Co_Folio,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    )
ORDER BY c.Co_Folio, producto_codigo
"""


QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES = """
SELECT
    MAX(CAST(CONVERT(nvarchar(100), d.Cd_Id) AS nvarchar(100))) AS partida_origen_id,
    MAX(CAST(d.Cd_Key AS nvarchar(100))) AS partida_key,
    MAX(CAST(c.Cl_Cve_Cliente AS nvarchar(100))) AS cliente_id,
    MAX(CAST(COALESCE(NULLIF(cl.Cl_Razon_Social,''),NULLIF(cl.Cl_Descripcion,'')) AS nvarchar(max))) AS cliente_nombre,
    MAX(CAST(cl.Cl_Razon_Social AS nvarchar(max))) AS cliente_razon_social,
    MAX(CAST(cl.Cl_Descripcion AS nvarchar(max))) AS cliente_descripcion,
    MAX(CAST(cl.Cl_Cve_Maestro AS nvarchar(100))) AS cliente_maestro_id,
    MAX(CAST(cl.Sc_Cve_Sucursal AS nvarchar(50))) AS cliente_sucursal_origen,
    MAX(CAST(cl.Cl_Contacto_1 AS nvarchar(max))) AS cliente_contacto,
    MAX(CAST(cl.Cl_R_F_C AS nvarchar(50))) AS cliente_rfc,
    MAX(CAST(cl.Cl_Direccion_1 AS nvarchar(max))) AS cliente_direccion_1,
    MAX(CAST(cl.Cl_Direccion_2 AS nvarchar(max))) AS cliente_direccion_2,
    MAX(CAST(cl.Cl_Direccion_3 AS nvarchar(max))) AS cliente_direccion_3,
    MAX(CAST(cl.Cl_Calle AS nvarchar(max))) AS cliente_calle,
    MAX(CAST(cl.Cl_Numero_Exterior AS nvarchar(max))) AS cliente_numero_exterior,
    MAX(CAST(cl.Cl_Numero_Interior AS nvarchar(max))) AS cliente_numero_interior,
    MAX(CAST(cl.Cl_Colonia AS nvarchar(max))) AS cliente_colonia,
    MAX(CAST(cl.Cl_Ciudad AS nvarchar(max))) AS cliente_ciudad,
    MAX(CAST(cl.Cl_Municipio AS nvarchar(max))) AS cliente_municipio,
    MAX(CAST(cl.Cl_Estado AS nvarchar(max))) AS cliente_estado,
    MAX(CAST(cl.Cl_Pais AS nvarchar(max))) AS cliente_pais,
    MAX(CAST(cl.Cl_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal,
    MAX(CAST(c.Co_Fecha AS datetime2)) AS ticket_fecha,
    MAX(CAST(NULL AS datetime2)) AS ticket_fecha_cierre,
    MAX(CAST(NULL AS tinyint)) AS ticket_pagado,
    MAX(CAST(NULL AS tinyint)) AS ticket_impreso,
    MAX(CAST(NULL AS int)) AS ticket_impresiones,
    MAX(CAST(c.Co_Comentario AS nvarchar(max))) AS ticket_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS ticket_comentario_descuento,
    MAX(CAST(c.Fecha_Alta AS datetime2)) AS ticket_fecha_alta,
    MAX(CAST(c.Oper_Ult_Modif AS nvarchar(100))) AS ticket_oper_ult_modif,
    MAX(CAST(c.Oper_Baja AS nvarchar(100))) AS ticket_oper_baja,
    MAX(CAST(c.Fecha_Baja AS datetime2)) AS ticket_fecha_baja,
    MAX(CAST(d.Cd_Comentario AS nvarchar(max))) AS partida_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario_descuento,
    MAX(CAST(d.Cd_Comentario_Cancelacion AS nvarchar(max))) AS partida_comentario_cancelacion,
    MAX(CAST(d.Oper_Baja AS nvarchar(100))) AS partida_oper_baja,
    MAX(CAST(d.Fecha_Baja AS datetime2)) AS partida_fecha_baja,
    MAX(CAST(d.Cd_Tipo_Descuento AS nvarchar(100))) AS tipo_descuento_id,
    MAX(CAST(td.Td_Descripcion AS nvarchar(max))) AS tipo_descuento_descripcion,
    MAX(CAST(td.Td_Porcentaje AS decimal(18,6))) AS tipo_descuento_valor,
    MAX(CAST(cl.Cl_Cruzamiento_1 AS nvarchar(max))) AS cliente_cruzamiento_1,
    MAX(CAST(cl.Cl_Cruzamiento_2 AS nvarchar(max))) AS cliente_cruzamiento_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_1 AS nvarchar(max))) AS cliente_entrega_direccion_1,
    MAX(CAST(cl.Cl_Direccion_Entrega_2 AS nvarchar(max))) AS cliente_entrega_direccion_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_3 AS nvarchar(max))) AS cliente_entrega_direccion_3,
    MAX(CAST(cl.Cl_Ciudad_Entrega AS nvarchar(max))) AS cliente_entrega_ciudad,
    MAX(CAST(cl.Cl_Estado_Entrega AS nvarchar(max))) AS cliente_entrega_estado,
    MAX(CAST(cl.Cl_Pais_Entrega AS nvarchar(max))) AS cliente_entrega_pais,
    MAX(CAST(cl.Cl_Codigo_Postal_Entrega AS nvarchar(max))) AS cliente_entrega_codigo_postal,
    MAX(CAST(cl.Cl_Cve_Colonia AS nvarchar(max))) AS cliente_colonia_origen_id,
    MAX(CAST(cl.Cl_Cve_Ciudad AS nvarchar(max))) AS cliente_ciudad_origen_id,
    MAX(CAST(cl.Cl_Cve_Municipio AS nvarchar(max))) AS cliente_municipio_origen_id,
    MAX(CAST(cl.Cl_Cve_Estado AS nvarchar(max))) AS cliente_estado_origen_id,
    MAX(CAST(cl.Cl_Cve_Pais AS nvarchar(max))) AS cliente_pais_origen_id,
    MAX(CAST(cl.Cl_Cve_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal_origen_id,
    MAX(CAST(cl.Cl_Latitud AS nvarchar(max))) AS cliente_latitud,
    MAX(CAST(cl.Cl_Longitud AS nvarchar(max))) AS cliente_longitud,
    CONVERT(varchar(64), c.Co_Folio) AS folio,
    CONVERT(varchar(64), c.Co_Folio) AS folio_origen,
    'CERRADA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(c.Co_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), c.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))))
        OVER (PARTITION BY c.Co_Folio) AS total_ticket,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    ) AS producto_codigo,
    COALESCE(
        MAX(CONVERT(varchar(300), d.Cd_Concepto)),
        'VENTA SIN DETALLE DE PRODUCTO'
    ) AS producto_nombre,
    SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) AS cantidad,
    CASE
        WHEN SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) <> 0
        THEN
            SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4)))
            / SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4)))
        ELSE MAX(CAST(ISNULL(d.Cd_Precio, 0) AS decimal(18,4)))
    END AS precio_unitario,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_bruto
FROM Comanda c
LEFT JOIN Comanda_Detalle d
    ON d.Co_Folio = c.Co_Folio
   AND ISNULL(d.Es_Cve_Estado, '') = 'AC'
   AND d.Fecha_Baja IS NULL
LEFT JOIN Cliente cl ON cl.Cl_Cve_Cliente=c.Cl_Cve_Cliente
LEFT JOIN Tipo_Descuento td ON td.Td_Cve_Tipo_Descuento=d.Cd_Tipo_Descuento
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = c.Vn_Cve_Vendedor
WHERE CAST(c.Co_Fecha AS date) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND c.Es_Cve_Estado = 'PA'
GROUP BY
    d.Cd_Id,
    c.Co_Folio,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    )
ORDER BY c.Co_Folio, producto_codigo
"""


# Fallbacks resumidos MPRO.
#
# Se usan cuando la consulta de detalle por producto no puede materializar
# todos los folios que ya fueron contados por el encabezado del mismo ciclo.
# Mantienen exactamente la identidad, total, PAX y vendedor del ticket y
# evitan conservar un detalle viejo mientras el encabezado avanza.
QUERY_MPRO_DETALLE_ABIERTAS_RESUMEN = """
SELECT
    MAX(CAST(NULL AS nvarchar(100))) AS partida_origen_id,
    MAX(CAST(NULL AS nvarchar(100))) AS partida_key,
    MAX(CAST(c.Cl_Cve_Cliente AS nvarchar(100))) AS cliente_id,
    MAX(CAST(COALESCE(NULLIF(cl.Cl_Razon_Social,''),NULLIF(cl.Cl_Descripcion,'')) AS nvarchar(max))) AS cliente_nombre,
    MAX(CAST(cl.Cl_Razon_Social AS nvarchar(max))) AS cliente_razon_social,
    MAX(CAST(cl.Cl_Descripcion AS nvarchar(max))) AS cliente_descripcion,
    MAX(CAST(cl.Cl_Cve_Maestro AS nvarchar(100))) AS cliente_maestro_id,
    MAX(CAST(cl.Sc_Cve_Sucursal AS nvarchar(50))) AS cliente_sucursal_origen,
    MAX(CAST(cl.Cl_Contacto_1 AS nvarchar(max))) AS cliente_contacto,
    MAX(CAST(cl.Cl_R_F_C AS nvarchar(50))) AS cliente_rfc,
    MAX(CAST(cl.Cl_Direccion_1 AS nvarchar(max))) AS cliente_direccion_1,
    MAX(CAST(cl.Cl_Direccion_2 AS nvarchar(max))) AS cliente_direccion_2,
    MAX(CAST(cl.Cl_Direccion_3 AS nvarchar(max))) AS cliente_direccion_3,
    MAX(CAST(cl.Cl_Calle AS nvarchar(max))) AS cliente_calle,
    MAX(CAST(cl.Cl_Numero_Exterior AS nvarchar(max))) AS cliente_numero_exterior,
    MAX(CAST(cl.Cl_Numero_Interior AS nvarchar(max))) AS cliente_numero_interior,
    MAX(CAST(cl.Cl_Colonia AS nvarchar(max))) AS cliente_colonia,
    MAX(CAST(cl.Cl_Ciudad AS nvarchar(max))) AS cliente_ciudad,
    MAX(CAST(cl.Cl_Municipio AS nvarchar(max))) AS cliente_municipio,
    MAX(CAST(cl.Cl_Estado AS nvarchar(max))) AS cliente_estado,
    MAX(CAST(cl.Cl_Pais AS nvarchar(max))) AS cliente_pais,
    MAX(CAST(cl.Cl_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal,
    MAX(CAST(c.Co_Fecha AS datetime2)) AS ticket_fecha,
    MAX(CAST(NULL AS datetime2)) AS ticket_fecha_cierre,
    MAX(CAST(NULL AS tinyint)) AS ticket_pagado,
    MAX(CAST(NULL AS tinyint)) AS ticket_impreso,
    MAX(CAST(NULL AS int)) AS ticket_impresiones,
    MAX(CAST(c.Co_Comentario AS nvarchar(max))) AS ticket_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS ticket_comentario_descuento,
    MAX(CAST(c.Fecha_Alta AS datetime2)) AS ticket_fecha_alta,
    MAX(CAST(c.Oper_Ult_Modif AS nvarchar(100))) AS ticket_oper_ult_modif,
    MAX(CAST(c.Oper_Baja AS nvarchar(100))) AS ticket_oper_baja,
    MAX(CAST(c.Fecha_Baja AS datetime2)) AS ticket_fecha_baja,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario_descuento,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario_cancelacion,
    MAX(CAST(NULL AS nvarchar(100))) AS partida_oper_baja,
    MAX(CAST(NULL AS datetime2)) AS partida_fecha_baja,
    MAX(CAST(NULL AS nvarchar(100))) AS tipo_descuento_id,
    MAX(CAST(NULL AS nvarchar(max))) AS tipo_descuento_descripcion,
    MAX(CAST(NULL AS decimal(18,6))) AS tipo_descuento_valor,
    MAX(CAST(cl.Cl_Cruzamiento_1 AS nvarchar(max))) AS cliente_cruzamiento_1,
    MAX(CAST(cl.Cl_Cruzamiento_2 AS nvarchar(max))) AS cliente_cruzamiento_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_1 AS nvarchar(max))) AS cliente_entrega_direccion_1,
    MAX(CAST(cl.Cl_Direccion_Entrega_2 AS nvarchar(max))) AS cliente_entrega_direccion_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_3 AS nvarchar(max))) AS cliente_entrega_direccion_3,
    MAX(CAST(cl.Cl_Ciudad_Entrega AS nvarchar(max))) AS cliente_entrega_ciudad,
    MAX(CAST(cl.Cl_Estado_Entrega AS nvarchar(max))) AS cliente_entrega_estado,
    MAX(CAST(cl.Cl_Pais_Entrega AS nvarchar(max))) AS cliente_entrega_pais,
    MAX(CAST(cl.Cl_Codigo_Postal_Entrega AS nvarchar(max))) AS cliente_entrega_codigo_postal,
    MAX(CAST(cl.Cl_Cve_Colonia AS nvarchar(max))) AS cliente_colonia_origen_id,
    MAX(CAST(cl.Cl_Cve_Ciudad AS nvarchar(max))) AS cliente_ciudad_origen_id,
    MAX(CAST(cl.Cl_Cve_Municipio AS nvarchar(max))) AS cliente_municipio_origen_id,
    MAX(CAST(cl.Cl_Cve_Estado AS nvarchar(max))) AS cliente_estado_origen_id,
    MAX(CAST(cl.Cl_Cve_Pais AS nvarchar(max))) AS cliente_pais_origen_id,
    MAX(CAST(cl.Cl_Cve_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal_origen_id,
    MAX(CAST(cl.Cl_Latitud AS nvarchar(max))) AS cliente_latitud,
    MAX(CAST(cl.Cl_Longitud AS nvarchar(max))) AS cliente_longitud,
    CONVERT(varchar(64), c.Co_Folio) AS folio,
    CONVERT(varchar(64), c.Co_Folio) AS folio_origen,
    'ABIERTA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(c.Co_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), c.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS total_ticket,
    'SIN_CODIGO' AS producto_codigo,
    'CUENTA ABIERTA MPRO - DETALLE RESUMIDO' AS producto_nombre,
    CAST(1 AS decimal(18,4)) AS cantidad,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS precio_unitario,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_bruto,
    CAST(0 AS decimal(9,4)) AS descuento_pct,
    CAST(0 AS decimal(18,4)) AS descuento_producto,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_neto_producto,
    CAST(0 AS decimal(18,4)) AS descuento_encabezado_reportado,
    CAST(0 AS decimal(18,4)) AS descuento_total_reportado
FROM Comanda c
INNER JOIN Comanda_Detalle d
    ON d.Co_Folio = c.Co_Folio
   AND d.Es_Cve_Estado = 'AC'
   AND d.Fecha_Baja IS NULL
LEFT JOIN Cliente cl ON cl.Cl_Cve_Cliente=c.Cl_Cve_Cliente
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = c.Vn_Cve_Vendedor
WHERE CAST(c.Co_Fecha AS date) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND c.Es_Cve_Estado IN ('AC', 'IM')
GROUP BY c.Co_Folio
ORDER BY c.Co_Folio
"""


QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_RESUMEN = """
SELECT
    MAX(CAST(NULL AS nvarchar(100))) AS partida_origen_id,
    MAX(CAST(NULL AS nvarchar(100))) AS partida_key,
    MAX(CAST(c.Cl_Cve_Cliente AS nvarchar(100))) AS cliente_id,
    MAX(CAST(COALESCE(NULLIF(cl.Cl_Razon_Social,''),NULLIF(cl.Cl_Descripcion,'')) AS nvarchar(max))) AS cliente_nombre,
    MAX(CAST(cl.Cl_Razon_Social AS nvarchar(max))) AS cliente_razon_social,
    MAX(CAST(cl.Cl_Descripcion AS nvarchar(max))) AS cliente_descripcion,
    MAX(CAST(cl.Cl_Cve_Maestro AS nvarchar(100))) AS cliente_maestro_id,
    MAX(CAST(cl.Sc_Cve_Sucursal AS nvarchar(50))) AS cliente_sucursal_origen,
    MAX(CAST(cl.Cl_Contacto_1 AS nvarchar(max))) AS cliente_contacto,
    MAX(CAST(cl.Cl_R_F_C AS nvarchar(50))) AS cliente_rfc,
    MAX(CAST(cl.Cl_Direccion_1 AS nvarchar(max))) AS cliente_direccion_1,
    MAX(CAST(cl.Cl_Direccion_2 AS nvarchar(max))) AS cliente_direccion_2,
    MAX(CAST(cl.Cl_Direccion_3 AS nvarchar(max))) AS cliente_direccion_3,
    MAX(CAST(cl.Cl_Calle AS nvarchar(max))) AS cliente_calle,
    MAX(CAST(cl.Cl_Numero_Exterior AS nvarchar(max))) AS cliente_numero_exterior,
    MAX(CAST(cl.Cl_Numero_Interior AS nvarchar(max))) AS cliente_numero_interior,
    MAX(CAST(cl.Cl_Colonia AS nvarchar(max))) AS cliente_colonia,
    MAX(CAST(cl.Cl_Ciudad AS nvarchar(max))) AS cliente_ciudad,
    MAX(CAST(cl.Cl_Municipio AS nvarchar(max))) AS cliente_municipio,
    MAX(CAST(cl.Cl_Estado AS nvarchar(max))) AS cliente_estado,
    MAX(CAST(cl.Cl_Pais AS nvarchar(max))) AS cliente_pais,
    MAX(CAST(cl.Cl_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal,
    MAX(CAST(c.Co_Fecha AS datetime2)) AS ticket_fecha,
    MAX(CAST(NULL AS datetime2)) AS ticket_fecha_cierre,
    MAX(CAST(NULL AS tinyint)) AS ticket_pagado,
    MAX(CAST(NULL AS tinyint)) AS ticket_impreso,
    MAX(CAST(NULL AS int)) AS ticket_impresiones,
    MAX(CAST(c.Co_Comentario AS nvarchar(max))) AS ticket_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS ticket_comentario_descuento,
    MAX(CAST(c.Fecha_Alta AS datetime2)) AS ticket_fecha_alta,
    MAX(CAST(c.Oper_Ult_Modif AS nvarchar(100))) AS ticket_oper_ult_modif,
    MAX(CAST(c.Oper_Baja AS nvarchar(100))) AS ticket_oper_baja,
    MAX(CAST(c.Fecha_Baja AS datetime2)) AS ticket_fecha_baja,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario_descuento,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario_cancelacion,
    MAX(CAST(NULL AS nvarchar(100))) AS partida_oper_baja,
    MAX(CAST(NULL AS datetime2)) AS partida_fecha_baja,
    MAX(CAST(NULL AS nvarchar(100))) AS tipo_descuento_id,
    MAX(CAST(NULL AS nvarchar(max))) AS tipo_descuento_descripcion,
    MAX(CAST(NULL AS decimal(18,6))) AS tipo_descuento_valor,
    MAX(CAST(cl.Cl_Cruzamiento_1 AS nvarchar(max))) AS cliente_cruzamiento_1,
    MAX(CAST(cl.Cl_Cruzamiento_2 AS nvarchar(max))) AS cliente_cruzamiento_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_1 AS nvarchar(max))) AS cliente_entrega_direccion_1,
    MAX(CAST(cl.Cl_Direccion_Entrega_2 AS nvarchar(max))) AS cliente_entrega_direccion_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_3 AS nvarchar(max))) AS cliente_entrega_direccion_3,
    MAX(CAST(cl.Cl_Ciudad_Entrega AS nvarchar(max))) AS cliente_entrega_ciudad,
    MAX(CAST(cl.Cl_Estado_Entrega AS nvarchar(max))) AS cliente_entrega_estado,
    MAX(CAST(cl.Cl_Pais_Entrega AS nvarchar(max))) AS cliente_entrega_pais,
    MAX(CAST(cl.Cl_Codigo_Postal_Entrega AS nvarchar(max))) AS cliente_entrega_codigo_postal,
    MAX(CAST(cl.Cl_Cve_Colonia AS nvarchar(max))) AS cliente_colonia_origen_id,
    MAX(CAST(cl.Cl_Cve_Ciudad AS nvarchar(max))) AS cliente_ciudad_origen_id,
    MAX(CAST(cl.Cl_Cve_Municipio AS nvarchar(max))) AS cliente_municipio_origen_id,
    MAX(CAST(cl.Cl_Cve_Estado AS nvarchar(max))) AS cliente_estado_origen_id,
    MAX(CAST(cl.Cl_Cve_Pais AS nvarchar(max))) AS cliente_pais_origen_id,
    MAX(CAST(cl.Cl_Cve_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal_origen_id,
    MAX(CAST(cl.Cl_Latitud AS nvarchar(max))) AS cliente_latitud,
    MAX(CAST(cl.Cl_Longitud AS nvarchar(max))) AS cliente_longitud,
    CONVERT(varchar(64), ve.Vn_Documento) AS folio,
    MAX(CONVERT(varchar(64), ve.Vn_Folio)) AS folio_origen,
    'CERRADA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(ve.Vn_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), ve.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(CAST(ISNULL(ve.Vn_Precio_Neto_Importe, 0) AS decimal(18,4))) AS total_ticket,
    'SIN_CODIGO' AS producto_codigo,
    'VENTA CERRADA MPRO - DETALLE RESUMIDO' AS producto_nombre,
    CAST(1 AS decimal(18,4)) AS cantidad,
    SUM(CAST(ISNULL(ve.Vn_Precio_Neto_Importe, 0) AS decimal(18,4))) AS precio_unitario,
    SUM(CAST(ISNULL(ve.Vn_Precio_Neto_Importe, 0) AS decimal(18,4))) AS importe_bruto,
    CAST(0 AS decimal(9,4)) AS descuento_pct,
    CAST(0 AS decimal(18,4)) AS descuento_producto,
    SUM(CAST(ISNULL(ve.Vn_Precio_Neto_Importe, 0) AS decimal(18,4))) AS importe_neto_producto,
    CAST(0 AS decimal(18,4)) AS descuento_encabezado_reportado,
    CAST(0 AS decimal(18,4)) AS descuento_total_reportado
FROM Venta_Encabezado ve
LEFT JOIN Comanda c
    ON c.Co_Folio = ve.Vn_Documento
   AND c.Sc_Cve_Sucursal = ve.Sc_Cve_Sucursal
LEFT JOIN Cliente cl ON cl.Cl_Cve_Cliente=c.Cl_Cve_Cliente
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = ve.Vn_Cve_Vendedor
WHERE CAST(ve.Vn_Fecha AS date) = '{fecha_operacion}'
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
  AND ve.Es_Cve_Estado IN ('AC', 'FA')
  AND ve.Fecha_Baja IS NULL
GROUP BY ve.Vn_Documento
ORDER BY ve.Vn_Documento
"""


QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES_RESUMEN = """
SELECT
    MAX(CAST(NULL AS nvarchar(100))) AS partida_origen_id,
    MAX(CAST(NULL AS nvarchar(100))) AS partida_key,
    MAX(CAST(c.Cl_Cve_Cliente AS nvarchar(100))) AS cliente_id,
    MAX(CAST(COALESCE(NULLIF(cl.Cl_Razon_Social,''),NULLIF(cl.Cl_Descripcion,'')) AS nvarchar(max))) AS cliente_nombre,
    MAX(CAST(cl.Cl_Razon_Social AS nvarchar(max))) AS cliente_razon_social,
    MAX(CAST(cl.Cl_Descripcion AS nvarchar(max))) AS cliente_descripcion,
    MAX(CAST(cl.Cl_Cve_Maestro AS nvarchar(100))) AS cliente_maestro_id,
    MAX(CAST(cl.Sc_Cve_Sucursal AS nvarchar(50))) AS cliente_sucursal_origen,
    MAX(CAST(cl.Cl_Contacto_1 AS nvarchar(max))) AS cliente_contacto,
    MAX(CAST(cl.Cl_R_F_C AS nvarchar(50))) AS cliente_rfc,
    MAX(CAST(cl.Cl_Direccion_1 AS nvarchar(max))) AS cliente_direccion_1,
    MAX(CAST(cl.Cl_Direccion_2 AS nvarchar(max))) AS cliente_direccion_2,
    MAX(CAST(cl.Cl_Direccion_3 AS nvarchar(max))) AS cliente_direccion_3,
    MAX(CAST(cl.Cl_Calle AS nvarchar(max))) AS cliente_calle,
    MAX(CAST(cl.Cl_Numero_Exterior AS nvarchar(max))) AS cliente_numero_exterior,
    MAX(CAST(cl.Cl_Numero_Interior AS nvarchar(max))) AS cliente_numero_interior,
    MAX(CAST(cl.Cl_Colonia AS nvarchar(max))) AS cliente_colonia,
    MAX(CAST(cl.Cl_Ciudad AS nvarchar(max))) AS cliente_ciudad,
    MAX(CAST(cl.Cl_Municipio AS nvarchar(max))) AS cliente_municipio,
    MAX(CAST(cl.Cl_Estado AS nvarchar(max))) AS cliente_estado,
    MAX(CAST(cl.Cl_Pais AS nvarchar(max))) AS cliente_pais,
    MAX(CAST(cl.Cl_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal,
    MAX(CAST(c.Co_Fecha AS datetime2)) AS ticket_fecha,
    MAX(CAST(NULL AS datetime2)) AS ticket_fecha_cierre,
    MAX(CAST(NULL AS tinyint)) AS ticket_pagado,
    MAX(CAST(NULL AS tinyint)) AS ticket_impreso,
    MAX(CAST(NULL AS int)) AS ticket_impresiones,
    MAX(CAST(c.Co_Comentario AS nvarchar(max))) AS ticket_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS ticket_comentario_descuento,
    MAX(CAST(c.Fecha_Alta AS datetime2)) AS ticket_fecha_alta,
    MAX(CAST(c.Oper_Ult_Modif AS nvarchar(100))) AS ticket_oper_ult_modif,
    MAX(CAST(c.Oper_Baja AS nvarchar(100))) AS ticket_oper_baja,
    MAX(CAST(c.Fecha_Baja AS datetime2)) AS ticket_fecha_baja,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario_descuento,
    MAX(CAST(NULL AS nvarchar(max))) AS partida_comentario_cancelacion,
    MAX(CAST(NULL AS nvarchar(100))) AS partida_oper_baja,
    MAX(CAST(NULL AS datetime2)) AS partida_fecha_baja,
    MAX(CAST(NULL AS nvarchar(100))) AS tipo_descuento_id,
    MAX(CAST(NULL AS nvarchar(max))) AS tipo_descuento_descripcion,
    MAX(CAST(NULL AS decimal(18,6))) AS tipo_descuento_valor,
    MAX(CAST(cl.Cl_Cruzamiento_1 AS nvarchar(max))) AS cliente_cruzamiento_1,
    MAX(CAST(cl.Cl_Cruzamiento_2 AS nvarchar(max))) AS cliente_cruzamiento_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_1 AS nvarchar(max))) AS cliente_entrega_direccion_1,
    MAX(CAST(cl.Cl_Direccion_Entrega_2 AS nvarchar(max))) AS cliente_entrega_direccion_2,
    MAX(CAST(cl.Cl_Direccion_Entrega_3 AS nvarchar(max))) AS cliente_entrega_direccion_3,
    MAX(CAST(cl.Cl_Ciudad_Entrega AS nvarchar(max))) AS cliente_entrega_ciudad,
    MAX(CAST(cl.Cl_Estado_Entrega AS nvarchar(max))) AS cliente_entrega_estado,
    MAX(CAST(cl.Cl_Pais_Entrega AS nvarchar(max))) AS cliente_entrega_pais,
    MAX(CAST(cl.Cl_Codigo_Postal_Entrega AS nvarchar(max))) AS cliente_entrega_codigo_postal,
    MAX(CAST(cl.Cl_Cve_Colonia AS nvarchar(max))) AS cliente_colonia_origen_id,
    MAX(CAST(cl.Cl_Cve_Ciudad AS nvarchar(max))) AS cliente_ciudad_origen_id,
    MAX(CAST(cl.Cl_Cve_Municipio AS nvarchar(max))) AS cliente_municipio_origen_id,
    MAX(CAST(cl.Cl_Cve_Estado AS nvarchar(max))) AS cliente_estado_origen_id,
    MAX(CAST(cl.Cl_Cve_Pais AS nvarchar(max))) AS cliente_pais_origen_id,
    MAX(CAST(cl.Cl_Cve_Codigo_Postal AS nvarchar(max))) AS cliente_codigo_postal_origen_id,
    MAX(CAST(cl.Cl_Latitud AS nvarchar(max))) AS cliente_latitud,
    MAX(CAST(cl.Cl_Longitud AS nvarchar(max))) AS cliente_longitud,
    CONVERT(varchar(64), c.Co_Folio) AS folio,
    CONVERT(varchar(64), c.Co_Folio) AS folio_origen,
    'CERRADA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(c.Co_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), c.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS total_ticket,
    'SIN_CODIGO' AS producto_codigo,
    'VENTA CERRADA MPRO - DETALLE RESUMIDO' AS producto_nombre,
    CAST(1 AS decimal(18,4)) AS cantidad,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS precio_unitario,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_bruto,
    CAST(0 AS decimal(9,4)) AS descuento_pct,
    CAST(0 AS decimal(18,4)) AS descuento_producto,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_neto_producto,
    CAST(0 AS decimal(18,4)) AS descuento_encabezado_reportado,
    CAST(0 AS decimal(18,4)) AS descuento_total_reportado
FROM Comanda c
INNER JOIN Comanda_Detalle d
    ON d.Co_Folio = c.Co_Folio
   AND d.Es_Cve_Estado = 'AC'
   AND d.Fecha_Baja IS NULL
LEFT JOIN Cliente cl ON cl.Cl_Cve_Cliente=c.Cl_Cve_Cliente
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = c.Vn_Cve_Vendedor
WHERE CAST(c.Co_Fecha AS date) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND c.Es_Cve_Estado = 'PA'
GROUP BY c.Co_Folio
ORDER BY c.Co_Folio
"""


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _json_default(value: Any):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def serialize_open_detail_rows(rows: List[Dict[str, Any]]) -> str:
    """Normaliza las lineas abiertas a un contrato JSON pequeno y estable."""
    normalized = []
    for row in rows or []:
        folio = str(row.get("folio") or "").strip()
        if not folio:
            continue
        importe_bruto = _number(row.get("importe_bruto"))
        descuento_producto = _number(row.get("descuento_producto"))
        raw_importe_neto = row.get("importe_neto_producto")
        importe_neto_producto = (
            _number(raw_importe_neto)
            if raw_importe_neto is not None
            else importe_bruto - descuento_producto
        )
        normalized.append({
            **fields_from(row),
            "folio": folio,
            "folio_origen": str(row.get("folio_origen") or "").strip() or None,
            "estado_ticket": str(row.get("estado_ticket") or "ABIERTA").strip().upper(),
            "sistema_origen": str(row.get("sistema_origen") or "").strip() or None,
            "fecha_hora": row.get("fecha_hora"),
            "pax": int(_number(row.get("pax"))),
            "propina": _number(row.get("propina")),
            "vendedor_id": str(row.get("vendedor_id") or "").strip() or None,
            "vendedor_nombre": str(row.get("vendedor_nombre") or "").strip() or None,
            "mesa": str(row.get("mesa") or "").strip() or None,
            "total_ticket": _number(row.get("total_ticket")),
            "producto_codigo": str(row.get("producto_codigo") or "SIN_CODIGO"),
            "producto_nombre": str(
                row.get("producto_nombre") or "VENTA SIN DETALLE DE PRODUCTO"
            )[:300],
            "cantidad": _number(row.get("cantidad")),
            "precio_unitario": _number(row.get("precio_unitario")),
            "importe_bruto": importe_bruto,
            "descuento_pct": _number(row.get("descuento_pct")),
            "descuento_producto": descuento_producto,
            "importe_neto_producto": importe_neto_producto,
            "descuento_encabezado_reportado": _number(
                row.get("descuento_encabezado_reportado")
            ),
            "descuento_total_reportado": _number(
                row.get("descuento_total_reportado")
            ),
        })
    return json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_json_default,
    )
