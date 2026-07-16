#!/usr/bin/env python3
"""Ejecutor controlado para la auditoria read-only de Cortes Z en Preview/Development.

Usa la excepcion temporal autorizada para cargar /app/backend/.env mediante
python-dotenv. No imprime valores de entorno, no permite Produccion y exige
la identidad canonica HRLectura antes de delegar al runner SQL.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path("/app")
BACKEND = ROOT / "backend"
ENV_FILE = BACKEND / ".env"
SQL_FILE = (
    BACKEND
    / "