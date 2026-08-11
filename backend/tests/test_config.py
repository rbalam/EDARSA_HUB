"""
Configuracion compartida minima para tests EDARSAHUB.

Solo resuelve configuracion de entorno.
No contiene MongoDB, secretos ni credenciales hardcodeadas.
"""

import os


class TestConfig:
    TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL")
    TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD")

    TEST_ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL")
    TEST_ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD")

    TEST_SUPERVISOR_EMAIL = os.getenv("TEST_SUPERVISOR_EMAIL")
    TEST_SUPERVISOR_PASSWORD = os.getenv("TEST_SUPERVISOR_PASSWORD")

    TEST_SUPERADMIN_EMAIL = os.getenv("TEST_SUPERADMIN_EMAIL")
    TEST_SUPERADMIN_PASSWORD = os.getenv("TEST_SUPERADMIN_PASSWORD")

    TEST_BASE_URL = (
        os.getenv("TEST_BASE_URL")
        or os.getenv("REACT_APP_BACKEND_URL")
        or ""
    )

    @property
    def admin_email(self):
        return self.TEST_ADMIN_EMAIL

    @property
    def admin_password(self):
        return self.TEST_ADMIN_PASSWORD

    @property
    def supervisor_email(self):
        return self.TEST_SUPERVISOR_EMAIL

    @property
    def supervisor_password(self):
        return self.TEST_SUPERVISOR_PASSWORD

    @classmethod
    def get_test_credentials(cls, user_type: str = "user") -> dict:
        if user_type == "user":
            email = cls.TEST_USER_EMAIL
            password = cls.TEST_USER_PASSWORD
        elif user_type == "admin":
            email = cls.TEST_ADMIN_EMAIL
            password = cls.TEST_ADMIN_PASSWORD
        elif user_type == "supervisor":
            email = cls.TEST_SUPERVISOR_EMAIL
            password = cls.TEST_SUPERVISOR_PASSWORD
        elif user_type == "superadmin":
            email = cls.TEST_SUPERADMIN_EMAIL
            password = cls.TEST_SUPERADMIN_PASSWORD
        else:
            raise ValueError(
                f"Unsupported test user type: {user_type}"
            )

        if not email or not password:
            raise RuntimeError(
                f"Missing test credentials for user_type={user_type}"
            )

        return {
            "email": email,
            "password": password,
        }


test_config = TestConfig()
