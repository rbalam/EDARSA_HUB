"""Connection-to-homologation profile binding rules.

Pure, persistence-agnostic resolver used by Integrations Center and workers.
It never certifies by vendor name alone and fails closed when evidence or
profile identity is incomplete.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Iterable, Optional

from .homologation import (
    CertificationSource,
    HomologationProfile,
    HomologationStatus,
    compatibility_status,
    empty_connection_homologation,
)


def _profile_key(profile: HomologationProfile) -> tuple[str, str]:
    return (
        str(profile.system_type or "").strip().upper(),
        str(profile.transport_type or "").strip().upper(),
    )


def candidate_profiles(
    *,
    system_type: str,
    transport_type: str,
    profiles: Iterable[HomologationProfile],
) -> list[HomologationProfile]:
    wanted = (
        str(system_type or "").strip().upper(),
        str(transport_type or "").strip().upper(),
    )
    if not all(wanted):
        return []

    return [
        profile
        for profile in profiles
        if _profile_key(profile) == wanted
    ]


def resolve_homologation_binding(
    *,
    system_type: str,
    transport_type: str,
    observed_fingerprint: Optional[str],
    profiles: Iterable[HomologationProfile],
) -> Dict[str, Any]:
    matches = candidate_profiles(
        system_type=system_type,
        transport_type=transport_type,
        profiles=profiles,
    )

    if not matches:
        value = empty_connection_homologation()
        value["status"] = HomologationStatus.PENDING.value
        return value

    certified = [
        profile
        for profile in matches
        if profile.status == HomologationStatus.CERTIFIED
    ]

    if not certified:
        # No inventar certificación si sólo existen perfiles incompletos.
        statuses = {profile.status for profile in matches}
        if HomologationStatus.BLOCKED in statuses:
            status = HomologationStatus.BLOCKED
        elif HomologationStatus.REVALIDATION_REQUIRED in statuses:
            status = HomologationStatus.REVALIDATION_REQUIRED
        elif HomologationStatus.IN_PROGRESS in statuses:
            status = HomologationStatus.IN_PROGRESS
        elif HomologationStatus.PARTIAL in statuses:
            status = HomologationStatus.PARTIAL
        else:
            status = HomologationStatus.PENDING

        value = empty_connection_homologation()
        value["status"] = status.value
        return value

    if not observed_fingerprint:
        value = empty_connection_homologation()
        value["status"] = HomologationStatus.REVALIDATION_REQUIRED.value
        return value

    exact = [
        profile
        for profile in certified
        if compatibility_status(
            profile=profile,
            observed_fingerprint=observed_fingerprint,
        ) == HomologationStatus.CERTIFIED
    ]

    if len(exact) == 1:
        profile = exact[0]
        return {
            "status": HomologationStatus.CERTIFIED.value,
            "profile_id": profile.profile_id,
            "certification_source": CertificationSource.REUSED.value,
            "schema_fingerprint": profile.schema_fingerprint,
            "source_contract_version": profile.source_contract_version,
            "edarsahub_contract_version": profile.edarsahub_contract_version,
            "last_validated_at_utc": profile.last_validated_at_utc,
            "domains": [asdict(domain) for domain in profile.domains],
        }

    # Cero exactos => el contrato observado cambió.
    # Más de uno => catálogo de perfiles ambiguo. Ambos casos fallan cerrados.
    value = empty_connection_homologation()
    value["status"] = HomologationStatus.REVALIDATION_REQUIRED.value
    value["schema_fingerprint"] = observed_fingerprint
    return value
