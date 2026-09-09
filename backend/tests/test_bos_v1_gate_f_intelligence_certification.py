from pathlib import Path
import json
import os

ROOT=Path(__file__).resolve().parents[2]
PROGRAM=(ROOT/'docs/BOS/PROGRAMA_ESTRATEGICO_BOS_EDARSAHUB_DIRECCION.md').read_text(encoding='utf-8').lower()

def corpus():
    parts=[]
    for base in (ROOT/'backend',ROOT/'docs'):
        for p in base.rglob('*'):
            if p.is_file() and p.suffix.lower() in {'.py','.md','.json'} and 'test_bos_v1_gate_f_intelligence_certification.py' not in str(p):
                try: parts.append(p.read_text(encoding='utf-8',errors='ignore').lower())
                except Exception: pass
    return '\n'.join(parts)

def certified_terminal_text():
    runtime=Path(str(os.environ.get('EDARSAHUB_ROOT') or '/app'))/'.git/universal-worker-queue/results'
    out=[]
    if runtime.is_dir():
        for p in runtime.glob('*.json'):
            try:
                d=json.loads(p.read_text(encoding='utf-8'))
                if d.get('certification') in {'CERTIFIED','CERTIFIED_READ_ONLY'} and d.get('percent_complete')==100 and not d.get('production_touched',False): out.append(str(d).lower())
            except Exception: pass
    return '\n'.join(out)

def test_gate_f_existing_intelligence_evidence_complete():
    assert 'gate f - inteligencia' in PROGRAM
    text=corpus()+'\n'+certified_terminal_text()
    required={
      'anomalies':['anomalia','anomaly'],
      'trends':['tendencia','trend'],
      'forecast':['forecast','proyeccion','predic'],
      'opportunities':['oportunidad','opportunity'],
      'risks':['riesgo','risk'],
      'recommendations':['recomend','recommendation'],
      'prices':['precio','price'],
      'menus':['menu'],
      'promotions':['promocion','promotion'],
      'reviews_reputation':['resena','review','reputacion','reputation'],
      'reservations':['reserva','reservation'],
      'benchmarking':['benchmark']
    }
    missing=[]
    for name,tokens in required.items():
        if not any(t in text for t in tokens): missing.append(name)
    assert not missing, 'GATE_F_MISSING_EVIDENCE:'+','.join(missing)
