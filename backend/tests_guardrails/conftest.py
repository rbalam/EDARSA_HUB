"""Conftest para guardrails que importan módulos de la app.

Carga el .env del backend en os.environ y asegura /app/backend en sys.path,
para que los tests que hacen `import modules.*` / `import core.*` (los cuales
requieren EDARSAHUB_SQL_* al cargar config) funcionen bajo pytest desde bash/CI.
"""
import sys
from pathlib import Path

from dotenv import load_dotenv

_BACK = Path(__file__).resolve().parents[1]  # /app/backend

_ENV = _BACK / ".env"
if _ENV.exists():
    load_dotenv(_ENV, override=False)

_back_str = str(_BACK)
if _back_str not in sys.path:
    sys.path.insert(0, _back_str)
