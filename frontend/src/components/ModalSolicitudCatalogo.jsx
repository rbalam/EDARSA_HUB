/**
 * Modal para Solicitar Alta en Catálogos
 * 
 * Se integra en cualquier selector para permitir solicitar
 * la creación de un nuevo elemento cuando no existe.
 * 
 * Flujo: Usuario → Supervisor (Crea) → Administrador (Autoriza)
 */

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import { Plus, Send, AlertCircle, CheckCircle2 } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Configuración de campos por catálogo
const CAMPOS_CATALOGO = {
  puestos: {
    nombre: 'Puesto',
    campos: [
      { id: 'nombre', label: 'Nombre del Puesto', tipo: 'text', requerido: true },
      { id: 'descripcion', label: 'Descripción', tipo: 'textarea', requerido: false },
      { id: 'nivel_jerarquico', label: 'Nivel Jerárquico', tipo: 'select', requerido: false, 
        opciones: ['Operativo', 'Supervisor', 'Gerencial', 'Directivo'] }
    ]
  },
  departamentos: {
    nombre: 'Departamento',
    campos: [
      { id: 'nombre', label: 'Nombre del Departamento', tipo: 'text', requerido: true },
      { id: 'codigo', label: 'Código', tipo: 'text', requerido: false },
      { id: 'descripcion', label: 'Descripción', tipo: 'textarea', requerido: false }
    ]
  },
  sucursales: {
    nombre: 'Sucursal',
    campos: [
      { id: 'nombre', label: 'Nombre de la Sucursal', tipo: 'text', requerido: true },
      { id: 'ciudad', label: 'Ciudad', tipo: 'text', requerido: false },
      { id: 'direccion', label: 'Dirección', tipo: 'text', requerido: false },
      { id: 'telefono', label: 'Teléfono', tipo: 'text', requerido: false }
    ]
  },
  tipos_incidencia: {
    nombre: 'Tipo de Incidencia',
    campos: [
      { id: 'nombre', label: 'Nombre', tipo: 'text', requerido: true },
      { id: 'codigo', label: 'Código/Símbolo', tipo: 'text', requerido: true },
      { id: 'descripcion', label: 'Descripción', tipo: 'textarea', requerido: false },
      { id: 'afecta_nomina', label: '¿Afecta Nómina?', tipo: 'select', requerido: false,
        opciones: ['Sí', 'No'] }
    ]
  }
};

export function ModalSolicitudCatalogo({ 
  isOpen, 
  onClose, 
  tipoCatalogo, 
  valorInicial = '',
  onSolicitudCreada 
}) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({});
  const [motivo, setMotivo] = useState('');
  const [success, setSuccess] = useState(false);
  
  const config = CAMPOS_CATALOGO[tipoCatalogo];
  const token = localStorage.getItem('token');

  useEffect(() => {
    if (isOpen) {
      // Inicializar formulario con valor inicial si existe
      const initial = {};
      config?.campos.forEach(c => {
        initial[c.id] = c.id === 'nombre' ? valorInicial : '';
      });
      setFormData(initial);
      setMotivo('');
      setSuccess(false);
    }
  }, [isOpen, valorInicial, tipoCatalogo]);

  const handleChange = (campo, valor) => {
    setFormData(prev => ({ ...prev, [campo]: valor }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validar campos requeridos
    const camposRequeridos = config.campos.filter(c => c.requerido);
    for (const campo of camposRequeridos) {
      if (!formData[campo.id]?.trim()) {
        toast.error(`El campo "${campo.label}" es requerido`);
        return;
      }
    }
    
    if (!motivo.trim() || motivo.length < 5) {
      toast.error('Ingrese un motivo válido (mínimo 5 caracteres)');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/rrhh/solicitudes-catalogo`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tipo_catalogo: tipoCatalogo,
          nombre_elemento: formData.nombre,
          motivo: motivo,
          datos_adicionales: formData
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al crear solicitud');
      }

      const data = await response.json();
      setSuccess(true);
      toast.success('Solicitud enviada correctamente');
      
      if (onSolicitudCreada) {
        onSolicitudCreada(data.solicitud);
      }
      
      // Cerrar después de 2 segundos
      setTimeout(() => {
        onClose();
      }, 2000);

    } catch (error) {
      console.error('Error:', error);
      toast.error(error.message || 'Error al enviar solicitud');
    } finally {
      setLoading(false);
    }
  };

  if (!config) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5 text-blue-600" />
            Solicitar Alta: {config.nombre}
          </DialogTitle>
        </DialogHeader>

        {success ? (
          <div className="py-8 text-center">
            <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-green-700">¡Solicitud Enviada!</h3>
            <p className="text-sm text-zinc-500 mt-2">
              Su solicitud será revisada por el equipo correspondiente.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Campos dinámicos según catálogo */}
            {config.campos.map(campo => (
              <div key={campo.id}>
                <Label className="text-sm">
                  {campo.label} {campo.requerido && <span className="text-red-500">*</span>}
                </Label>
                
                {campo.tipo === 'text' && (
                  <Input
                    value={formData[campo.id] || ''}
                    onChange={(e) => handleChange(campo.id, e.target.value)}
                    placeholder={`Ingrese ${campo.label.toLowerCase()}`}
                    className="mt-1"
                    required={campo.requerido}
                  />
                )}
                
                {campo.tipo === 'textarea' && (
                  <Textarea
                    value={formData[campo.id] || ''}
                    onChange={(e) => handleChange(campo.id, e.target.value)}
                    placeholder={`Ingrese ${campo.label.toLowerCase()}`}
                    className="mt-1"
                    rows={2}
                  />
                )}
                
                {campo.tipo === 'select' && (
                  <select
                    value={formData[campo.id] || ''}
                    onChange={(e) => handleChange(campo.id, e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 mt-1 text-sm"
                  >
                    <option value="">Seleccionar...</option>
                    {campo.opciones?.map(op => (
                      <option key={op} value={op}>{op}</option>
                    ))}
                  </select>
                )}
              </div>
            ))}

            {/* Motivo/Justificación */}
            <div>
              <Label className="text-sm">
                Motivo de la Solicitud <span className="text-red-500">*</span>
              </Label>
              <Textarea
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                placeholder="Explique por qué necesita este nuevo elemento en el catálogo..."
                className="mt-1"
                rows={3}
                required
              />
            </div>

            {/* Nota informativa */}
            <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg text-sm">
              <AlertCircle className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-blue-700">Flujo de Aprobación</p>
                <p className="text-blue-600 text-xs mt-1">
                  Su solicitud será revisada por un Supervisor (creación) 
                  y luego por un Administrador (autorización).
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
                Cancelar
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin">⏳</span> Enviando...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Send className="h-4 w-4" /> Enviar Solicitud
                  </span>
                )}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

/**
 * Botón que se agrega a los selectores para solicitar alta
 */
export function BotonSolicitarAlta({ tipoCatalogo, valorBusqueda, className = '' }) {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setModalOpen(true)}
        className={`text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 ${className}`}
      >
        <Plus className="h-3 w-3" />
        Solicitar alta
      </button>
      
      <ModalSolicitudCatalogo
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        tipoCatalogo={tipoCatalogo}
        valorInicial={valorBusqueda}
      />
    </>
  );
}

export default ModalSolicitudCatalogo;
