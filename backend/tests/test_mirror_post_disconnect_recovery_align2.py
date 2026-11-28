"""GATE-ALIGN-2 tests: safe post-disconnect recovery for edarsahub-mirror-sync without weakening fail-closed controls."""
from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WATCHDOG = ROOT / "tools/bootstrap/edarsahub_bootstrap_watchdog.py"
MIRROR_START = ROOT / "tools/mirror_sync/mirror_sync_start.sh"
MIRROR_STOP = ROOT / "tools/mirror_sync/mirror_sync_stop.sh"
MIRROR_CONF = ROOT / "tools/mirror_sync/supervisor/edarsahub-mirror-sync.conf"
SAFETY_GUARD = ROOT / "tools/mirror_sync/shared_app_safety_guard.sh"


def _load_watchdog(tmp_path: Path, monkeypatch, *, app_dir: Path | None = None):
    state_dir = tmp_path / "bootstrap_state"
    temp_stop = tmp_path / "tmp_mirror_stop"
    monkeypatch.setenv("EDARSAHUB_BOOTSTRAP_STATE", str(state_dir))
    monkeypatch.setenv("EDARSAHUB_MIRROR_TEMP_STOP", str(temp_stop))
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    if app_dir is not None:
        monkeypatch.setenv("EDARSAHUB_APP", str(app_dir))
    monkeypatch.setenv("EDARSAHUB_MIRROR_RECOVERY_COOLDOWN", "120")
    monkeypatch.setenv("EDARSAHUB_MIRROR_RECOVERY_MAX_ATTEMPTS", "3")

    spec = importlib.util.spec_from_file_location(
        f"edarsahub_watchdog_align2_{id(tmp_path)}",
        WATCHDOG,
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _git(repo: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return res.stdout.strip()


def _setup_isolated_preview_repo(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    app = tmp_path / "app"
    _git(tmp_path, "init", "--bare", str(remote))
    app.mkdir()
    _git(app, "init")
    _git(app, "config", "user.email", "test@edarsa.local")
    _git(app, "config", "user.name", "Test")
    (app / ".emergent").mkdir(parents=True)
    (app / ".emergent/system_deps.txt").write_text("git\n", encoding="utf-8")
    (app / "tools/mirror_sync").mkdir(parents=True)
    (app / "tools/mirror_sync/shared_app_safety_guard.sh").write_text(
        SAFETY_GUARD.read_text(encoding="utf-8"), encoding="utf-8"
    )
    start_dst = app / "tools/mirror_sync/mirror_sync_start.sh"
    start_dst.write_text(MIRROR_START.read_text(encoding="utf-8"), encoding="utf-8")
    os.chmod(start_dst, 0o755)
    _git(app, "add", ".")
    _git(app, "commit", "-m", "seed")
    _git(app, "branch", "-M", "Edarsahub_Desarrollo")
    _git(app, "remote", "add", "origin", str(remote))
    _git(app, "push", "-u", "origin", "Edarsahub_Desarrollo")
    # Simular deriva esperada de plataforma Emergent
    (app / ".emergent/system_deps.txt").write_text("", encoding="utf-8")
    return remote, app


def test_post_disconnect_authorized_not_started_recovers_once(tmp_path: Path, monkeypatch) -> None:
    _, app = _setup_isolated_preview_repo(tmp_path)
    (app / ".git/mirror-sync").mkdir(parents=True, exist_ok=True)
    (app / ".git/mirror-sync/ENABLED").write_text("ENABLED_AT_UTC=2026-11-20T00:00:00Z\n", encoding="utf-8")

    wd = _load_watchdog(tmp_path, monkeypatch, app_dir=app)
    running = False
    recover_calls: list[list[str]] = []

    def fake_run(args, cwd=None, timeout=60):
        nonlocal running
        if args[:2] == ["supervisorctl", "status"]:
            if running:
                return subprocess.CompletedProcess(args, 0, stdout="edarsahub-mirror-sync RUNNING pid 555, uptime 0:00:02\n")
            return subprocess.CompletedProcess(args, 3, stdout="edarsahub-mirror-sync STOPPED Not started\n")
        if args[:1] == ["/bin/bash"] and "--recover-authorized" in args:
            recover_calls.append(list(args))
            running = True
            return subprocess.CompletedProcess(args, 0, stdout="MIRROR_SYNC_RECOVERY=STARTED\n")
        return subprocess.run(args, cwd=str(cwd or app), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

    monkeypatch.setattr(wd, "run", fake_run)

    auth = wd.mirror_authorization()
    assert auth == {"authorized": True, "state": "AUTHORIZED"}

    first = wd.maybe_recover_mirror_sync(auth)
    assert first["state"] == "RECOVERED"
    assert first["started"] is True
    assert first["production_touched"] is False
    assert len(recover_calls) == 1

    # Segunda ejecucion con servicio ya RUNNING -> idempotente, cero duplicados
    second = wd.maybe_recover_mirror_sync(auth)
    assert second["state"] == "ALREADY_RUNNING"
    assert second["started"] is False
    assert len(recover_calls) == 1


def test_emergency_stop_disabled_pause_and_admin_stop_never_autostart(tmp_path: Path, monkeypatch) -> None:
    _, app = _setup_isolated_preview_repo(tmp_path)
    ms_dir = app / ".git/mirror-sync"
    ms_dir.mkdir(parents=True, exist_ok=True)

    wd = _load_watchdog(tmp_path, monkeypatch, app_dir=app)
    recover_calls: list[list[str]] = []
    sup_stdout = "edarsahub-mirror-sync STOPPED Not started\n"

    def fake_run(args, cwd=None, timeout=60):
        if args[:2] == ["supervisorctl", "status"]:
            return subprocess.CompletedProcess(args, 3, stdout=sup_stdout)
        if args[:1] == ["/bin/bash"]:
            recover_calls.append(list(args))
            return subprocess.CompletedProcess(args, 0, stdout="")
        return subprocess.run(args, cwd=str(cwd or app), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

    monkeypatch.setattr(wd, "run", fake_run)

    # 1. ENABLED ausente -> no iniciar
    auth_disabled = wd.mirror_authorization()
    assert auth_disabled == {"authorized": False, "state": "EXPLICIT_ENABLE_REQUIRED"}
    r1 = wd.maybe_recover_mirror_sync(auth_disabled)
    assert r1["state"] == "NOT_AUTHORIZED" and r1["started"] is False

    # 2. Persistent EMERGENCY_STOP activo -> no iniciar aunque exista ENABLED
    (ms_dir / "ENABLED").write_text("ok\n", encoding="utf-8")
    (ms_dir / "STOP").write_text("STOPPED\n", encoding="utf-8")
    auth_stop = wd.mirror_authorization()
    assert auth_stop == {"authorized": False, "state": "PERSISTENT_KILL_SWITCH"}
    r2 = wd.maybe_recover_mirror_sync(auth_stop)
    assert r2["state"] == "NOT_AUTHORIZED" and r2["started"] is False
    (ms_dir / "STOP").unlink()

    # 3. Temporary EMERGENCY_STOP activo -> no iniciar
    wd.MIRROR_TEMP_STOP.write_text("TEMP_STOP\n", encoding="utf-8")
    auth_tstop = wd.mirror_authorization()
    assert auth_tstop == {"authorized": False, "state": "TEMPORARY_KILL_SWITCH"}
    r3 = wd.maybe_recover_mirror_sync(auth_tstop)
    assert r3["state"] == "NOT_AUTHORIZED" and r3["started"] is False
    wd.MIRROR_TEMP_STOP.unlink()

    # 4. Parada administrativa explicita (STOPPED con timestamp, NO "Not started") -> respetar sin reiniciar
    sup_stdout = "edarsahub-mirror-sync STOPPED Nov 20 15:12 PM\n"
    auth_ok = wd.mirror_authorization()
    assert auth_ok["authorized"] is True
    r4 = wd.maybe_recover_mirror_sync(auth_ok)
    assert r4["state"] == "ADMINISTRATIVE_STOP_RESPECTED"
    assert r4["started"] is False

    # 5. Entorno Produccion -> bloqueado fail-closed
    sup_stdout = "edarsahub-mirror-sync STOPPED Not started\n"
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    r5 = wd.maybe_recover_mirror_sync(auth_ok)
    assert r5["state"] == "BLOCKED_PRODUCTION_ENV"
    assert r5["started"] is False

    assert recover_calls == []


def test_recovery_cooldown_and_max_attempts_prevent_restart_loops(tmp_path: Path, monkeypatch) -> None:
    _, app = _setup_isolated_preview_repo(tmp_path)
    (app / ".git/mirror-sync").mkdir(parents=True, exist_ok=True)
    (app / ".git/mirror-sync/ENABLED").write_text("ok\n", encoding="utf-8")

    wd = _load_watchdog(tmp_path, monkeypatch, app_dir=app)
    wd.MIRROR_RECOVERY_MAX_ATTEMPTS = 2
    wd.MIRROR_RECOVERY_COOLDOWN = 60

    def fake_run(args, cwd=None, timeout=60):
        if args[:2] == ["supervisorctl", "status"]:
            return subprocess.CompletedProcess(args, 3, stdout="edarsahub-mirror-sync STOPPED Not started\n")
        if args[:1] == ["/bin/bash"]:
            return subprocess.CompletedProcess(args, 90, stdout="MIRROR_SYNC_RECOVERY=START_UNCONFIRMED\n")
        return subprocess.run(args, cwd=str(cwd or app), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

    monkeypatch.setattr(wd, "run", fake_run)
    auth = {"authorized": True, "state": "AUTHORIZED"}

    f1 = wd.maybe_recover_mirror_sync(auth)
    assert f1["state"] == "RECOVERY_FAILED" and f1["attempts"] == 1

    # Inmediatamente entra en COOLDOWN (cero bucle de reinicio)
    cd = wd.maybe_recover_mirror_sync(auth)
    assert cd["state"] == "COOLDOWN" and cd["started"] is False

    # Al expirar cooldown, intenta 2da vez y al agotar max_attempts se detiene fail-closed
    st = wd._read_mirror_recovery_state()
    st["cooldown_until_epoch"] = 0.0
    wd._write_mirror_recovery_state(st)
    f2 = wd.maybe_recover_mirror_sync(auth)
    assert f2["state"] == "RECOVERY_FAILED" and f2["attempts"] == 2

    st2 = wd._read_mirror_recovery_state()
    st2["cooldown_until_epoch"] = 0.0
    wd._write_mirror_recovery_state(st2)
    ex = wd.maybe_recover_mirror_sync(auth)
    assert ex["state"] == "ATTEMPTS_EXHAUSTED" and ex["started"] is False


def test_mirror_sync_start_recover_authorized_real_shell_matrix(tmp_path: Path) -> None:
    _, app = _setup_isolated_preview_repo(tmp_path)
    ms_dir = app / ".git/mirror-sync"
    ms_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = tmp_path / "mirror_temp"
    temp_dir.mkdir()

    fake_bin = tmp_path / "fake_bin"
    fake_bin.mkdir()
    sup_state_file = tmp_path / "sup_state.txt"
    sup_log_file = tmp_path / "sup_calls.log"
    fake_sup = fake_bin / "supervisorctl"
    fake_sup.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$*" >> {str(sup_log_file)!r}\n'
        'if [ "$1" = "status" ]; then\n'
        f'  cat {str(sup_state_file)!r}\n'
        '  exit 0\n'
        'fi\n'
        'if [ "$1" = "start" ]; then\n'
        f'  echo "edarsahub-mirror-sync RUNNING pid 999, uptime 0:00:01" > {str(sup_state_file)!r}\n'
        '  echo "edarsahub-mirror-sync: started"\n'
        '  exit 0\n'
        'fi\n'
        'exit 1\n',
        encoding="utf-8",
    )
    os.chmod(fake_sup, 0o755)

    def run_start(*extra: str) -> subprocess.CompletedProcess:
        env = {
            **os.environ,
            "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}",
            "EDARSAHUB_APP": str(app),
            "EDARSAHUB_MIRROR_TEMP_DIR": str(temp_dir),
            "EDARSA_ENV": "PREVIEW",
        }
        return subprocess.run(
            ["/bin/bash", str(app / "tools/mirror_sync/mirror_sync_start.sh"), *extra],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            check=False,
        )

    # 1. ENABLED ausente -> exit 87
    sup_state_file.write_text("edarsahub-mirror-sync STOPPED Not started\n", encoding="utf-8")
    r_no_en = run_start("--recover-authorized")
    assert r_no_en.returncode == 87
    assert "MIRROR_SYNC_RECOVERY=BLOCKED_EXPLICIT_ENABLE_REQUIRED" in r_no_en.stdout
    assert not (ms_dir / "ENABLED").exists()

    # 2. STOP activo -> exit 86 y NO borra STOP
    (ms_dir / "ENABLED").write_text("ok\n", encoding="utf-8")
    (ms_dir / "STOP").write_text("STOPPED\n", encoding="utf-8")
    r_stop = run_start("--recover-authorized")
    assert r_stop.returncode == 86
    assert "MIRROR_SYNC_RECOVERY=BLOCKED_EMERGENCY_STOP" in r_stop.stdout
    assert (ms_dir / "STOP").exists()
    (ms_dir / "STOP").unlink()

    # 3. Parada administrativa explicita -> exit 88
    sup_state_file.write_text("edarsahub-mirror-sync STOPPED Nov 20 15:12 PM\n", encoding="utf-8")
    r_adm = run_start("--recover-authorized")
    assert r_adm.returncode == 88
    assert "MIRROR_SYNC_RECOVERY=BLOCKED_ADMINISTRATIVE_STOP" in r_adm.stdout

    # 4. Autorizado + STOPPED Not started + clean (con drift esperado .emergent/system_deps.txt) -> inicia una vez
    sup_state_file.write_text("edarsahub-mirror-sync STOPPED Not started\n", encoding="utf-8")
    r_ok = run_start("--recover-authorized")
    assert r_ok.returncode == 0, r_ok.stdout
    assert "MIRROR_SYNC_RECOVERY=STARTED" in r_ok.stdout
    assert "PRODUCTION_TOUCHED=NO" in r_ok.stdout

    # 5. Ya RUNNING -> idempotente (exit 0, sin nuevo supervisorctl start)
    calls_before = sup_log_file.read_text(encoding="utf-8").splitlines()
    r_idem = run_start("--recover-authorized")
    assert r_idem.returncode == 0, r_idem.stdout
    assert "MIRROR_SYNC_ALREADY_RUNNING=YES" in r_idem.stdout
    calls_after = sup_log_file.read_text(encoding="utf-8").splitlines()
    assert sum(1 for c in calls_after if c.startswith("start ")) == sum(1 for c in calls_before if c.startswith("start "))


def test_scripts_syntax_executable_bits_and_supervisor_contract() -> None:
    for sh in (MIRROR_START, MIRROR_STOP, SAFETY_GUARD):
        chk = subprocess.run(["bash", "-n", str(sh)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        assert chk.returncode == 0, f"bash -n fallo en {sh}: {chk.stdout}"
    assert stat.S_IMODE(MIRROR_START.stat().st_mode) == 0o755
    conf = MIRROR_CONF.read_text(encoding="utf-8")
    assert "autostart=false" in conf
    assert "autorestart=true" in conf
