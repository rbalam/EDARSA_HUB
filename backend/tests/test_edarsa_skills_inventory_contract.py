from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / '.agents' / 'skills'
EXPECTED = {
    'edarsa-auditor',
    'edarsa-coder',
    'edarsa-validator',
    'edarsa-committer',
}


def test_existing_edarsa_skills_are_reused_not_replaced():
    actual = {p.name for p in SKILLS.iterdir() if p.is_dir() and (p / 'SKILL.md').is_file()}
    assert EXPECTED.issubset(actual)


def test_existing_skills_are_instruction_procedures_not_authority_catalogs():
    for name in EXPECTED:
        text = (SKILLS / name / 'SKILL.md').read_text(encoding='utf-8')
        assert 'name:' in text
        assert 'description:' in text
        assert 'production_allowed' not in text
