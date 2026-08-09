from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MIGRATION = (
    ROOT
    / "database"
    / "migrations"
    / "20260808_001_economia_inegi_xml_metadata.sql"
)


def _text():
    return MIGRATION.read_text(encoding="utf-8")


def test_migration_exists():
    assert MIGRATION.is_file()


def test_target_is_canonical_not_identity_hardcode():
    text = _text()

    assert "MX.INPC.INFLACION_ANUAL" in text
    assert "p.Codigo = @ProveedorCodigo" in text

    assert "WHERE SerieEconomicaID = 5" not in text
    assert "SerieEconomicaID = 5" not in text


def test_migration_requires_fail_closed_chain():
    text = _text()

    assert "Serie INEGI debe permanecer inactiva" in text
    assert "Proveedor INEGI debe permanecer inactivo" in text
    assert "Conexion INEGI debe permanecer inactiva" in text


def test_migration_requires_zero_existing_values():
    text = _text()

    assert "FROM dbo.Economia_Valores" in text
    assert (
        "Serie INEGI ya contiene valores; requiere nueva auditoria"
        in text
    )


def test_migration_requires_exact_old_contract():
    text = _text()

    assert (
        "INDICATOR/{codigo}/es/00/false/BISE/2.0/{token}"
        in text
    )
    assert "Series.0.OBSERVATIONS" in text
    assert "TIME_PERIOD" in text
    assert "OBS_VALUE" in text
    assert "OBS_SOURCE" in text


def test_migration_writes_real_xml_contract():
    text = _text()

    assert '"base_url":"https://www.inegi.org.mx"' in text
    assert '"endpoint":"servicios/xml/INPCA_M_O_H.xml"' in text
    assert '"requires_auth":false' in text
    assert '"response_format":"xml"' in text
    assert '"items_path":"DATASET.SERIE.Obs"' in text
    assert '"fecha_field":"@TimePeriod"' in text
    assert '"valor_field":"@CurrentValue"' in text


def test_migration_only_updates_series_metadata():
    text = _text()

    assert "UPDATE dbo.Economia_Series" in text

    forbidden = (
        "UPDATE dbo.Economia_Proveedores",
        "UPDATE dbo.Servidores_Conexiones",
        "INSERT INTO dbo.Economia_Valores",
        "UPDATE dbo.Economia_Valores",
        "DELETE FROM dbo.Economia_Valores",
    )

    for token in forbidden:
        assert token not in text


def test_migration_is_transactional_and_idempotent():
    text = _text()

    assert "SET XACT_ABORT ON" in text
    assert "BEGIN TRANSACTION" in text
    assert "COMMIT TRANSACTION" in text
    assert "ROLLBACK TRANSACTION" in text

    assert "si ya esta migrada" in text.lower()
    assert "RETURN;" in text


def test_migration_validates_single_row_update():
    text = _text()

    assert "@@ROWCOUNT <> 1" in text
    assert "UPDATE no afecto exactamente una serie" in text
