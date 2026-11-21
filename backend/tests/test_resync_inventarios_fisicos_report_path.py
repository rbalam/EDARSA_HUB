from pathlib import Path
import importlib.util
import os


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "backend" / "tools" / "resync_inventarios_fisicos.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "resync_inventarios_fisicos_report_path_contract",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_report_dir_is_absolute_and_repository_rooted():
    module = _load_module()
    expected = ROOT / "docs" / "reports" / "inventarios"

    assert module.REPO_ROOT == ROOT
    assert module.REPORT_DIR == expected
    assert module.REPORT_DIR.is_absolute()


def test_report_dir_does_not_depend_on_current_working_directory(tmp_path):
    previous = Path.cwd()
    try:
        os.chdir(tmp_path)
        module = _load_module()
    finally:
        os.chdir(previous)

    assert module.REPORT_DIR == ROOT / "docs" / "reports" / "inventarios"


def test_report_dir_never_targets_backend_docs():
    module = _load_module()

    assert module.REPORT_DIR != (
        ROOT / "backend" / "docs" / "reports" / "inventarios"
    )
