/**
 * EDARSA HUB - Formulario de Socio
 * =================================
 * Página para crear y editar socios de cava con soporte de autocompletado
 * desde el catálogo maestro canónico de clientes.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Users, Save, ArrowLeft, Loader2, AlertCircle,
  UserCheck, Search, RefreshCw
} from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '@/lib/api';
import { toast } from 'sonner';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  CorporateFiltersProvider,
  CorporateFilterSelect,
  useCorporateFilters,
} from '../../filters';
import { useAccessContext } from '../../hooks/useAccessContext';

const TIPOS_MEMBRESIA = [
  { value: 'ESTANDAR', label: 'Estándar (12 botellas)' },
  { value: 'PREMIUM', label: 'Premium (24 botellas)' },
  { value: 'VIP', label: 'VIP (48 botellas)' },
  { value: 'CORPORATIVO', label: 'Corporativo (100 botellas)' }
];

const MEMBRESIA_BOTELLAS = {
  'ESTANDAR': 12,
  'PREMIUM': 24,
  'VIP': 48,
  'CORPORATIVO': 100
};

function SocioFormContent() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = !!id && id !== 'nuevo';
  const { selected, loading: filtersLoading } = useCorporateFilters();
  const { context, loading: contextLoading, error: contextError } = useAccessContext();
  const unidadNegocioPk = selected?.unidades_negocio || context?.unidad_activa || '';
  
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  
  // Modal de búsqueda de clientes canónicos
  const [showBuscarCanonico, setShowBuscarCanonico] = useState(false);
  const [searchCanonicoTerm, setSearchCanonicoTerm] = useState('');
  const [clientesCanonicos, setClientesCanonicos] = useState([]);
  const [loadingCanonicos, setLoadingCanonicos] = useState(false);

  const [formData, setFormData] = useState({
    nombre_completo: '',
    numero_socio: '',
    email: '',
    telefono: '',
    cliente_crm_id: '',
    tipo_membresia: 'ESTANDAR',
    maximo_botellas: 12,
    fecha_vencimiento: '',
    observaciones: ''
  });

  useEffect(() => {
    if (filtersLoading || contextLoading) return;
    if (isEditing) {
      loadSocio();
    } else if (!unidadNegocioPk) {
      setError('Selecciona una unidad de negocio autorizada para registrar socios.');
    }
  }, [id, isEditing, unidadNegocioPk, filtersLoading, contextLoading]);

  const loadSocio = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/cava-socios/socios/${id}?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`);
      const socio = response.data;
      setFormData({
        nombre_completo: socio.nombre_completo || '',
        numero_socio: socio.numero_socio || '',
        email: socio.email || '',
        telefono: socio.telefono || '',
        cliente_crm_id: socio.cliente_crm_id || '',
        tipo_membresia: socio.tipo_membresia || 'ESTANDAR',
        maximo_botellas: socio.maximo_botellas || 12,
        fecha_vencimiento: socio.fecha_vencimiento?.split('T')[0] || '',
        observaciones: socio.observaciones || ''
      });
    } catch (err) {
      console.error('Error loading socio:', err);
      setError('Error cargando datos del socio');
    } finally {
      setLoading(false);
    }
  };

  const handleBuscarCanonicos = async () => {
    if (!unidadNegocioPk) return;
    setLoadingCanonicos(true);
    try {
      const params = new URLSearchParams({
        unidad_negocio_pk: unidadNegocioPk,
        search: searchCanonicoTerm.trim(),
        limit: 25
      });
      const response = await api.get(`/cava-socios/clientes-canonicos?${params}`);
      setClientesCanonicos(response.data?.clientes || []);
    } catch (err) {
      console.error('Error buscando clientes canónicos:', err);
    } finally {
      setLoadingCanonicos(false);
    }
  };

  const handleSelectCanonico = (cli) => {
    setFormData(prev => ({
      ...prev,
      nombre_completo: cli.nombre_completo || '',
      email: cli.email || '',
      telefono: cli.telefono || '',
      cliente_crm_id: String(cli.cliente_id || ''),
      observaciones: prev.observaciones || `Vinculado a cliente maestro #${cli.codigo_cliente || cli.cliente_id}`
    }));
    setShowBuscarCanonico(false);
    toast.success(`Datos cargados de: ${cli.nombre_completo}`);
  };

  const handleChange = (field, value) => {
    setFormData(prev => {
      const updated = { ...prev, [field]: value };
      if (field === 'tipo_membresia') {
        updated.maximo_botellas = MEMBRESIA_BOTELLAS[value] || 12;
      }
      return updated;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!unidadNegocioPk) {
      toast.error('Selecciona una unidad de negocio autorizada.');
      return;
    }
    
    if (!formData.nombre_completo?.trim()) {
      toast.error('El nombre completo es obligatorio');
      return;
    }
    
    setSaving(true);
    try {
      if (isEditing) {
        await api.put(`/cava-socios/socios/${id}?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`, formData);
        toast.success('Socio actualizado correctamente');
      } else {
        await api.post(`/cava-socios/socios?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`, formData);
        toast.success('Socio creado correctamente');
      }
      navigate('/cava-socios/socios');
    } catch (err) {
      console.error('Error saving socio:', err);
      toast.error(err.response?.data?.detail || 'Error guardando socio');
    } finally {
      setSaving(false);
    }
  };

  if (loading || filtersLoading || contextLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="socio-form-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Users className="h-7 w-7 text-purple-600" />
              {isEditing ? 'Editar Socio' : 'Nuevo Socio'}
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {isEditing ? 'Actualiza los datos del socio' : 'Registra un nuevo socio en la cava'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!isEditing && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setShowBuscarCanonico(true);
                handleBuscarCanonicos();
              }}
            >
              <UserCheck className="h-4 w-4 mr-2 text-indigo-600" />
              Buscar en Catálogo Maestro
            </Button>
          )}
          <div className="min-w-[260px]">
            <CorporateFilterSelect
              filterKey="unidades_negocio"
              label="Unidad de negocio"
              placeholder="Selecciona una unidad"
            />
          </div>
        </div>
      </div>

      {(error || contextError) && (
        <div className="p-4 rounded-lg bg-red-50 text-red-700 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          {error || contextError?.message || 'No se pudo resolver el contexto de acceso.'}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Datos del Socio</CardTitle>
            <CardDescription>
              Información del socio de cava y membresía
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Nombre */}
              <div className="space-y-2">
                <Label htmlFor="nombre_completo">Nombre Completo *</Label>
                <Input
                  id="nombre_completo"
                  value={formData.nombre_completo}
                  onChange={(e) => handleChange('nombre_completo', e.target.value)}
                  placeholder="Juan Pérez García"
                  required
                  data-testid="input-nombre"
                />
              </div>

              {/* Número de Socio */}
              <div className="space-y-2">
                <Label htmlFor="numero_socio">Número de Socio</Label>
                <Input
                  id="numero_socio"
                  value={formData.numero_socio}
                  onChange={(e) => handleChange('numero_socio', e.target.value)}
                  placeholder="Auto-generado si vacío"
                  data-testid="input-numero"
                />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  placeholder="socio@email.com"
                  data-testid="input-email"
                />
              </div>

              {/* Teléfono */}
              <div className="space-y-2">
                <Label htmlFor="telefono">Teléfono / WhatsApp</Label>
                <Input
                  id="telefono"
                  value={formData.telefono}
                  onChange={(e) => handleChange('telefono', e.target.value)}
                  placeholder="+52 55 1234 5678"
                  data-testid="input-telefono"
                />
              </div>

              {/* Tipo de Membresía */}
              <div className="space-y-2">
                <Label htmlFor="tipo_membresia">Tipo de Membresía</Label>
                <Select
                  value={formData.tipo_membresia}
                  onValueChange={(val) => handleChange('tipo_membresia', val)}
                >
                  <SelectTrigger data-testid="select-membresia">
                    <SelectValue placeholder="Selecciona tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIPOS_MEMBRESIA.map((tipo) => (
                      <SelectItem key={tipo.value} value={tipo.value}>
                        {tipo.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Máximo de Botellas */}
              <div className="space-y-2">
                <Label htmlFor="maximo_botellas">Capacidad Máxima (Botellas)</Label>
                <Input
                  id="maximo_botellas"
                  type="number"
                  min="1"
                  max="500"
                  value={formData.maximo_botellas}
                  onChange={(e) => handleChange('maximo_botellas', parseInt(e.target.value) || 12)}
                  data-testid="input-capacidad"
                />
              </div>

              {/* Fecha de Vencimiento */}
              <div className="space-y-2">
                <Label htmlFor="fecha_vencimiento">Fecha de Vencimiento</Label>
                <Input
                  id="fecha_vencimiento"
                  type="date"
                  value={formData.fecha_vencimiento}
                  onChange={(e) => handleChange('fecha_vencimiento', e.target.value)}
                  data-testid="input-vencimiento"
                />
              </div>
            </div>

            {/* Observaciones */}
            <div className="space-y-2">
              <Label htmlFor="observaciones">Observaciones / Notas</Label>
              <Textarea
                id="observaciones"
                rows={3}
                value={formData.observaciones}
                onChange={(e) => handleChange('observaciones', e.target.value)}
                placeholder="Preferencias de vinos, casillero preferido, notas de servicio..."
                data-testid="input-observaciones"
              />
            </div>

            {/* Botones de acción */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/cava-socios/socios')}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={saving} data-testid="btn-guardar-socio">
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    {isEditing ? 'Actualizar Socio' : 'Registrar Socio'}
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>

      {/* Modal Búsqueda Catálogo Canónico */}
      <Dialog open={showBuscarCanonico} onOpenChange={setShowBuscarCanonico}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserCheck className="h-5 w-5 text-indigo-600" />
              Seleccionar Cliente del Catálogo Maestro
            </DialogTitle>
            <DialogDescription>
              Busca y selecciona un cliente registrado en la base de datos para autocompletar el formulario
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar por razón social, nombre o RFC..."
                  className="pl-9"
                  value={searchCanonicoTerm}
                  onChange={(e) => setSearchCanonicoTerm(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleBuscarCanonicos()}
                />
              </div>
              <Button onClick={handleBuscarCanonicos} disabled={loadingCanonicos}>
                {loadingCanonicos ? <RefreshCw className="h-4 w-4 animate-spin" /> : 'Buscar'}
              </Button>
            </div>

            <div className="border rounded-lg max-h-56 overflow-y-auto">
              {loadingCanonicos ? (
                <div className="py-8 text-center text-muted-foreground">
                  <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                  Buscando en catálogo maestro...
                </div>
              ) : clientesCanonicos.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Razón Social / Nombre</TableHead>
                      <TableHead>RFC</TableHead>
                      <TableHead>Email / Teléfono</TableHead>
                      <TableHead className="text-right">Acción</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {clientesCanonicos.map((cli) => (
                      <TableRow key={cli.cliente_id}>
                        <TableCell>
                          <div className="font-medium text-sm">{cli.nombre_completo}</div>
                          <div className="text-xs text-muted-foreground">{cli.codigo_cliente || cli.cliente_id}</div>
                        </TableCell>
                        <TableCell className="text-xs font-mono">{cli.rfc || '-'}</TableCell>
                        <TableCell className="text-xs">
                          <div>{cli.email || '-'}</div>
                          <div>{cli.telefono || ''}</div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            onClick={() => handleSelectCanonico(cli)}
                          >
                            Seleccionar
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="py-8 text-center text-xs text-muted-foreground">
                  No se encontraron clientes. Ingresa un término de búsqueda.
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBuscarCanonico(false)}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function SocioForm() {
  return (
    <CorporateFiltersProvider scope="cava_socios">
      <SocioFormContent />
    </CorporateFiltersProvider>
  );
}
