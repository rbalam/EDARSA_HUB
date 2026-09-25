from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

REDTEAM_SCHEMA = 'edarsahub.bos-redteam-report.v1'
VALID_OUTCOMES = frozenset({'PASS', 'FAIL'})


class RedTeamError(ValueError):
    pass


@dataclass(frozen=True)
class RedTeamFinding:
    case_id: str
    category: str
    outcome: str
    expected_guard: str
    observed_guard: str

    def __post_init__(self) -> None:
        if not str(self.case_id or '').strip():
            raise RedTeamError('CASE_ID_REQUIRED')
        if not str(self.category or '').strip():
            raise RedTeamError('CATEGORY_REQUIRED')
        if self.outcome not in VALID_OUTCOMES:
            raise RedTeamError('OUTCOME_INVALID')
        if not str(self.expected_guard or '').strip():
            raise RedTeamError('EXPECTED_GUARD_REQUIRED')
        if not str(self.observed_guard or '').strip():
            raise RedTeamError('OBSERVED_GUARD_REQUIRED')


@dataclass(frozen=True)
class RedTeamReport:
    findings: tuple[RedTeamFinding, ...]
    schema: str = REDTEAM_SCHEMA

    def __post_init__(self) -> None:
        if not self.findings:
            raise RedTeamError('FINDINGS_REQUIRED')
        ids = [item.case_id for item in self.findings]
        if len(ids) != len(set(ids)):
            raise RedTeamError('DUPLICATE_CASE_ID')

    @property
    def passed(self) -> bool:
        return all(item.outcome == 'PASS' for item in self.findings)

    @property
    def failed_cases(self) -> tuple[str, ...]:
        return tuple(sorted(item.case_id for item in self.findings if item.outcome == 'FAIL'))


class RedTeamRecorder:
    def build(self, findings: Iterable[RedTeamFinding]) -> RedTeamReport:
        items = tuple(sorted(tuple(findings), key=lambda item: item.case_id))
        if not all(isinstance(item, RedTeamFinding) for item in items):
            raise RedTeamError('FINDING_TYPE_INVALID')
        return RedTeamReport(findings=items)
