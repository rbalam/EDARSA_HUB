"""Compatibility shim for tests that load the dispatcher outside its script directory."""

from tools.mirror_sync.worker_concurrency import evaluate_scope_advance, normalize_paths

__all__ = ["evaluate_scope_advance", "normalize_paths"]
