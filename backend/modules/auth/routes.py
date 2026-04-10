"""
EDARSA HUB - Auth Routes
========================
Endpoints de autenticación (login, registro, permisos).

NOTA: Los endpoints actuales están en server.py.
Este archivo se usará cuando se autorice la migración.

Endpoints a migrar:
- POST /api/auth/login
- POST /api/auth/register
- GET /api/auth/me
- PUT /api/users/{user_id}/permissions
"""

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Los endpoints se migrarán desde server.py en fases posteriores
# Por ahora este archivo solo define la estructura
