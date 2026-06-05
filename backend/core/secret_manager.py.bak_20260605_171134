"""
EDARSA HUB - Secret Manager
============================

Servicio central de cifrado/descifrado de secretos para servidores.

FASE 3C: Seguridad de secretos en SQL.

USO:
    from core.secret_manager import encrypt_secret, decrypt_secret, mask_secret

VARIABLE DE ENTORNO REQUERIDA:
    SERVER_SECRET_KEY - Clave de cifrado de 32 bytes en base64
    
    Generar clave:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

FORMATO DE SECRETOS CIFRADOS:
    enc:v1:<ciphertext_base64>

CREADO: FASE 3C - Diciembre 2025
"""

import os
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Prefijo para identificar secretos cifrados
SECRET_PREFIX = "enc:v1:"

# Valores que indican que se debe preservar el secreto existente
MASKED_VALUES = frozenset([
    None, "", "********", "••••••••", "●●●●●●●●",
    "[PROTECTED]", "[ENCRYPTED]", "[HIDDEN]"
])


class SecretManagerError(Exception):
    """Error en operaciones de cifrado/descifrado."""
    pass


def _get_fernet():
    """
    Obtiene instancia de Fernet con la clave de entorno.
    
    Returns:
        Fernet instance o None si no hay clave
    """
    try:
        from cryptography.fernet import Fernet
        
        key = os.environ.get('SERVER_SECRET_KEY')
        
        if not key:
            logger.warning("[SECRET_MANAGER] SERVER_SECRET_KEY no configurada. Cifrado deshabilitado.")
            return None
        
        # Validar que la clave sea válida para Fernet
        try:
            fernet = Fernet(key.encode() if isinstance(key, str) else key)
            return fernet
        except Exception as e:
            logger.error(f"[SECRET_MANAGER] SERVER_SECRET_KEY inválida: {e}")
            return None
            
    except ImportError:
        logger.error("[SECRET_MANAGER] cryptography no instalado")
        return None


def _get_key_fingerprint() -> str:
    """
    Obtiene fingerprint de la clave actual (sin exponer la clave).
    
    Returns:
        Hash corto de la clave o "none" si no hay clave
    """
    import hashlib
    key = os.environ.get('SERVER_SECRET_KEY', '')
    if not key:
        return "none"
    # Solo usar los primeros 8 chars del hash para fingerprint
    return hashlib.sha256(key.encode()).hexdigest()[:8]


# FASE 3C.1: Cache con detección automática de cambio de clave
_fernet_instance = None
_fernet_key_fingerprint = None


def get_fernet():
    """
    Obtiene instancia de Fernet (cacheada con detección de cambio de clave).
    
    FASE 3C.1: Detecta automáticamente si la clave de entorno cambió
    y recrea la instancia de Fernet sin necesidad de limpieza manual.
    """
    global _fernet_instance, _fernet_key_fingerprint
    
    current_fingerprint = _get_key_fingerprint()
    
    # Si cambió la clave, invalidar cache automáticamente
    if _fernet_key_fingerprint != current_fingerprint:
        if _fernet_key_fingerprint is not None:
            logger.info(f"[SECRET_MANAGER][CACHE_INVALIDATED] Clave de cifrado cambió (fingerprint: {_fernet_key_fingerprint[:4]}... -> {current_fingerprint[:4]}...)")
        _fernet_instance = _get_fernet()
        _fernet_key_fingerprint = current_fingerprint
    
    return _fernet_instance


def reset_fernet_cache():
    """
    Reinicia el cache de Fernet (útil para testing).
    
    FASE 3C.1: Actualizado para limpiar fingerprint también.
    """
    global _fernet_instance, _fernet_key_fingerprint
    _fernet_instance = None
    _fernet_key_fingerprint = None
    logger.debug("[SECRET_MANAGER][CACHE_RESET] Cache de Fernet limpiado manualmente")


def get_secret_key() -> Optional[str]:
    """
    Obtiene la clave de cifrado del entorno.
    
    Returns:
        Clave de cifrado o None si no está configurada
    """
    return os.environ.get('SERVER_SECRET_KEY')


def is_encryption_available() -> bool:
    """
    Verifica si el cifrado está disponible.
    
    Returns:
        True si hay clave válida configurada
    """
    return get_fernet() is not None


def encrypt_secret(value: str) -> str:
    """
    Cifra un secreto.
    
    Args:
        value: Texto plano a cifrar
        
    Returns:
        Valor cifrado con prefijo enc:v1: o valor original si cifrado no disponible
        
    Note:
        Si el cifrado no está disponible, devuelve el valor original
        con un warning en logs (sin exponer el valor).
    """
    if not value:
        return value
    
    # Si ya está cifrado, no doble cifrar
    if is_encrypted_secret(value):
        return value
    
    fernet = get_fernet()
    
    if not fernet:
        logger.warning("[SECRET_MANAGER] Guardando secreto SIN cifrar (SERVER_SECRET_KEY no configurada)")
        return value
    
    try:
        encrypted = fernet.encrypt(value.encode('utf-8'))
        return f"{SECRET_PREFIX}{encrypted.decode('utf-8')}"
    except Exception as e:
        logger.error(f"[SECRET_MANAGER] Error cifrando secreto: {type(e).__name__}")
        # No exponer el secreto en el error
        raise SecretManagerError("Error al cifrar secreto")


def decrypt_secret(value: str) -> str:
    """
    Descifra un secreto.
    
    Args:
        value: Valor cifrado (con prefijo enc:v1:) o texto plano legacy
        
    Returns:
        Texto plano descifrado
        
    Note:
        Si el valor no está cifrado (legacy), lo devuelve tal cual
        para compatibilidad con servidores existentes.
    """
    if not value:
        return value
    
    # Si no está cifrado, es legacy - devolver tal cual
    if not is_encrypted_secret(value):
        # No loguear warning aquí porque es esperado durante migración
        return value
    
    fernet = get_fernet()
    
    if not fernet:
        logger.error("[SECRET_MANAGER] No se puede descifrar: SERVER_SECRET_KEY no configurada")
        raise SecretManagerError("Clave de descifrado no disponible")
    
    try:
        # Remover prefijo
        ciphertext = value[len(SECRET_PREFIX):]
        decrypted = fernet.decrypt(ciphertext.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"[SECRET_MANAGER] Error descifrando secreto: {type(e).__name__}")
        raise SecretManagerError("Error al descifrar secreto")


def is_encrypted_secret(value: str) -> bool:
    """
    Verifica si un valor está cifrado.
    
    Args:
        value: Valor a verificar
        
    Returns:
        True si el valor tiene el prefijo de cifrado enc:v1:
    """
    if not value or not isinstance(value, str):
        return False
    return value.startswith(SECRET_PREFIX)


def mask_secret(value: str, mask_char: str = "*", visible_chars: int = 0) -> str:
    """
    Enmascara un secreto para mostrar en responses.
    
    Args:
        value: Secreto a enmascarar
        mask_char: Caracter de enmascaramiento
        visible_chars: Cuántos caracteres mostrar (0 = ninguno)
        
    Returns:
        Valor enmascarado (ej: "********")
    """
    if not value:
        return ""
    
    # Siempre devolver máscara fija, nunca el valor real
    return mask_char * 8


def should_preserve_existing_secret(new_value) -> bool:
    """
    Determina si se debe preservar el secreto existente.
    
    Args:
        new_value: Valor nuevo que viene del payload
        
    Returns:
        True si el nuevo valor indica que se debe conservar el existente
    """
    if new_value is None:
        return True
    
    if isinstance(new_value, str):
        # Normalizar para comparación
        normalized = new_value.strip()
        
        # Valores enmascarados conocidos
        if normalized in MASKED_VALUES:
            return True
        
        # Patrones de enmascaramiento
        if all(c in '*•●' for c in normalized) and len(normalized) >= 4:
            return True
    
    return False


def prepare_secret_for_storage(
    new_value: Optional[str],
    existing_value: Optional[str] = None
) -> Tuple[Optional[str], bool]:
    """
    Prepara un secreto para almacenamiento.
    
    Args:
        new_value: Valor nuevo del payload
        existing_value: Valor existente en BD
        
    Returns:
        Tuple (valor_a_guardar, fue_modificado)
        
    Comportamiento:
        - Si new_value es enmascarado → preserva existing_value
        - Si new_value es real → cifra y devuelve
        - Si new_value ya está cifrado → no doble cifra
    """
    # Preservar existente si el nuevo es enmascarado
    if should_preserve_existing_secret(new_value):
        return existing_value, False
    
    # Valor nuevo real - cifrar
    encrypted = encrypt_secret(new_value)
    was_modified = encrypted != existing_value
    
    return encrypted, was_modified


def get_secret_status(value: Optional[str]) -> dict:
    """
    Obtiene estado de un secreto para responses.
    
    Args:
        value: Valor del secreto
        
    Returns:
        Dict con estado del secreto (sin exponer valor)
    """
    if not value:
        return {
            'configured': False,
            'encrypted': False
        }
    
    return {
        'configured': True,
        'encrypted': is_encrypted_secret(value)
    }


# Funciones de utilidad para migración

def needs_encryption(value: Optional[str]) -> bool:
    """
    Determina si un valor necesita ser cifrado.
    
    Returns:
        True si el valor existe y no está cifrado
    """
    if not value:
        return False
    return not is_encrypted_secret(value)


def generate_encryption_key() -> str:
    """
    Genera una nueva clave de cifrado Fernet.
    
    Returns:
        Clave en formato base64 lista para usar en SERVER_SECRET_KEY
    """
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode('utf-8')


# Verificación de inicialización
def verify_secret_manager_ready() -> dict:
    """
    Verifica que el secret manager esté correctamente configurado.
    
    Returns:
        Dict con estado de configuración (sin exponer clave)
    """
    key = get_secret_key()
    fernet = get_fernet()
    fingerprint = _get_key_fingerprint()
    
    status = {
        'key_configured': key is not None,
        'key_valid': fernet is not None,
        'encryption_available': is_encryption_available(),
        'key_fingerprint': fingerprint,  # Solo fingerprint, no la clave
        'warnings': []
    }
    
    if not key:
        status['warnings'].append("SERVER_SECRET_KEY no configurada - secretos se guardarán sin cifrar")
    elif not fernet:
        status['warnings'].append("SERVER_SECRET_KEY inválida - verificar formato base64 Fernet")
    
    return status


def validate_secret_key_config() -> dict:
    """
    Valida la configuración de la clave de cifrado.
    
    FASE 3C.1: Función de validación que NO expone la clave.
    
    Returns:
        Dict con resultado de validación
    """
    result = {
        'valid': False,
        'fingerprint': None,
        'issues': []
    }
    
    key = os.environ.get('SERVER_SECRET_KEY')
    
    if not key:
        result['issues'].append("SERVER_SECRET_KEY no está definida en variables de entorno")
        return result
    
    if len(key) != 44:
        result['issues'].append(f"Longitud de clave incorrecta: {len(key)} (esperado: 44)")
        return result
    
    # Validar que es base64 válido
    try:
        import base64
        decoded = base64.urlsafe_b64decode(key)
        if len(decoded) != 32:
            result['issues'].append("Clave no tiene 32 bytes después de decodificar")
            return result
    except Exception as e:
        result['issues'].append(f"Clave no es base64 válido: {type(e).__name__}")
        return result
    
    # Validar que Fernet puede usarla
    try:
        from cryptography.fernet import Fernet
        fernet = Fernet(key.encode())
        # Test rápido
        test = fernet.encrypt(b"test")
        fernet.decrypt(test)
    except Exception as e:
        result['issues'].append(f"Fernet no puede usar la clave: {type(e).__name__}")
        return result
    
    result['valid'] = True
    result['fingerprint'] = _get_key_fingerprint()
    
    return result


def clear_secret_manager_cache():
    """
    Alias de reset_fernet_cache() para consistencia de nomenclatura.
    
    FASE 3C.1: Función explícita para limpiar cache del secret manager.
    """
    reset_fernet_cache()


# =============================================================================
# FASE 4C: Funciones para Rotación de Claves
# =============================================================================

def validate_fernet_key(key: str) -> dict:
    """
    Valida si una clave es válida para Fernet.
    
    FASE 4C: Soporte para rotación de claves.
    
    Args:
        key: Clave a validar (NO se imprime en logs)
        
    Returns:
        Dict con valid, fingerprint, issues
    """
    result = {
        'valid': False,
        'fingerprint': None,
        'issues': []
    }
    
    if not key:
        result['issues'].append("Clave vacía")
        return result
    
    if len(key) != 44:
        result['issues'].append(f"Longitud incorrecta: {len(key)} (esperado: 44)")
        return result
    
    try:
        import base64
        import hashlib
        decoded = base64.urlsafe_b64decode(key)
        if len(decoded) != 32:
            result['issues'].append("No tiene 32 bytes después de decodificar")
            return result
    except Exception as e:
        result['issues'].append(f"No es base64 válido: {type(e).__name__}")
        return result
    
    try:
        from cryptography.fernet import Fernet
        fernet = Fernet(key.encode())
        test = fernet.encrypt(b"rotation_test")
        fernet.decrypt(test)
    except Exception as e:
        result['issues'].append(f"Fernet no puede usar la clave: {type(e).__name__}")
        return result
    
    result['valid'] = True
    import hashlib
    result['fingerprint'] = hashlib.sha256(key.encode()).hexdigest()[:8]
    
    return result


def get_key_fingerprint(key: str) -> str:
    """
    Obtiene fingerprint de una clave (sin exponerla).
    
    FASE 4C: Soporte para rotación de claves.
    
    Args:
        key: Clave de la cual obtener fingerprint
        
    Returns:
        Hash corto de la clave o "none" si es vacía
    """
    import hashlib
    if not key:
        return "none"
    return hashlib.sha256(key.encode()).hexdigest()[:8]


def encrypt_secret_with_key(value: str, key: str) -> str:
    """
    Cifra un secreto usando una clave específica.
    
    FASE 4C: Soporte para rotación de claves.
    
    SEGURIDAD: No imprime ni logea la clave ni el valor.
    
    Args:
        value: Texto plano a cifrar
        key: Clave de cifrado Fernet
        
    Returns:
        Valor cifrado con prefijo enc:v1:
        
    Raises:
        SecretManagerError: Si hay error en el cifrado
    """
    if not value:
        return value
    
    if not key:
        raise SecretManagerError("Clave de cifrado no proporcionada")
    
    # Si ya está cifrado, no doble cifrar
    if is_encrypted_secret(value):
        # Necesitamos descifrar y re-cifrar con la nueva clave
        # NO hacer esto aquí - la lógica de rotación debe manejar esto
        raise SecretManagerError("El valor ya está cifrado. Use decrypt_secret_with_key primero.")
    
    try:
        from cryptography.fernet import Fernet
        fernet = Fernet(key.encode() if isinstance(key, str) else key)
        encrypted = fernet.encrypt(value.encode('utf-8'))
        return f"{SECRET_PREFIX}{encrypted.decode('utf-8')}"
    except Exception as e:
        logger.error(f"[SECRET_MANAGER][ROTATE] Error cifrando con clave específica: {type(e).__name__}")
        raise SecretManagerError("Error al cifrar con clave específica")


def decrypt_secret_with_key(value: str, key: str) -> str:
    """
    Descifra un secreto usando una clave específica.
    
    FASE 4C: Soporte para rotación de claves.
    
    SEGURIDAD: No imprime ni logea la clave ni el valor.
    
    Args:
        value: Valor cifrado (con prefijo enc:v1:)
        key: Clave de descifrado Fernet
        
    Returns:
        Texto plano descifrado
        
    Raises:
        SecretManagerError: Si hay error en el descifrado
    """
    if not value:
        return value
    
    if not key:
        raise SecretManagerError("Clave de descifrado no proporcionada")
    
    # Si no está cifrado, devolver tal cual (legacy)
    if not is_encrypted_secret(value):
        return value
    
    try:
        from cryptography.fernet import Fernet
        fernet = Fernet(key.encode() if isinstance(key, str) else key)
        ciphertext = value[len(SECRET_PREFIX):]
        decrypted = fernet.decrypt(ciphertext.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"[SECRET_MANAGER][ROTATE] Error descifrando con clave específica: {type(e).__name__}")
        raise SecretManagerError("Error al descifrar con clave específica")


def rotate_secret(encrypted_value: str, old_key: str, new_key: str) -> str:
    """
    Rota un secreto de una clave a otra.
    
    FASE 4C: Función principal para rotación.
    
    SEGURIDAD: No imprime ni logea claves ni valores.
    
    Args:
        encrypted_value: Valor cifrado con old_key
        old_key: Clave de cifrado actual
        new_key: Nueva clave de cifrado
        
    Returns:
        Valor re-cifrado con new_key
        
    Raises:
        SecretManagerError: Si hay error en la rotación
    """
    if not encrypted_value:
        return encrypted_value
    
    # Si no está cifrado, cifrarlo directamente con la nueva clave
    if not is_encrypted_secret(encrypted_value):
        return encrypt_secret_with_key(encrypted_value, new_key)
    
    # Descifrar con clave actual
    plaintext = decrypt_secret_with_key(encrypted_value, old_key)
    
    # Cifrar con clave nueva
    new_encrypted = encrypt_secret_with_key(plaintext, new_key)
    
    return new_encrypted


def validate_rotation_keys(old_key: str, new_key: str) -> dict:
    """
    Valida las claves para una rotación.
    
    FASE 4C: Validación pre-rotación.
    
    Args:
        old_key: Clave actual
        new_key: Nueva clave
        
    Returns:
        Dict con valid, old_fingerprint, new_fingerprint, issues
    """
    result = {
        'valid': False,
        'old_fingerprint': None,
        'new_fingerprint': None,
        'issues': []
    }
    
    # Validar clave actual
    old_validation = validate_fernet_key(old_key)
    if not old_validation['valid']:
        result['issues'].append(f"Clave actual inválida: {old_validation['issues']}")
        return result
    result['old_fingerprint'] = old_validation['fingerprint']
    
    # Validar clave nueva
    new_validation = validate_fernet_key(new_key)
    if not new_validation['valid']:
        result['issues'].append(f"Clave nueva inválida: {new_validation['issues']}")
        return result
    result['new_fingerprint'] = new_validation['fingerprint']
    
    # Verificar que son diferentes
    if old_key == new_key:
        result['issues'].append("La clave nueva es igual a la actual")
        return result
    
    result['valid'] = True
    return result

