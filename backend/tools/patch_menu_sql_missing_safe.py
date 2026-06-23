from core.config.edarsahub_sql import get_edarsahub_connection
from datetime import datetime

APPLY = True  # cambia a True después de revisar DRY_RUN

CANDIDATES = [
    ("SISTEMA", "sistema.centro_excepciones", "Centro de Excepciones", "Excepciones y alertas operativas", "ShieldAlert", "/admin/centro-excepciones", "centro_excepciones"),
    ("COMERCIAL", "comercial.pricing_ia", "Pricing IA", "Pricing e inteligencia de precios", "Sparkles", "/comercial/pricing-ia", "comercial.pricing_ia"),
    ("CRM", "crm.actividades", "Actividades", "Actividades CRM", "CalendarCheck", "/crm/actividades", "crm"),
    ("CRM", "crm.operaciones", "Operaciones", "Operaciones CRM", "Workflow", "/crm/operaciones", "crm"),
    ("CRM", "crm.implementaciones", "Implementaciones", "Implementaciones CRM", "Rocket", "/crm/implementaciones", "crm"),
    ("CRM", "crm.postventa", "Postventa", "Postventa CRM", "Headphones", "/crm/postventa", "crm"),
    ("CRM", "crm.kpis", "KPIs", "Indicadores CRM", "BarChart3", "/crm/kpis", "crm"),
    ("COMANDERO_RESTAURANTERO", "comandero.dashboard", "Comandero", "Dashboard comandero", "Utensils", "/comandero", "comandero"),
    ("FINANZAS", "finanzas.super_caja", "Super Caja", "Control avanzado de caja", "Wallet", "/super-caja", "finanzas"),
]

conn = get_edarsahub_connection(timeout=30)
cur = conn.cursor(as_dict=True)

backup = f"BAK_Sistema_ModulosMenus_MissingSafe_{datetime.now():%Y%m%d_%H%M%S}"
cur.execute(f"SELECT * INTO dbo.{backup} FROM dbo.Sistema_ModulosMenus")
print("BACKUP", backup)

for modulo_codigo, codigo, nombre, desc, icono, ruta, permiso in CANDIDATES:
    cur.execute("SELECT TOP 1 ModuloID FROM dbo.Sistema_Modulos WHERE Codigo=%s AND ISNULL(Activo,1)=1", (modulo_codigo,))
    mod = cur.fetchone()
    if not mod:
        print("SKIP_MODULO_NO_EXISTE", modulo_codigo, codigo)
        continue

    cur.execute("SELECT TOP 1 MenuID FROM dbo.Sistema_ModulosMenus WHERE Codigo=%s OR Ruta=%s", (codigo, ruta))
    exists = cur.fetchone()
    if exists:
        print("SKIP_EXISTE", codigo, ruta)
        continue

    cur.execute("SELECT ISNULL(MAX(Orden),0)+1 AS Orden FROM dbo.Sistema_ModulosMenus WHERE ModuloID=%s", (mod["ModuloID"],))
    orden = cur.fetchone()["Orden"]

    print("INSERT", modulo_codigo, codigo, ruta, "orden", orden)

    if APPLY:
        cur.execute("""
            INSERT INTO dbo.Sistema_ModulosMenus
            (ModuloID, MenuPadreID, Codigo, Nombre, Descripcion, Icono, Ruta, Orden, RequierePermiso, Activo, FechaCreacion)
            VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s, 1, GETDATE())
        """, (mod["ModuloID"], codigo, nombre, desc, icono, ruta, orden, permiso))

if APPLY:
    conn.commit()
    print("PATCH_APPLIED")
else:
    conn.rollback()
    print("DRY_RUN_ONLY")

conn.close()
