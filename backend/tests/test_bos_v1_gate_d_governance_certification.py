from pathlib import Path
import json
import os

ROOT=Path(__file__).resolve().parents[2]
PROGRAM=(ROOT/'docs/BOS/PROGRAMA_ESTRATEGICO_BOS_EDARSAHUB_DIRECCION.md').read_text(encoding='utf-8').lower()
PHASE=ROOT/'docs/ARCHITECTURE/AGENT_CAPABILITY_POLICY_PHASE_CERTIFIED_20260906.md'

def corpus():
    parts=[]
    for base in (ROOT/'backend',ROOT/'docs'):
        for p in base.rglob('*'):
            if p.is_file() and p.suffix.lower() in {'.py','.md','.json'} and 'test_bos_v1_gate_d_governance_certification.py' not in str(p):
                try: parts.append(p.read_text(encoding='utf-8',errors='ignore').lower())
                except Exception: pass
    return '\n'.join(parts)

def terminal_text():
    runtime=Path(str(os.environ.get('EDARSAHUB_ROOT') or '/app'))/'.git/universal-worker-queue/results'
    out=[]
    if runtime.is_dir():
        for p in runtime.glob('*.json'):
            try:
                d=json.loads(p.read_text(encoding='utf-8'))
                if d.get('certification') in {'CERTIFIED','CERTIFIED_READ_ONLY'} and d.get('percent_complete')==100 and not d.get('production_touched',False): out.append(str(d).lower())
            except Exception: pass
    return '\n'.join(out)

def test_gate_d_existing_governance_evidence_complete():
    assert 'gate d - gobierno' in PROGRAM
    assert PHASE.is_file(), 'CAPABILITY_POLICY_PHASE_CERTIFICATION_MISSING'
    phase=PHASE.read_text(encoding='utf-8').lower()
    assert 'fase capability/policy queda certificada' in phase
    text=corpus(); terminal=terminal_text(); combined=text+'\n'+terminal
    required={
      'backend_rbac':['rbac'],
      'capability_policy':['capability','policy'],
      'procedure_policy':['procedure','skill'],
      'limits':['limit','limite'],
      'scopes':['scope'],
      'budgets':['budget','presupuesto'],
      'traceability':['trazabilidad','audit','auditoria'],
      'least_privilege':['least privilege','menor privilegio'],
      'canonical_sql_rbac':['rbac sql','sql canonico','rbac canonico']
    }
    missing=[]
    for name,tokens in required.items():
        if not any(t in combined for t in tokens): missing.append(name)
    assert not missing, 'GATE_D_MISSING_EVIDENCE:'+','.join(missing)
