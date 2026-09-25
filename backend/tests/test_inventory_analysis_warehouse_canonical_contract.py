from pathlib import Path


def test_warehouse_catalog_is_sql_first_and_unit_scoped():
    root = Path(__file__).resolve().parents[2]
    source = (root / 'backend/modules/configuracion/repositories/config_asignaciones_repository.py').read_text(encoding='utf-8')
    start = source.index('    async def listar_almacenes(self, unidad_negocio_pk: str)')
    end = source.index('    async def sincronizar_almacenes_unidad', start)
    block = source[start:end]
    assert 'dbo.Compras_Inventarios_Fisicos_Sync' in block
    assert 'dbo.Inventario_Almacenes' in block
    assert 'unidad_negocio_id = %s' in block
    assert 'Servidores_Conexiones' not in block
    assert 'servidor remoto' not in block.lower()
    assert "'EDARSAHUB_SQL'" in block
