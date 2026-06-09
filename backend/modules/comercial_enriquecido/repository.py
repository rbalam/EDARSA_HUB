"""
Repository SQL-first del Catálogo Comercial Enriquecido (Bloque C).
===================================================================
NO-LIVE: lee/escribe EXCLUSIVAMENTE en EDARSAHUB SQL via conexión central.
Tabla: dbo.Comercial_Productos_Enriquecidos (enriquecimiento) + LEFT JOIN a
dbo.Sync_Productos (campos base canónicos siempre frescos).

Sin hardcode, parametrizado. RBAC se aplica en routes (allowed_server_ids).
"""
import logging
from typing import List, Dict, Optional

from core.db import execute_sql_query_params
from core.server_registry import EDARSAHUB_CONFIG
from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)


def _conn():
    c = EDARSAHUB_CONFIG
    return (c['host'], c['port'], c['database'], c['username'], c['password'])


_SELECT = """
    SELECT
        CONVERT(varchar(36), e.id) AS id,
        CONVERT(varchar(36), e.producto_id) AS producto_id,
        e.server_id, e.system_type, e.unidad_codigo,
        e.codigo_producto_origen,
        COALESCE(p.Nombre, e.nombre_producto) AS nombre_producto,
        COALESCE(p.FamiliaNombre, e.familia_origen) AS familia_origen,
        p.CategoriaNombre AS categoria_origen,
        p.SubFamiliaNombre AS subfamilia_origen,
        p.EsVendible AS es_vendible,
        p.TieneReceta AS tiene_receta,
        e.grupo_comercial, e.casa_comercial, e.marca,
        e.categoria, e.subcategoria, e.tipo_alcohol,
        e.es_alcoholico, e.grado_alcohol, e.presentacion_ml, e.presentacion_texto,
        e.ean, e.imagen_url,
        CONVERT(varchar(36), e.proveedor_id) AS proveedor_id,
        CONVERT(varchar(36), e.representante_id) AS representante_id,
        COALESCE(e.precio_venta, p.PrecioVenta) AS precio_venta,
        e.confianza, e.requiere_validacion, e.regla_usada, e.observaciones,
        e.activo, e.fuente, e.fecha_creacion, e.fecha_actualizacion
    FROM dbo.Comercial_Productos_Enriquecidos e
    LEFT JOIN dbo.Sync_Productos p ON p.ProductoID = e.producto_id
"""

# Campos enriquecibles (editables vía POST/PUT)
CAMPOS_EDITABLES = [
    "grupo_comercial", "casa_comercial", "marca", "categoria", "subcategoria",
    "tipo_alcohol", "es_alcoholico", "grado_alcohol", "presentacion_ml",
    "presentacion_texto", "ean", "imagen_url", "proveedor_id", "representante_id",
    "precio_venta", "confianza", "requiere_validacion", "regla_usada", "observaciones",
]


def _build_where(filtros: Dict, allowed_server_ids: Optional[List[str]]):
    where: List[str] = []
    params: List = []

    # RBAC: lista no vacía => restringir; vacía/None => sin restricción (admin)
    if allowed_server_ids:
        ph = ",".join(["%s"] * len(allowed_server_ids))
        where.append(f"e.server_id IN ({ph})")
        params += [str(s) for s in allowed_server_ids]

    if filtros.get("server_id"):
        where.append("e.server_id = %s")
        params.append(str(filtros["server_id"]))
    if filtros.get("unidad_codigo"):
        where.append("e.unidad_codigo = %s")
        params.append(str(filtros["unidad_codigo"]))
    if filtros.get("grupo_comercial"):
        where.append("e.grupo_comercial = %s")
        params.append(filtros["grupo_comercial"])
    if filtros.get("casa_comercial"):
        where.append("e.casa_comercial = %s")
        params.append(filtros["casa_comercial"])
    if filtros.get("marca"):
        where.append("e.marca = %s")
        params.append(filtros["marca"])
    if filtros.get("categoria"):
        where.append("e.categoria = %s")
        params.append(filtros["categoria"])
    if filtros.get("subcategoria"):
        where.append("e.subcategoria = %s")
        params.append(filtros["subcategoria"])
    if filtros.get("tipo_alcohol"):
        where.append("e.tipo_alcohol = %s")
        params.append(filtros["tipo_alcohol"])
    if filtros.get("es_alcoholico") is not None:
        where.append("e.es_alcoholico = %s")
        params.append(1 if filtros["es_alcoholico"] else 0)
    if filtros.get("grado_alcohol_min") is not None:
        where.append("e.grado_alcohol >= %s")
        params.append(float(filtros["grado_alcohol_min"]))
    if filtros.get("grado_alcohol_max") is not None:
        where.append("e.grado_alcohol <= %s")
        params.append(float(filtros["grado_alcohol_max"]))
    if filtros.get("requiere_validacion") is not None:
        where.append("e.requiere_validacion = %s")
        params.append(1 if filtros["requiere_validacion"] else 0)
    if filtros.get("activo") is not None:
        where.append("e.activo = %s")
        params.append(1 if filtros["activo"] else 0)
    if filtros.get("texto_busqueda"):
        where.append("(e.nombre_producto LIKE %s OR e.codigo_producto_origen LIKE %s OR e.marca LIKE %s)")
        t = f"%{filtros['texto_busqueda']}%"
        params += [t, t, t]

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    return where_sql, params


class ComercialEnriquecidoRepository:

    @staticmethod
    def listar(filtros: Dict, allowed_server_ids: Optional[List[str]], limit: int = 100, offset: int = 0) -> Dict:
        where_sql, params = _build_where(filtros, allowed_server_ids)
        # Total
        total_sql = (f"SELECT COUNT(*) AS n FROM dbo.Comercial_Productos_Enriquecidos e "
                     f"LEFT JOIN dbo.Sync_Productos p ON p.ProductoID = e.producto_id{where_sql}")
        total_rows = execute_sql_query_params(*_conn(), total_sql, tuple(params))
        total = int(total_rows[0]["n"]) if total_rows else 0
        # Página
        page_sql = (f"{_SELECT}{where_sql} ORDER BY COALESCE(p.Nombre, e.nombre_producto) "
                    f"OFFSET {int(offset)} ROWS FETCH NEXT {int(limit)} ROWS ONLY")
        items = execute_sql_query_params(*_conn(), page_sql, tuple(params))
        return {"total": total, "items": items, "limit": int(limit), "offset": int(offset)}

    @staticmethod
    def get_by_id(id_: str, allowed_server_ids: Optional[List[str]]) -> Optional[Dict]:
        where_sql, params = _build_where({}, allowed_server_ids)
        sep = " AND " if where_sql else " WHERE "
        sql = f"{_SELECT}{where_sql}{sep}e.id = %s"
        rows = execute_sql_query_params(*_conn(), sql, tuple(params) + (str(id_),))
        return rows[0] if rows else None

    @staticmethod
    def crear(data: Dict, usuario: Optional[str]) -> Optional[str]:
        cols = ["producto_id", "server_id", "system_type", "unidad_codigo",
                "codigo_producto_origen", "nombre_producto", "familia_origen"] + CAMPOS_EDITABLES + \
               ["activo", "fuente", "usuario_creacion"]
        vals = {
            "producto_id": data.get("producto_id"),
            "server_id": data.get("server_id"),
            "system_type": data.get("system_type"),
            "unidad_codigo": data.get("unidad_codigo"),
            "codigo_producto_origen": data.get("codigo_producto_origen"),
            "nombre_producto": data.get("nombre_producto"),
            "familia_origen": data.get("familia_origen"),
            "activo": 1 if data.get("activo", True) else 0,
            "fuente": data.get("fuente") or "MANUAL",
            "usuario_creacion": usuario,
        }
        for c in CAMPOS_EDITABLES:
            v = data.get(c)
            if c in ("es_alcoholico", "requiere_validacion"):
                v = 1 if v else 0
            vals[c] = v
        conn = get_sql_connection()
        cur = conn.cursor()
        try:
            placeholders = ", ".join(["%s"] * len(cols))
            cur.execute(
                f"INSERT INTO dbo.Comercial_Productos_Enriquecidos ({', '.join(cols)}) "
                f"OUTPUT CONVERT(varchar(36), INSERTED.id) AS id VALUES ({placeholders})",
                tuple(vals[c] for c in cols))
            row = cur.fetchone()
            new_id = row[0] if row else None
            conn.commit()
            return new_id
        except Exception as e:
            conn.rollback()
            logger.error(f"[CPE_REPO] Error crear: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def actualizar(id_: str, data: Dict, usuario: Optional[str]) -> bool:
        sets = []
        params = []
        for c in CAMPOS_EDITABLES:
            if c in data:
                v = data[c]
                if c in ("es_alcoholico", "requiere_validacion"):
                    v = 1 if v else 0
                sets.append(f"{c} = %s")
                params.append(v)
        if not sets:
            return False
        sets.append("usuario_actualizacion = %s")
        params.append(usuario)
        sets.append("fecha_actualizacion = SYSUTCDATETIME()")
        conn = get_sql_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                f"UPDATE dbo.Comercial_Productos_Enriquecidos SET {', '.join(sets)} WHERE id = %s",
                tuple(params) + (str(id_),))
            afectadas = cur.rowcount
            conn.commit()
            return afectadas > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"[CPE_REPO] Error actualizar: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def set_activo(id_: str, activo: bool, usuario: Optional[str]) -> bool:
        conn = get_sql_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE dbo.Comercial_Productos_Enriquecidos SET activo = %s, "
                "usuario_actualizacion = %s, fecha_actualizacion = SYSUTCDATETIME() WHERE id = %s",
                (1 if activo else 0, usuario, str(id_)))
            afectadas = cur.rowcount
            conn.commit()
            return afectadas > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"[CPE_REPO] Error set_activo: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def importar(rows: List[Dict], usuario: Optional[str]) -> Dict:
        """UPSERT por producto_id de filas de enriquecimiento (sin inventar datos)."""
        conn = get_sql_connection()
        cur = conn.cursor()
        n_ins = n_upd = n_skip = 0
        try:
            cur.execute("SELECT CONVERT(varchar(36), producto_id) pid FROM dbo.Comercial_Productos_Enriquecidos WHERE producto_id IS NOT NULL")
            existentes = {r[0].lower() for r in cur.fetchall()}
            set_cols = [c for c in CAMPOS_EDITABLES]
            for d in rows:
                pid = (d.get("producto_id") or "").strip()
                if not pid:
                    n_skip += 1
                    continue
                norm = {}
                for c in set_cols:
                    v = d.get(c)
                    if c in ("es_alcoholico", "requiere_validacion"):
                        v = 1 if v else 0
                    norm[c] = v
                if pid.lower() in existentes:
                    sets = ", ".join(f"{c}=%s" for c in set_cols)
                    cur.execute(
                        f"UPDATE dbo.Comercial_Productos_Enriquecidos SET {sets}, "
                        "usuario_actualizacion=%s, fecha_actualizacion=SYSUTCDATETIME() WHERE producto_id=%s",
                        tuple(norm[c] for c in set_cols) + (usuario, pid))
                    n_upd += 1
                else:
                    cols = ["producto_id", "server_id", "system_type", "unidad_codigo",
                            "codigo_producto_origen", "nombre_producto"] + set_cols + ["fuente", "usuario_creacion"]
                    base = {
                        "producto_id": pid,
                        "server_id": d.get("server_id"),
                        "system_type": d.get("system_type"),
                        "unidad_codigo": d.get("unidad_codigo"),
                        "codigo_producto_origen": d.get("codigo_producto_origen"),
                        "nombre_producto": d.get("nombre_producto"),
                        "fuente": d.get("fuente") or "IMPORT_API",
                        "usuario_creacion": usuario,
                    }
                    base.update(norm)
                    cur.execute(
                        f"INSERT INTO dbo.Comercial_Productos_Enriquecidos ({', '.join(cols)}) "
                        f"VALUES ({', '.join(['%s'] * len(cols))})",
                        tuple(base[c] for c in cols))
                    n_ins += 1
                    existentes.add(pid.lower())
            conn.commit()
            return {"insertadas": n_ins, "actualizadas": n_upd, "omitidas": n_skip}
        except Exception as e:
            conn.rollback()
            logger.error(f"[CPE_REPO] Error importar: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def catalogos_filtros(allowed_server_ids: Optional[List[str]]) -> Dict:
        where_sql, params = _build_where({}, allowed_server_ids)

        def _distinct(col):
            sql = (f"SELECT DISTINCT {col} AS v FROM dbo.Comercial_Productos_Enriquecidos e"
                   f"{where_sql} AND {col} IS NOT NULL ORDER BY {col}" if where_sql
                   else f"SELECT DISTINCT {col} AS v FROM dbo.Comercial_Productos_Enriquecidos e WHERE {col} IS NOT NULL ORDER BY {col}")
            return [r["v"] for r in execute_sql_query_params(*_conn(), sql, tuple(params))]

        def _count(cond):
            sep = " AND " if where_sql else " WHERE "
            sql = (f"SELECT COUNT(*) AS n FROM dbo.Comercial_Productos_Enriquecidos e"
                   f"{where_sql}{sep}{cond}")
            r = execute_sql_query_params(*_conn(), sql, tuple(params))
            return int(r[0]["n"]) if r else 0

        return {
            "grupos_comerciales": _distinct("e.grupo_comercial"),
            "casas_comerciales": _distinct("e.casa_comercial"),
            "marcas": _distinct("e.marca"),
            "categorias": _distinct("e.categoria"),
            "subcategorias": _distinct("e.subcategoria"),
            "tipos_alcohol": _distinct("e.tipo_alcohol"),
            "indicadores": {
                "sin_marca": _count("e.marca IS NULL"),
                "sin_grupo_comercial": _count("e.grupo_comercial IS NULL"),
                "alcoholico_sin_grado": _count("e.es_alcoholico = 1 AND e.grado_alcohol IS NULL"),
                "sin_presentacion": _count("e.presentacion_ml IS NULL"),
                "requiere_validacion": _count("e.requiere_validacion = 1"),
                "total": _count("1 = 1"),
            },
        }
