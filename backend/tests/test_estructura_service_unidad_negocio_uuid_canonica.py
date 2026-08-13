from pathlib import Path


TARGET = Path(
    "/app/backend/modules/sistema/estructura_service.py"
)


def _source():
    return TARGET.read_text(
        encoding="utf-8",
    )


def test_no_usa_unidad_negocio_id_int_de_sistema_sucursales():
    text = _source()

    assert "s.UnidadNegocioID" not in text
    assert 'suc.get("UnidadNegocioID")' not in text
    assert 'r.get("UnidadNegocioID")' not in text


def test_estructura_organizacional_resuelve_uuid_canonico():
    text = _source()

    assert "u.id AS UnidadNegocioPK" in text
    assert 'suc.get("UnidadNegocioPK")' in text
    assert "dbo.Unidades_Negocio u" in text
    assert "dbo.Sistema_SucursalServidorMapeo m" in text


def test_mapeo_servidores_publica_uuid_canonico():
    text = _source()

    assert "u.id AS UnidadNegocioPK" in text
    assert '"unidad_negocio_pk": (' in text
    assert 'str(r.get("UnidadNegocioPK"))' in text


def test_resolucion_usa_server_y_sucursal_origen():
    text = _source()

    assert "u.server_id" in text
    assert "m.ServidorID" in text
    assert "u.sucursal_origen_id" in text
    assert "m.SucursalOrigenID" in text
