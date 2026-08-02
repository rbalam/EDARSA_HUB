from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path("/app")
BACKEND = ROOT / "backend"
REGISTRY_PATH = (
    ROOT
    / "frontend"
    / "src"
    / "config"
    / "enterpriseNavigationRegistry.json"
)

load_dotenv(
    BACKEND / ".env",
    override=False,
)

sys.path.insert(0, str(BACKEND))

from core.sql_first.db import get_sql_connection


registry = json.loads(
    REGISTRY_PATH.read_text(
        encoding="utf-8"
    )
)

expected_modules = {
    str(code).strip().upper()
    for code in registry["moduleMappings"]
}

expected_menus = {
    str(code).strip().lower()
    for code in registry["menuMappings"]
}

cn = get_sql_connection()
cur = cn.cursor(as_dict=True)

try:
    cur.execute(
        """
        SELECT
            DB_NAME() AS database_name,
            SUSER_SNAME() AS login_name,
            USER_NAME() AS database_user
        """
    )

    identity = cur.fetchone() or {}

    database = str(
        identity.get("database_name") or ""
    ).upper()

    login = str(
        identity.get("login_name") or ""
    ).upper()

    database_user = str(
        identity.get("database_user") or ""
    ).upper()

    assert database == "EDARSAHUB", identity
    assert login == "HRLECTURA", identity
    assert database_user == "HRLECTURA", identity

    cur.execute(
        """
        SELECT
            ModuloID,
            Codigo,
            Activo
        FROM dbo.Sistema_Modulos
        ORDER BY ModuloID
        """
    )

    modules = cur.fetchall() or []

    cur.execute(
        """
        SELECT
            MenuID,
            ModuloID,
            Codigo,
            Ruta,
            Activo
        FROM dbo.Sistema_ModulosMenus
        ORDER BY MenuID
        """
    )

    menus = cur.fetchall() or []

    sql_modules = {
        str(row.get("Codigo") or "")
        .strip()
        .upper()
        for row in modules
        if str(row.get("Codigo") or "").strip()
    }

    sql_menus = {
        str(row.get("Codigo") or "")
        .strip()
        .lower()
        for row in menus
        if str(row.get("Codigo") or "").strip()
    }

    missing_modules = sorted(
        sql_modules - expected_modules
    )

    stale_modules = sorted(
        expected_modules - sql_modules
    )

    missing_menus = sorted(
        sql_menus - expected_menus
    )

    stale_menus = sorted(
        expected_menus - sql_menus
    )

    routes = [
        str(row.get("Ruta") or "").strip()
        for row in menus
        if str(row.get("Ruta") or "").strip()
    ]

    duplicate_routes = {
        route: count
        for route, count in Counter(routes).items()
        if count > 1
    }

    cur.execute(
        """
        SELECT
            COUNT(*) AS filas,
            COUNT(DISTINCT Ruta) AS rutas
        FROM dbo.Usuario_MenuFavoritos
        """
    )

    favorites = cur.fetchone() or {}

    cur.execute(
        """
        SELECT DISTINCT
            f.Ruta
        FROM dbo.Usuario_MenuFavoritos f
        LEFT JOIN dbo.Sistema_ModulosMenus m
            ON m.Ruta = f.Ruta
        WHERE ISNULL(f.Activo, 1) = 1
          AND m.MenuID IS NULL
        """
    )

    orphan_favorites = [
        str(row.get("Ruta") or "")
        for row in (cur.fetchall() or [])
    ]

    print(
        "IDENTIDAD_SQL="
        f"{database}/{login}/{database_user}"
    )
    print(f"MODULOS_SQL={len(modules)}")
    print(f"MENUS_SQL={len(menus)}")
    print(
        "MENUS_SQL_ACTIVOS="
        f"{sum(bool(row.get('Activo')) for row in menus)}"
    )
    print(
        "MENUS_SQL_INACTIVOS="
        f"{sum(not bool(row.get('Activo')) for row in menus)}"
    )
    print(
        "FAVORITOS_FILAS="
        f"{int(favorites.get('filas') or 0)}"
    )
    print(
        "FAVORITOS_RUTAS="
        f"{int(favorites.get('rutas') or 0)}"
    )
    print(
        "FAVORITOS_HUERFANOS="
        f"{len(orphan_favorites)}"
    )

    for value in missing_modules:
        print(
            f"MODULO_SIN_CLASIFICACION={value}"
        )

    for value in stale_modules:
        print(
            f"CLASIFICACION_MODULO_SIN_SQL={value}"
        )

    for value in missing_menus:
        print(
            f"MENU_SIN_CLASIFICACION={value}"
        )

    for value in stale_menus:
        print(
            f"CLASIFICACION_MENU_SIN_SQL={value}"
        )

    for route, count in sorted(
        duplicate_routes.items()
    ):
        print(
            f"RUTA_DUPLICADA={route}:{count}"
        )

    for route in orphan_favorites:
        print(
            f"FAVORITO_HUERFANO={route}"
        )

    errors = any(
        (
            missing_modules,
            stale_modules,
            missing_menus,
            stale_menus,
            duplicate_routes,
            orphan_favorites,
        )
    )

    if errors:
        print("ENTERPRISE_SQL_GUARDIAN=FAIL")
        raise SystemExit(1)

    print("ENTERPRISE_SQL_GUARDIAN=PASS")
    print("SQL=SELECT_ONLY")
    print("SQL_DML=NO")

finally:
    try:
        cur.close()
    finally:
        cn.close()
