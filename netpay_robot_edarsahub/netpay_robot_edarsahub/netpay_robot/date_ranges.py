from __future__ import annotations

from datetime import date, timedelta
from dataclasses import dataclass


MAX_NETPAY_CUSTOM_DAYS = 31


@dataclass(frozen=True)
class DateBlock:
    number: int
    total: int
    date_from: date
    date_to: date


def split_date_range(date_from: date, date_to: date, max_days: int = MAX_NETPAY_CUSTOM_DAYS) -> list[DateBlock]:
    if date_to < date_from:
        raise ValueError('date_to no puede ser menor que date_from')
    if max_days < 1:
        raise ValueError('max_days debe ser positivo')

    raw: list[tuple[date, date]] = []
    cursor = date_from
    while cursor <= date_to:
        block_to = min(cursor + timedelta(days=max_days - 1), date_to)
        raw.append((cursor, block_to))
        cursor = block_to + timedelta(days=1)

    total = len(raw)
    return [DateBlock(i + 1, total, start, end) for i, (start, end) in enumerate(raw)]
