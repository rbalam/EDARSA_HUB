from fastapi import APIRouter, Depends, Query
from core.security import get_current_user
from core.config.edarsahub_sql import get_edarsahub_connection

router = APIRouter(prefix="/api/rentabilidad", tags=["Rentabilidad"])

def q(sql, params=()):
    cn = get_edarsahub_connection()
    cur = cn.cursor(as_dict=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cn.close()
    return rows

@router.get("/productos")
async def rentabilidad_productos(
    server_id: str = Query(default=""),
    limite: int = Query(default=200, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    where = ""
    params = []

    if server_id:
        where = "WHERE CAST(p.ServerID AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))"
        params.append(server_id)

    rows = q(f"""
    SELECT TOP ({int(limite)})
        p.ServerID,
        s.nombre AS servidor,
        p.ProductoID,
        p.ProductoCodigo,
        p.ProductoNombre,
        CAST(p.PrecioFinal AS FLOAT) AS precio_final,
        CAST(ISNULL(sp.CostoReceta, 0) AS FLOAT) AS costo_receta,
        CAST(
            CASE 
                WHEN ISNULL(p.PrecioFinal,0) > 0
                THEN ((ISNULL(p.PrecioFinal,0) - ISNULL(sp.CostoReceta,0)) / ISNULL(p.PrecioFinal,0)) * 100
                ELSE 0
            END AS FLOAT
        ) AS margen_pct,
        CAST(ISNULL(p.PrecioFinal,0) - ISNULL(sp.CostoReceta,0) AS FLOAT) AS utilidad_bruta,
        CASE
            WHEN ISNULL(sp.CostoReceta,0) = 0 THEN 'SIN_COSTO'
            WHEN ISNULL(p.PrecioFinal,0) = 0 THEN 'SIN_PRECIO'
            WHEN ((ISNULL(p.PrecioFinal,0) - ISNULL(sp.CostoReceta,0)) / NULLIF(ISNULL(p.PrecioFinal,0),0)) * 100 < 20 THEN 'MARGEN_BAJO'
            WHEN ((ISNULL(p.PrecioFinal,0) - ISNULL(sp.CostoReceta,0)) / NULLIF(ISNULL(p.PrecioFinal,0),0)) * 100 < 40 THEN 'MARGEN_MEDIO'
            ELSE 'MARGEN_OK'
        END AS status_margen
    FROM Sync_Precios_Historicos p
    LEFT JOIN Sync_Productos sp
        ON CAST(sp.ProductoID AS NVARCHAR(100)) = CAST(p.ProductoID AS NVARCHAR(100))
       AND CAST(sp.ServerID AS NVARCHAR(100)) = CAST(p.ServerID AS NVARCHAR(100))
    LEFT JOIN Servidores_Conexiones s
        ON CAST(s.id AS NVARCHAR(100)) = CAST(p.ServerID AS NVARCHAR(100))
    {where}
    ORDER BY status_margen, margen_pct ASC, p.ProductoNombre
    """, tuple(params))

    resumen = {
        "total": len(rows),
        "sin_costo": len([x for x in rows if x.get("status_margen") == "SIN_COSTO"]),
        "sin_precio": len([x for x in rows if x.get("status_margen") == "SIN_PRECIO"]),
        "margen_bajo": len([x for x in rows if x.get("status_margen") == "MARGEN_BAJO"]),
        "margen_medio": len([x for x in rows if x.get("status_margen") == "MARGEN_MEDIO"]),
        "margen_ok": len([x for x in rows if x.get("status_margen") == "MARGEN_OK"]),
    }

    return {
        "success": True,
        "source": "EDARSAHUB_SQL",
        "resumen": resumen,
        "data": rows
    }

@router.get("/resumen")
async def rentabilidad_resumen(
    server_id: str = Query(default=""),
    current_user: dict = Depends(get_current_user)
):
    where = ""
    params = []

    if server_id:
        where = "WHERE CAST(p.ServerID AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))"
        params.append(server_id)

    rows = q(f"""
    SELECT
        p.ServerID,
        ISNULL(s.nombre, p.ServerID) AS servidor,
        COUNT(*) AS productos,
        SUM(CASE WHEN ISNULL(sp.CostoReceta,0)=0 THEN 1 ELSE 0 END) AS sin_costo,
        AVG(CASE 
            WHEN ISNULL(p.PrecioFinal,0)>0 AND ISNULL(sp.CostoReceta,0)>0
            THEN ((ISNULL(p.PrecioFinal,0)-ISNULL(sp.CostoReceta,0))/ISNULL(p.PrecioFinal,0))*100
            ELSE NULL
        END) AS margen_promedio_pct,
        AVG(CAST(p.PrecioFinal AS FLOAT)) AS precio_promedio,
        AVG(CAST(ISNULL(sp.CostoReceta,0) AS FLOAT)) AS costo_promedio
    FROM Sync_Precios_Historicos p
    LEFT JOIN Sync_Productos sp
        ON CAST(sp.ProductoID AS NVARCHAR(100)) = CAST(p.ProductoID AS NVARCHAR(100))
       AND CAST(sp.ServerID AS NVARCHAR(100)) = CAST(p.ServerID AS NVARCHAR(100))
    LEFT JOIN Servidores_Conexiones s
        ON CAST(s.id AS NVARCHAR(100)) = CAST(p.ServerID AS NVARCHAR(100))
    {where}
    GROUP BY p.ServerID, ISNULL(s.nombre, p.ServerID)
    ORDER BY margen_promedio_pct ASC
    """, tuple(params))

    return {
        "success": True,
        "source": "EDARSAHUB_SQL",
        "data": rows
    }
