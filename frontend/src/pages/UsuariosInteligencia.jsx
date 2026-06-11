/**
 * Administración de Usuarios del Portal de Inteligencia Comercial (EXTERNOS).
 * Se renderiza como pestaña dentro de la pantalla de Proveedores.
 * CRUD contra /api/portal-intel/admin/* (protegido por admin del CRM). Sin mocks.
 */
import React, { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Plus, RefreshCw, Trash2, Pencil, X, Check, Power, Loader2, KeyRound, BarChart3,
} from 'lucide-react';

const emptyForm = { id: null, email: '', nombre: '', password: '', unidades: [], activo: true };

export default function UsuariosInteligencia() {
  const [usuarios, setUsuarios] = useState([]);
  const [unidades, setUnidades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [u, un] = await Promise.all([
        api.get('/portal-intel/admin/usuarios'),
        api.get('/inteligencia/unidades'),
      ]);
      setUsuarios(u.data?.usuarios || []);
      setUnidades(un.data?.unidades || []);
    } catch (e) {
      setUsuarios([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openNew = () => { setForm(emptyForm); setError(''); setShowModal(true); };
  const openEdit = (u) => {
    setForm({ id: u.id, email: u.email, nombre: u.nombre, password: '', unidades: u.unidades || [], activo: u.activo });
    setError('');
    setShowModal(true);
  };

  const toggleUnidad = (codigo) => {
    setForm((f) => ({
      ...f,
      unidades: f.unidades.includes(codigo) ? f.unidades.filter((c) => c !== codigo) : [...f.unidades, codigo],
    }));
  };

  const save = async () => {
    setError('');
    if (!form.id && (!form.email || !form.password)) { setError('Email y contraseña son obligatorios'); return; }
    if (form.unidades.length === 0) { setError('Asigna al menos una unidad de negocio'); return; }
    setSaving(true);
    try {
      if (form.id) {
        const payload = { nombre: form.nombre, unidades: form.unidades, activo: form.activo };
        if (form.password) payload.password = form.password;
        await api.put(`/portal-intel/admin/usuarios/${form.id}`, payload);
      } else {
        await api.post('/portal-intel/admin/usuarios', {
          email: form.email, password: form.password, nombre: form.nombre, unidades: form.unidades,
        });
      }
      setShowModal(false);
      load();
    } catch (e) {
      setError(e.response?.data?.detail || 'No se pudo guardar');
    } finally {
      setSaving(false);
    }
  };

  const toggleActivo = async (u) => {
    await api.put(`/portal-intel/admin/usuarios/${u.id}`, { activo: !u.activo });
    load();
  };

  const eliminar = async (u) => {
    if (!window.confirm(`¿Eliminar al usuario ${u.email}?`)) return;
    await api.delete(`/portal-intel/admin/usuarios/${u.id}`);
    load();
  };

  const nombreUnidad = (codigo) => unidades.find((x) => x.codigo === codigo)?.nombre || codigo;

  if (loading) {
    return <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-zinc-400" /></div>;
  }

  return (
    <div className="space-y-4" data-testid="usuarios-inteligencia">
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-500">
          Usuarios externos con acceso de consulta al Portal de Inteligencia Comercial, acotados a las unidades que asignes.
        </p>
        <div className="flex gap-2">
          <Button variant="outline" onClick={load} className="flex items-center gap-2"><RefreshCw className="h-4 w-4" /> Actualizar</Button>
          <Button onClick={openNew} data-testid="btn-nuevo-usuario-intel" className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700">
            <Plus className="h-4 w-4" /> Nuevo usuario
          </Button>
        </div>
      </div>

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full">
          <thead className="bg-zinc-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Usuario</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Unidades asignadas</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Estado</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Último acceso</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {usuarios.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-10 text-center text-zinc-400">Aún no hay usuarios. Crea el primero con "Nuevo usuario".</td></tr>
            ) : usuarios.map((u) => (
              <tr key={u.id} data-testid={`usuario-intel-${u.email}`}>
                <td className="px-4 py-3">
                  <div className="font-medium text-zinc-900">{u.nombre || '—'}</div>
                  <div className="text-xs text-zinc-500">{u.email}</div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {(u.unidades || []).map((c) => (
                      <span key={c} className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded text-xs">{nombreUnidad(c)}</span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs ${u.activo ? 'bg-green-100 text-green-700' : 'bg-zinc-200 text-zinc-600'}`}>
                    {u.activo ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-zinc-500">
                  {u.ultimo_acceso ? new Date(u.ultimo_acceso).toLocaleString('es-MX') : 'Nunca'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    <Button size="sm" variant="outline" onClick={() => openEdit(u)} title="Editar" data-testid={`edit-${u.email}`}><Pencil className="h-4 w-4" /></Button>
                    <Button size="sm" variant="outline" onClick={() => toggleActivo(u)} title={u.activo ? 'Desactivar' : 'Activar'}><Power className="h-4 w-4" /></Button>
                    <Button size="sm" variant="destructive" onClick={() => eliminar(u)} title="Eliminar"><Trash2 className="h-4 w-4" /></Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-auto" data-testid="usuario-intel-modal">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2"><BarChart3 className="h-5 w-5 text-emerald-600" /> {form.id ? 'Editar usuario' : 'Nuevo usuario de Inteligencia'}</h2>
              <Button variant="ghost" size="sm" onClick={() => setShowModal(false)}><X className="h-4 w-4" /></Button>
            </div>
            <div className="p-6 space-y-4">
              {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">{error}</div>}
              <div>
                <label className="text-xs text-zinc-500 uppercase">Email</label>
                <Input type="email" value={form.email} disabled={!!form.id} data-testid="intel-form-email"
                  onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="socio@empresa.com" />
              </div>
              <div>
                <label className="text-xs text-zinc-500 uppercase">Nombre</label>
                <Input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} placeholder="Nombre del socio/usuario" />
              </div>
              <div>
                <label className="text-xs text-zinc-500 uppercase flex items-center gap-1"><KeyRound className="h-3 w-3" /> {form.id ? 'Nueva contraseña (opcional)' : 'Contraseña'}</label>
                <Input type="password" value={form.password} data-testid="intel-form-password"
                  onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder={form.id ? 'Dejar vacío para no cambiar' : 'Mínimo 6 caracteres'} />
              </div>
              <div>
                <label className="text-xs text-zinc-500 uppercase mb-1 block">Unidades asignadas</label>
                <div className="grid grid-cols-2 gap-2 border rounded-lg p-3 max-h-48 overflow-auto">
                  {unidades.map((un) => (
                    <label key={un.codigo} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input type="checkbox" checked={form.unidades.includes(un.codigo)}
                        onChange={() => toggleUnidad(un.codigo)} data-testid={`unidad-${un.codigo}`} />
                      {un.nombre || un.codigo}
                    </label>
                  ))}
                </div>
              </div>
              {form.id && (
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={form.activo} onChange={(e) => setForm({ ...form, activo: e.target.checked })} />
                  Cuenta activa
                </label>
              )}
            </div>
            <div className="sticky bottom-0 bg-white border-t px-6 py-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowModal(false)}>Cancelar</Button>
              <Button onClick={save} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700 flex items-center gap-2" data-testid="intel-form-save">
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />} Guardar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
