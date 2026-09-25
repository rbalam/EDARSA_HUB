from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def read(path): return (ROOT/path).read_text(encoding='utf-8')

def test_service_uses_only_canonical_api_client_and_domain_root():
    s=read('frontend/src/services/catalogoAmpliadoApi.js')
    assert "from '@/lib/api'" in s
    assert "const ROOT = '/catalogo-ampliado'" in s
    assert 'axios' not in s.lower()
    assert 'fetch(' not in s
    assert 'http://' not in s and 'https://' not in s
    assert 'Gobierno_' not in s

def test_page_has_no_direct_sql_or_parallel_rbac():
    p=read('frontend/src/pages/catalogo-ampliado/CatalogoAmpliadoDashboard.jsx')
    assert 'catalogoAmpliadoApi' in p
    assert 'Gobierno_' not in p
    assert 'SELECT ' not in p and 'INSERT ' not in p and 'UPDATE dbo.' not in p
    assert 'has_full_access' not in p
    assert 'SUPERADMIN' not in p
    assert 'axios' not in p.lower()
    assert 'fetch(' not in p

def test_frontend_covers_gate5_surfaces():
    p=read('frontend/src/pages/catalogo-ampliado/CatalogoAmpliadoDashboard.jsx')
    for marker in ('Activacion por empresa','Personas','Vinculo canonico','Documentos','Nueva version','Kardex','Vencimientos','Alertas'):
        assert marker in p
    for key in ('usuario_id','cliente_id','proveedor_id','contacto_cliente_id','contacto_proveedor_id'):
        assert key in p

def test_route_registered_under_protected_layout():
    app=read('frontend/src/App.js')
    assert "import CatalogoAmpliadoDashboard from '@/pages/catalogo-ampliado/CatalogoAmpliadoDashboard'" in app
    assert '<Route path="catalogo-ampliado" element={<CatalogoAmpliadoDashboard />} />' in app
    assert app.index('<Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>') < app.index('<Route path="catalogo-ampliado" element={<CatalogoAmpliadoDashboard />} />')

def test_navigation_registry_exempts_explicit_gate5_route():
    registry=read('frontend/src/config/enterpriseNavigationRegistry.json')
    assert '"/catalogo-ampliado"' in registry
