"""
Servicio del Catálogo Canónico de Sincronizaciones
==================================================
Fuente única (NO hardcode) de los tipos de sync, agrupados por `Grupo`, con
dependencias y orden. Lee/escribe dbo.Sistema_Sync_Catalogo.

- get_catalogo() / get_catalogo_agrupado()
- get_tipo(codigo)
- crear_tipo / actualizar_tipo / toggle_activo
- resolver_dependencias(codigos): expande dependencias (recursivo) y devuelve el
  conjunto ORDENADO (topológico + Orden), marcando origen/obligatoria.

NO USA MONGODB - 100% SQL Server (EDARSAHUB).
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)

_RUNTIME_IMPLEMENTED_HANDLERS = {'inventarios_fisicos': 'sync_inventarios_fisicos'}

_CAMPOS = (
    "Codigo, Nombre, Grupo, Descripcion, Orden, NivelRiesgo, PermiteResync, "
    "PermiteDryRun, RequiereUnidad, RequiereRangoFechas, RangoMaxDias, Handler, "
    "HandlerImplementado, TablaDestino, Dependencias, Activo"
)


def _row_to_dict(r: Dict[str, Any]) -> Dict[str, Any]:
    deps_raw = r.get('Dependencias')
    try:
        deps = json.loads(deps_raw) if deps_raw else []
    except Exception:
        deps = []
    return {
        'codigo': r['Codigo'],
        'nombre': r['Nombre'],
        'grupo': r['Grupo'],
        'descripcion': r.get('Descripcion') or '',
        'orden': int(r.get('Orden') or 100),
        'nivel_riesgo': r.get('NivelRiesgo') or 'MEDIO',
        'permite_resync': bool(r.get('PermiteResync')),
        'permite_dry_run': bool(r.get('PermiteDryRun')),
        'requiere_unidad': bool(r.get('RequiereUnidad')),
        'requiere_rango_fechas': bool(r.get('RequiereRangoFechas')),
        'rango_max_dias': int(r.get('RangoMaxDias') or 30),
        'handler': r.get('Handler'),
        'handler_implementado': bool(r.get('HandlerImplementado')) or _RUNTIME_IMPLEMENTED_HANDLERS.get(r['Codigo']) == r.get('Handler'),
        'tabla_destino': r.get('TablaDestino'),
        'dependencias': deps,
        'activo': bool(r.get('Activo')),
    }


def get_catalogo(incluir_inactivos: bool = False) -> List[Dict[str, Any]]:
    """Devuelve todos los tipos de sync del catálogo."""
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    where = "" if incluir_inactivos else "WHERE ISNULL(Activo,1)=1"
    cur.execute(f"SELECT {_CAMPOS} FROM dbo.Sistema_Sync_Catalogo {where} ORDER BY Grupo, Orden, Nombre")
    rows = list(cur.fetchall())
    cur.close()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_catalogo_agrupado(incluir_inactivos: bool = False) -> List[Dict[str, Any]]:
    """Devuelve el catálogo agrupado: [{grupo, tipos:[...]}] ordenado por Orden mín."""
    items = get_catalogo(incluir_inactivos)
    grupos: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        grupos.setdefault(it['grupo'], []).append(it)
    out = [{'grupo': g, 'tipos': tipos} for g, tipos in grupos.items()]
    # Ordenar grupos por el orden mínimo de sus tipos (estabilidad visual)
    out.sort(key=lambda gr: min((t['orden'] for t in gr['tipos']), default=100))
    return out


def get_tipo(codigo: str) -> Optional[Dict[str, Any]]:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(f"SELECT {_CAMPOS} FROM dbo.Sistema_Sync_Catalogo WHERE Codigo=%s", (codigo,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return _row_to_dict(row) if row else None


def crear_tipo(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un nuevo tipo de sync (canónico)."""
    codigo = (data.get('codigo') or '').strip()
    if not codigo:
        raise ValueError("codigo requerido")
    if get_tipo(codigo):
        raise ValueError(f"El tipo '{codigo}' ya existe")
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Sistema_Sync_Catalogo
        (Codigo, Nombre, Grupo, Descripcion, Orden, NivelRiesgo, PermiteResync,
         PermiteDryRun, RequiereUnidad, RequiereRangoFechas, RangoMaxDias, Handler,
         HandlerImplementado, TablaDestino, Dependencias, Activo)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (codigo, data.get('nombre') or codigo, data.get('grupo') or 'General',
         data.get('descripcion'), int(data.get('orden', 100)),
         data.get('nivel_riesgo', 'MEDIO'),
         1 if data.get('permite_resync', True) else 0,
         1 if data.get('permite_dry_run', True) else 0,
         1 if data.get('requiere_unidad', True) else 0,
         1 if data.get('requiere_rango_fechas', True) else 0,
         int(data.get('rango_max_dias', 30)), data.get('handler'),
         1 if data.get('handler_implementado', False) else 0,
         data.get('tabla_destino'),
         json.dumps(data.get('dependencias') or []),
         1 if data.get('activo', True) else 0)
    )
    conn.commit()
    cur.close()
    conn.close()
    return get_tipo(codigo)


def actualizar_tipo(codigo: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Actualiza campos editables de un tipo existente."""
    actual = get_tipo(codigo)
    if not actual:
        raise ValueError(f"Tipo '{codigo}' no encontrado")
    campos_map = {
        'nombre': 'Nombre', 'grupo': 'Grupo', 'descripcion': 'Descripcion',
        'orden': 'Orden', 'nivel_riesgo': 'NivelRiesgo',
        'permite_resync': 'PermiteResync', 'permite_dry_run': 'PermiteDryRun',
        'requiere_unidad': 'RequiereUnidad', 'requiere_rango_fechas': 'RequiereRangoFechas',
        'rango_max_dias': 'RangoMaxDias', 'handler': 'Handler',
        'handler_implementado': 'HandlerImplementado', 'tabla_destino': 'TablaDestino',
        'dependencias': 'Dependencias', 'activo': 'Activo',
    }
    sets, vals = [], []
    for k, col in campos_map.items():
        if k not in data:
            continue
        v = data[k]
        if k == 'dependencias':
            v = json.dumps(v or [])
        elif isinstance(v, bool):
            v = 1 if v else 0
        sets.append(f"{col}=%s")
        vals.append(v)
    if not sets:
        return actual
    sets.append("FechaActualizacion=%s")
    vals.append(datetime.now(timezone.utc))
    vals.append(codigo)
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE dbo.Sistema_Sync_Catalogo SET {', '.join(sets)} WHERE Codigo=%s", tuple(vals))
    conn.commit()
    cur.close()
    conn.close()
    return get_tipo(codigo)


def toggle_activo(codigo: str) -> Dict[str, Any]:
    actual = get_tipo(codigo)
    if not actual:
        raise ValueError(f"Tipo '{codigo}' no encontrado")
    return actualizar_tipo(codigo, {'activo': not actual['activo']})


def resolver_dependencias(codigos: List[str]) -> Dict[str, Any]:
    """
    Dado un conjunto de códigos seleccionados por el usuario, expande sus
    dependencias (recursivo) y devuelve el conjunto ORDENADO para ejecutar.

    Cada item:
      - codigo, nombre, grupo, orden, handler_implementado, requiere_*
      - seleccionado_directo: True si lo pidió el usuario; False si es dependencia
      - obligatoria: True si alguna relación que lo trae es obligatoria
    El orden respeta: primero dependencias, luego dependientes; desempate por Orden.
    """
    catalogo = {t['codigo']: t for t in get_catalogo(incluir_inactivos=False)}
    resueltos: Dict[str, Dict[str, Any]] = {}

    def visitar(cod: str, directo: bool, obligatoria: bool):
        tipo = catalogo.get(cod)
        if not tipo:
            return
        if cod in resueltos:
            resueltos[cod]['seleccionado_directo'] = resueltos[cod]['seleccionado_directo'] or directo
            resueltos[cod]['obligatoria'] = resueltos[cod]['obligatoria'] or obligatoria
            return
        resueltos[cod] = {
            'codigo': tipo['codigo'], 'nombre': tipo['nombre'], 'grupo': tipo['grupo'],
            'orden': tipo['orden'], 'nivel_riesgo': tipo['nivel_riesgo'],
            'handler_implementado': tipo['handler_implementado'],
            'requiere_unidad': tipo['requiere_unidad'],
            'requiere_rango_fechas': tipo['requiere_rango_fechas'],
            'rango_max_dias': tipo['rango_max_dias'],
            'seleccionado_directo': directo, 'obligatoria': obligatoria,
        }
        for dep in tipo.get('dependencias', []):
            visitar(dep.get('codigo'), directo=False, obligatoria=bool(dep.get('obligatoria')))

    for c in codigos:
        visitar(c, directo=True, obligatoria=False)

    # Orden topológico: dependencias antes que dependientes; desempate por Orden.
    orden_final: List[str] = []
    visitando = set()

    def topo(cod: str):
        if cod in orden_final or cod not in resueltos:
            return
        if cod in visitando:  # ciclo: rompe sin reventar
            return
        visitando.add(cod)
        tipo = catalogo.get(cod, {})
        deps = sorted([d.get('codigo') for d in tipo.get('dependencias', []) if d.get('codigo') in resueltos],
                      key=lambda x: catalogo.get(x, {}).get('orden', 100))
        for d in deps:
            topo(d)
        visitando.discard(cod)
        if cod not in orden_final:
            orden_final.append(cod)

    for c in sorted(resueltos.keys(), key=lambda x: resueltos[x]['orden']):
        topo(c)

    items = [resueltos[c] for c in orden_final]
    deps_agregadas = [i for i in items if not i['seleccionado_directo']]
    return {
        'items': items,
        'total': len(items),
        'agregadas_por_dependencia': [i['codigo'] for i in deps_agregadas],
        'requiere_confirmar': len(deps_agregadas) > 0,
    }
