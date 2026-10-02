import { useCallback, useEffect, useState } from 'react';
import api from '../../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { CheckCircle2, Clock3, Loader2, Play, RefreshCw, RotateCcw, Server } from 'lucide-react';

const ACTIVE = new Set(['JOB_QUEUED','JOB_RUNNING','JOB_WAITING_LOCK']);
const RESUMABLE = new Set(['JOB_PARTIAL','JOB_FAILED','JOB_STALE']);

export default function ComercialRangeResyncCard({ options, onFinished }) {
  const [units,setUnits]=useState([]);
  const [start,setStart]=useState('');
  const [end,setEnd]=useState('');
  const [reason,setReason]=useState('Re-sincronización por rango para refrescar datos históricos');
  const [job,setJob]=useState(null);
  const [loading,setLoading]=useState(false);
  const available = options?.unidades || [];

  const loadActive = useCallback(async()=>{
    try {
      const r=await api.get('/admin/scheduler/resync/comercial-range/active');
      if(r.data?.active) setJob(r.data);
    } catch(e) { console.error(e); }
  },[]);
  useEffect(()=>{loadActive();},[loadActive]);
  useEffect(()=>{
    if(!job?.job_id || !ACTIVE.has(job.status)) return undefined;
    const timer=setInterval(async()=>{
      try {
        const r=await api.get(`/admin/scheduler/resync/comercial-range/jobs/${job.job_id}`);
        setJob(r.data);
        if(!ACTIVE.has(r.data?.status)) onFinished?.();
      } catch(e){ console.error(e); }
    },4000);
    return ()=>clearInterval(timer);
  },[job?.job_id,job?.status,onFinished]);

  const toggle=(id)=>setUnits(p=>p.includes(id)?p.filter(x=>x!==id):[...p,id]);
  const all=available.length>0 && available.every(u=>units.includes(u.id));
  const valid=units.length>0 && start && end && start<=end && reason.trim().length>=10 && !ACTIVE.has(job?.status);

  const startJob=async()=>{
    setLoading(true);
    try{
      const r=await api.post('/admin/scheduler/resync/comercial-range/jobs',{
        unidades:units,fecha_inicio:start,fecha_fin:end,motivo:reason.trim()
      });
      setJob(r.data);
    }catch(e){alert(e.response?.data?.detail||e.message);}
    finally{setLoading(false);}
  };

  const resume=async()=>{
    setLoading(true);
    try{
      const r=await api.post(`/admin/scheduler/resync/comercial-range/jobs/${job.job_id}/resume`);
      setJob(r.data);
    }catch(e){alert(e.response?.data?.detail||e.message);}
    finally{setLoading(false);}
  };

  const pct=Number(job?.percent_complete||0);
  return <Card data-testid="comercial-range-resync-card" className="border-sky-200">
    <CardHeader>
      <CardTitle className="flex items-center gap-2"><RefreshCw className="w-5 h-5"/> Re-sincronización Comercial por rango</CardTitle>
      <CardDescription>
        Elige una o varias sucursales y fechas. El proceso vuelve a leer el origen y refresca registros existentes,
        útil cuando se agregan campos como mesa, referencia, vendedor o descuentos.
      </CardDescription>
    </CardHeader>
    <CardContent className="space-y-5">
      <Alert><Clock3 className="w-4 h-4"/><AlertTitle>Proceso persistente</AlertTitle><AlertDescription>
        Puede cerrarse la pantalla; el servidor continúa hasta terminar. Usa el lock canónico de Ventas Cerradas y no toca ventas abiertas.
      </AlertDescription></Alert>

      <div className="space-y-2">
        <div className="flex items-center justify-between"><Label>Sucursales</Label>
          <Button type="button" variant="outline" size="sm" onClick={()=>setUnits(all?[]:available.map(u=>u.id))}>
            {all?'Quitar todas':'Seleccionar todas'}
          </Button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {available.map(u=><label key={u.id} className="flex items-center gap-2 rounded-md border p-2 text-sm cursor-pointer">
            <Checkbox checked={units.includes(u.id)} onCheckedChange={()=>toggle(u.id)}/>
            <Server className="w-4 h-4 text-zinc-500"/><span>{u.nombre}</span>
            <Badge variant="outline" className="ml-auto text-[10px]">{u.sistema}</Badge>
          </label>)}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2"><Label>Fecha inicio</Label><Input type="date" value={start} onChange={e=>setStart(e.target.value)}/></div>
        <div className="space-y-2"><Label>Fecha fin</Label><Input type="date" value={end} onChange={e=>setEnd(e.target.value)}/></div>
      </div>
      <div className="space-y-2"><Label>Motivo</Label><Textarea value={reason} onChange={e=>setReason(e.target.value)} rows={2}/></div>

      <div className="flex items-center gap-3">
        <Button onClick={startJob} disabled={!valid||loading}>
          {loading?<Loader2 className="w-4 h-4 mr-2 animate-spin"/>:<Play className="w-4 h-4 mr-2"/>}
          Iniciar re-sincronización
        </Button>
        {job?.force_refresh_existing && <Badge variant="secondary">Actualiza existentes</Badge>}
      </div>

      {job&&<div className="rounded-lg border p-4 space-y-4" data-testid="range-progress">
        <div className="flex justify-between text-sm"><strong>Avance general</strong><span>{pct.toFixed(1)}%</span></div>
        <div className="h-3 rounded-full bg-zinc-200 overflow-hidden"><div className="h-full bg-sky-600" style={{width:`${Math.min(100,Math.max(0,pct))}%`}}/></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
          <div><strong>Rango:</strong> {job.fecha_inicio} → {job.fecha_fin}</div>
          <div><strong>Bloque actual:</strong> {job.current_block||'-'}</div>
          <div><strong>Sucursal actual:</strong> {job.current_unit||'-'}</div>
        </div>
        <p className="text-sm text-zinc-600">{job.message}</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {(job.units||[]).map(unit=>{const p=job.unit_progress?.[unit]||{};return <div key={unit} className="flex justify-between rounded-md border px-3 py-2 text-sm">
            <span className="font-medium">{unit}</span><span>{p.pass||0}/{p.total||0} OK{(p.pending_recovery||0)>0?` · ${p.pending_recovery} pendiente(s)`:''}</span>
          </div>})}
        </div>
        {job.status==='JOB_SUCCESS'&&<div className="flex items-center gap-2 text-emerald-700 text-sm"><CheckCircle2 className="w-4 h-4"/>Rango completado.</div>}
        {RESUMABLE.has(job.status)&&<Button variant="outline" onClick={resume} disabled={loading}><RotateCcw className="w-4 h-4 mr-2"/>Reanudar pendientes</Button>}
      </div>}
    </CardContent>
  </Card>;
}
