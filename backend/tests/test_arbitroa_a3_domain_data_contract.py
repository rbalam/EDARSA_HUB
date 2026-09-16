from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs' / 'BOS' / 'ARBITROA_BOS_A3_DOMAIN_DATA_CONTRACT_V1.md'


def text():
    return DOC.read_text(encoding='utf-8')


def test_a3_contract_exists_and_is_non_executable():
    value = text()
    assert 'A3 Domain Data Contract V1' in value
    assert 'No ejecuta DDL' in value
    assert 'A4 solo puede materializar estas siete tablas' in value


def test_a3_reuses_canonical_bos_masters():
    value = text()
    for token in (
        'Gobierno_Persona(PersonaID)',
        'Usuario_Catalogo(UsuarioID)',
        'Sistema_Empresas(EmpresaID)',
        'Gobierno_Documento(DocumentoID)',
    ):
        assert token in value


def test_a3_forbids_duplicate_identity_and_mongo():
    value = text()
    for token in (
        'ARBITROA_Usuarios',
        'ARBITROA_Personas',
        'no MongoDB',
        'segundo sistema documental',
        'segundo sistema de pagos',
    ):
        assert token in value


def test_a3_defines_minimum_gate_foundation():
    value = text()
    for table in (
        'ARBITROA_Deportes',
        'ARBITROA_Organizaciones',
        'ARBITROA_Afiliaciones',
        'ARBITROA_OrganizacionPersonas',
        'ARBITROA_Sedes',
        'ARBITROA_Canchas',
        'ARBITROA_Reglamentos',
    ):
        assert table in value


def test_a3_keeps_geo_non_authoritative_for_attendance():
    value = text()
    assert 'GEO nunca crea asistencia' in value
    assert 'ARBITROA_GeoSesiones' in value
    assert 'ARBITROA_AsistenciasPartido' in value


def test_a3_defers_real_payment_to_finance_contract():
    value = text()
    assert 'ARBITROA_ServiciosLiquidables' in value
    assert 'A10 certifica FK/semantica compatible' in value


def test_a3_core_slimming_and_production_guard():
    value = text()
    assert 'no crecer `backend/core`' in value
    assert 'Production prohibida' in value
