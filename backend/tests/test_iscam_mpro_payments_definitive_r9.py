from pathlib import Path

from core.scheduler.jobs import inteligencia_comercial_enrich as enrich

ROOT = Path(__file__).resolve().parents[2]
ENRICH = ROOT / "backend/core/scheduler/jobs/inteligencia_comercial_enrich.py"


class _TupleCursor:
    description = [("folio",), ("importe",)]

    def fetchall(self):
        return [("T-1", 125.50)]


class _FallbackConnection:
    def __init__(self):
        self.calls = []

    def cursor(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if kwargs:
            raise TypeError("pyodbc cursor no acepta as_dict")
        return _TupleCursor()


class _Context:
    unidad_codigo = "130QRO"
    unidad_negocio_pk = "pk-130qro"
    sucursal_origen_id = "0021"
    server_id = "srv-mpro"
    system_type = "MANAGEMENTPRO"

    def external_connection_config(self, *, as_dict):
        assert as_dict is True
        return {
            "host": "example.invalid",
            "port": 1433,
            "database": "CENTRAL2020",
            "username": "u",
            "password": "p",
            "as_dict": True,
        }


def test_cursor_driver_fallback_normalizes_tuple_rows():
    conn = _FallbackConnection()
    cur = enrich._cursor_as_dict(conn)
    assert enrich._fetchall_dicts(cur) == [{"folio": "T-1", "importe": 125.50}]
    assert len(conn.calls) == 2


def test_payments_resync_uses_canonical_runtime_context(monkeypatch):
    captured = {}

    def fake_resolver(unit, expected_system_types=None):
        captured["unit"] = unit
        captured["types"] = expected_system_types
        return _Context()

    def fake_extract(cfg, fi, ff):
        captured["cfg"] = cfg
        captured["period"] = (fi, ff)
        return [], [
            {
                "folio": "21-0043748",
                "codigo": "0006",
                "forma": "TARJETA",
                "importe": 3652,
                "propina": 476,
                "referencia": None,
                "fecha": "2026-08-01",
            }
        ]

    monkeypatch.setattr(enrich, "resolve_pos_runtime_context", fake_resolver)
    monkeypatch.setattr(enrich, "_extract_mpro", fake_extract)

    result = enrich.resync_pagos_unidad(
        "130QRO", "2026-08-01", "2026-09-01", dry_run=True
    )

    assert captured["unit"] == "130QRO"
    assert "MANAGEMENTPRO" in captured["types"]
    assert captured["cfg"]["sucursal_origen_id"] == "0021"
    assert captured["cfg"]["unidad_pk"] == "pk-130qro"
    assert result["sistema"] == "MPRO"
    assert result["pagos_extraidos"] == 1
    assert result["dry_run"] is True


def test_mpro_payment_join_is_document_reference():
    text = ENRICH.read_text(encoding="utf-8")
    block = text.split("def _extract_mpro", 1)[1].split(
        "# ============================================================================\n# ESCRITURA EN EDARSAHUB", 1
    )[0]
    assert "cp.Co_Folio = v.Vn_Documento" in block
