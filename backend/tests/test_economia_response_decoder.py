import pytest

from modules.economia.response_decoder import (
    SUPPORTED_RESPONSE_FORMATS,
    decode_http_response,
    decode_xml_text,
)


def test_formatos_soportados_son_explicitos():
    assert SUPPORTED_RESPONSE_FORMATS == frozenset(
        {"json", "xml"}
    )


def test_decode_json_delega_response_json():
    class Response:
        text = '{"ignorar": true}'

        def json(self):
            return {
                "items": [
                    {"fecha": "2026-07-01", "valor": "10.5"}
                ]
            }

    result = decode_http_response(Response(), "json")

    assert result == {
        "items": [
            {"fecha": "2026-07-01", "valor": "10.5"}
        ]
    }


def test_decode_xml_convierte_hijos_repetidos_a_lista():
    xml = """
    <response>
        <items>
            <item>
                <fecha>2026-07-01</fecha>
                <valor>10.5</valor>
            </item>
            <item>
                <fecha>2026-08-01</fecha>
                <valor>11.2</valor>
            </item>
        </items>
    </response>
    """

    result = decode_xml_text(xml)

    assert result == {
        "response": {
            "items": {
                "item": [
                    {
                        "fecha": "2026-07-01",
                        "valor": "10.5",
                    },
                    {
                        "fecha": "2026-08-01",
                        "valor": "11.2",
                    },
                ]
            }
        }
    }


def test_decode_xml_soporta_atributos():
    result = decode_xml_text(
        '<dato id="ABC" preliminar="true">123.45</dato>'
    )

    assert result == {
        "dato": {
            "@id": "ABC",
            "@preliminar": "true",
            "#text": "123.45",
        }
    }


def test_decode_xml_elimina_namespace_del_tag():
    result = decode_xml_text(
        """
        <ns:response xmlns:ns="urn:test">
            <ns:valor>123</ns:valor>
        </ns:response>
        """
    )

    assert result == {
        "response": {
            "valor": "123",
        }
    }


def test_decode_xml_rechaza_vacio():
    with pytest.raises(
        ValueError,
        match="XML vacía",
    ):
        decode_xml_text("")


def test_decode_xml_rechaza_xml_invalido():
    with pytest.raises(
        ValueError,
        match="XML inválida",
    ):
        decode_xml_text("<response>")


def test_decode_http_rechaza_formato_no_soportado():
    class Response:
        text = ""

        def json(self):
            return {}

    with pytest.raises(
        ValueError,
        match="response_format no soportado",
    ):
        decode_http_response(
            Response(),
            "csv",
        )


def test_decoder_no_contiene_logica_inegi():
    from pathlib import Path
    import modules.economia.response_decoder as decoder

    text = Path(decoder.__file__).read_text(
        encoding="utf-8"
    ).lower()

    assert "inegi" not in text
    assert "910406" not in text
    assert "www.inegi" not in text


def test_decoder_no_hace_http_ni_sql():
    from pathlib import Path
    import modules.economia.response_decoder as decoder

    text = Path(decoder.__file__).read_text(
        encoding="utf-8"
    ).lower()

    forbidden = (
        "httpx.",
        "requests.",
        "select ",
        "insert ",
        "update ",
        "delete ",
        "commit(",
    )

    for token in forbidden:
        assert token not in text


def test_decode_xml_payload_soporta_utf8_bom():
    from modules.economia.response_decoder import (
        decode_xml_payload,
    )

    payload = (
        b"\xef\xbb\xbf"
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b"<DATASET>"
        b"<METADATA>"
        b"<Nemonic>INPCA_M_O</Nemonic>"
        b"</METADATA>"
        b"</DATASET>"
    )

    result = decode_xml_payload(payload)

    assert result == {
        "DATASET": {
            "METADATA": {
                "Nemonic": "INPCA_M_O"
            }
        }
    }


def test_decode_http_xml_usa_content_bytes():
    from modules.economia.response_decoder import (
        decode_http_response,
    )

    class Response:
        content = (
            b"\xef\xbb\xbf"
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b"<DATASET><SERIE><Obs>1</Obs></SERIE></DATASET>"
        )

        @property
        def text(self):
            raise AssertionError(
                "XML no debe depender de response.text"
            )

        def json(self):
            raise AssertionError(
                "XML no debe llamar response.json()"
            )

    result = decode_http_response(
        Response(),
        "xml",
    )

    assert result == {
        "DATASET": {
            "SERIE": {
                "Obs": "1"
            }
        }
    }
