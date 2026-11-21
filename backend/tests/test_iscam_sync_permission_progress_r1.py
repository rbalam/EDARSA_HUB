from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / 'frontend' / 'src' / 'portal-inteligencia' / 'pages' / 'ReportesISCAMPage.jsx'


def _source():
    return FRONTEND.read_text(encoding='utf-8')


def test_sync_button_uses_canonical_effective_permission():
    text = _source()
    assert "'/auth/me/effective-permissions'" in text
    assert "'SCHEDULER_ADMIN'" in text
    assert 'const [canSynchronize, setCanSynchronize] = useState(false);' in text
    assert '!syncPermissionLoading && canSynchronize && (freshness?.stale || freshness?.detail_stale)' in text
    assert 'if (!canSynchronize || !(headerGap || detailGap)' in text


def test_sync_progress_counts_only_successful_real_days():
    text = _source()
    assert 'const [syncProgress, setSyncProgress] = useState({ completed: 0, total: 0 });' in text
    assert 'Días procesados ${syncProgress.processed ?? syncProgress.completed} de ${syncProgress.total}' in text
    assert 'Sincronizados ${syncProgress.completed}' in text
    assert 'Fallidos ${syncProgress.failed || 0}' in text
    assert 'freshness?.detail_problem_dates || []' in text
    assert 'freshness?.missing_closed_dates || []' in text
    assert 'syncDates.map((fecha) => [fecha, fecha])' in text
    assert 'setSyncProgress({ completed: 0, total: chunks.length });' in text

    real_pos = text.index("const real = await apiPost('/admin/scheduler/resync/execute'")
    real_ok_pos = text.index('if (real.estado !== ESTADO.OK || real.data?.success !== true)', real_pos)
    increment_pos = text.index('setSyncProgress((prev) => ({ ...prev, completed: prev.completed + 1 }));', real_ok_pos)
    assert real_pos < real_ok_pos < increment_pos
