/**
 * EDARSA HUB - Formulario de Socio
 * =================================
 * Página para crear y editar socios de cava.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Users, Save, ArrowLeft, Loader2, AlertCircle
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
  
  const [formData, setFormData] = useState({
    nombre_completo: '',
    numero_socio: '',
    email: '',
    telefono: '',
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const handleChange = (field, value) => {
    setFormData(prev => {
      const updated = { ...prev, [field]: value };
      
      // Auto-ajustar máximo de botellas según tipo de membresía
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

    
    if (!formData.nombre_completo.trim()) {
      toast.error('El nombre es requerido');
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

        <div className="ml-auto min-w-[260px]">
          <CorporateFilterSelect
            filterKey="unidades_negocio"
            label="Unidad de negocio"
            placeholder="Selecciona una unidad"
          />
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
              Información básica del socio de cava
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
                <Label htmlFor="email">Correo Electrónico</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  placeholder="socio@ejemplo.com"
                  data-testid="input-email"
                />
              </div>

              {/* Teléfono */}
              <div className="space-y-2">
                <Label htmlFor="telefono">Teléfono</Label>
                <Input
                  id="telefono"
                  value={formData.telefono}
                  onChange={(e) => handleChange('telefono', e.target.value)}
                  placeholder="+52 555 123 4567"
                  data-testid="input-telefono"
                />
              </div>

              {/* Tipo de Membresía */}
              <div className="space-y-2">
                <Label htmlFor="tipo_membresia">Tipo de Membresía</Label>
                <Select 
                  value={formData.tipo_membresia} 
                  onValueChange={(v) => handleChange('tipo_membresia', v)}
                >
                  <SelectTrigger data-testid="select-membresia">
                    <SelectValue placeholder="Selecciona tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIPOS_MEMBRESIA.map(tipo => (
                      <SelectItem key={tipo.value} value={tipo.value}>
                        {tipo.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Máximo de Botellas */}
              <div className="space-y-2">
                <Label htmlFor="maximo_botellas">Máximo de Botellas</Label>
                <Input
                  id="maximo_botellas"
                  type="number"
                  min="1"
                  max="200"
                  value={formData.maximo_botellas}
                  onChange={(e) => handleChange('maximo_botellas', parseInt(e.target.value) || 12)}
                  data-testid="input-max-botellas"
                />
              </div>

              {/* Fecha de Vencimiento */}
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="fecha_vencimiento">Fecha de Vencimiento de Membresía</Label>
                <Input
                  id="fecha_vencimiento"
                  type="date"
                  value={formData.fecha_vencimiento}
                  onChange={(e) => handleChange('fecha_vencimiento', e.target.value)}
                  data-testid="input-fecha-vencimiento"
                />
              </div>

              {/* Observaciones */}
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="observaciones">Observaciones</Label>
                <Textarea
                  id="observaciones"
                  value={formData.observaciones}
                  onChange={(e) => handleChange('observaciones', e.target.value)}
                  placeholder="Notas adicionales sobre el socio..."
                  rows={3}
                  data-testid="input-observaciones"
                />
              </div>
            </div>

            {/* Botones */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(-1)}
                disabled={saving}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={saving || !unidadNegocioPk}
                data-testid="submit-socio"
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    {isEditing ? 'Actualizar Socio' : 'Crear Socio'}
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
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
