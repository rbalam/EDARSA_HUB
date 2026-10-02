from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "backend" / "database" / "migrations" / "20260918_001_arbitroa_a4_foundation.sql"
MODULE = ROOT / "backend" / "modules" / "arbitroa" / "__init__.py"

A4_TABLES = {
    "ARBITROA_Deportes",
    "ARBITROA_Organizaciones",
    "ARBITROA_Afiliaciones",
    "ARBITROA_OrganizacionPersonas",
    "ARBITROA_Sedes",
    "ARBITROA_Canchas",
    "ARBITROA_Reglamentos",
}

FORBIDDEN_LATER = {
    "ARBITROA_Temporadas",
    "ARBITROA_Torneos",
    "ARBITROA_Equipos",
    "ARBITROA_Jornadas",
    "ARBITROA_Partidos",
    "ARBITROA_PerfilesArbitrales",
    "ARBITROA_Designaciones",
    "ARBITROA_Cedulas",
    "ARBITROA_Incidencias",
    "ARBITROA_TiposEventoDeportivo",
    "ARBITROA_TarifasArbitrales",
    "ARBITROA_GeoSesiones",
    "ARBITROA_SafeChecklists",
}

def sql():
    return MIGRATION.read_text(encoding="utf-8")

def test_a4_exactly_seven_domain_tables():
    text = sql()
    created = set(re.findall(r"CREATE TABLE dbo\.(ARBITROA_[A-Za-z0-9_]+)", text))
    assert created == A4_TABLES

def test_no_later_gate_tables_are_created():
    text = sql()
    for name in FORBIDDEN_LATER:
        assert f"CREATE TABLE dbo.{name}" not in text

def test_sql_first_and_transactional_contract():
    text = sql()
    for token in (
        "SET XACT_ABORT ON",
        "BEGIN TRANSACTION",
        "COMMIT TRANSACTION",
        "ROLLBACK TRANSACTION",
        "dbo.Gobierno_Persona",
        "dbo.Gobierno_Documento",
        "dbo.Usuario_Catalogo",
    ):
        assert token in text

def test_rbac_menu_is_canonical_and_satellite():
    text = sql()
    for token in (
        "dbo.Sistema_Modulos",
        "dbo.Sistema_ModulosMenus",
        "dbo.Sistema_ModulosPermisos",
        "N'ARBITROA'",
        "N'arbitroa.ver'",
        "N'arbitroa.administrar'",
        "N'/arbitroa'",
        "EsSatelite",
    ):
        assert token in text
    assert "ARBITROA_Usuarios" not in text
    assert "ARBITROA_Personas" not in text
    assert "Mongo" not in text

def test_seeds_resolve_by_code_not_ids():
    text = sql()
    for code in ("FUTBOL", "FUTBOL7", "FUTBOL_RAPIDO", "BASQUETBOL", "VOLEIBOL", "BEISBOL"):
        assert code in text
    assert "IDENTITY_INSERT" not in text

def test_backend_namespace_is_bounded_context():
    assert MODULE.is_file()
    source = MODULE.read_text(encoding="utf-8")
    assert "ARBITROA" in source
