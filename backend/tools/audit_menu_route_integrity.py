from pathlib import Path
import re
import json
from datetime import datetime

from core.config.edarsahub_sql import get_edarsahub_connection

APP = Path("/app/frontend/src/App.js")
OUT_DIR = Path("/app/docs/reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def norm(route):
    if not route:
        return ""
    route = "/" + str(route).strip().strip("/")
    return "" if route == "/" else route.rstrip("/")


def frontend_routes():
    text = APP.read_text(encoding="utf-8")
    rows = []

    for m in re.finditer(r'<Route\s+path="([^"]+)"\s+element=\{<([^ />]+)', text):
        raw_ruta = m.group(1)
        ruta = norm(raw_ruta.replace("/*", ""))
        componente = m.group(2)

        if ruta in {"", "/*"}:
            continue
        if ":" in ruta:
            continue
        if componente in {
            "ProtectedRoute",
            "CatchAllRedirect",
            "Login",
            "ForgotPassword",
            "ResetPassword",
        }:
            continue

        route_type = "wildcard" if "*" in raw_ruta else "redirect" if componente == "Navigate" else "screen"
        rows.append({"ruta": ruta, "componente": componente, "route_type": route_type})

    return rows


def route_is_covered_by_frontend(sql_route, frontend_rows):
    sql_route = norm(sql_route)
    for row in frontend_rows:
        front_route = norm(row["ruta"])
        if sql_route == front_route:
            return True
        if row.get("route_type") == "wildcard" and (
            sql_route == front_route or sql_route.startswith(front_route + "/")
        ):
            return True
    return False


RBAC_COVERED_BY_PARENT = {
    "AUDITORIAS": "automatizaciones",
    "RBAC": "usuarios",
    "SEGURIDAD": "usuarios",
    "INTELIGENCIA_COMERCIAL": "inteligencia-comercial",
    "CONFIG": "config",
    "REPORTES": "reportes",
    "TAREAS": "tareas",
    "WORKFLOW": "internal_component",
    "SLA": "internal_component",
    "NOTIFICACIONES": "internal_component",
    "CARGOS": "internal_component",
    "RESPONSABILIDAD": "internal_component",
    "COMPRAS_FACT": "compras",
    "COMPRAS_COT": "compras",
    "COMPRAS_OC": "compras",
    "TES_PAGOS": "finanzas",
    "VENTA_COT": "comercial",
    "VENTA_PED": "comercial",
    "VENTA_LISTAS": "comercial",
}


def rbac_parent_prefix(codigo):
    if not codigo:
        return ""
    if "." in codigo:
        return codigo.split(".", 1)[0]
    if "_" in codigo:
        return codigo.split("_", 1)[0]
    return codigo


FRONT_ROUTE_CLASSIFICATIONS = {
    "/admin": {
        "classification": "hub_internal",
        "decision": "no_menu_sql",
        "reason": "Hub interno de administracion; no debe contarse como menu operativo independiente.",
    },
    "/admin/dashboard-ejecutivo": {
        "classification": "alias_redirect",
        "decision": "no_menu_sql",
        "reason": "Duplicado legacy de /tablero-ejecutivo, que ya existe en SQL.",
    },
    "/produccion": {
        "classification": "legacy_route",
        "decision": "no_menu_sql",
        "reason": "Ruta contenedora legacy de produccion; no insertar sin validar menu funcional activo.",
    },
    "/produccion/tablajeria": {
        "classification": "legacy_route",
        "decision": "no_menu_sql",
        "reason": "Alias legacy de TablajeriaDashboard; evitar duplicar menu.",
    },
    "/produccion/tablajeria/plantillas": {
        "classification": "legacy_route",
        "decision": "no_menu_sql",
        "reason": "Ruta legacy de plantillas de tablajeria; evitar duplicar menu.",
    },
    "/produccion/tablajeria/ordenes": {
        "classification": "legacy_route",
        "decision": "no_menu_sql",
        "reason": "Ruta legacy de ordenes de tablajeria; evitar duplicar menu.",
    },
    "/produccion/tablajeria/captura-directa": {
        "classification": "legacy_route",
        "decision": "no_menu_sql",
        "reason": "Ruta legacy de captura directa de tablajeria; evitar duplicar menu.",
    },
    "/tablajeria": {
        "classification": "alias_redirect",
        "decision": "no_menu_sql",
        "reason": "Alias de /tablajeria/dashboard; no debe crear menu duplicado.",
    },
    "/cava-socios/socios/nuevo": {
        "classification": "internal_form",
        "decision": "no_menu_sql",
        "reason": "Formulario interno de alta; debe abrir desde el flujo de socios, no como menu.",
    },
    "/admin/dba-credential": {
        "classification": "sensitive_superadmin",
        "decision": "no_menu_sql",
        "reason": "Herramienta sensible restringida a SuperAdministrador; no debe exponerse como menu general.",
    },
}


def classify_front_missing(row):
    meta = FRONT_ROUTE_CLASSIFICATIONS.get(row["ruta"])
    if meta:
        return {**row, **meta}
    return {
        **row,
        "classification": "real_missing_menu",
        "decision": "review_insert_menu",
        "reason": "Ruta frontend sin menu SQL y sin clasificacion tecnica.",
    }


def sql_menus(cur):
    cur.execute("""
        SELECT
            sm.ModuloID,
            sm.Codigo AS ModuloCodigo,
            sm.Nombre AS ModuloNombre,
            mm.MenuID,
            mm.Codigo AS MenuCodigo,
            mm.Nombre AS MenuNombre,
            mm.Ruta,
            mm.Orden,
            mm.RequierePermiso
        FROM dbo.Sistema_ModulosMenus mm
        INNER JOIN dbo.Sistema_Modulos sm ON sm.ModuloID = mm.ModuloID
        WHERE ISNULL(mm.Activo,1)=1
          AND mm.Ruta IS NOT NULL
        ORDER BY sm.Orden, mm.Orden, mm.Nombre
    """)
    return cur.fetchall() or []


def rbac_modules_without_menu(cur):
    cur.execute("""
        SELECT DISTINCT
            m.ModuloID,
            m.CodigoModulo,
            m.NombreModulo
        FROM dbo.Usuario_Modulos m
        INNER JOIN dbo.Usuario_PermisosRolModulo prm ON prm.ModuloID = m.ModuloID
        WHERE ISNULL(m.Activo,1)=1
          AND ISNULL(prm.Activo,1)=1
          AND ISNULL(prm.Permitido,0)=1
        ORDER BY m.NombreModulo
    """)
    modules = cur.fetchall() or []

    cur.execute("""
        SELECT
            sm.Codigo AS ModuloCodigo,
            mm.Codigo AS MenuCodigo,
            mm.Ruta,
            mm.RequierePermiso
        FROM dbo.Sistema_ModulosMenus mm
        INNER JOIN dbo.Sistema_Modulos sm ON sm.ModuloID = mm.ModuloID
        WHERE ISNULL(mm.Activo,1)=1
    """)
    menus = cur.fetchall() or []

    uncovered = []
    for module in modules:
        codigo = module.get("CodigoModulo") or ""
        codigo_l = codigo.lower()
        parent_l = rbac_parent_prefix(codigo).lower()
        known_cover = RBAC_COVERED_BY_PARENT.get(codigo)
        covered = False

        if known_cover:
            known_l = known_cover.lower()
            covered = any(
                known_l == "internal_component"
                or known_l in str(menu.get("MenuCodigo") or "").lower()
                or known_l in str(menu.get("Ruta") or "").lower()
                or known_l in str(menu.get("RequierePermiso") or "").lower()
                for menu in menus
            )

        if not covered:
            for menu in menus:
                menu_codigo = str(menu.get("MenuCodigo") or "").lower()
                permiso = str(menu.get("RequierePermiso") or "").lower()
                ruta = str(menu.get("Ruta") or "").lower()
                modulo = str(menu.get("ModuloCodigo") or "").lower()

                if codigo_l in {menu_codigo, permiso, modulo}:
                    covered = True
                    break

                if "." in codigo_l and (
                    menu_codigo.startswith(parent_l + ".")
                    or permiso == parent_l
                    or parent_l in ruta
                    or modulo == parent_l
                ):
                    covered = True
                    break

                if "_" in codigo_l and (
                    permiso == parent_l
                    or parent_l in ruta
                    or parent_l in menu_codigo
                ):
                    covered = True
                    break

        if not covered:
            uncovered.append(module)

    return uncovered


def main():
    conn = get_edarsahub_connection(timeout=30)
    cur = conn.cursor(as_dict=True)

    front = frontend_routes()
    menus = sql_menus(cur)
    rbac_sin_menu = rbac_modules_without_menu(cur)

    front_routes_set = {r["ruta"] for r in front}
    sql_routes_set = {norm(r["Ruta"]) for r in menus if r.get("Ruta")}

    front_sin_sql_raw = [
        r for r in front
        if r.get("route_type") == "screen"
        and r["ruta"] not in sql_routes_set
    ]
    front_sin_sql_classified = [classify_front_missing(r) for r in front_sin_sql_raw]
    front_sin_sql = [
        r for r in front_sin_sql_classified
        if r["classification"] == "real_missing_menu"
    ]
    front_sin_sql_no_accionable = [
        r for r in front_sin_sql_classified
        if r["classification"] != "real_missing_menu"
    ]
    sql_sin_front = [
        r for r in menus
        if not route_is_covered_by_frontend(r.get("Ruta"), front)
    ]

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"MENU_ROUTE_INTEGRITY_{stamp}.json"
    md_path = OUT_DIR / f"MENU_ROUTE_INTEGRITY_{stamp}.md"

    payload = {
        "generated_at": stamp,
        "frontend_routes_count": len(front),
        "sql_menus_count": len(menus),
        "frontend_without_sql_menu_actionable": front_sin_sql,
        "frontend_without_sql_menu_classified": front_sin_sql_classified,
        "frontend_without_sql_menu_no_actionable": front_sin_sql_no_accionable,
        "sql_menu_without_frontend_route": sql_sin_front,
        "rbac_modules_without_sql_menu": rbac_sin_menu,
    }

    json_path.write_text(json.dumps(payload, default=str, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# Auditoría de Integridad Menú ↔ Route ↔ RBAC\n")
    md.append(f"Generado: `{stamp}`\n")
    md.append(f"- Rutas frontend auditadas: **{len(front)}**")
    md.append(f"- Menús SQL activos auditados: **{len(menus)}**")
    md.append(f"- Rutas frontend sin menú SQL bruto: **{len(front_sin_sql_raw)}**")
    md.append(f"- Rutas frontend sin menú SQL accionables: **{len(front_sin_sql)}**")
    md.append(f"- Rutas frontend técnicas/alias/formularios/sensibles: **{len(front_sin_sql_no_accionable)}**")
    md.append(f"- Menús SQL sin route frontend: **{len(sql_sin_front)}**")
    md.append(f"- Módulos RBAC con permisos pero sin menú SQL: **{len(rbac_sin_menu)}**\n")

    md.append("## Rutas frontend sin menú SQL accionables\n")
    if not front_sin_sql:
        md.append("- Sin pendientes accionables.")
    for r in front_sin_sql:
        md.append(f"- `{r['ruta']}` → `{r['componente']}` / `{r['classification']}` / `{r['decision']}` / {r['reason']}")

    md.append("\n## Rutas frontend sin menú SQL clasificadas como no accionables\n")
    if not front_sin_sql_no_accionable:
        md.append("- Sin rutas no accionables.")
    for r in front_sin_sql_no_accionable:
        md.append(f"- `{r['ruta']}` → `{r['componente']}` / `{r['classification']}` / `{r['decision']}` / {r['reason']}")

    md.append("\n## Menús SQL sin route frontend\n")
    for r in sql_sin_front:
        md.append(f"- `{r['Ruta']}` → `{r['MenuCodigo']}` / `{r['MenuNombre']}`")

    md.append("\n## Módulos RBAC con permisos pero sin menú SQL\n")
    for r in rbac_sin_menu:
        md.append(f"- `{r['CodigoModulo']}` → `{r['NombreModulo']}`")

    md_path.write_text("\n".join(md), encoding="utf-8")

    print("AUDIT_OK")
    print("JSON:", json_path)
    print("MD:", md_path)
    print("FRONT_WITHOUT_SQL_RAW:", len(front_sin_sql_raw))
    print("FRONT_WITHOUT_SQL_ACTIONABLE:", len(front_sin_sql))
    print("FRONT_WITHOUT_SQL_NO_ACTIONABLE:", len(front_sin_sql_no_accionable))
    print("SQL_WITHOUT_FRONT:", len(sql_sin_front))
    print("RBAC_WITHOUT_MENU:", len(rbac_sin_menu))

    conn.close()


if __name__ == "__main__":
    main()
