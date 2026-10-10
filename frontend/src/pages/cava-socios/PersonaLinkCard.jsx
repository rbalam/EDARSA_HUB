/**
 * EDARSA HUB - Cava de Socios / Identidad BOS
 * Vinculación explícita de membresía Cava con Gobierno_Persona.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Link2, Loader2, Search, ShieldCheck, Unlink, UserPlus, UserRoundCheck } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

const EMPTY_PERSONA = {
  nombre: '',
  apellido_paterno: '',
  apellido_materno: '',
  rfc: '',
  curp: '',
  fecha_nacimiento: '',
  nacionalidad: '',
};

export default function PersonaLinkCard({ socioId, unidadNegocioPk, onChanged }) {
  const [link, setLink] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showExisting, setShowExisting] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState('');
  const [personas, setPersonas] = useState([]);
  const [searching, setSearching] = useState(false);
  const [personaForm, setPersonaForm] = useState(EMPTY_PERSONA);

  const scopeQuery = unidadNegocioPk
    ? `?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`
    : '';

  const fetchLink = useCallback(async () => {
    if (!socioId || !unidadNegocioPk) return;
    setLoading(true);
    try {
      const response = await api.get(
        `/cava-socios/socios/${socioId}/persona-link${scopeQuery}`
      );
      setLink(response.data);
    } catch (err) {
      setLink(null);
      if (err?.response?.status !== 404) {
        console.error('Error cargando vínculo BOS:', err);
      }
    } finally {
      setLoading(false);
    }
  }, [socioId, unidadNegocioPk, scopeQuery]);

  useEffect(() => {
    fetchLink();
  }, [fetchLink]);

  const buscarPersonas = async () => {
    setSearching(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.set('search', search.trim());
      params.set('limit', '50');
      const response = await api.get(`/cava-socios/personas-canonicas?${params.toString()}`);
      setPersonas(response.data?.personas || []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'No se pudo consultar Personas BOS');
    } finally {
      setSearching(false);
    }
  };

  const vincularExistente = async (personaId) => {
    setSaving(true);
    try {
      await api.post(
        `/cava-socios/socios/${socioId}/persona-link${scopeQuery}`,
        { persona_id: personaId }
      );
      toast.success('Persona BOS vinculada correctamente');
      setShowExisting(false);
      setSearch('');
      setPersonas([]);
      await fetchLink();
      await onChanged?.();
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'No se pudo vincular la Persona');
    } finally {
      setSaving(false);
    }
  };

  const crearPersona = async () => {
    if (!personaForm.nombre.trim()) {
      toast.error('El nombre es requerido');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...personaForm,
        nombre: personaForm.nombre.trim(),
        apellido_paterno: personaForm.apellido_paterno.trim() || null,
        apellido_materno: personaForm.apellido_materno.trim() || null,
        rfc: personaForm.rfc.trim() || null,
        curp: personaForm.curp.trim() || null,
        fecha_nacimiento: personaForm.fecha_nacimiento || null,
        nacionalidad: personaForm.nacionalidad.trim() || null,
      };
      await api.post(
        `/cava-socios/socios/${socioId}/persona-link/crear-persona${scopeQuery}`,
        payload
      );
      toast.success('Persona BOS creada y vinculada');
      setShowCreate(false);
      setPersonaForm(EMPTY_PERSONA);
      await fetchLink();
      await onChanged?.();
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'No se pudo crear/vincular la Persona');
    } finally {
      setSaving(false);
    }
  };

  const desvincular = async () => {
    if (!window.confirm(
      'Se quitará únicamente el vínculo de esta membresía con la Persona BOS. La Persona y sus vínculos canónicos no se eliminarán. ¿Continuar?'
    )) return;

    setSaving(true);
    try {
      await api.delete(
        `/cava-socios/socios/${socioId}/persona-link${scopeQuery}`
      );
      toast.success('Membresía desvinculada de la Persona BOS');
      await fetchLink();
      await onChanged?.();
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'No se pudo desvincular la Persona');
    } finally {
      setSaving(false);
    }
  };

  const persona = link?.persona;
  const linked = Boolean(link?.persona_id);

  return (
    <>
      <Card data-testid="persona-link-card">
        <CardHeader className="pb-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-indigo-600" />
                Identidad BOS
              </CardTitle>
              <CardDescription>
                La membresía conserva su SocioID; esta relación conecta al socio con la Persona canónica de EDARSAHUB.
              </CardDescription>
            </div>
            <span
              className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                linked
                  ? 'bg-green-100 text-green-800'
                  : 'bg-amber-100 text-amber-800'
              }`}
            >
              {linked ? 'Vinculada' : 'Pendiente de vincular'}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Consultando identidad...
            </div>
          ) : linked ? (
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="space-y-1 text-sm">
                <div className="font-medium">
                  {[persona?.nombre, persona?.apellido_paterno, persona?.apellido_materno]
                    .filter(Boolean)
                    .join(' ') || `Persona #${link.persona_id}`}
                </div>
                <div className="text-muted-foreground">
                  PersonaID: {link.persona_id}
                  {persona?.rfc ? ` · RFC: ${persona.rfc}` : ''}
                  {persona?.curp ? ` · CURP: ${persona.curp}` : ''}
                </div>
                {Array.isArray(link?.vinculos) && link.vinculos.length > 0 && (
                  <div className="text-xs text-muted-foreground">
                    {link.vinculos.length} vínculo(s) canónico(s) activo(s)
                  </div>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={desvincular}
                disabled={saving}
                data-testid="persona-unlink-button"
              >
                {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Unlink className="h-4 w-4 mr-2" />}
                Desvincular membresía
              </Button>
            </div>
          ) : (
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="text-sm text-muted-foreground">
                Selecciona una Persona existente o crea una nueva de forma explícita. No se hacen coincidencias automáticas por nombre, email o teléfono.
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowExisting(true)}
                  data-testid="persona-link-existing-button"
                >
                  <Link2 className="h-4 w-4 mr-2" />
                  Vincular existente
                </Button>
                <Button
                  size="sm"
                  onClick={() => setShowCreate(true)}
                  data-testid="persona-create-link-button"
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  Crear Persona
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={showExisting} onOpenChange={setShowExisting}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Vincular Persona BOS existente</DialogTitle>
            <DialogDescription>
              Busca y selecciona manualmente la identidad correcta. La selección es explícita y auditable.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Nombre, apellido, RFC o CURP"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && buscarPersonas()}
                />
              </div>
              <Button onClick={buscarPersonas} disabled={searching}>
                {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Buscar'}
              </Button>
            </div>

            <div className="max-h-72 overflow-y-auto rounded-md border">
              {personas.length === 0 ? (
                <div className="p-6 text-center text-sm text-muted-foreground">
                  Realiza una búsqueda para consultar Personas BOS.
                </div>
              ) : (
                personas.map((item) => (
                  <div
                    key={item.PersonaID}
                    className="flex items-center justify-between gap-3 border-b p-3 last:border-b-0"
                  >
                    <div className="min-w-0">
                      <div className="font-medium text-sm">
                        {[item.Nombre, item.ApellidoPaterno, item.ApellidoMaterno]
                          .filter(Boolean)
                          .join(' ')}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        PersonaID {item.PersonaID}
                        {item.RFC ? ` · RFC ${item.RFC}` : ''}
                        {item.CURP ? ` · CURP ${item.CURP}` : ''}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => vincularExistente(item.PersonaID)}
                      disabled={saving}
                    >
                      <UserRoundCheck className="h-4 w-4 mr-2" />
                      Seleccionar
                    </Button>
                  </div>
                ))
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowExisting(false)}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Crear Persona BOS</DialogTitle>
            <DialogDescription>
              Crea la identidad solo cuando se haya confirmado que no existe. RFC y CURP se validan contra duplicados en backend.
            </DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2 md:col-span-2">
              <Label>Nombre *</Label>
              <Input
                value={personaForm.nombre}
                onChange={(e) => setPersonaForm((f) => ({ ...f, nombre: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Apellido paterno</Label>
              <Input
                value={personaForm.apellido_paterno}
                onChange={(e) => setPersonaForm((f) => ({ ...f, apellido_paterno: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Apellido materno</Label>
              <Input
                value={personaForm.apellido_materno}
                onChange={(e) => setPersonaForm((f) => ({ ...f, apellido_materno: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>RFC</Label>
              <Input
                value={personaForm.rfc}
                onChange={(e) => setPersonaForm((f) => ({ ...f, rfc: e.target.value.toUpperCase() }))}
              />
            </div>
            <div className="space-y-2">
              <Label>CURP</Label>
              <Input
                value={personaForm.curp}
                onChange={(e) => setPersonaForm((f) => ({ ...f, curp: e.target.value.toUpperCase() }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Fecha de nacimiento</Label>
              <Input
                type="date"
                value={personaForm.fecha_nacimiento}
                onChange={(e) => setPersonaForm((f) => ({ ...f, fecha_nacimiento: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Nacionalidad</Label>
              <Input
                value={personaForm.nacionalidad}
                onChange={(e) => setPersonaForm((f) => ({ ...f, nacionalidad: e.target.value }))}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)} disabled={saving}>
              Cancelar
            </Button>
            <Button onClick={crearPersona} disabled={saving || !personaForm.nombre.trim()}>
              {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <UserPlus className="h-4 w-4 mr-2" />}
              Crear y vincular
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
