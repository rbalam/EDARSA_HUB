from core.config.edarsahub_sql import get_edarsahub_connection
from pathlib import Path
from datetime import datetime

OUT = Path("/app/docs/reports")
OUT.mkdir(parents=True, exist_ok=True)

FRONT_MISSING_SQL = [
    ("/admin/centro-excepciones","CentroExcepciones"),
    ("/admin/dashboard-ejecutivo","DashboardEjecutivo"),
    ("/comercial/pricing-ia","PricingIA"),
    ("/crm/actividades","ActividadesPage"),
    ("/crm/operaciones","OperacionesPage"),
    ("/crm/implementaciones","ImplementacionesPage"),
    ("/crm/postventa","PostventaPage"),
    ("/crm/kpis","KPIsPage"),
    ("/proveedores","Proveedores"),
    ("/super-caja","SuperCajaPage"),
    ("/comandero","ComanderoPage"),
]

conn = get_edarsahub_connection(timeout=30)
cur = conn.cursor(as_dict=True)

lines = []
lines.append("# PROPUESTA MENU SQL")
lines.append("")

for ruta, componente in FRONT_MISSING_SQL:
    cur.execute("""
        SELECT TOP 20
            ModuloID,
            Codigo,
            Nombre
        FROM dbo.Sistema_Modulos
        WHERE Activo = 1
        ORDER BY Nombre
    """)
    mods = cur.fetchall()

    lines.append(f"## {ruta}")
    lines.append(f"Frontend: {componente}")
    lines.append("Posibles módulos:")
    for m in mods[:10]:
        lines.append(
            f"- {m['ModuloID']} | {m['Codigo']} | {m['Nombre']}"
        )
    lines.append("")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report = OUT / f"MENU_SQL_RECOMMENDATIONS_{stamp}.md"
report.write_text("\n".join(lines), encoding="utf-8")

print(report)

conn.close()
