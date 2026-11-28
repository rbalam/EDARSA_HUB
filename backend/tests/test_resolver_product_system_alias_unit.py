from core.inventarios import resolver_canonico as rc


def _prepare(monkeypatch, server_id):
    rc.clear_resolver_caches()
    monkeypatch.setattr(
        rc,
        "_server_id_de_unidad",
        lambda unidad_codigo: server_id,
    )
    monkeypatch.setattr(
        rc,
        "_tabla_existe",
        lambda table_name: True,
    )


def test_product_resolver_normalizes_mpro_system_aliases(monkeypatch):
    for alias in ("MPRO", "ManagementPro", "ManagmentPro", "MANAGEMENT PRO"):
        _prepare(monkeypatch, "server-mpro")

        def fake_fetchall(sql, params=(), as_dict=False):
            if "CodigoFuente, ProductoID" in sql:
                assert params[1] == "MPRO"
                return [("P001", 123)]
            if "SELECT TOP 1 ProductoID" in sql:
                assert params[1] == "MPRO"
                return [(123,)]
            return []

        monkeypatch.setattr(rc, "_fetchall", fake_fetchall)

        assert rc.precargar_productos_mapeo("130QRO", alias) == 1
        result = rc.resolver_producto_id("130QRO", alias, "P001")
        assert result.resuelto is True
        assert result.canonical_id == 123


def test_product_resolver_normalizes_softrestaurant_aliases(monkeypatch):
    _prepare(monkeypatch, "server-soft")

    def fake_fetchall(sql, params=(), as_dict=False):
        if "CodigoFuente, ProductoID" in sql:
            assert params[1] == "SOFTRESTAURANT_PRO"
            return [("A100001", 456)]
        if "SELECT TOP 1 ProductoID" in sql:
            assert params[1] == "SOFTRESTAURANT_PRO"
            return [(456,)]
        return []

    monkeypatch.setattr(rc, "_fetchall", fake_fetchall)

    assert rc.precargar_productos_mapeo("CIENFUEGOS", "SoftRestaurant") == 1
    result = rc.resolver_producto_id(
        "CIENFUEGOS",
        "SOFTRESTAURANT",
        "A100001",
    )
    assert result.resuelto is True
    assert result.canonical_id == 456
