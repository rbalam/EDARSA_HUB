from __future__ import annotations

import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken


def _derive_fernet_key(server_secret_key: str) -> bytes:
    if not server_secret_key or len(server_secret_key) < 16:
        raise ValueError('SERVER_SECRET_KEY debe existir y tener al menos 16 caracteres.')
    digest = hashlib.sha256(server_secret_key.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(plaintext: str, server_secret_key: str) -> str:
    if not plaintext:
        raise ValueError('No se recibió secreto para cifrar.')
    fernet = Fernet(_derive_fernet_key(server_secret_key))
    return fernet.encrypt(plaintext.encode('utf-8')).decode('utf-8')


def decrypt_secret(ciphertext: str, server_secret_key: str) -> str:
    if not ciphertext:
        raise ValueError('No se recibió secreto cifrado.')
    fernet = Fernet(_derive_fernet_key(server_secret_key))
    try:
        return fernet.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except InvalidToken as exc:
        raise ValueError('No fue posible descifrar el secreto. Verifica SERVER_SECRET_KEY.') from exc
