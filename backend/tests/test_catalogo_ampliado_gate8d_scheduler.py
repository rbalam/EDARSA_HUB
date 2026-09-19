from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/'backend/core/scheduler/config.py'
MAN=ROOT/'backend/core/scheduler/scheduler_manager.py'
JOB=ROOT/'backend/core/scheduler/jobs/catalogo_ampliado_alertas_job.py'
SERVICE=ROOT/'backend/modules/catalogo_ampliado/alert_service.py'


def test_uses_canonical_scheduler_and_config():
    cfg=CFG.read_text(encoding='utf-8')
    man=MAN.read_text(encoding='utf-8')
    assert 'SCHEDULER_CATALOGO_AMPLIADO_ALERTAS_ENABLED' in cfg
    assert 'SCHEDULER_CATALOGO_AMPLIADO_ALERTAS_INTERVAL_SECONDS' in cfg
    assert '"catalogo_ampliado_alertas": JobConfig' in cfg
    assert 'self._scheduler.add_job' in man
    assert 'id="catalogo_ampliado_alertas"' in man
    assert 'replace_existing=True' in man
    assert 'max_instances=1' in man
    assert 'get_lock_manager' in man and 'get_job_logger' in man


def test_scheduler_calls_catalogo_service_and_external_delivery_is_delegated():
    job=JOB.read_text(encoding='utf-8')
    svc=SERVICE.read_text(encoding='utf-8')
    assert 'alert_service.planificar_alertas' in job
    assert 'alert_service.despachar_alertas' in job
    assert 'dispatch_external_alert' in svc
    assert 'send_message' not in svc


def test_no_parallel_scheduler_or_schema():
    joined='\n'.join([CFG.read_text(encoding='utf-8'),MAN.read_text(encoding='utf-8'),JOB.read_text(encoding='utf-8')]).lower()
    assert 'create table' not in joined
    assert 'asyncioscheduler(' in MAN.read_text(encoding='utf-8').lower()
    assert 'production' not in JOB.read_text(encoding='utf-8').lower()
