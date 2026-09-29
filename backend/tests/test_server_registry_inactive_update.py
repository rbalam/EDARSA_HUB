import asyncio

from core import server_registry


def test_update_server_can_resolve_inactive_record_without_activating_it(monkeypatch):
    seen = {}

    def fake_get(server_id, include_inactive=False):
        seen['server_id'] = server_id
        seen['include_inactive'] = include_inactive
        return {'tipo_conexion': 'DATA_SOURCE'}

    def fake_validate(payload, mode):
        assert mode == 'update'
        return dict(payload)

    captured = {}

    def fake_write(query, values):
        captured['query'] = query
        captured['values'] = values
        return True

    monkeypatch.setattr(server_registry, '_get_server_by_id_from_sql', fake_get)
    monkeypatch.setattr(server_registry, 'validate_server_payload', fake_validate)
    monkeypatch.setattr(server_registry, '_execute_sql_write', fake_write)

    result = asyncio.run(
        server_registry.update_server(
            'inactive-server-id',
            {'database_name': 'cavas_www'},
        )
    )

    assert result['success'] is True
    assert seen == {
        'server_id': 'inactive-server-id',
        'include_inactive': True,
    }
    assert 'database_name = %s' in captured['query']
    assert 'activo' not in captured['query'].lower()
    assert captured['values'][0] == 'cavas_www'
