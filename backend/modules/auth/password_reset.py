"""
Password Reset Module - TEMPORAL / SOLO PREVIEW
================================================

DECLARACION ARQUITECTONICA:
- Esta implementacion es TEMPORAL y SOLO para PREVIEW
- NO redefine la arquitectura oficial del sistema
- MongoDB es ubicacion TRANSITORIA/LEGACY para usuarios
- La fuente maestra oficial sigue siendo BD EDARSAHUB
- NO aplica a produccion sin aprobacion separada

Ref: PROP-001 v2
"""

import secrets
import hashlib
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
import bcrypt
import os
import logging

logger = logging.getLogger(__name__)

# Configuracion
TOKEN_TTL_HOURS = 1
RATE_LIMIT_PER_EMAIL = 3  # solicitudes por hora
RATE_LIMIT_PER_IP = 5     # solicitudes por hora
RATE_LIMIT_WINDOW_HOURS = 1


def get_db() -> Database:
    """Obtener conexion a MongoDB (ubicacion TRANSITORIA de usuarios)"""
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "edarsa_hub")
    client = MongoClient(mongo_url)
    return client[db_name]


def generate_token() -> str:
    """Generar token seguro de 256 bits"""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hashear token con SHA-256 para almacenamiento seguro"""
    return hashlib.sha256(token.encode()).hexdigest()


def hash_password(password: str) -> str:
    """Hashear password con bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validar complejidad del password
    
    Requisitos:
    - Minimo 8 caracteres
    - Maximo 128 caracteres
    - Al menos 1 mayuscula
    - Al menos 1 minuscula
    - Al menos 1 numero
    """
    if len(password) < 8:
        return False, "La contrasena debe tener al menos 8 caracteres"
    if len(password) > 128:
        return False, "La contrasena no puede exceder 128 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "La contrasena debe incluir al menos una mayuscula"
    if not re.search(r'[a-z]', password):
        return False, "La contrasena debe incluir al menos una minuscula"
    if not re.search(r'[0-9]', password):
        return False, "La contrasena debe incluir al menos un numero"
    return True, "OK"


def check_rate_limit(db: Database, key: str, limit: int) -> Tuple[bool, int]:
    """
    Verificar rate limit
    
    Returns:
        (allowed: bool, remaining: int)
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=RATE_LIMIT_WINDOW_HOURS)
    
    # Buscar o crear registro de rate limit
    record = db.rate_limit_password_reset.find_one({"key": key})
    
    if record:
        # Verificar si esta en la ventana actual
        if record.get("window_start", now) > window_start:
            count = record.get("count", 0)
            if count >= limit:
                return False, 0
            return True, limit - count - 1
    
    return True, limit - 1


def increment_rate_limit(db: Database, key: str):
    """Incrementar contador de rate limit"""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=RATE_LIMIT_WINDOW_HOURS)
    
    db.rate_limit_password_reset.update_one(
        {"key": key},
        {
            "$inc": {"count": 1},
            "$setOnInsert": {
                "window_start": now,
                "expires_at": expires_at
            }
        },
        upsert=True
    )


def audit_log(db: Database, event: str, email: str, ip: str, user_agent: str, 
              success: bool, details: Optional[Dict] = None):
    """Registrar evento en auditoria"""
    db.audit_password_reset.insert_one({
        "event": event,
        "email": email,
        "ip": ip,
        "user_agent": user_agent,
        "success": success,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc)
    })


def request_password_reset(
    email: str,
    ip: str,
    user_agent: str,
    base_url: str
) -> Dict[str, Any]:
    """
    Solicitar recuperacion de password
    
    SIEMPRE retorna mensaje generico para no revelar si el email existe.
    
    Args:
        email: Email del usuario
        ip: IP del solicitante
        user_agent: User-Agent del navegador
        base_url: URL base para construir el link de reset
        
    Returns:
        {"success": True, "message": "..."}
    """
    db = get_db()
    generic_message = "Si el email esta registrado, recibiras instrucciones de recuperacion"
    
    # Validar formato de email basico
    if not email or "@" not in email:
        return {"success": True, "message": generic_message}
    
    email = email.lower().strip()
    
    # Verificar rate limit por IP
    ip_key = f"ip:{ip}"
    allowed, _ = check_rate_limit(db, ip_key, RATE_LIMIT_PER_IP)
    if not allowed:
        audit_log(db, "rate_limit_ip", email, ip, user_agent, False, {"key": ip_key})
        # Aun asi responder con mensaje generico
        logger.warning(f"Rate limit por IP alcanzado: {ip}")
        return {"success": True, "message": generic_message}
    
    # Verificar rate limit por email
    email_key = f"email:{email}"
    allowed, _ = check_rate_limit(db, email_key, RATE_LIMIT_PER_EMAIL)
    if not allowed:
        audit_log(db, "rate_limit_email", email, ip, user_agent, False, {"key": email_key})
        logger.warning(f"Rate limit por email alcanzado: {email}")
        return {"success": True, "message": generic_message}
    
    # Incrementar rate limits
    increment_rate_limit(db, ip_key)
    increment_rate_limit(db, email_key)
    
    # Buscar usuario en MongoDB (ubicacion TRANSITORIA)
    user = db.users.find_one({"email": email})
    
    if not user:
        # Usuario no existe - NO revelar, solo auditar internamente
        audit_log(db, "request_user_not_found", email, ip, user_agent, False)
        logger.info(f"Password reset solicitado para email inexistente: {email}")
        return {"success": True, "message": generic_message}
    
    # Verificar si usuario esta activo
    if not user.get("active", True):
        audit_log(db, "request_user_inactive", email, ip, user_agent, False, 
                  {"user_id": str(user.get("id", user.get("_id")))})
        logger.info(f"Password reset solicitado para usuario inactivo: {email}")
        return {"success": True, "message": generic_message}
    
    user_id = str(user.get("id", user.get("_id")))
    
    # Invalidar tokens anteriores del mismo usuario
    db.password_reset_tokens.update_many(
        {"user_id": user_id, "used": False, "invalidated": False},
        {"$set": {"invalidated": True, "invalidated_reason": "new_request"}}
    )
    
    # Generar nuevo token
    token = generate_token()
    token_hash = hash_token(token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=TOKEN_TTL_HOURS)
    
    # Almacenar token (solo el hash)
    db.password_reset_tokens.insert_one({
        "token_hash": token_hash,
        "user_id": user_id,
        "email": email,
        "created_at": now,
        "expires_at": expires_at,
        "used": False,
        "used_at": None,
        "ip_request": ip,
        "ip_reset": None,
        "user_agent_request": user_agent[:500] if user_agent else None,
        "invalidated": False,
        "invalidated_reason": None
    })
    
    # Construir URL de reset
    reset_url = f"{base_url}/reset-password?token={token}"
    
    # Enviar email
    email_sent = send_reset_email(email, user.get("nombre", ""), reset_url)
    
    audit_log(db, "request_success", email, ip, user_agent, email_sent, 
              {"user_id": user_id, "email_sent": email_sent})
    
    if email_sent:
        logger.info(f"Password reset email enviado a: {email}")
    else:
        logger.error(f"Fallo envio de email de reset a: {email}")
    
    return {"success": True, "message": generic_message}


def reset_password(
    token: str,
    new_password: str,
    ip: str,
    user_agent: str
) -> Dict[str, Any]:
    """
    Cambiar password usando token valido
    
    Args:
        token: Token de reset (en texto plano)
        new_password: Nueva contrasena
        ip: IP del solicitante
        user_agent: User-Agent del navegador
        
    Returns:
        {"success": True/False, "message": "..."}
    """
    db = get_db()
    
    # Validar que hay token
    if not token:
        return {"success": False, "message": "Token invalido o expirado"}
    
    # Calcular hash del token
    token_hash = hash_token(token)
    now = datetime.now(timezone.utc)
    
    # Buscar token valido
    token_record = db.password_reset_tokens.find_one({
        "token_hash": token_hash,
        "used": False,
        "invalidated": False,
        "expires_at": {"$gt": now}
    })
    
    if not token_record:
        audit_log(db, "reset_invalid_token", "unknown", ip, user_agent, False,
                  {"token_hash_partial": token_hash[:16]})
        logger.warning(f"Intento de reset con token invalido desde IP: {ip}")
        return {"success": False, "message": "Token invalido o expirado"}
    
    email = token_record.get("email", "unknown")
    user_id = token_record.get("user_id")
    
    # Validar complejidad del nuevo password
    valid, error_msg = validate_password_strength(new_password)
    if not valid:
        audit_log(db, "reset_weak_password", email, ip, user_agent, False,
                  {"user_id": user_id})
        return {"success": False, "message": error_msg}
    
    # Buscar usuario
    user = db.users.find_one({"$or": [{"id": user_id}, {"_id": user_id}]})
    if not user:
        # Caso muy raro - usuario eliminado despues de solicitar reset
        audit_log(db, "reset_user_not_found", email, ip, user_agent, False,
                  {"user_id": user_id})
        return {"success": False, "message": "Token invalido o expirado"}
    
    # Hashear nuevo password
    new_password_hash = hash_password(new_password)
    
    # Actualizar password en MongoDB (ubicacion TRANSITORIA)
    result = db.users.update_one(
        {"$or": [{"id": user_id}, {"_id": user_id}]},
        {"$set": {"password": new_password_hash}}
    )
    
    if result.modified_count == 0:
        audit_log(db, "reset_update_failed", email, ip, user_agent, False,
                  {"user_id": user_id})
        logger.error(f"Fallo al actualizar password para user_id: {user_id}")
        return {"success": False, "message": "Error al actualizar contrasena"}
    
    # Marcar token como usado
    db.password_reset_tokens.update_one(
        {"_id": token_record["_id"]},
        {"$set": {
            "used": True,
            "used_at": now,
            "ip_reset": ip
        }}
    )
    
    # Invalidar otros tokens pendientes del usuario
    db.password_reset_tokens.update_many(
        {"user_id": user_id, "used": False, "invalidated": False},
        {"$set": {"invalidated": True, "invalidated_reason": "password_reset_completed"}}
    )
    
    # Opcional: Invalidar sesiones en EDARSAHUB
    # (Implementacion futura si se aprueba)
    
    audit_log(db, "reset_success", email, ip, user_agent, True,
              {"user_id": user_id})
    
    logger.info(f"Password reset completado para: {email}")
    
    return {"success": True, "message": "Contrasena actualizada correctamente"}


def send_reset_email(email: str, nombre: str, reset_url: str) -> bool:
    """
    Enviar email de recuperacion de contrasena usando SMTP directo.
    
    Returns:
        True si se envio correctamente, False si fallo
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        # Obtener configuracion de email desde variables de entorno
        host = os.environ.get("EMAIL_HOST", "mail.edarsa.com.mx")
        port = int(os.environ.get("EMAIL_PORT", 587))
        username = os.environ.get("EMAIL_USER", "")
        password = os.environ.get("EMAIL_PASSWORD", "")
        from_email = os.environ.get("EMAIL_FROM", "notificaciones@edarsa.com.mx")
        from_name = os.environ.get("EMAIL_FROM_NAME", "EDARSA HUB")
        use_tls = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
        
        if not all([host, username, password]):
            logger.error("Configuracion de email incompleta")
            return False
        
        # Plantilla HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Recuperacion de contrasena</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #1a365d; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">EDARSA HUB</h1>
    </div>
    
    <div style="padding: 30px; background: #f7fafc; border: 1px solid #e2e8f0;">
        <h2 style="color: #2d3748;">Recuperacion de contrasena</h2>
        
        <p>Hola{' ' + nombre if nombre else ''},</p>
        
        <p>Hemos recibido una solicitud para restablecer la contrasena de tu cuenta.</p>
        
        <p>Haz clic en el siguiente boton para crear una nueva contrasena:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" 
               style="background: #3182ce; color: white; padding: 15px 30px; 
                      text-decoration: none; border-radius: 5px; font-weight: bold;">
                Restablecer contrasena
            </a>
        </div>
        
        <p style="color: #718096; font-size: 14px;">
            Este enlace expirara en <strong>1 hora</strong>.
        </p>
        
        <p style="color: #718096; font-size: 14px;">
            Si no solicitaste este cambio, puedes ignorar este correo. 
            Tu contrasena actual seguira siendo valida.
        </p>
        
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
        
        <p style="color: #a0aec0; font-size: 12px;">
            Si el boton no funciona, copia y pega esta URL en tu navegador:<br>
            <span style="word-break: break-all;">{reset_url}</span>
        </p>
    </div>
    
    <div style="padding: 20px; text-align: center; color: #a0aec0; font-size: 12px;">
        <p>Este es un correo automatico de EDARSA HUB. Por favor no respondas.</p>
        <p>&copy; 2026 EDARSA. Todos los derechos reservados.</p>
    </div>
</body>
</html>
"""
        
        # Construir mensaje
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Recuperacion de contrasena - EDARSA HUB"
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = email
        
        # Agregar contenido HTML
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        
        # Enviar
        with smtplib.SMTP(host, port, timeout=30) as server:
            if use_tls:
                server.starttls()
            server.login(username, password)
            server.sendmail(from_email, [email], msg.as_string())
        
        logger.info(f"Email de reset enviado exitosamente a: {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email de reset: {str(e)}")
        return False
