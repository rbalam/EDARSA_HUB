from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ADAPTER=ROOT/'backend/modules/catalogo_ampliado/external_delivery.py'
DISPATCHER=ROOT/'backend/core/communications/dispatcher/dispatcher.py'
MIGRATION=ROOT/'backend/database/migrations/20260910_003_catalogo_ampliado_notifications_config.sql'
def test_adapter_uses_canonical_queue_and_preferences_and_blocks_app():
    t=ADAPTER.read_text(encoding='utf-8')
    assert 'Operativo_Notificaciones_Queue' in t
    assert 'UsuarioObjetivoID' in t
    assert 'RecibeEmailNotificaciones' in t
    assert 'RecibeWhatsAppNotificaciones' in t
    assert 'BLOCKED_NO_CANONICAL_PUSH_PROVIDER' in t
    assert 'NotificationRepository' in t
    assert 'send_message' not in t
def test_dispatcher_real_mode_has_no_mock_fallback_and_routes_email_contact():
    t=DISPATCHER.read_text(encoding='utf-8')
    assert 'REAL_PROVIDER_UNAVAILABLE' in t
    assert 'dest.get("email") if str(canal).lower() == "email"' in t
    assert 'EmailSMTPProvider' in t
def test_migration_is_idempotent_and_has_only_canonical_email_whatsapp_config():
    t=MIGRATION.read_text(encoding='utf-8')
    assert t.count('IF NOT EXISTS') >= 6
    assert 'notification_config' in t
    assert 'notification_provider_config' in t
    assert 'notification_templates' in t
    assert '"modo_envio":"real"' in t
    assert 'APP' not in t and 'push' not in t.lower()
