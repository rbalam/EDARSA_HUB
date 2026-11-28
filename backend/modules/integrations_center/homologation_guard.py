"""Operational homologation guard.

Consumers must request the domain they intend to use. A healthy connection or
a globally certified profile does not authorize consumption of a domain that
has not itself been certified.
"""

from __future__ import annotations

from typing import Any, Mapping

from .homologation import HomologationStatus


class HomologationGuardError(RuntimeError):
    pass


def domain_homologation_status(
    homologation: Mapping[str, Any] | None,
    domain: str,
) -> HomologationStatus:
    wanted = str(domain or "").strip().lower()
    if not wanted:
        raise HomologationGuardError("HOMOLOGATION_DOMAIN_REQUIRED")

    state = homologation or {}
    if str(state.get("status") or "").strip().upper() != HomologationStatus.CERTIFIED.value:
        return HomologationStatus.NOT_ASSESSED

    matches = [
        item
        for item in (state.get("domains") or [])
        if str(item.get("domain") or "").strip().lower() == wanted
    ]
    if len(matches) != 1:
        return HomologationStatus.NOT_ASSESSED

    raw = str(matches[0].get("status") or "").strip().upper()
    try:
        return HomologationStatus(raw)
    except ValueError:
        return HomologationStatus.NOT_ASSESSED


def require_certified_domain(
    homologation: Mapping[str, Any] | None,
    domain: str,
) -> None:
    status = domain_homologation_status(homologation, domain)
    if status != HomologationStatus.CERTIFIED:
        raise HomologationGuardError(
            f"HOMOLOGATION_DOMAIN_NOT_CERTIFIED:{domain}:{status.value}"
        )
