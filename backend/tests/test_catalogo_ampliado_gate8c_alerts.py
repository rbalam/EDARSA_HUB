from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT/'backend/modules/catalogo_ampliado/repository.py'
SERVICE=ROOT/'backend/modules/catalogo_ampliado/alert_service.py'
ROUTES=ROOT/'backend/modules/catalogo_ampliado/routes.py'


def test_planner_is_sql_idempotent_and_uses_existing_event_unique_shape():
    t=REPO.read_text(encoding='utf-8')
    assert 'def plan_alerta_eventos' in t
    assert "v.EstadoRevision='VALIDADO'" in t
    assert 'v.NumeroVersion=(SELECT MAX' in t
    assert 'NOT EXISTS(SELECT 1 FROM dbo.Gobierno_AlertaEvento' in t
    assert 'DocumentoVersionID=v.DocumentoVersionID' in t
    assert 'AlertaReglaID=r.AlertaReglaID' in t
    assert 'FechaObjetivo=v.FechaVencimiento' in t


def test_dispatcher_reuses_sistema_tareas_and_delegates_external_delivery():
    r=REPO.read_text(encoding='utf-8')
    s=SERVICE.read_text(encoding='utf-8')
    assert 'INSERT INTO dbo.Sistema_Tareas' in r
    assert "Modulo='CATALOGO_AMPLIADO'" in r
    assert "EntidadTipo='GOBIERNO_ALERTA_EVENTO'" in r
    assert 'NotificationDispatcher' not in s
    assert 'send_message' not in s
    assert 'dispatch_external_alert' in s


def test_no_parallel_schema_or_scheduler_and_admin_events_route_is_rbac_guarded():
    text='\n'.join([REPO.read_text(encoding='utf-8'),SERVICE.read_text(encoding='utf-8'),ROUTES.read_text(encoding='utf-8')]).lower()
    assert 'create table' not in text
    assert 'scheduler' not in SERVICE.read_text(encoding='utf-8').lower()
    routes=ROUTES.read_text(encoding='utf-8')
    assert "@router.get('/empresas/{empresa_id}/alertas/eventos')" in routes
    assert 'Depends(_gobierno_admin)' in routes


def test_service_dispatches_task_and_delegates_external(monkeypatch):
    from modules.catalogo_ampliado import alert_service
    class DummyRepo:
        def list_due_alert_events(self, limit):
            return [
                {'AlertaEventoID':1,'Canal':'TAREA'},
                {'AlertaEventoID':2,'Canal':'EMAIL'},
                {'AlertaEventoID':3,'Canal':'WHATSAPP'},
                {'AlertaEventoID':4,'Canal':'APP'},
            ]
        def ensure_canonical_task_for_alert(self, event_id):
            assert event_id==1
            return {'TareaSistemaID':99}
    monkeypatch.setattr(alert_service,'repo',DummyRepo())
    monkeypatch.setattr(alert_service,'dispatch_external_alert',lambda e:{'alerta_evento_id':e['AlertaEventoID'],'canal':e['Canal'],'status':'DELEGATED'})
    out=alert_service.despachar_alertas()
    assert out['processed']==4
    assert out['items'][0]['reference']=='99'
    assert all(x['status']=='DELEGATED' for x in out['items'][1:])
