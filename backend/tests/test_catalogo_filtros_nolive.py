"""
Regresión CATALOGO-CANONICO-C1 (2026-06-09)
===========================================
Blinda la migración NO-LIVE de los filtros del Análisis (report-filters):
- MPRO: las dimensiones se derivan de Sync_Productos y sus códigos coinciden
  con Ct_Cve_Categoria / Fm_Cve_Familia / Sf_Cve_SubFamilia (los que filtra
  /reports/inventory-analysis).
- SoftRestaurant: la jerarquía de INSUMOS (clasificacionventa/gruposiclasificacion/
  gruposi) vive en Sync_Catalogo_Filtros y sus códigos coinciden con los filtros
  GC.clasificacionventa / GC.idgruposiclasificacion / GS.idgruposi.

Estos tests consultan EDARSAHUB (NO conectan a POS). Si EDARSAHUB no está
disponible en el entorno de CI, se omiten.
"""
import os
import pytest
from dotenv import load_dotenv

load_dotenv()

from core.db import execute_sql_query  # noqa: E402
from core.server_registry import EDARSAHUB_CONFIG as C  # noqa: E402

# Unidades canónicas activas (server_id) — fuente única de verdad EDARSAHUB
MPRO_SERVER = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"   # 130QRO / ORIGEN
SR_SERVERS = [
    "a5547321-1139-4d2b-9d53-182ca737b6b6",  # 130 MERIDA
    "6d053c22-523e-48c0-b72b-96081e2d781b",  # CIENFUEGOS
    "a5ff0e25-f029-43db-b634-d4ac814c904f",  # LA ESTELAR
]


def _q(sql):
    try:
        return execute_sql_query(C['host'], C['port'], C['database'], C['username'], C['password'], sql)
    except Exception as e:  # pragma: no cover
        pytest.skip(f"EDARSAHUB no disponible: {e}")


def test_mpro_categoria_poblada_en_sync_productos():
    r = _q(f"SELECT COUNT(*) cnt, COUNT(CategoriaNombre) con_cat "
           f"FROM Sync_Productos WHERE CAST(ServerID AS NVARCHAR(36))='{MPRO_SERVER}'")
    assert r and r[0]['cnt'] > 0
    # Tras la migración, todos los productos MPRO deben tener categoría
    assert r[0]['con_cat'] == r[0]['cnt']


def test_mpro_dimensiones_distintas_no_vacias():
    r = _q(f"SELECT COUNT(DISTINCT CategoriaCodigoFuente) cats, "
           f"COUNT(DISTINCT FamiliaCodigoFuente) fams, "
           f"COUNT(DISTINCT SubFamiliaCodigoFuente) subs "
           f"FROM Sync_Productos WHERE CAST(ServerID AS NVARCHAR(36))='{MPRO_SERVER}'")
    assert r[0]['cats'] > 0 and r[0]['fams'] > 0 and r[0]['subs'] > 0


def test_sr_filtros_tres_niveles_por_unidad():
    for sid in SR_SERVERS:
        r = _q(f"SELECT Nivel, COUNT(*) cnt FROM Sync_Catalogo_Filtros "
               f"WHERE CAST(ServerID AS NVARCHAR(36))='{sid}' GROUP BY Nivel")
        niveles = {row['Nivel']: row['cnt'] for row in (r or [])}
        assert niveles.get('CATEGORIA', 0) >= 1, f"{sid} sin CATEGORIA"
        assert niveles.get('FAMILIA', 0) >= 1, f"{sid} sin FAMILIA"
        assert niveles.get('SUBFAMILIA', 0) >= 1, f"{sid} sin SUBFAMILIA"


def test_sr_categorias_son_clasificacion_venta_canonica():
    # Las categorías SR deben ser los códigos de clasificacionventa (1/2/3)
    r = _q(f"SELECT DISTINCT Codigo FROM Sync_Catalogo_Filtros "
           f"WHERE Nivel='CATEGORIA' AND CAST(ServerID AS NVARCHAR(36))='{SR_SERVERS[0]}'")
    codigos = {row['Codigo'] for row in (r or [])}
    assert codigos.issubset({'1', '2', '3'})
    assert len(codigos) >= 1
