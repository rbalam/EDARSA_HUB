"""Canonical SQL-first helpers for Comercial daily KPI drill-down.

This module is intentionally connection-agnostic. It does not open database
connections, access MongoDB, call POS systems, or contain unit-specific
mappings. Callers must supply the existing EDARSAHUB query executor.
"""

from __future__ import annotations

from dataclasses