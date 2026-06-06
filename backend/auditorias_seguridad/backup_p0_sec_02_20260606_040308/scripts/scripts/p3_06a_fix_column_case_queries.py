from pathlib import Path
import re
import shutil
from datetime import datetime
from collections import defaultdict

ROOT = Path("/app/backend")
SCHEMA = Path("/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

if not SCHEMA.exists():
    raise SystemExit(f"No existe schema: {SCHEMA}")

schema_txt = SCHEMA.read_text(errors="ignore")

# Extraer tablas y columnas del DDL
tables = defaultdict(dict)

create_blocks = re.finditer(
    r"CREATE\s+TABLE\s+(?:\[dbo\]\.)?\[?([A-Za-z0-9_]+)\]?\s*\((.*?)\)\s*(?:ON|;|\nGO)",
    schema_txt,
    re.I | re.S
)

for m in create_blocks:
    table = m.group(1)
    body = m.group(2)
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        cm = re.match(r"\[?([A-Za-z0-9_]+)\]?\s+\[?(bigint|int|nvarchar|varchar|decimal|datetime|datetime2|date|bit|float|uniqueidentifier|money)", line, re.I)
        if cm:
            col = cm.group(1)
            tables[table][col.lower()] = col

print("Tablas detectadas:", len(tables))

# Correcciones comunes por tabla
GLOBAL_CANONICAL = {
    "server_id": "ServerID",
    "servidor_id": "ServidorID",
    "empresa_id": "EmpresaID",
    "unidad_negocio_id": "UnidadNegocioID",
    "producto_id": "ProductoID",
    "sucursal_id": "SucursalID",
    "familia_id": "FamiliaID",
    "grupo_id": "GrupoID",
    "categoria_id": "CategoriaID",
    "proveedor_id": "ProveedorID",
    "almacen_id": "AlmacenID",
    "fecha_sync": "FechaSync",
    "system_type": "SystemType",
}

SPECIAL_TABLE_RULES = {
    "Comercial_KPIs_Diarios_v2": {
        "ServerID": "server_id",
        "UnidadNegocioID": "unidad_negocio_id",
        "FechaOperacion": "fecha_operacion",
        "VentasNetas": "ventas_total",
        "ventas_netas": "ventas_total",
        "num_cheques": "tickets_total",
        "pax": "pax_total",
    },
    "Servidores_Conexiones": {
        "ServerID": "id",
        "server_id": "id",
        "Nombre": "nombre",
        "SystemType": "system_type",
        "TipoConexion": "tipo_conexion",
    },
}

SQL_BLOCK_RE = re.compile(r'("""|\'\'\')([\s\S]*?)(\1)')

def table_aliases(sql):
    aliases = {}
    for tm in re.finditer(r"\b(?:FROM|JOIN|UPDATE|INTO)\s+\[?([A-Za-z_][A-Za-z0-9_]*)\]?(?:\s+(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*))?", sql, re.I):
        table = tm.group(1)
        alias = tm.group(2)

        if table not in tables:
            continue

        aliases[table] = table
        if alias and alias.upper() not in {
            "ON", "WHERE", "INNER", "LEFT", "RIGHT", "FULL",
            "GROUP", "ORDER", "SET", "VALUES", "SELECT"
        }:
            aliases[alias] = table

    return aliases

changed_files = []
issues = []

for py in list(ROOT.rglob("*.py")):
    path_str = str(py)
    if any(x in path_str for x in [".bak_", "__pycache__", "/scripts/", "/tests/"]):
        continue

    txt = py.read_text(errors="ignore")
    original = txt

    def fix_sql_block(match):
        quote = match.group(1)
        sql = match.group(2)
        aliases = table_aliases(sql)
        fixed = sql

        if not aliases:
            return match.group(0)

        # 1) alias.col
        for alias, table in aliases.items():
            cols_lower = tables.get(table, {})
            special = SPECIAL_TABLE_RULES.get(table, {})

            for used, correct in list(special.items()):
                if used != correct:
                    fixed = re.sub(
                        rf"\b{re.escape(alias)}\.{re.escape(used)}\b",
                        f"{alias}.{correct}",
                        fixed
                    )

            for used_lower, correct in cols_lower.items():
                # si existe misma columna con diferente case
                fixed = re.sub(
                    rf"\b{re.escape(alias)}\.{re.escape(used_lower)}\b",
                    f"{alias}.{correct}",
                    fixed
                )

        # 2) columnas sin alias en queries de una sola tabla
        real_tables = sorted(set(aliases.values()))
        if len(real_tables) == 1:
            table = real_tables[0]
            cols_lower = tables.get(table, {})
            special = SPECIAL_TABLE_RULES.get(table, {})

            for used, correct in special.items():
                if used != correct:
                    fixed = re.sub(rf"\b{re.escape(used)}\b", correct, fixed)

            for wrong, canonical in GLOBAL_CANONICAL.items():
                actual = cols_lower.get(canonical.lower())
                if actual:
                    fixed = re.sub(rf"\b{re.escape(wrong)}\b", actual, fixed)

            for used_lower, correct in cols_lower.items():
                fixed = re.sub(rf"\b{re.escape(used_lower)}\b", correct, fixed)

        if fixed != sql:
            issues.append((str(py), sql[:120].replace("\n", " "), fixed[:120].replace("\n", " ")))

        return quote + fixed + quote

    txt = SQL_BLOCK_RE.sub(fix_sql_block, txt)

    if txt != original:
        backup = py.with_suffix(py.suffix + f".bak_column_case_{STAMP}")
        shutil.copy2(py, backup)
        py.write_text(txt)
        changed_files.append(str(py))

print("\nARCHIVOS MODIFICADOS:")
for f in changed_files:
    print(f)

print("\nTOTAL ARCHIVOS MODIFICADOS:", len(changed_files))

print("\nCAMBIOS SQL DETECTADOS:", len(issues))
for i, item in enumerate(issues[:80], start=1):
    print(f"\n#{i}")
    print("archivo:", item[0])
    print("antes:", item[1])
    print("despues:", item[2])
