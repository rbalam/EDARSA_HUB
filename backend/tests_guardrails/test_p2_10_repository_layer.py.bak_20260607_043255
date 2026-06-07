from pathlib import Path
import sys

targets = [
"modules/comercial/service.py",
"modules/comercial/routes.py",
"modules/comercial_v2/repository_readonly.py",
"modules/comercial_v2/repository_comercial_edarsahub.py",
"modules/comercial_v2/routes.py",
"modules/finanzas/repository_softrestaurant.py",
"modules/finanzas/cuentas_por_pagar.py",
"modules/dashboard_ejecutivo/routes.py",
"modules/inteligencia_comercial/routes.py",
"core/server_registry.py",
"core/auth/user_repository_sql.py",
]

bad = []

for f in targets:
    p = Path(f)
    if not p.exists():
        continue
    txt = p.read_text(errors="ignore")

    if "mongodb://" in txt or "MONGO_URL" in txt or "import pymongo" in txt:
        bad.append((f, "Mongo runtime directo"))

    if "Comercial_KPIs_Diarios_v2" in txt and "vw_Comercial_KPIs_Diarios_v2_Runtime" not in txt:
        bad.append((f, "KPI diario legacy"))

    if "Comercial_KPIs_Mensuales_v2" in txt and "vw_Comercial_KPIs_Mensuales_v2_Runtime" not in txt:
        bad.append((f, "KPI mensual legacy"))

if bad:
    print("FAIL")
    for b in bad:
        print(b)
    sys.exit(1)

print("PASS")
