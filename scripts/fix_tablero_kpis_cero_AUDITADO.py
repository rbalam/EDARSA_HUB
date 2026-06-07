#!/usr/bin/env python3
"""
FIX P0 (versión AUDITADA y corregida) - Tablero Ejecutivo KPIs en cero - Junio 2026.

Causas raíz confirmadas contra el esquema real de EDARSAHUB SQL:
  1) Las queries filtran columnas INEXISTENTES `activo`/`es_demo` -> error -> [] -> KPIs cero.
  2) Filtran `unidad_negocio_pk` (GUID) con CÓDIGOS canónicos -> nunca matchea.
     Las unidades permitidas (get_unidades_permitidas_v2) son CÓDIGOS -> filtrar por `unidad_negocio_id`.
  3) `get_kpis_por_unidad` arma SQL INVÁLIDO (texto literal `UnidadesService.resolver_codigo(...) or '...'`).

Máximas aplicadas:
  - Fuente única: vistas EDARSAHUB SQL `vw_Comercial_KPIs_*_v2_Runtime` (NO base table, NO live, NO Mongo).
  - KPI ventas = ventas_sin_propina; propinas_total separado y FUERA del KPI.
  - Sin LIKE/nombre para resolver unidad: GROUP BY / filtro por unidad_negocio_id canónico.
"""
import re
from pathlib import Path
from datetime import datetime

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
REPO = Path("/app/backend/modules/comercial_v2/repository_readonly.py")
ROUTES = Path("/app/backend/modules/comercial_v2/routes.py")

repo = REPO.read_text(encoding="utf-8")
routes = ROUTES.read_text(encoding="utf-8")

# Respaldos
REPO.with_suffix(f".py.bak_{TS}").write_text(repo, encoding="utf-8")
ROUTES.with_suffix(f".py.bak_{TS}").write_text(routes, encoding="utf-8")

errors = []

def must(cond, msg):
    if not cond:
        errors.append(msg)

# ---------------------------------------------------------------------------
# R1: get_kpis_diarios_agregados  (bloque exacto)
# ---------------------------------------------------------------------------
old_agg = '''def get_kpis_diarios_agregados(
    fecha_inicio: date,
    fecha_fin: date,
    unidades_permitidas: Optional[List[str]] = None
) -> Dict:
    """
    Obtiene KPIs diarios agregados (totales) para el dashboard.
    """
    where_clauses = [
        f"fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'",
        "activo = 1",
        "es_demo = 0"
    ]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{u}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_pk IN ({ids_quoted})")
    
    query = f"""
    SELECT 
        COUNT(*) as total_registros,
        COUNT(DISTINCT unidad_negocio_pk) as total_unidades,
        COUNT(DISTINCT fecha_operacion) as total_dias,
        SUM(ventas_total) as ventas_total,
        SUM(tickets_total) as tickets_total,
        SUM(pax_total) as pax_total,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {' AND '.join(where_clauses)}
    """
    
    result = _execute_readonly_query(query)
    return result[0] if result else {}'''

new_agg = '''def get_kpis_diarios_agregados(
    fecha_inicio: date,
    fecha_fin: date,
    unidades_permitidas: Optional[List[str]] = None
) -> Dict:
    """
    Obtiene KPIs diarios agregados (totales) para el dashboard.

    MÁXIMA: KPI de ventas = ventas_sin_propina (las propinas NO cuentan como venta);
    propinas_total se informa por separado. Filtro por unidad_negocio_id canónico.
    Fuente: vw_Comercial_KPIs_Diarios_v2_Runtime (EDARSAHUB SQL, NO live, NO Mongo).
    """
    where_clauses = [
        f"fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'"
    ]
    
    if unidades_permitidas:
        ids_quoted = ','.join([f"'{str(u).replace(chr(39), chr(39)+chr(39))}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")
    
    query = f"""
    SELECT 
        COUNT(*) as total_registros,
        COUNT(DISTINCT unidad_negocio_id) as total_unidades,
        COUNT(DISTINCT fecha_operacion) as total_dias,
        SUM(ISNULL(ventas_sin_propina, 0)) as ventas_total,
        SUM(ISNULL(propinas_total, 0)) as propinas_total,
        SUM(ISNULL(tickets_total, 0)) as tickets_total,
        SUM(ISNULL(pax_total, 0)) as pax_total,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {' AND '.join(where_clauses)}
    """
    
    result = _execute_readonly_query(query)
    return result[0] if result else {}'''

must(old_agg in repo, "R1: no se encontró el bloque exacto get_kpis_diarios_agregados")
repo = repo.replace(old_agg, new_agg, 1)

# ---------------------------------------------------------------------------
# R2: get_kpis_por_unidad  (regex DOTALL: desde def hasta su return)
# ---------------------------------------------------------------------------
new_por_unidad = '''def get_kpis_por_unidad(
    fecha_inicio: date,
    fecha_fin: date,
    unidades_permitidas: Optional[List[str]] = None
) -> List[Dict]:
    """
    Obtiene KPIs agregados por unidad para el dashboard desde EDARSAHUB SQL.

    MÁXIMA:
    - Se agrupa por unidad_negocio_id canónico (sin LIKE/nombre, sin SQL inválido).
    - KPI ventas = ventas_sin_propina; propinas_total queda separado y FUERA del KPI.
    - Fuente: vw_Comercial_KPIs_Diarios_v2_Runtime (NO live, NO Mongo).
    """
    where_clauses = [
        f"fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'"
    ]

    if unidades_permitidas:
        ids_quoted = ','.join([f"'{str(u).replace(chr(39), chr(39)+chr(39))}'" for u in unidades_permitidas])
        where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")

    query = f"""
    SELECT 
        unidad_negocio_id as unidad_negocio_pk,
        MAX(unidad_negocio_nombre) as unidad_negocio_nombre,
        MAX(sistema_origen) as sistema_origen,
        COUNT(DISTINCT fecha_operacion) as dias,
        SUM(ISNULL(ventas_sin_propina, 0)) as ventas_total,
        SUM(ISNULL(ventas_sin_propina, 0)) as ventas_sin_propina,
        SUM(ISNULL(propinas_total, 0)) as propinas_total,
        SUM(ISNULL(tickets_total, 0)) as tickets_total,
        SUM(ISNULL(pax_total, 0)) as pax_total,
        CASE WHEN SUM(ISNULL(tickets_total, 0)) > 0
             THEN SUM(ISNULL(ventas_sin_propina, 0)) / SUM(ISNULL(tickets_total, 0))
             ELSE 0 END as ticket_promedio_avg,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {' AND '.join(where_clauses)}
    GROUP BY unidad_negocio_id
    ORDER BY ventas_total DESC
    """

    return _execute_readonly_query(query)
'''

pat_por_unidad = re.compile(
    r"def get_kpis_por_unidad\(.*?\n    return _execute_readonly_query\(query\)\n",
    re.S,
)
must(pat_por_unidad.search(repo) is not None, "R2: no se encontró get_kpis_por_unidad")
repo = pat_por_unidad.sub(lambda m: new_por_unidad, repo, count=1)

# ---------------------------------------------------------------------------
# Reemplazos globales en REPO (tras R1/R2)
# ---------------------------------------------------------------------------
# Quitar activo/es_demo (columnas inexistentes en TODAS las tablas)
n = repo.count(',\n        "activo = 1",\n        "es_demo = 0"')
must(n == 1, f"R3a: se esperaba 1 bloque activo/es_demo restante, hay {n}")
repo = repo.replace(',\n        "activo = 1",\n        "es_demo = 0"', '')

n = repo.count(',\n        "activo = 1"\n    ]')
must(n == 1, f"R3b: se esperaba 1 'activo = 1' (mensuales), hay {n}")
repo = repo.replace(',\n        "activo = 1"\n    ]', '\n    ]')

must('where_clauses = ["activo = 1", "es_demo = 0"]' in repo, "R3c: unidades_disponibles where")
repo = repo.replace('where_clauses = ["activo = 1", "es_demo = 0"]', 'where_clauses = []')

must('WHERE activo = 1 AND es_demo = 0' in repo, "R3d: check_v2_health where")
repo = repo.replace('WHERE activo = 1 AND es_demo = 0', 'WHERE 1 = 1')

# Filtro pk(GUID) -> id(codigo)
n = repo.count('where_clauses.append(f"unidad_negocio_pk IN ({ids_quoted})")')
must(n >= 5, f"R4: se esperaban >=5 filtros pk IN, hay {n}")
repo = repo.replace('where_clauses.append(f"unidad_negocio_pk IN ({ids_quoted})")',
                    'where_clauses.append(f"unidad_negocio_id IN ({ids_quoted})")')

# get_ventas_dia_abiertas: alias id->pk + PARTITION por id
must('            id,\n            unidad_negocio_pk,\n            unidad_negocio_nombre,' in repo, "R5a: CTE abiertas")
repo = repo.replace('            id,\n            unidad_negocio_pk,\n            unidad_negocio_nombre,',
                    '            id,\n            unidad_negocio_id AS unidad_negocio_pk,\n            unidad_negocio_nombre,')
must('PARTITION BY unidad_negocio_pk ORDER BY snapshot_timestamp DESC' in repo, "R5b: PARTITION abiertas")
repo = repo.replace('PARTITION BY unidad_negocio_pk ORDER BY snapshot_timestamp DESC',
                    'PARTITION BY unidad_negocio_id ORDER BY snapshot_timestamp DESC')

# get_unidades_disponibles ventas
must('SUM(ventas_total) as ventas_historicas' in repo, "R6: ventas_historicas")
repo = repo.replace('SUM(ventas_total) as ventas_historicas',
                    'SUM(ISNULL(ventas_sin_propina, 0)) as ventas_historicas')

# get_comparativos_diarios
n = repo.count("WHERE unidad_negocio_pk = '{unidad_negocio_pk}'\n      AND activo = 1 AND es_demo = 0")
must(n == 2, f"R7a: comparativos pk+activo, hay {n}")
repo = repo.replace("WHERE unidad_negocio_pk = '{unidad_negocio_pk}'\n      AND activo = 1 AND es_demo = 0",
                    "WHERE unidad_negocio_id = '{unidad_negocio_pk}'")
must("WHERE unidad_negocio_pk = '{unidad_negocio_pk}'\n      AND fecha_operacion" in repo, "R7b: comparativos actual")
repo = repo.replace("WHERE unidad_negocio_pk = '{unidad_negocio_pk}'\n      AND fecha_operacion",
                    "WHERE unidad_negocio_id = '{unidad_negocio_pk}'\n      AND fecha_operacion")
n = repo.count('ISNULL(ventas_total, 0) as ventas')
must(n == 2, f"R7c: comparativos ISNULL ventas, hay {n}")
repo = repo.replace('ISNULL(ventas_total, 0) as ventas', 'ISNULL(ventas_sin_propina, 0) as ventas')

# ---------------------------------------------------------------------------
# Reemplazos en ROUTES
# ---------------------------------------------------------------------------
n = routes.count('          AND activo = 1\n          AND es_demo = 0\n')
must(n == 5, f"RT1: se esperaban 5 activo/es_demo en routes, hay {n}")
routes = routes.replace('          AND activo = 1\n          AND es_demo = 0\n', '')

n = routes.count('\n          AND activo = 1 AND es_demo = 0')
must(n == 1, f"RT2: se esperaba 1 activo/es_demo inline, hay {n}")
routes = routes.replace('\n          AND activo = 1 AND es_demo = 0', '')

n = routes.count("WHERE unidad_negocio_pk = '{unidad_negocio_pk}'")
must(n == 4, f"RT3: se esperaban 4 WHERE pk= en routes, hay {n}")
routes = routes.replace("WHERE unidad_negocio_pk = '{unidad_negocio_pk}'",
                        "WHERE unidad_negocio_id = '{unidad_negocio_pk}'")

n = routes.count('WHERE unidad_negocio_pk IN ({ids_quoted})')
must(n == 2, f"RT4: se esperaban 2 WHERE pk IN en routes, hay {n}")
routes = routes.replace('WHERE unidad_negocio_pk IN ({ids_quoted})',
                        'WHERE unidad_negocio_id IN ({ids_quoted})')

n = routes.count('SUM(ventas_total) as ventas,')
must(n == 5, f"RT5: se esperaban 5 SUM(ventas_total) as ventas, hay {n}")
routes = routes.replace('SUM(ventas_total) as ventas,',
                        'SUM(ISNULL(ventas_sin_propina, 0)) as ventas,')

# ---------------------------------------------------------------------------
# Validación final
# ---------------------------------------------------------------------------
if errors:
    print("ABORTADO - fallaron aserciones (NO se escribió nada):")
    for e in errors:
        print("  -", e)
    raise SystemExit(2)

# Asserts post: no debe quedar activo/es_demo ni filtro pk inválido
for label, txt in [("repo", repo), ("routes", routes)]:
    assert 'activo = 1' not in txt, f"{label}: aún queda 'activo = 1'"
    assert 'es_demo = 0' not in txt, f"{label}: aún queda 'es_demo = 0'"
    assert 'unidad_negocio_pk IN (' not in txt, f"{label}: aún queda filtro pk IN"
    assert "unidad_negocio_pk = '{unidad_negocio_pk}'" not in txt, f"{label}: aún queda filtro pk ="
assert 'UnidadesService.resolver_codigo' not in repo.split('FUNCIONES DE LECTURA - KPIs MENSUALES')[0], "repo: SQL inválido aún presente en por_unidad"

REPO.write_text(repo, encoding="utf-8")
ROUTES.write_text(routes, encoding="utf-8")
print("OK - parches aplicados y verificados. Backups .bak_%s" % TS)
