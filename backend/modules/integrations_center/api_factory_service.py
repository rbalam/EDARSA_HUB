"""Read-only API Factory H8 administrative service."""

from __future__ import annotations

from typing import Dict, List

from . import api_factory_repository as repository


def get_overview() -> Dict:
    return repository.get_overview()


def list_apis() -> List[Dict]:
    return repository.list_apis()


def list_versions(api_id: str) -> List[Dict]:
    return repository.list_versions(api_id)


def list_consumers() -> List[Dict]:
    return repository.list_consumers()


def list_consumer_grants(consumer_id: str) -> List[Dict]:
    return repository.list_consumer_grants(consumer_id)
