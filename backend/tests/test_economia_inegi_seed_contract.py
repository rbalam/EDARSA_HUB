from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SEED = (
    ROOT
    / "database"
    / "seeds"
    / "20260807_001_economia_inegi_inpc_910406.sql"
)


def _text():
    return SEED.read_text(
        encoding="utf-8",
        errors="replace",
    )


def test_seed_inegi_es_idempotente():
    text = _text()

    assert "IF @PaisID IS NULL" in text
    assert "IF @CategoriaID IS NULL" in text
    assert "IF @ProveedorID IS NULL" in text
    assert "IF NOT EXISTS" in text


def test_seed_inegi_usa_catalogos_canonicos():
    text = _text()

    assert "dbo.Economia_Paises" in text
    assert "dbo.Economia_CategoriasIndicador" in text
    assert "dbo.Economia_Proveedores" in text
    assert "dbo.Economia_Series" in text
    assert "dbo.Proveedor_Monedas" in text
    assert "ClaveMoneda = 'MXN'" in text


def test_seed_inegi_serie_oficial_910406():
    text = _text()

    assert "910406" in text
    assert "MX.INPC.INFLACION_ANUAL" in text
    assert "MENSUAL" in text
    assert "PORCENTAJE" in text


def test_seed_inegi_auth_configurable_sin_token():
    text = _text()

    assert '"requires_auth":false' in text
    assert '"placement":"path"' not in text
    assert '"placeholder":"token"' not in text

    upper = text.upper()

    assert "API_KEY=" not in upper
    assert "TOKEN_SECRETO" not in upper
    assert "BEARER " not in upper


def test_seed_inegi_fail_closed():
    text = _text()

    assert "ServerConexionID" in text
    assert "NULL" in text

    # Proveedor y serie se crean desactivados.
    assert text.count(
        "            0\n        );"
    ) >= 2


def test_seed_inegi_normalizacion_api_oficial():
    text = _text()

    assert '"items_path":"DATASET.SERIE.Obs"' in text
    assert '"fecha_field":"@TimePeriod"' in text
    assert '"valor_field":"@CurrentValue"' in text
    assert '"fecha_format":"%Y/%m"' in text
    assert '"base_url":"https://www.inegi.org.mx"' in text
    assert '"endpoint":"servicios/xml/INPCA_M_O_H.xml"' in text
    assert '"requires_auth":false' in text
    assert '"response_format":"xml"' in text
    assert "INDICATOR/{codigo}" not in text
    assert '"params":{"type":"json"}' not in text


def test_seed_no_activa_scheduler():
    text = _text()

    assert "SCHEDULER_ECONOMIA_SYNC_ENABLED" not in text
    assert "Sys_Scheduler" not in text
