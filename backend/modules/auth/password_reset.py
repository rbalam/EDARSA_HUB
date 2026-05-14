"""
Password Reset Module - MIGRADO A EDARSAHUB SQL
================================================

FASE 3-I: Migración de MongoDB a EDARSAHUB SQL
Fecha: 2026-05-14
Autorización: Explícita

ARQUITECTURA:
- EDARSAHUB SQL es el cerebro del sistema
- Usuario_Catalogo: usuarios, email, PasswordHashTexto
- Usuario_TokensRecuperacion: tokens de reset
- MongoDB ya NO es fuente productiva para usuarios/password/tokens

FLUJO:
1. Solicitar reset → buscar usuario en SQL → generar token → guardar hash en SQL
2. Validar token → buscar en SQL → verificar expiración/uso
3. Cambiar password → actualizar PasswordHashTexto en SQL → marcar token usado

DEUDA P2 DOCUMENTADA:
- rate_limit_password_reset: Permanece en MongoDB (defensa en profundidad)
- audit_password_reset: Permanece en MongoDB (log de soporte)
- Migrar en subfase AUTH-RESET-P2
"""

import secrets
import hashlib
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
import pymssql
import bcrypt
import os
import logging

logger = logging.getLogger(__name__)

# Configuracion
TOKEN_TTL_HOURS = 1
RATE_LIMIT_PER_EMAIL = 3  # solicitudes por hora
RATE_LIMIT_PER_IP = 5     # solicitudes por hora
RATE_LIMIT_WINDOW_HOURS = 1


# =========================================================================
# CONEXIONES
# =========================================================================

def _get_sql_connection():
    """Obtener conexión a EDARSAHUB SQL (fuente productiva)."""
    return pymssql.connect(
        server='54.39.104.176',
        port=1433,
        user='HRLectura',
        password='National09$',
        database='EDARSAHUB'
    )


def get_db() -> Database:
    """
    Obtener conexión a MongoDB.
    SOLO para rate_limit y audit (DEUDA P2).
    NO usar para usuarios, passwords ni tokens.
    """
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "edarsa_hub")
    client = MongoClient(mongo_url)
    return client[db_name]


# =========================================================================
# FUNCIONES DE UTILIDAD
# =========================================================================

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


# =========================================================================
# RATE LIMIT (MongoDB - DEUDA P2)
# =========================================================================

def check_rate_limit(db: Database, key: str, limit: int) -> Tuple[bool, int]:
    """
    Verificar rate limit (MongoDB - DEUDA P2).
    
    Returns:
        (allowed: bool, remaining: int)
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=RATE_LIMIT_WINDOW_HOURS)
    
    record = db.rate_limit_password_reset.find_one({"key": key})
    
    if record:
        if record.get("window_start", now) > window_start:
            count = record.get("count", 0)
            if count >= limit:
                return False, 0
            return True, limit - count - 1
    
    return True, limit - 1


def increment_rate_limit(db: Database, key: str):
    """Incrementar contador de rate limit (MongoDB - DEUDA P2)."""
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


# =========================================================================
# AUDITORÍA (MongoDB - DEUDA P2)
# =========================================================================

def audit_log(db: Database, event: str, email: str, ip: str, user_agent: str, 
              success: bool, details: Optional[Dict] = None):
    """Registrar evento en auditoria (MongoDB - DEUDA P2)."""
    db.audit_password_reset.insert_one({
        "event": event,
        "email": email,
        "ip": ip,
        "user_agent": user_agent,
        "success": success,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc)
    })


# =========================================================================
# HELPERS SQL
# =========================================================================

def _find_user_by_email_sql(email: str) -> Optional[Dict]:
    """
    Buscar usuario por email en Usuario_Catalogo (SQL).
    FASE 3-I: Fuente productiva.
    """
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                UsuarioID,
                Email,
                Nombre,
                Activo,
                CAST(PublicUUID AS VARCHAR(36)) as PublicUUID
            FROM Usuario_Catalogo
            WHERE LOWER(Email) = LOWER(%s)
        ''', (email,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'usuario_id_sql': row[0],
            'email': row[1],
            'nombre': row[2],
            'active': bool(row[3]),
            'id': row[4],  # PublicUUID como id público
        }
    finally:
        conn.close()


def _find_user_by_id_sql(user_id: str) -> Optional[Dict]:
    """
    Buscar usuario por PublicUUID en Usuario_Catalogo (SQL).
    """
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                UsuarioID,
                Email,
                Nombre,
                Activo,
                CAST(PublicUUID AS VARCHAR(36)) as PublicUUID
            FROM Usuario_Catalogo
            WHERE LOWER(CAST(PublicUUID AS VARCHAR(36))) = LOWER(%s)
        ''', (user_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'usuario_id_sql': row[0],
            'email': row[1],
            'nombre': row[2],
            'active': bool(row[3]),
            'id': row[4],
        }
    finally:
        conn.close()


def _invalidate_previous_tokens_sql(usuario_id_sql: int, reason: str):
    """
    Invalidar tokens anteriores del usuario en SQL.
    """
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE Usuario_TokensRecuperacion
            SET Invalidado = 1,
                MotivoInvalidacion = %s,
                FechaModificacion = GETUTCDATE()
            WHERE UsuarioID = %s 
              AND Usado = 0 
              AND Invalidado = 0
        ''', (reason, usuario_id_sql))
        conn.commit()
    finally:
        conn.close()


def _save_token_sql(token_hash: str, usuario_id_sql: int, email: str, 
                    expires_at: datetime, ip: str, user_agent: str):
    """
    Guardar token hasheado en Usuario_TokensRecuperacion (SQL).
    NUNCA guardar token plano.
    """
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Usuario_TokensRecuperacion (
                TokenHash, UsuarioID, Email, FechaExpiracion,
                IPSolicitud, UserAgentSolicitud
            ) VALUES (%s, %s, %s, %s, %s, %s)
        ''', (token_hash, usuario_id_sql, email, expires_at, 
              ip, user_agent[:500] if user_agent else None))
        conn.commit()
    finally:
        conn.close()


def _find_valid_token_sql(token_hash: str) -> Optional[Dict]:
    """
    Buscar token válido (no usado, no invalidado, no expirado) en SQL.
    """
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                TokenRecuperacionID,
                UsuarioID,
                Email,
                FechaExpiracion
            FROM Usuario_TokensRecuperacion
            WHERE TokenHash = %s
              AND Usado = 0
              AND Invalidado = 0
              AND FechaExpiracion > GETUTCDATE()
        ''', (token_hash,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'token_id': row[0],
            'usuario_id_sql': row[1],
            'email': row[2],
            'expires_at': row[3],
        }
    finally:
        conn.close()


def _mark_token_used_sql(token_id: int, ip: str, user_agent: str):
    """
    Marcar token como usado en SQL.
    """
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE Usuario_TokensRecuperacion
            SET Usado = 1,
                FechaUso = GETUTCDATE(),
                FechaModificacion = GETUTCDATE(),
                IPUso = %s,
                UserAgentUso = %s
            WHERE TokenRecuperacionID = %s
        ''', (ip, user_agent[:500] if user_agent else None, token_id))
        conn.commit()
    finally:
        conn.close()


def _update_password_sql(usuario_id_sql: int, password_hash: str):
    """
    Actualizar PasswordHashTexto en Usuario_Catalogo (SQL).
    FASE 3-I: Fuente productiva.
    """
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE Usuario_Catalogo
            SET PasswordHashTexto = %s,
                UltimoCambioPassword = GETUTCDATE(),
                FechaModificacion = GETUTCDATE(),
                DebeCambiarPassword = 0,
                PasswordTemporal = 0
            WHERE UsuarioID = %s
        ''', (password_hash, usuario_id_sql))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =========================================================================
# FUNCIONES PRINCIPALES
# =========================================================================

def request_password_reset(
    email: str,
    ip: str,
    user_agent: str,
    base_url: str
) -> Dict[str, Any]:
    """
    Solicitar recuperación de password.
    
    FASE 3-I: Usuario se busca en EDARSAHUB SQL.
    Token se guarda en Usuario_TokensRecuperacion (SQL).
    
    SIEMPRE retorna mensaje genérico para no revelar si el email existe.
    
    Args:
        email: Email del usuario
        ip: IP del solicitante
        user_agent: User-Agent del navegador
        base_url: URL base para construir el link de reset
        
    Returns:
        {"success": True, "message": "..."}
    """
    db = get_db()  # Solo para rate_limit y audit (DEUDA P2)
    generic_message = "Si el email esta registrado, recibiras instrucciones de recuperacion"
    
    # Validar formato de email básico
    if not email or "@" not in email:
        return {"success": True, "message": generic_message}
    
    email = email.lower().strip()
    
    # Verificar rate limit por IP (MongoDB - DEUDA P2)
    ip_key = f"ip:{ip}"
    allowed, _ = check_rate_limit(db, ip_key, RATE_LIMIT_PER_IP)
    if not allowed:
        audit_log(db, "rate_limit_ip", email, ip, user_agent, False, {"key": ip_key})
        logger.warning(f"Rate limit por IP alcanzado: {ip}")
        return {"success": True, "message": generic_message}
    
    # Verificar rate limit por email (MongoDB - DEUDA P2)
    email_key = f"email:{email}"
    allowed, _ = check_rate_limit(db, email_key, RATE_LIMIT_PER_EMAIL)
    if not allowed:
        audit_log(db, "rate_limit_email", email, ip, user_agent, False, {"key": email_key})
        logger.warning(f"Rate limit por email alcanzado: {email}")
        return {"success": True, "message": generic_message}
    
    # Incrementar rate limits (MongoDB - DEUDA P2)
    increment_rate_limit(db, ip_key)
    increment_rate_limit(db, email_key)
    
    # =========================================================================
    # FASE 3-I: Buscar usuario en EDARSAHUB SQL (fuente productiva)
    # =========================================================================
    user = _find_user_by_email_sql(email)
    
    if not user:
        audit_log(db, "request_user_not_found", email, ip, user_agent, False)
        logger.info(f"Password reset solicitado para email inexistente: {email}")
        return {"success": True, "message": generic_message}
    
    # Verificar si usuario está activo
    if not user.get("active", True):
        audit_log(db, "request_user_inactive", email, ip, user_agent, False, 
                  {"user_id": user.get("id")})
        logger.info(f"Password reset solicitado para usuario inactivo: {email}")
        return {"success": True, "message": generic_message}
    
    user_id = user.get("id")  # PublicUUID
    usuario_id_sql = user.get("usuario_id_sql")
    
    # =========================================================================
    # FASE 3-I: Invalidar tokens anteriores en SQL
    # =========================================================================
    _invalidate_previous_tokens_sql(usuario_id_sql, "new_request")
    
    # Generar nuevo token
    token = generate_token()
    token_hash = hash_token(token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=TOKEN_TTL_HOURS)
    
    # =========================================================================
    # FASE 3-I: Guardar token hasheado en SQL (NUNCA token plano)
    # =========================================================================
    _save_token_sql(token_hash, usuario_id_sql, email, expires_at, ip, user_agent)
    
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
    Cambiar password usando token válido.
    
    FASE 3-I: Token se valida en SQL.
    Password se actualiza en Usuario_Catalogo (SQL).
    
    Args:
        token: Token de reset (en texto plano)
        new_password: Nueva contraseña
        ip: IP del solicitante
        user_agent: User-Agent del navegador
        
    Returns:
        {"success": True/False, "message": "..."}
    """
    db = get_db()  # Solo para audit (DEUDA P2)
    
    # Validar que hay token
    if not token:
        return {"success": False, "message": "Token invalido o expirado"}
    
    # Calcular hash del token
    token_hash = hash_token(token)
    
    # =========================================================================
    # FASE 3-I: Buscar token válido en SQL
    # =========================================================================
    token_record = _find_valid_token_sql(token_hash)
    
    if not token_record:
        audit_log(db, "reset_invalid_token", "unknown", ip, user_agent, False,
                  {"token_hash_partial": token_hash[:16]})
        logger.warning(f"Intento de reset con token invalido desde IP: {ip}")
        return {"success": False, "message": "Token invalido o expirado"}
    
    email = token_record.get("email", "unknown")
    usuario_id_sql = token_record.get("usuario_id_sql")
    token_id = token_record.get("token_id")
    
    # Validar complejidad del nuevo password
    valid, error_msg = validate_password_strength(new_password)
    if not valid:
        audit_log(db, "reset_weak_password", email, ip, user_agent, False,
                  {"usuario_id_sql": usuario_id_sql})
        return {"success": False, "message": error_msg}
    
    # =========================================================================
    # FASE 3-I: Buscar usuario en SQL para obtener PublicUUID
    # =========================================================================
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT CAST(PublicUUID AS VARCHAR(36)) as PublicUUID
            FROM Usuario_Catalogo
            WHERE UsuarioID = %s AND Activo = 1
        ''', (usuario_id_sql,))
        row = cursor.fetchone()
        if not row:
            audit_log(db, "reset_user_not_found", email, ip, user_agent, False,
                      {"usuario_id_sql": usuario_id_sql})
            return {"success": False, "message": "Token invalido o expirado"}
        user_id = row[0]
    finally:
        conn.close()
    
    # Hashear nuevo password
    new_password_hash = hash_password(new_password)
    
    # =========================================================================
    # FASE 3-I: Actualizar password en Usuario_Catalogo (SQL)
    # =========================================================================
    updated = _update_password_sql(usuario_id_sql, new_password_hash)
    
    if not updated:
        audit_log(db, "reset_update_failed", email, ip, user_agent, False,
                  {"usuario_id_sql": usuario_id_sql})
        logger.error(f"Fallo al actualizar password para usuario_id_sql: {usuario_id_sql}")
        return {"success": False, "message": "Error al actualizar contrasena"}
    
    # =========================================================================
    # FASE 3-I: Marcar token como usado en SQL
    # =========================================================================
    _mark_token_used_sql(token_id, ip, user_agent)
    
    # Invalidar otros tokens pendientes del usuario
    _invalidate_previous_tokens_sql(usuario_id_sql, "password_reset_completed")
    
    audit_log(db, "reset_success", email, ip, user_agent, True,
              {"user_id": user_id})
    
    logger.info(f"Password reset completado para: {email}")
    
    return {"success": True, "message": "Contrasena actualizada correctamente"}


def send_reset_email(email: str, nombre: str, reset_url: str) -> bool:
    """
    Enviar email de recuperación de contraseña usando SMTP directo.
    
    Returns:
        True si se envió correctamente, False si falló
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        # Obtener configuración de email desde variables de entorno
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
