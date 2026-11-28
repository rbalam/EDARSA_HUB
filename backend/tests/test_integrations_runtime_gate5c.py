from modules.integrations_runtime.sync_ledger import _idempotency_key, _valid_uuid


def test_gate5c_idempotency_key_is_deterministic_and_bounded():
    a = _idempotency_key('COMPRAS_SYNC', 'run-1')
    b = _idempotency_key('COMPRAS_SYNC', 'run-1')
    assert a == b == 'COMPRAS_SYNC:run-1'
    assert len(_idempotency_key('X' * 150, 'Y' * 150)) <= 200


def test_gate5c_uuid_parser_fail_closed():
    assert _valid_uuid('not-a-uuid') is None
    assert _valid_uuid(None) is None
    assert _valid_uuid('11111111-1111-1111-1111-111111111111') == '11111111-1111-1111-1111-111111111111'


def test_gate5c_health_module_has_no_parallel_table_contract():
    from modules.integrations_runtime import health
    source = open(health.__file__, encoding='utf-8').read()
    assert 'Servidores_ConexionEstado' in source
    assert 'CREATE TABLE' not in source.upper()
    assert 'DROP TABLE' not in source.upper()
