"""
EDARSA HUB - Test Configuration
================================
Configuración centralizada para tests.
Usa variables de entorno para evitar hardcoded secrets.
"""

import os
from dotenv import load_dotenv

# Cargar .env.test si existe, sino .env
if os.path.exists('/app/backend/.env.test'):
    load_dotenv('/app/backend/.env.test')
else:
    load_dotenv('/app/backend/.env')


class TestConfig:
    """Configuración centralizada para tests."""
    
    # Credenciales de test (usar variables de entorno)
    TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'test@example.com')
    TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'test_password_123')
    TEST_ADMIN_EMAIL = os.getenv('TEST_ADMIN_EMAIL', 'admin@inventario.com')
    TEST_ADMIN_PASSWORD = os.getenv('TEST_ADMIN_PASSWORD', 'admin123')
    
    # JWT para tests
    TEST_JWT_SECRET = os.getenv('JWT_SECRET', 'test_jwt_secret_for_tests_only')
    
    # Base URL
    TEST_BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:8001')
    
    # MongoDB
    TEST_MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    TEST_DB_NAME = os.getenv('DB_NAME', 'edarsa_hub_test')
    
    @classmethod
    def get_test_credentials(cls, user_type: str = 'user') -> dict:
        """Retorna credenciales de test según el tipo de usuario."""
        if user_type == 'admin':
            return {
                'email': cls.TEST_ADMIN_EMAIL,
                'password': cls.TEST_ADMIN_PASSWORD
            }
        return {
            'email': cls.TEST_USER_EMAIL,
            'password': cls.TEST_USER_PASSWORD
        }


# Instancia global
test_config = TestConfig()
