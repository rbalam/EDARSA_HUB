from pathlib import Path

mongo=0
legacy=0

for root in [
"/app/backend/modules",
"/app/backend/repositories",
"/app/backend/utils"
]:
    p=Path(root)
    if not p.exists():
        continue

    for f in p.rglob("*.py"):

        txt=f.read_text(errors="ignore")

        mongo += txt.count("mongodb://")
        mongo += txt.count("MongoClient(")

        legacy += txt.count("Comercial_KPIs_Diarios_v2")
        legacy += txt.count("Comercial_KPIs_Mensuales_v2")

print("MONGO_RUNTIME=",mongo)
print("KPI_LEGACY=",legacy)
