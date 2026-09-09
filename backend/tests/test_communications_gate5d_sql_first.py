from pathlib import Path
from core.communications.notifications.repository_sql import NotificationRepository,QUEUE_TABLE,CONFIG_TABLE,LOG_TABLE

def test_gate5d_uses_canonical_sql_objects():
 assert CONFIG_TABLE=='dbo.Sistema_NotificacionesConfig'; assert QUEUE_TABLE=='dbo.Operativo_Notificaciones_Queue'; assert LOG_TABLE=='dbo.Operativo_Notificaciones_Log'

def test_gate5d_kind_classification_is_provider_neutral():
 repo=NotificationRepository(None); assert repo._kind({'ColeccionOrigen':'notification_templates'},{'codigo':'x','template_texto':'hola'})=='template'; assert repo._kind({'ColeccionOrigen':'notification_provider_config'},{'provider':'twilio'})=='provider'; assert repo._kind({'ColeccionOrigen':'notification_config'},{'evento':'SLA_VENCIDO'})=='config'

def test_gate5d_no_mongo_runtime_or_secret_storage():
 text=(Path(__file__).parents[1]/'core/communications/notifications/repository_sql.py').read_text(encoding='utf-8').lower(); assert 'pymongo' not in text; assert 'mongodb://' not in text; assert 'auth_token' not in text; assert 'password_encrypted' not in text

def test_gate5d_migration_only_creates_missing_queue():
 text=(Path(__file__).parents[1]/'database/migrations/20260909_002_communications_queue_rbac.sql').read_text(encoding='utf-8'); assert "OBJECT_ID('dbo.Operativo_Notificaciones_Queue','U') IS NULL" in text; assert 'CREATE TABLE dbo.Operativo_Notificaciones_Queue' in text; assert 'CREATE TABLE dbo.Sistema_NotificacionesConfig' not in text; assert 'CREATE TABLE dbo.Operativo_Notificaciones_Log' not in text; assert "r.codigo=N'SUPERADMIN'" in text
