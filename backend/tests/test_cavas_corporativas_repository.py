from datetime import time

from modules.cavas_corporativas.repository import _policy_from_json


def test_policy_json_maps_to_domain_without_hardcoded_hours():
    policy = _policy_from_json([
        '{"allowed_weekdays":[0,1,2],"start_time":"15:30:00","end_time":"21:45:00","requires_reservation":true,"max_guests":12}'
    ])
    assert policy.allowed_weekdays == frozenset({0, 1, 2})
    assert policy.start_time == time(15, 30)
    assert policy.end_time == time(21, 45)
    assert policy.requires_reservation is True
    assert policy.max_guests == 12


def test_policy_layers_can_override_previous_values():
    policy = _policy_from_json([
        '{"requires_reservation":false,"max_guests":20}',
        '{"requires_reservation":true,"max_guests":8}'
    ])
    assert policy.requires_reservation is True
    assert policy.max_guests == 8
