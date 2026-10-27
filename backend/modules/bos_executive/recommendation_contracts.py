# E3C_RECOMMENDATION_CONTRACT_V1

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import ConfidenceClass


class RecommendationRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
