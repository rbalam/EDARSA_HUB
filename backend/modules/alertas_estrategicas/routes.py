from fastapi import APIRouter, Depends, Query
from core.security import get_current_user
from core.config.edarsahub_sql import get_edarsahub_connection

router = APIRouter(prefix="/api/alertas-estrategicas", tags=["Alertas Estratégicas"])

def q(sql, params=()):
    cn = get_edarsahub_connection()
    cur = cn.cursor(as_dict=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cn.close()
    return rows

@router.get("/resumen")
async def resumen_alertas(
    server_id: str = Query(default=""),
    limite: int = Query(default=200, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    where_server_p = ""
    params_p = []

    if server_id:
        where_server_p = "AND CAST(p.ServerID AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))"
        params_p.append(server_id)

    rentabilidad = q(f"""
    SELECT TOP ({int(limite)})
        'FINANCIERA' AS perspectiva_bsc,
        CASE
            WHEN ISNULL(p.PrecioFinal,0)=0 AND ISNULL(sp.CostoReceta,0)>0 THEN 'PRECIO_CERO_CON_COSTO'
            WHEN ISNULL(sp.CostoReceta,0)>ISNULL(p.PrecioFinal,0) AND ISNULL(p.PrecioFinal,0)>0 THEN 'MARGEN_NEGATIVO'
            WHEN ISNULL(sp.CostoReceta,0)=0 THEN 'SIN_COSTO_RECETA'
            WHEN ((ISNULL(p.PrecioFinal,0)-ISNULL(sp.CostoReceta,0))/NULLIF(ISNULL(p.PrecioFinal,0),0))*100 < 20 THEN 'MARGEN_BAJO'
            ELSE 'OK'
        END AS tipo_alerta,
        CASE
            WHEN ISNULL(p.PrecioFinal,0)=0 AND ISNULL(sp.CostoReceta,0)>0 THEN 'CRITICA'
            WHEN ISNULL(sp.CostoReceta,0)>ISNULL(p.PrecioFinal,0) AND ISNULL(p.PrecioFinal,0)>0 THEN 'CRITICA'
            WHEN ((ISNULL(p.PrecioFinal,0)-ISNULL(sp.CostoReceta,0))/NULLIF(ISNULL(p.PrecioFinal,0),0))*100 < 20 THEN 'ALTA'
            WHEN ISNULL(sp.CostoReceta,0)=0 THEN 'MEDIA'
            ELSE 'OK'
        END AS severidad,
        p.ServerID,
        ISNULL(s.nombre,p.ServerID) AS unidad,
        p.ProductoID,
        p.ProductoCodigo,
        p.ProductoNombre,
        CAST(ISNULL(p.PrecioFinal,0) AS FLOAT) AS precio,
        CAST(ISNULL(sp.CostoReceta,0) AS FLOAT) AS costo,
        CAST(ISNULL(p.PrecioFinal,0)-ISNULL(sp.CostoReceta,0) AS FLOAT) AS utilidad,
        CAST(
            CASE
                WHEN ISNULL(p.PrecioFinal,0)>0
                THEN ((ISNULL(p.PrecioFinal,0)-ISNULL(sp.CostoReceta,0))/ISNULL(p.PrecioFinal,0))*100
                ELSE NULL
            END AS FLOAT
        ) AS margen_pct,
        'Revisar precio, receta, configuración de producto o autorización de cortesía.' AS accion_sugerida
    FROM Sync_Precios_Historicos p
    LEFT JOIN Sync_Productos sp
        ON CAST(sp.ProductoID AS NVARCHAR(100)) = CAST(p.ProductoID AS NVARCHAR(100))
       AND CAST(sp.ServerID AS NVARCHAR(100)) = CAST(p.ServerID AS NVARCHAR(100))
    LEFT JOIN Servidores_Conexiones s
        ON CAST(s.id AS NVARCHAR(100)) = CAST(p.ServerID AS NVARCHAR(100))
    WHERE (
           (ISNULL(p.PrecioFinal,0)=0 AND ISNULL(sp.CostoReceta,0)>0)
        OR (ISNULL(sp.CostoReceta,0)>ISNULL(p.PrecioFinal,0) AND ISNULL(p.PrecioFinal,0)>0)
        OR (ISNULL(sp.CostoReceta,0)=0)
        OR (((ISNULL(p.PrecioFinal,0)-ISNULL(sp.CostoReceta,0))/NULLIF(ISNULL(p.PrecioFinal,0),0))*100 < 20)
    )
    {where_server_p}
    ORDER BY
        CASE
            WHEN ISNULL(p.PrecioFinal,0)=0 AND ISNULL(sp.CostoReceta,0)>0 THEN 1
            WHEN ISNULL(sp.CostoReceta,0)>ISNULL(p.PrecioFinal,0) AND ISNULL(p.PrecioFinal,0)>0 THEN 2
            WHEN ((ISNULL(p.PrecioFinal,0)-ISNULL(sp.CostoReceta,0))/NULLIF(ISNULL(p.PrecioFinal,0),0))*100 < 20 THEN 3
            WHEN ISNULL(sp.CostoReceta,0)=0 THEN 4
            ELSE 9
        END,
        margen_pct ASC
    """, tuple(params_p))

    compras = q("""
    SELECT
        'PROCESOS INTERNOS' AS perspectiva_bsc,
        'PEDIDO_SIN_DETALLE' AS tipo_alerta,
        'ALTA' AS severidad,
        CAST(p.EmpresaID AS NVARCHAR(100)) AS ServerID,
        CAST(p.EmpresaID AS NVARCHAR(100)) AS unidad,
        CAST(p.PedidoCompraID AS NVARCHAR(100)) AS entidad_id,
        p.FolioPedido AS entidad_codigo,
        CONCAT('Pedido sin detalle: ', p.FolioPedido) AS descripcion,
        CAST(ISNULL(p.Total,0) AS FLOAT) AS importe,
        'Revisar job de sincronización de compras y detalle del pedido.' AS accion_sugerida
    FROM Compras_Pedidos p
    WHERE ISNULL(p.Total,0)=0
      AND NOT EXISTS (
        SELECT 1 FROM Compras_PedidosDetalle d
        WHERE d.PedidoCompraID = p.PedidoCompraID
      )
    """)

    inventarios = q("""
    SELECT TOP 100
        'PROCESOS INTERNOS' AS perspectiva_bsc,
        'INVENTARIO_REVISAR' AS tipo_alerta,
        'MEDIA' AS severidad,
        CAST(NULL AS NVARCHAR(100)) AS ServerID,
        'EDARSAHUB' AS unidad,
        CAST(NULL AS NVARCHAR(100)) AS entidad_id,
        TABLE_NAME AS entidad_codigo,
        CONCAT('Tabla de inventarios detectada: ', TABLE_NAME) AS descripcion,
        0 AS importe,
        'Validar fecha de último inventario, diferencias y ajustes.' AS accion_sugerida
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_NAME LIKE '%Inventario%'
    ORDER BY TABLE_NAME
    """)

    all_alertas = []

    for r in rentabilidad:
        if r.get("severidad") != "OK":
            all_alertas.append({
                "perspectiva_bsc": r.get("perspectiva_bsc"),
                "tipo_alerta": r.get("tipo_alerta"),
                "severidad": r.get("severidad"),
                "server_id": r.get("ServerID"),
                "unidad": r.get("unidad"),
                "entidad_id": r.get("ProductoID"),
                "entidad_codigo": r.get("ProductoCodigo"),
                "descripcion": r.get("ProductoNombre"),
                "precio": r.get("precio"),
                "costo": r.get("costo"),
                "utilidad": r.get("utilidad"),
                "margen_pct": r.get("margen_pct"),
                "accion_sugerida": r.get("accion_sugerida"),
            })

    for r in compras[:200]:
        all_alertas.append({
            "perspectiva_bsc": r.get("perspectiva_bsc"),
            "tipo_alerta": r.get("tipo_alerta"),
            "severidad": r.get("severidad"),
            "server_id": r.get("ServerID"),
            "unidad": r.get("unidad"),
            "entidad_id": r.get("entidad_id"),
            "entidad_codigo": r.get("entidad_codigo"),
            "descripcion": r.get("descripcion"),
            "importe": r.get("importe"),
            "accion_sugerida": r.get("accion_sugerida"),
        })

    for r in inventarios[:50]:
        all_alertas.append({
            "perspectiva_bsc": r.get("perspectiva_bsc"),
            "tipo_alerta": r.get("tipo_alerta"),
            "severidad": r.get("severidad"),
            "server_id": r.get("ServerID"),
            "unidad": r.get("unidad"),
            "entidad_id": r.get("entidad_id"),
            "entidad_codigo": r.get("entidad_codigo"),
            "descripcion": r.get("descripcion"),
            "importe": r.get("importe"),
            "accion_sugerida": r.get("accion_sugerida"),
        })

    resumen = {
        "total": len(all_alertas),
        "criticas": len([x for x in all_alertas if x["severidad"] == "CRITICA"]),
        "altas": len([x for x in all_alertas if x["severidad"] == "ALTA"]),
        "medias": len([x for x in all_alertas if x["severidad"] == "MEDIA"]),
        "por_perspectiva": {},
        "por_tipo": {}
    }

    for a in all_alertas:
        resumen["por_perspectiva"][a["perspectiva_bsc"]] = resumen["por_perspectiva"].get(a["perspectiva_bsc"], 0) + 1
        resumen["por_tipo"][a["tipo_alerta"]] = resumen["por_tipo"].get(a["tipo_alerta"], 0) + 1

    return {
        "success": True,
        "source": "EDARSAHUB_SQL",
        "modelo_gestion": "BALANCED_SCORECARD",
        "resumen": resumen,
        "alertas": all_alertas[:limite]
    }
