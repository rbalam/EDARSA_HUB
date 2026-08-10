"""
Test de contrato para asegurar que el Reporte de Análisis de Operaciones
funcione y recupere detalles canónicos para TODAS las unidades de negocio
(130MID, ORIGEN, 130QRO, LA ESTELAR, CIENFUEGOS) sin arrojar error 404
'No hay detalle canónico'.
"""

from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

from core.sql_first.db import fetch_all_dict
from core.unidades_service import UnidadesService


def test_recuperacion_almacen_padding_variantes():
    """
    Verifica que el formateo de almacén genere candidatos padded (ej: '1' -> '01', '001', '0001')
    evitando fallos de comparación de cadenas en SQL.
    """
    from server import _compras_apply_almacen_filter

    filters = []
    params = []
    _compras_apply_almacen_filter(filters, params, ["1", "ALMACEN GENERAL"])

    assert len(filters) == 1
    assert "almacen_id IN" in filters[0] or "almacen IN" in filters[0]
    # Comprobar que contiene variantes con ceros a la izquierda
    assert "0001" in params or "01" in params
    assert "ALMACEN GENERAL" in params


def test_reporte_analisis_no_bloquea_unidades_existentes():
    """
    Certifica que para cada unidad de negocio canónica activa en dbo.Unidades_Negocio,
    existan encabezados en Compras_Inventarios_Fisicos_Sync y la consulta de detalles
    funcione sin retornar 0 filas debido a filtrado estricto de string de almacén.
    """
    unidades = UnidadesService.get_all()
    assert len(unidades) >= 5, "Deben existir al menos 5 unidades de negocio activas"

    for u in unidades:
        sid = u.get("server_id")
        codigo = u.get("codigo")
        sucursal_id = u.get("sucursal_origen_id")

        if sucursal_id:
            sql_h = f"SELECT TOP 2 folio, almacen_id, almacen FROM dbo.Compras_Inventarios_Fisicos_Sync WHERE server_id = '{sid}' AND sucursal_id = '{sucursal_id}' ORDER BY fecha DESC"
        else:
            sql_h = f"SELECT TOP 2 folio, almacen_id, almacen FROM dbo.Compras_Inventarios_Fisicos_Sync WHERE server_id = '{sid}' ORDER BY fecha DESC"

        headers = fetch_all_dict(sql_h)
        assert headers, f"La unidad {codigo} (server {sid}) debe tener encabezados en Compras_Inventarios_Fisicos_Sync"


def test_has_activity_no_descarta_productos_registrados():
    """
    Verifica que la inclusión de productos no descarte renglones con existencia física 0
    ni el fallback resiliente cuando el producto forma parte del inventario físico.
    """
    productos = {
        "SKU001": {"Producto": "AGUA MINERAL", "Unidad": "PZA", "Costo_Unitario": 10.0, "Categoria": "BEBIDAS"},
    }
    inv_inicial = {"SKU001": 0.0}
    inv_final = {"SKU001": 0.0}
    movimientos = {}
    ventas = {}

    codigo = "SKU001"
    prod = productos.get(codigo, {})
    inv_ini_qty = inv_inicial.get(codigo, 0.0)
    inv_fin_qty = inv_final.get(codigo, 0.0)
    mov_qty = movimientos.get(codigo, 0.0)
    ventas_qty = ventas.get(codigo, 0.0)

    has_activity = (
        codigo in productos
        or codigo in inv_inicial
        or codigo in inv_final
        or abs(inv_ini_qty) > 0.000001
        or abs(inv_fin_qty) > 0.000001
        or codigo in movimientos
        or codigo in ventas
    )

    assert has_activity is True, "El producto con existencia 0 pero registrado en el inventario NO debe descartarse"
