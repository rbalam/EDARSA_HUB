from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SEED = (
    ROOT
    / "database"
    / "seeds"
    / "20260807_002_economia_inegi_connection_fail_closed.sql"
)


def sql():
    return SEED.read_text(encoding="utf-8")


def test_usa_fuentes_canonicas():
    text = sql()
    assert "dbo.Servidores_Conexiones" in text
    assert "dbo.Economia_Proveedores" in text
    assert "ServerConexionID" in text


def test_no_usa_api_local():
    text = sql()
    assert "N'API_LOCAL'" not in text


def test_usa_data_source_e_inegi():
    text = sql()
    assert "N'DATA_SOURCE'" in text
    assert "N'INEGI'" in text


def test_fail_closed():
    text = " ".join(sql().split())

    assert "api_key_encrypted" in text
    assert "NULL, 0, 0, 0, 0, 0, 0" in text


def test_no_contiene_token():
    text = sql().lower()

    assert "token=" not in text
    assert "api_key=" not in text
    assert "bearer " not in text


def test_no_activa_proveedor_ni_serie():
    text = sql()

    assert "SET Activo = 1" not in text
    assert "Economia_Series" not in text


def test_idempotente():
    text = sql()

    assert "SELECT" in text
    assert "@ConexionID = ServerConexionID" in text
    assert "IF @ConexionID IS NOT NULL" in text
    assert "system_type))) = N'INEGI'" in text
    assert "IF @ConexionID IS NULL" in text


def test_guardrails_transaccionales():
    text = sql()

    assert "SET XACT_ABORT ON" in text
    assert "BEGIN TRANSACTION" in text
    assert "ROLLBACK TRANSACTION" in text
    assert "THROW 51002" in text
    assert "THROW 51003" in text
    assert "THROW 51004" in text
