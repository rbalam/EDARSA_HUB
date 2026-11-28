import React, { useCallback, useEffect, useState } from 'react';
import { AlertCircle, Bell, BookOpen, Building2, FileClock, FilePlus2, Link2, Loader2, RefreshCw, ShieldCheck, UserPlus, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import catalogoAmpliadoApi from '@/services/catalogoAmpliadoApi';

const emptyPersona = { nombre:'', apellido_paterno:'', apellido_materno:'', rfc:'', curp:'', nacionalidad:'' };
const emptyVinculo = { persona_id:'', tipo:'usuario_id', valor:'' };
const emptyDocumento = { tipo_documento_id:'', propietario_tipo:'EMPRESA', persona_id:'', persona_empresa_rol_id:'', titulo:'' };
const emptyVersion = { documento_id:'', nombre_archivo:'', storage_key:'', mime_type:'application/pdf', tamanio_bytes:'', sha256:'', fecha_emision:'', fecha_vencimiento:'', fecha_vencimiento_fuente:'CAPTURA' };
const emptyAlerta = { tipo_documento_id:'', usuario_objetivo_id:'', dias_antes:'30', canal:'APP' };

function message(error, fallback='No se pudo completar la operacion.') {
  const status = error?.response?.status;
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  if (status === 401) return 'Tu sesion no es valida o expiro.';
  if (status === 403) return 'No tienes permisos para Gobierno Corporativo.';
  if (status === 404) return 'No se encontro el registro solicitado.';
  if (status === 409) return 'El Catalogo Ampliado no esta activo para esta empresa.';
  if (status === 422) return 'Revisa los datos capturados.';
  return fallback;
}

const clean = value => value === '' ? null : value;
const intOrNull = value => value === '' ? null : Number(value);

export default function CatalogoAmpliadoDashboard() {
  const [empresaId,setEmpresaId]=useState('');
  const [dias,setDias]=useState('30');
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const [notice,setNotice]=useState('');
  const [config,setConfig]=useState(null);
  const [personas,setPersonas]=useState([]);
  const [tipos,setTipos]=useState([]);
  const [documentos,setDocumentos]=useState([]);
  const [vencimientos,setVencimientos]=useState([]);
  const [alertas,setAlertas]=useState([]);
  const [kardex,setKardex]=useState([]);
  const [persona,setPersona]=useState(emptyPersona);
  const [vinculo,setVinculo]=useState(emptyVinculo);
  const [documento,setDocumento]=useState(emptyDocumento);
  const [version,setVersion]=useState(emptyVersion);
  const [alerta,setAlerta]=useState(emptyAlerta);

  const empresa = Number(empresaId);
  const validEmpresa = Number.isInteger(empresa) && empresa > 0;

  const run = async (fn, success) => {
    setLoading(true); setError(''); setNotice('');
    try { const result = await fn(); if (success) setNotice(success); return result; }
    catch (e) { setError(message(e)); throw e; }
    finally { setLoading(false); }
  };

  const refresh = useCallback(async () => {
    if (!validEmpresa) return;
    setLoading(true); setError(''); setNotice('');
    try {
      const cfg = await catalogoAmpliadoApi.getConfiguracion(empresa);
      setConfig(cfg || null);
      if (cfg?.CatalogoLegalAmpliadoActivo) {
        const [p,t,d,v,a] = await Promise.all([
          catalogoAmpliadoApi.listPersonas(empresa), catalogoAmpliadoApi.listTiposDocumento(),
          catalogoAmpliadoApi.listDocumentos(empresa), catalogoAmpliadoApi.listVencimientos(empresa, Number(dias)||30),
          catalogoAmpliadoApi.listAlertas(empresa)
        ]);
        setPersonas(p || []); setTipos(t || []); setDocumentos(d || []); setVencimientos(v || []); setAlertas(a || []);
      } else { setPersonas([]); setTipos([]); setDocumentos([]); setVencimientos([]); setAlertas([]); }
    } catch(e) { setError(message(e)); } finally { setLoading(false); }
  }, [empresa, validEmpresa, dias]);

  useEffect(() => { setKardex([]); }, [empresaId]);

  const saveConfig = async active => {
    if (!validEmpresa) return setError('Captura un EmpresaID valido.');
    try {
      const result=await run(() => catalogoAmpliadoApi.updateConfiguracion(empresa,{ catalogo_legal_ampliado_activo:active,dias_alerta_default:Number(dias)||30 }),'Configuracion actualizada.');
      setConfig(result); if (active) await refresh();
    } catch(e) {}
  };

  const createPersona = async e => { e.preventDefault(); try { await run(() => catalogoAmpliadoApi.createPersona(Object.fromEntries(Object.entries(persona).map(([k,v])=>[k,clean(v)]))),'Persona creada.'); setPersona(emptyPersona); await refresh(); } catch(e) {} };
  const createVinculo = async e => { e.preventDefault(); const payload={ usuario_id:null,cliente_id:null,proveedor_id:null,contacto_cliente_id:null,contacto_proveedor_id:null,es_principal:true }; payload[vinculo.tipo]=Number(vinculo.valor); try { await run(() => catalogoAmpliadoApi.createVinculo(Number(vinculo.persona_id),payload),'Vinculo canonico creado.'); setVinculo(emptyVinculo); } catch(e) {} };
  const createDocumento = async e => { e.preventDefault(); const payload={ tipo_documento_id:Number(documento.tipo_documento_id),propietario_tipo:documento.propietario_tipo,persona_id:intOrNull(documento.persona_id),persona_empresa_rol_id:intOrNull(documento.persona_empresa_rol_id),titulo:documento.titulo }; try { await run(() => catalogoAmpliadoApi.createDocumento(empresa,payload),'Documento creado.'); setDocumento(emptyDocumento); await refresh(); } catch(e) {} };
  const createVersion = async e => { e.preventDefault(); const payload={ nombre_archivo:version.nombre_archivo,storage_key:version.storage_key,mime_type:clean(version.mime_type),tamanio_bytes:intOrNull(version.tamanio_bytes),sha256:version.sha256,fecha_emision:clean(version.fecha_emision),fecha_vencimiento:clean(version.fecha_vencimiento),fecha_vencimiento_fuente:clean(version.fecha_vencimiento_fuente),ocr_texto:null,ocr_metadata_json:null,ocr_confianza:null }; try { await run(() => catalogoAmpliadoApi.createVersion(Number(version.documento_id),payload),'Version agregada.'); setVersion(emptyVersion); await refresh(); } catch(e) {} };
  const createAlerta = async e => { e.preventDefault(); const payload={ tipo_documento_id:intOrNull(alerta.tipo_documento_id),usuario_objetivo_id:intOrNull(alerta.usuario_objetivo_id),dias_antes:Number(alerta.dias_antes),canal:alerta.canal }; try { await run(() => catalogoAmpliadoApi.createAlerta(empresa,payload),'Regla de alerta creada.'); setAlerta(emptyAlerta); await refresh(); } catch(e) {} };
  const loadKardex = async id => { try { const rows=await run(() => catalogoAmpliadoApi.getKardex(id)); setKardex(rows || []); } catch(e) {} };

  return <div className="p-6 space-y-6" data-testid="catalogo-ampliado-dashboard">
    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"><div className="flex items-center gap-3"><div className="rounded-xl bg-slate-900 p-2 text-white"><ShieldCheck className="h-6 w-6"/></div><div><h1 className="text-2xl font-semibold">Catalogo Ampliado</h1><p className="text-sm text-muted-foreground">Gobierno corporativo y cumplimiento. Las reglas y permisos se resuelven en backend.</p></div></div><div className="flex gap-2 items-end"><div><Label>EmpresaID</Label><Input className="w-32" type="number" min="1" value={empresaId} onChange={e=>setEmpresaId(e.target.value)}/></div><div><Label>Vencimientos</Label><Input className="w-24" type="number" min="0" max="3650" value={dias} onChange={e=>setDias(e.target.value)}/></div><Button onClick={refresh} disabled={!validEmpresa||loading}>{loading?<Loader2 className="h-4 w-4 animate-spin"/>:<RefreshCw className="h-4 w-4"/>}</Button></div></div>
    {error && <div className="rounded-lg bg-red-50 text-red-700 p-4 flex gap-2"><AlertCircle className="h-5 w-5 shrink-0"/>{error}</div>}
    {notice && <div className="rounded-lg bg-emerald-50 text-emerald-700 p-4">{notice}</div>}
    <Card><CardHeader><CardTitle className="flex gap-2 items-center"><Building2 className="h-5 w-5"/>Activacion por empresa</CardTitle><CardDescription>El backend decide si el dominio esta habilitado para la empresa seleccionada.</CardDescription></CardHeader><CardContent className="flex flex-wrap gap-3 items-center"><div className="text-sm">Estado: <b>{config?.CatalogoLegalAmpliadoActivo?'ACTIVO':'INACTIVO'}</b></div><Button onClick={()=>saveConfig(true)} disabled={!validEmpresa||loading}>Activar</Button><Button variant="outline" onClick={()=>saveConfig(false)} disabled={!validEmpresa||loading}>Desactivar</Button></CardContent></Card>
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <Card><CardHeader><CardTitle className="flex gap-2"><Users className="h-5 w-5"/>Personas</CardTitle><CardDescription>{personas.length} registros vinculados a la empresa.</CardDescription></CardHeader><CardContent className="space-y-4"><div className="max-h-56 overflow-auto divide-y">{personas.map(p=><div key={p.PersonaID} className="py-2 text-sm"><b>#{p.PersonaID}</b> {p.Nombre} {p.ApellidoPaterno||''} <span className="text-muted-foreground">{p.RFC||''}</span></div>)}</div><form onSubmit={createPersona} className="grid grid-cols-2 gap-2"><Input placeholder="Nombre" required value={persona.nombre} onChange={e=>setPersona({...persona,nombre:e.target.value})}/><Input placeholder="Apellido paterno" value={persona.apellido_paterno} onChange={e=>setPersona({...persona,apellido_paterno:e.target.value})}/><Input placeholder="RFC" value={persona.rfc} onChange={e=>setPersona({...persona,rfc:e.target.value})}/><Input placeholder="CURP" value={persona.curp} onChange={e=>setPersona({...persona,curp:e.target.value})}/><Button className="col-span-2" disabled={loading}><UserPlus className="h-4 w-4 mr-2"/>Crear persona</Button></form></CardContent></Card>
      <Card><CardHeader><CardTitle className="flex gap-2"><Link2 className="h-5 w-5"/>Vinculo canonico</CardTitle><CardDescription>Selecciona exactamente una llave canonica existente.</CardDescription></CardHeader><CardContent><form onSubmit={createVinculo} className="space-y-3"><Input type="number" min="1" placeholder="PersonaID" required value={vinculo.persona_id} onChange={e=>setVinculo({...vinculo,persona_id:e.target.value})}/><select className="w-full border rounded-md h-10 px-3" value={vinculo.tipo} onChange={e=>setVinculo({...vinculo,tipo:e.target.value})}><option value="usuario_id">UsuarioID</option><option value="cliente_id">ClienteID</option><option value="proveedor_id">ProveedorID</option><option value="contacto_cliente_id">ContactoClienteID</option><option value="contacto_proveedor_id">ContactoProveedorID</option></select><Input type="number" min="1" placeholder="ID canonico" required value={vinculo.valor} onChange={e=>setVinculo({...vinculo,valor:e.target.value})}/><Button disabled={loading}>Crear vinculo</Button></form></CardContent></Card>
      <Card className="xl:col-span-2"><CardHeader><CardTitle className="flex gap-2"><BookOpen className="h-5 w-5"/>Documentos</CardTitle><CardDescription>Listado servido por backend con su ultima version.</CardDescription></CardHeader><CardContent className="space-y-4"><div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="text-left border-b"><th className="py-2">ID</th><th>Titulo</th><th>Tipo</th><th>Version</th><th>Vence</th><th></th></tr></thead><tbody>{documentos.map(d=><tr key={d.DocumentoID} className="border-b"><td className="py-2">{d.DocumentoID}</td><td>{d.Titulo}</td><td>{d.TipoDocumentoNombre}</td><td>{d.NumeroVersion||'-'}</td><td>{d.FechaVencimiento||'-'}</td><td><Button size="sm" variant="ghost" onClick={()=>loadKardex(d.DocumentoID)}>Kardex</Button></td></tr>)}</tbody></table></div><form onSubmit={createDocumento} className="grid md:grid-cols-4 gap-2"><select className="border rounded-md h-10 px-3" required value={documento.tipo_documento_id} onChange={e=>setDocumento({...documento,tipo_documento_id:e.target.value})}><option value="">Tipo documento</option>{tipos.map(t=><option key={t.TipoDocumentoID} value={t.TipoDocumentoID}>{t.Nombre}</option>)}</select><select className="border rounded-md h-10 px-3" value={documento.propietario_tipo} onChange={e=>setDocumento({...documento,propietario_tipo:e.target.value})}><option>EMPRESA</option><option>PERSONA</option><option>RELACION</option></select><Input placeholder="PersonaID / relacion segun propietario" value={documento.propietario_tipo==='RELACION'?documento.persona_empresa_rol_id:documento.persona_id} onChange={e=>documento.propietario_tipo==='RELACION'?setDocumento({...documento,persona_empresa_rol_id:e.target.value}):setDocumento({...documento,persona_id:e.target.value})}/><Input placeholder="Titulo" required value={documento.titulo} onChange={e=>setDocumento({...documento,titulo:e.target.value})}/><Button className="md:col-span-4" disabled={loading}><FilePlus2 className="h-4 w-4 mr-2"/>Crear documento</Button></form></CardContent></Card>
      <Card><CardHeader><CardTitle>Nueva version</CardTitle><CardDescription>El numero de version y el kardex los controla backend.</CardDescription></CardHeader><CardContent><form onSubmit={createVersion} className="space-y-2"><Input type="number" min="1" placeholder="DocumentoID" required value={version.documento_id} onChange={e=>setVersion({...version,documento_id:e.target.value})}/><Input placeholder="Nombre archivo" required value={version.nombre_archivo} onChange={e=>setVersion({...version,nombre_archivo:e.target.value})}/><Input placeholder="Storage key" required value={version.storage_key} onChange={e=>setVersion({...version,storage_key:e.target.value})}/><Input placeholder="SHA256 (64 caracteres)" required value={version.sha256} onChange={e=>setVersion({...version,sha256:e.target.value})}/><div className="grid grid-cols-2 gap-2"><Input type="date" value={version.fecha_emision} onChange={e=>setVersion({...version,fecha_emision:e.target.value})}/><Input type="date" value={version.fecha_vencimiento} onChange={e=>setVersion({...version,fecha_vencimiento:e.target.value})}/></div><Button disabled={loading}>Agregar version</Button></form></CardContent></Card>
      <Card><CardHeader><CardTitle>Kardex</CardTitle><CardDescription>Historial inmutable devuelto por backend.</CardDescription></CardHeader><CardContent><div className="max-h-72 overflow-auto divide-y">{kardex.map(k=><div key={k.MovimientoID} className="py-2 text-sm"><b>{k.TipoMovimiento}</b><div className="text-muted-foreground">{String(k.FechaUTC||'')}</div></div>)}</div></CardContent></Card>
      <Card><CardHeader><CardTitle className="flex gap-2"><FileClock className="h-5 w-5"/>Vencimientos</CardTitle></CardHeader><CardContent><div className="divide-y">{vencimientos.map(v=><div key={v.DocumentoVersionID} className="py-2 text-sm"><b>{v.Titulo}</b><div>{v.FechaVencimiento} · {v.DiasRestantes} dias</div></div>)}</div></CardContent></Card>
      <Card><CardHeader><CardTitle className="flex gap-2"><Bell className="h-5 w-5"/>Alertas</CardTitle><CardDescription>La programacion y entrega no se calculan en React.</CardDescription></CardHeader><CardContent className="space-y-3"><div className="divide-y max-h-44 overflow-auto">{alertas.map(a=><div key={a.AlertaReglaID} className="py-2 text-sm">{a.DiasAntes} dias · {a.Canal}</div>)}</div><form onSubmit={createAlerta} className="grid grid-cols-2 gap-2"><Input type="number" placeholder="TipoDocumentoID opcional" value={alerta.tipo_documento_id} onChange={e=>setAlerta({...alerta,tipo_documento_id:e.target.value})}/><Input type="number" placeholder="UsuarioObjetivoID opcional" value={alerta.usuario_objetivo_id} onChange={e=>setAlerta({...alerta,usuario_objetivo_id:e.target.value})}/><Input type="number" min="0" max="3650" required value={alerta.dias_antes} onChange={e=>setAlerta({...alerta,dias_antes:e.target.value})}/><select className="border rounded-md h-10 px-3" value={alerta.canal} onChange={e=>setAlerta({...alerta,canal:e.target.value})}><option>TAREA</option><option>EMAIL</option><option>WHATSAPP</option><option>APP</option></select><Button className="col-span-2" disabled={loading}>Crear regla</Button></form></CardContent></Card>
    </div>
  </div>;
}
