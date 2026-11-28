from pathlib import Path
from modules.integrations_center.communications_routes import router,_safe_doc

def test_gate5d_generic_routes_are_provider_neutral():
 paths={route.path for route in router.routes}; required={'/communications/configs','/communications/templates','/communications/providers','/communications/queue','/communications/logs'}; assert required <= paths; assert all('twilio' not in p.lower() and 'whatsapp' not in p.lower() for p in paths)

def test_gate5d_generic_routes_require_canonical_permissions():
 source=(Path(__file__).parents[1]/'modules/integrations_center/communications_routes.py').read_text(encoding='utf-8'); assert 'NOTIFICACIONES_VER' in source; assert 'NOTIFICACIONES_CONFIGURAR' in source

def test_gate5d_generic_routes_never_return_secrets():
 safe=_safe_doc({'provider':'x','token':'a','auth_token':'b','api_key':'c','password':'d','secret_ref':'e','normal':'ok'}); assert safe=={'provider':'x','normal':'ok'}

def test_gate5d_route_module_uses_sql_repository_alias():
 source=(Path(__file__).parents[1]/'modules/integrations_center/communications_routes.py').read_text(encoding='utf-8'); assert 'NotificationRepository' in source; assert 'pymongo' not in source.lower(); assert 'StubDatabase' not in source
