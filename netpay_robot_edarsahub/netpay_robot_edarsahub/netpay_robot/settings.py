from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    netpay_portal_url: str = Field(default='https://manager.netpay.com.mx', alias='NETPAY_PORTAL_URL')
    netpay_username: str = Field(default='', alias='NETPAY_USERNAME')
    netpay_password_plaintext: str = Field(default='', alias='NETPAY_PASSWORD_PLAINTEXT')
    netpay_allow_plaintext_fallback: str = Field(default='', alias='NETPAY_ALLOW_PLAINTEXT_FALLBACK')
    netpay_password_ciphertext: str = Field(default='', alias='NETPAY_PASSWORD_CIPHERTEXT')
    netpay_expected_company: str = Field(default='', alias='NETPAY_EXPECTED_COMPANY')
    netpay_expected_unit: str = Field(default='', alias='NETPAY_EXPECTED_UNIT')
    netpay_connector_id: int = Field(default=0, alias='NETPAY_CONNECTOR_ID')
    netpay_headless: bool = Field(default=True, alias='NETPAY_HEADLESS')
    netpay_download_dir: Path = Field(default=Path('/tmp/netpay_downloads'), alias='NETPAY_DOWNLOAD_DIR')

    server_secret_key: str = Field(default='', alias='SERVER_SECRET_KEY')

    edarsahub_sql_host: str = Field(default='', alias='EDARSAHUB_SQL_HOST')
    edarsahub_sql_database: str = Field(default='', alias='EDARSAHUB_SQL_DATABASE')
    edarsahub_sql_user: str = Field(default='', alias='EDARSAHUB_SQL_USER')
    edarsahub_sql_password: str = Field(default='', alias='EDARSAHUB_SQL_PASSWORD')
    edarsahub_sql_port: int = Field(default=1433, alias='EDARSAHUB_SQL_PORT')

    def ensure_download_dir(self) -> Path:
        self.netpay_download_dir.mkdir(parents=True, exist_ok=True)
        return self.netpay_download_dir
