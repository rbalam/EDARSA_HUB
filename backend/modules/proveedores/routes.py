"""
EDARSA HUB - Proveedores Routes
===============================
Endpoints del portal de proveedores.

NOTA: Los endpoints actuales están en routes/portal_proveedores.py y server.py.
Este archivo se usará cuando se autorice la migración.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/proveedores", tags=["Proveedores"])

# Endpoints a migrar desde portal_proveedores.py
