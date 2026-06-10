from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
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
    where = "WHERE p.Activo = 1"
    params = []

    if server_id:
        where += " AND CAST(p.ServerID AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))"
        params.append(server_id)

    rows = q(f"""
    SELECT TOP ({int(limite)})
        x.ServerID,
        x.servidor,
        x.ProductoID,
        x.ProductoCodigo,
        x.ProductoNombre,
        x.precio_final,
        x.costo_receta,
        CAST(CASE WHEN x.precio_final > 0
            THEN ((x.precio_final - x.costo_receta) / x.precio_final) * 100 ELSE 0 END AS FLOAT) AS margen_pct,
        CAST(x.precio_final - x.costo_receta AS FLOAT) AS utilidad_bruta,
        CASE
            WHEN x.costo_receta = 0 THEN 'SIN_COSTO'
            WHEN x.precio_final < 1 THEN 'SIN_PRECIO'
            WHEN x.costo_receta > x.precio_final * 2 THEN 'ANOMALIA'
            WHEN ((x.precio_final - x.costo_receta) / x.precio_final) * 100 < 20 THEN 'MARGEN_BAJO'
            WHEN ((x.precio_final - x.costo_receta) / x.precio_final) * 100 < 40 THEN 'MARGEN_MEDIO'
            ELSE 'MARGEN_OK'
        END AS status_margen
    FROM (
        SELECT
            p.ServerID,
            ISNULL(s.nombre, CAST(p.ServerID AS NVARCHAR(100))) AS servidor,
            CAST(p.ProductoID AS NVARCHAR(36)) AS ProductoID,
            p.CodigoFuente AS ProductoCodigo,
            p.Nombre AS ProductoNombre,
            CAST(p.PrecioVenta AS FLOAT) AS precio_final,
            CAST(COALESCE(
                (SELECT SUM(r.CostoTotal) FROM Sync_Productos_Recetas r
                 WHERE r.ProductoCodigoFuente = p.CodigoFuente AND r.ServerID = p.ServerID),
                p.CostoReceta, 0
            ) AS FLOAT) AS costo_receta
        FROM Sync_Productos p
        LEFT JOIN Servidores_Conexiones s
            ON CAST(s.id AS NVARCHAR(100)) = CAST(p.ServerID AS NVARCHAR(100))
        {where}
    ) x
    ORDER BY status_margen, margen_pct ASC, x.ProductoNombre
    """, tuple(params))

    resumen = {
        "total": len(rows),
        "sin_costo": len([x for x in rows if x.get("status_margen") == "SIN_COSTO"]),
        "sin_precio": len([x for x in rows if x.get("status_margen") == "SIN_PRECIO"]),
        "anomalias": len([x for x in rows if x.get("status_margen") == "ANOMALIA"]),
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
    where = "WHERE p.Activo = 1"
    params = []

    if server_id:
        where += " AND CAST(p.ServerID AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))"
        params.append(server_id)

    # Rentabilidad Base canónica:
    #  - Maestro: Sync_Productos (no historial de precios)
    #  - Costo receta CANÓNICO: SUM(Sync_Productos_Recetas.CostoTotal) por producto
    #    (fallback Sync_Productos.CostoReceta). Mismo origen que Costos/Márgenes.
    #  - Guardas de sanidad para el margen promedio: excluye precios placeholder
    #    (< $1) y costos anómalos (> 2x el precio = error de datos del origen),
    #    que se reportan aparte en 'anomalias_costo'.
    rows = q(f"""
    SELECT
        x.ServerID,
        ISNULL(s.nombre, CAST(x.ServerID AS NVARCHAR(100))) AS servidor,
        COUNT(*) AS productos,
        SUM(CASE WHEN x.costo_receta = 0 THEN 1 ELSE 0 END) AS sin_costo,
        SUM(CASE WHEN x.precio_venta >= 1 AND x.costo_receta > x.precio_venta * 2 THEN 1 ELSE 0 END) AS anomalias_costo,
        AVG(CASE
            WHEN x.precio_venta >= 1 AND x.costo_receta > 0 AND x.costo_receta <= x.precio_venta * 2
            THEN ((x.precio_venta - x.costo_receta) / x.precio_venta) * 100
            ELSE NULL
        END) AS margen_promedio_pct,
        AVG(CASE WHEN x.precio_venta >= 1 THEN x.precio_venta ELSE NULL END) AS precio_promedio,
        AVG(CASE WHEN x.costo_receta > 0 AND x.costo_receta <= x.precio_venta * 2 THEN x.costo_receta ELSE NULL END) AS costo_promedio
    FROM (
        SELECT
            p.ServerID,
            CAST(p.PrecioVenta AS FLOAT) AS precio_venta,
            CAST(COALESCE(
                (SELECT SUM(r.CostoTotal) FROM Sync_Productos_Recetas r
                 WHERE r.ProductoCodigoFuente = p.CodigoFuente AND r.ServerID = p.ServerID),
                p.CostoReceta, 0
            ) AS FLOAT) AS costo_receta
        FROM Sync_Productos p
        {where}
    ) x
    LEFT JOIN Servidores_Conexiones s
        ON CAST(s.id AS NVARCHAR(100)) = CAST(x.ServerID AS NVARCHAR(100))
    GROUP BY x.ServerID, ISNULL(s.nombre, CAST(x.ServerID AS NVARCHAR(100)))
    ORDER BY servidor
    """, tuple(params))

    return {
        "success": True,
        "source": "EDARSAHUB_SQL",
        "costo_origen": "Sync_Productos_Recetas (canónico)",
        "data": rows
    }
