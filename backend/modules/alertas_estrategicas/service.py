from core.config.edarsahub_sql import get_edarsahub_connection
from core.unidades_service import UnidadesService
from fastapi import HTTPException
from core.auth.sql_user_identity import resolve_sql_usuario_id
from core.connections.edarsahub_readonly_repository import (
    get_unit_scope_metadata_readonly,
)
from core.connections.hrlectura_connection_factory import (
    build_hrlectura_connection_factory,
)
from core.rbac_sql.runtime import (
    can_access_unit_metadata_sql,
)


def q(sql, params=()):
    cn = get_edarsahub_connection()
    cur = cn.cursor(as_dict=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cn.close()
    return rows



async def obtener_resumen_alertas(
    server_id: str,
    limite: int,
    current_user,
):

    requested_server_id = (server_id or "").strip()

    usuario_id = resolve_sql_usuario_id(current_user)

    if not usuario_id:
        raise HTTPException(
            status_code=403,
            detail="No fue posible resolver la identidad SQL del usuario",
        )

    permission_code = "ALERTAS_VER"

    connection_factory = build_hrlectura_connection_factory()

    unidades = UnidadesService.get_all() or []

    allowed_metadata = []

    for unidad in unidades:
        unidad_ref = (
            unidad.get("id")
            or unidad.get("codigo")
        )

        if not unidad_ref:
            continue

        metadata = get_unit_scope_metadata_readonly(
            unidad=str(unidad_ref),
            connection_factory=connection_factory,
        )

        if not metadata:
            continue

        if can_access_unit_metadata_sql(
            usuario_id,
            permission_code,
            metadata,
        ):
            allowed_metadata.append(metadata)

    if not allowed_metadata:
        where_server_p = "AND 1 = 0"
        params_p = []
        where_empresa_compras = "AND 1 = 0"
        params_compras = []

    else:
        allowed_servers = sorted({
            str(row.get("server_id") or "").strip()
            for row in allowed_metadata
            if str(row.get("server_id") or "").strip()
        })

        allowed_empresas = sorted({
            str(row.get("empresa_id") or "").strip()
            for row in allowed_metadata
            if str(row.get("empresa_id") or "").strip()
        })

        if requested_server_id:
            requested_metadata = [
                row
                for row in allowed_metadata
                if str(
                    row.get("server_id") or ""
                ).strip() == requested_server_id
            ]

            if not requested_metadata:
                raise HTTPException(
                    status_code=403,
                    detail="Sin acceso al servidor solicitado",
                )

            where_server_p = (
                "AND CAST(p.ServerID AS NVARCHAR(100)) = "
                "CAST(%s AS NVARCHAR(100))"
            )
            params_p = [requested_server_id]

            where_empresa_compras = """
              AND EXISTS (
                  SELECT 1
                  FROM Sistema_EmpresasServidores ses
                  WHERE ses.EmpresaID = p.EmpresaID
                    AND CAST(ses.ServidorID AS NVARCHAR(100))
                        = CAST(%s AS NVARCHAR(100))
                    AND ses.Activo = 1
              )
            """
            params_compras = [requested_server_id]

        else:
            if allowed_servers:
                placeholders = ",".join(
                    ["%s"] * len(allowed_servers)
                )
                where_server_p = (
                    "AND CAST(p.ServerID AS NVARCHAR(100)) "
                    f"IN ({placeholders})"
                )
                params_p = list(allowed_servers)
            else:
                where_server_p = "AND 1 = 0"
                params_p = []

            if allowed_empresas:
                placeholders = ",".join(
                    ["%s"] * len(allowed_empresas)
                )
                where_empresa_compras = (
                    "AND CAST(p.EmpresaID AS NVARCHAR(100)) "
                    f"IN ({placeholders})"
                )
                params_compras = list(allowed_empresas)
            else:
                where_empresa_compras = "AND 1 = 0"
                params_compras = []

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

    compras = q(f"""
    SELECT
        'PROCESOS INTERNOS' AS perspectiva_bsc,
        'PEDIDO_SIN_DETALLE' AS tipo_alerta,
        'ALTA' AS severidad,
        CAST(NULL AS NVARCHAR(100)) AS ServerID,
        CAST(p.EmpresaID AS NVARCHAR(100)) AS empresa_id,
        CAST(p.SucursalID AS NVARCHAR(100)) AS sucursal_id,
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
      {where_empresa_compras}
    """, tuple(params_compras))

    # No generar alertas artificiales desde INFORMATION_SCHEMA.
    # Fuente operacional disponible:
    # dbo.Compras_Inventarios_Fisicos_Sync.
    #
    # La condición de alerta (vigencia, diferencia, ajuste, etc.)
    # debe provenir de una regla de negocio canónica/configurable;
    # hasta entonces el endpoint no inventa incidencias.
    inventarios = []

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
            "empresa_id": r.get("empresa_id"),
            "sucursal_id": r.get("sucursal_id"),
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
