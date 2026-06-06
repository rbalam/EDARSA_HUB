"""
Regresión Capa 2 / forgot-password (FASE AUTH-V2-ALIGN)
=======================================================
FreeTDS (tds_version 7.0) devuelve columnas DATETIME2 de SQL Server como string
(ej. '2026-06-06 00:22:04.2100000', con 7 decimales). El código asumía objetos
datetime y truenaba con:
  - check_rate_limit_sql: str.replace(tzinfo=...) -> TypeError
  - RBAC get_roles_usuario: str.isoformat() -> AttributeError

Este test valida el helper de coerción puntual sin tocar la conexión SQL.
"""
from datetime import datetime, timezone

from modules.auth.password_reset import _coerce_aware_dt


def test_coerce_none_returns_none():
    assert _coerce_aware_dt(None) is None


def test_coerce_datetime2_string_7_fraction_digits():
    # Formato real devuelto por FreeTDS para DATETIME2(7)
    dt = _coerce_aware_dt('2026-06-06 00:22:04.2100000')
    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None
    assert (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) == (2026, 6, 6, 0, 22, 4)


def test_coerce_string_without_fraction():
    dt = _coerce_aware_dt('2026-06-06 00:22:04')
    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None


def test_coerce_naive_datetime_gets_utc():
    naive = datetime(2026, 6, 6, 12, 0, 0)
    dt = _coerce_aware_dt(naive)
    assert dt.tzinfo == timezone.utc


def test_coerce_aware_datetime_passthrough():
    aware = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    dt = _coerce_aware_dt(aware)
    assert dt == aware


def test_comparison_does_not_raise():
    """El bug original: comparar string > datetime.now(). Ahora debe ser seguro."""
    now = datetime.now(timezone.utc)
    ventana = _coerce_aware_dt('2099-01-01 00:00:00.0000000')
    assert ventana > now  # no TypeError
