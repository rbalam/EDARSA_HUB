"""
CENTRO DE CONTROL EDARSA - Gestión de Destinatarios de Alertas
===============================================================
Almacena y gestiona los destinatarios de notificaciones en MongoDB.

Colección: alert_recipients
Estructura:
{
    "_id": ObjectId,
    "tipo": "email" | "whatsapp",
    "destinatario": "email@example.com" | "+521234567890",
    "nombre": "Nombre opcional",
    "activo": true,
    "created_at": datetime,
    "created_by": "user_email"
}
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = None  # P2-07: MongoDB eliminado
DB_NAME = os.environ.get('DB_NAME', 'edarsa_hub')

_db = None


def get_db():
    """Obtiene la conexión a la base de datos"""
    global _db
    if _db is None:
        client = None  # P2-07: MongoDB eliminado
        _db = client[DB_NAME]
    return _db


def get_collection():
    """Obtiene la colección de destinatarios"""
    db = get_db()
    return db['alert_recipients']


# ============================================================================
# CRUD OPERATIONS
# ============================================================================

def get_all_recipients(tipo: Optional[str] = None, solo_activos: bool = True) -> List[Dict[str, Any]]:
    """
    Obtiene todos los destinatarios de alertas.
    
    Args:
        tipo: Filtrar por tipo ("email" o "whatsapp")
        solo_activos: Si True, solo retorna destinatarios activos
        
    Returns:
        Lista de destinatarios
    """
    collection = get_collection()
    
    query = {}
    if tipo:
        query["tipo"] = tipo
    if solo_activos:
        query["activo"] = True
    
    recipients = []
    for doc in collection.find(query).sort("created_at", -1):
        recipients.append({
            "id": str(doc["_id"]),
            "tipo": doc.get("tipo"),
            "destinatario": doc.get("destinatario"),
            "nombre": doc.get("nombre"),
            "activo": doc.get("activo", True),
            "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
            "created_by": doc.get("created_by")
        })
    
    return recipients


def get_email_recipients() -> List[str]:
    """Obtiene lista de emails activos para alertas"""
    recipients = get_all_recipients(tipo="email", solo_activos=True)
    return [r["destinatario"] for r in recipients if r.get("destinatario")]


def get_whatsapp_recipients() -> List[str]:
    """Obtiene lista de números WhatsApp activos para alertas"""
    recipients = get_all_recipients(tipo="whatsapp", solo_activos=True)
    return [r["destinatario"] for r in recipients if r.get("destinatario")]


def add_recipient(
    tipo: str,
    destinatario: str,
    nombre: Optional[str] = None,
    created_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Agrega un nuevo destinatario de alertas.
    
    Args:
        tipo: "email" o "whatsapp"
        destinatario: Email o número de teléfono
        nombre: Nombre opcional del destinatario
        created_by: Email del usuario que crea
        
    Returns:
        Dict con el destinatario creado
    """
    collection = get_collection()
    
    # Validar tipo
    if tipo not in ["email", "whatsapp"]:
        raise ValueError("Tipo debe ser 'email' o 'whatsapp'")
    
    # Validar destinatario
    destinatario = destinatario.strip()
    if not destinatario:
        raise ValueError("Destinatario no puede estar vacío")
    
    # Para WhatsApp, asegurar formato E.164
    if tipo == "whatsapp":
        if not destinatario.startswith("+"):
            destinatario = "+" + destinatario
        # Remover espacios y guiones
        destinatario = destinatario.replace(" ", "").replace("-", "")
    
    # Verificar si ya existe
    existing = collection.find_one({
        "tipo": tipo,
        "destinatario": destinatario
    })
    if existing:
        raise ValueError(f"El destinatario {destinatario} ya existe")
    
    # Crear documento
    doc = {
        "tipo": tipo,
        "destinatario": destinatario,
        "nombre": nombre,
        "activo": True,
        "created_at": datetime.now(timezone.utc),
        "created_by": created_by
    }
    
    result = collection.insert_one(doc)
    
    logger.info(f"[RECIPIENTS] Nuevo destinatario agregado: {tipo} - {destinatario}")
    
    return {
        "id": str(result.inserted_id),
        "tipo": tipo,
        "destinatario": destinatario,
        "nombre": nombre,
        "activo": True,
        "created_at": doc["created_at"].isoformat(),
        "created_by": created_by
    }


def update_recipient(
    recipient_id: str,
    activo: Optional[bool] = None,
    nombre: Optional[str] = None
) -> Dict[str, Any]:
    """
    Actualiza un destinatario existente.
    
    Args:
        recipient_id: ID del destinatario
        activo: Nuevo estado activo/inactivo
        nombre: Nuevo nombre
        
    Returns:
        Dict con el destinatario actualizado
    """
    collection = get_collection()
    
    update_data = {}
    if activo is not None:
        update_data["activo"] = activo
    if nombre is not None:
        update_data["nombre"] = nombre
    
    if not update_data:
        raise ValueError("No hay datos para actualizar")
    
    result = collection.find_one_and_update(
        {"_id": ObjectId(recipient_id)},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        raise ValueError("Destinatario no encontrado")
    
    logger.info(f"[RECIPIENTS] Destinatario actualizado: {recipient_id}")
    
    return {
        "id": str(result["_id"]),
        "tipo": result.get("tipo"),
        "destinatario": result.get("destinatario"),
        "nombre": result.get("nombre"),
        "activo": result.get("activo", True),
        "created_at": result.get("created_at").isoformat() if result.get("created_at") else None,
        "created_by": result.get("created_by")
    }


def delete_recipient(recipient_id: str) -> bool:
    """
    Elimina un destinatario.
    
    Args:
        recipient_id: ID del destinatario
        
    Returns:
        True si se eliminó correctamente
    """
    collection = get_collection()
    
    result = collection.delete_one({"_id": ObjectId(recipient_id)})
    
    if result.deleted_count == 0:
        raise ValueError("Destinatario no encontrado")
    
    logger.info(f"[RECIPIENTS] Destinatario eliminado: {recipient_id}")
    
    return True


def get_recipients_summary() -> Dict[str, Any]:
    """
    Obtiene un resumen de los destinatarios configurados.
    
    Returns:
        Dict con conteos y listas resumidas
    """
    email_recipients = get_all_recipients(tipo="email", solo_activos=True)
    whatsapp_recipients = get_all_recipients(tipo="whatsapp", solo_activos=True)
    
    return {
        "email": {
            "count": len(email_recipients),
            "recipients": [
                {
                    "id": r["id"],
                    "destinatario": r["destinatario"][:3] + "***" + r["destinatario"][r["destinatario"].find("@"):] if "@" in r["destinatario"] else "***",
                    "nombre": r.get("nombre")
                }
                for r in email_recipients
            ]
        },
        "whatsapp": {
            "count": len(whatsapp_recipients),
            "recipients": [
                {
                    "id": r["id"],
                    "destinatario": r["destinatario"][:5] + "***" + r["destinatario"][-4:] if len(r["destinatario"]) > 9 else "***",
                    "nombre": r.get("nombre")
                }
                for r in whatsapp_recipients
            ]
        },
        "total": len(email_recipients) + len(whatsapp_recipients)
    }
