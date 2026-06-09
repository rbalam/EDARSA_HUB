"""
Loader: importa el Excel "Catálogo de Bebidas Enriquecido" a las tablas
canónicas dbo.Comercial_Productos_Enriquecidos y dbo.Comercial_Marcas_Diccionario.
========================================================================
COMERCIAL-ENRIQUECIDO-B2 (2026-06-09)

- Lee el Excel validado por el usuario (NO inventa marcas/grados).
- Enlaza por producto_id (UNIQUEIDENTIFIER) -> Sync_Productos.ProductoID
  (match verificado 100%).
- Idempotente: UPSERT por producto_id (catálogo) y por marca (diccionario).
- NO-LIVE, conexión central (get_sql_connection).

Uso:  PYTHONPATH=/app/backend python scripts/import_catalogo_enriquecido.py [ruta_xlsx]
"""
import os
import sys
import urllib.request
from dotenv import load_dotenv

load_dotenv()

from core.sql_first.db import get_sql_connection  # noqa: E402

XLSX_URL = ("https://customer-assets.emergentagent.com/job_ecfd41f5-4332-4ee1-b366-4822848a44a3/"
            "artifacts/emwx3lwk_Catalogo_Bebidas_EDARSAHUB_Enriquecido_Web_20260609.xlsx")
DEFAULT_PATH = "/tmp/catalogo.xlsx"


def _to_bool(v):
    if v is None:
        return 0
    s = str(v).strip().lower()
    return 1 if s in ("1", "true", "verdadero", "si", "sí", "yes", "x") else 0


def _to_dec(v):
    if v is None or str(v).strip() == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_str(v, maxlen=None):
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() == "none":
        return None
    return s[:maxlen] if maxlen else s


def _to_guid(v):
    s = _to_str(v)
    if not s or len(s) < 32:
        return None
    return s


def _rows(ws):
    it = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(it)]
    idx = {h: i for i, h in enumerate(header)}
    for r in it:
        if r is None or all(c is None for c in r):
            continue
        yield r, idx


def cargar_diccionario(wb, cur):
    ws = wb["Diccionario_marcas"]
    n_ins = n_upd = 0
    for r, idx in _rows(ws):
        marca = _to_str(r[idx["marca"]], 200)
        if not marca:
            continue
        vals = (
            _to_str(r[idx.get("patron", -1)] if "patron" in idx else None, 300),
            _to_str(r[idx.get("grupo_comercial", -1)] if "grupo_comercial" in idx else None, 200),
            _to_str(r[idx.get("categoria", -1)] if "categoria" in idx else None, 150),
            _to_str(r[idx.get("subcategoria_base", -1)] if "subcategoria_base" in idx else None, 150),
            _to_str(r[idx.get("tipo_alcohol", -1)] if "tipo_alcohol" in idx else None, 100),
            _to_dec(r[idx.get("grado_default", -1)] if "grado_default" in idx else None),
            _to_str(r[idx.get("fuente_grupo_url", -1)] if "fuente_grupo_url" in idx else None, 500),
            _to_str(r[idx.get("fuente_grado", -1)] if "fuente_grado" in idx else None, 500),
        )
        cur.execute("SELECT id FROM dbo.Comercial_Marcas_Diccionario WHERE marca=%s", (marca,))
        if cur.fetchone():
            cur.execute(
                "UPDATE dbo.Comercial_Marcas_Diccionario SET patron=%s, grupo_comercial=%s, "
                "categoria=%s, subcategoria_base=%s, tipo_alcohol=%s, grado_default=%s, "
                "fuente_grupo_url=%s, fuente_grado=%s WHERE marca=%s",
                vals + (marca,))
            n_upd += 1
        else:
            cur.execute(
                "INSERT INTO dbo.Comercial_Marcas_Diccionario "
                "(marca, patron, grupo_comercial, categoria, subcategoria_base, tipo_alcohol, "
                "grado_default, fuente_grupo_url, fuente_grado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (marca,) + vals)
            n_ins += 1
    return n_ins, n_upd


_CAMPOS = [
    "producto_id", "server_id", "system_type", "unidad_codigo", "codigo_producto_origen",
    "nombre_producto", "familia_origen", "grupo_comercial", "marca", "categoria",
    "subcategoria", "tipo_alcohol", "es_alcoholico", "grado_alcohol", "presentacion_ml",
    "proveedor_id", "representante_id", "precio_venta", "confianza", "requiere_validacion",
    "regla_usada", "fuente_grupo_url", "fuente_grado_url", "observaciones", "activo", "fuente",
]


def _extraer(r, idx):
    g = lambda k: r[idx[k]] if k in idx else None
    return {
        "producto_id": _to_guid(g("producto_id")),
        "server_id": _to_str(g("server_id"), 50),
        "system_type": _to_str(g("system_type"), 20),
        "unidad_codigo": _to_str(g("unidad_codigo"), 50),
        "codigo_producto_origen": _to_str(g("codigo_producto_origen"), 100),
        "nombre_producto": _to_str(g("nombre_producto"), 300),
        "familia_origen": _to_str(g("familia_origen"), 200),
        "grupo_comercial": _to_str(g("grupo_comercial"), 200),
        "marca": _to_str(g("marca"), 200),
        "categoria": _to_str(g("categoria"), 150),
        "subcategoria": _to_str(g("subcategoria"), 150),
        "tipo_alcohol": _to_str(g("tipo_alcohol"), 100),
        "es_alcoholico": _to_bool(g("es_alcoholico")),
        "grado_alcohol": _to_dec(g("grado_alcohol")),
        "presentacion_ml": _to_dec(g("presentacion_ml")),
        "proveedor_id": _to_guid(g("proveedor_id")),
        "representante_id": _to_guid(g("representante_id")),
        "precio_venta": _to_dec(g("precio_venta")),
        "confianza": _to_dec(g("confianza")),
        "requiere_validacion": _to_bool(g("requiere_validacion")),
        "regla_usada": _to_str(g("regla_usada"), 200),
        "fuente_grupo_url": _to_str(g("fuente_grupo_url"), 500),
        "fuente_grado_url": _to_str(g("fuente_grado_url"), 500),
        "observaciones": _to_str(g("observaciones"), 1000),
        "activo": _to_bool(g("activo")) if g("activo") is not None else 1,
    }


def cargar_catalogo(wb, cur, sheet, fuente):
    ws = wb[sheet]
    # mapa producto_id -> existe
    cur.execute("SELECT CONVERT(varchar(36), producto_id) pid FROM dbo.Comercial_Productos_Enriquecidos WHERE producto_id IS NOT NULL")
    existentes = {row[0].lower() for row in cur.fetchall()}
    n_ins = n_upd = n_skip = 0
    set_cols = [c for c in _CAMPOS if c not in ("producto_id", "fuente")]
    update_sql = ("UPDATE dbo.Comercial_Productos_Enriquecidos SET "
                  + ", ".join(f"{c}=%s" for c in set_cols)
                  + ", fuente=%s, fecha_actualizacion=SYSUTCDATETIME() WHERE producto_id=%s")
    insert_cols = _CAMPOS
    insert_sql = ("INSERT INTO dbo.Comercial_Productos_Enriquecidos ("
                  + ", ".join(insert_cols) + ") VALUES ("
                  + ", ".join(["%s"] * len(insert_cols)) + ")")
    for r, idx in _rows(ws):
        d = _extraer(r, idx)
        pid = d["producto_id"]
        if not pid:
            n_skip += 1
            continue
        if pid.lower() in existentes:
            params = tuple(d[c] for c in set_cols) + (fuente, pid)
            cur.execute(update_sql, params)
            n_upd += 1
        else:
            params = tuple(d.get(c) if c != "fuente" else fuente for c in insert_cols)
            cur.execute(insert_sql, params)
            n_ins += 1
            existentes.add(pid.lower())
    return n_ins, n_upd, n_skip


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    if not os.path.exists(path):
        print(f"[B2] Descargando Excel a {path}...")
        urllib.request.urlretrieve(XLSX_URL, path)
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        di, du = cargar_diccionario(wb, cur)
        print(f"[B2] Diccionario_marcas: insertadas={di}, actualizadas={du}")
        ei, eu, es = cargar_catalogo(wb, cur, "Catalogo_enriquecido", "IMPORT_EXCEL_BEBIDAS")
        print(f"[B2] Catalogo_enriquecido: insertadas={ei}, actualizadas={eu}, omitidas={es}")
        pi, pu, ps = cargar_catalogo(wb, cur, "Pendientes_validacion", "IMPORT_EXCEL_PENDIENTES")
        print(f"[B2] Pendientes_validacion: insertadas={pi}, actualizadas={pu}, omitidas={ps}")
        conn.commit()
        print("[B2] COMMIT OK")
    except Exception as e:
        conn.rollback()
        print("[B2] ROLLBACK por error:", e)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
