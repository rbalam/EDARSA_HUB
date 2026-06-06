/**
 * ResponsabilidadAccionesModal.jsx - Modal de Acciones de Responsabilidad
 * CAB-003 | Fase 2C.2
 * EDARSA HUB
 * 
 * Modal para ejecutar acciones sobre registros de responsabilidad económica.
 */

import { useState } from 'react';
// FASE AUTH-V2-ALIGN: auth canónica vía Bearer (authedFetch) + cookie httpOnly
import { authedFetch } from '../../services/operativoApi';
import { 
  X, 
  CheckCircle, 
  XCircle, 
  Shield, 
  AlertTriangle,
  ArrowRight,
  Send,
  Loader2
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

// Configuración de acciones
const ACCIONES_CONFIG = {
  PROPONER: {
    label: 'Proponer',
    color: 'blue',
    icon: ArrowRight,
    descripcion: 'Proponer formalmente el monto para revisión',
    endpoint: 'proponer',
    estadoDestino: 'PROPUESTO'
  },
  APROBAR: {
    label: 'Aprobar',
    color: 'green',
    icon: CheckCircle,
    descripcion: 'Aprobar el cargo propuesto',
    endpoint: 'aprobar',
    estadoDestino: 'APROBADO'
  },
  RECHAZAR: {
    label: 'Rechazar',
    color: 'red',
    icon: XCircle,
    descripcion: 'El monto NO procedía como fue planteado',
    endpoint: 'rechazar',
    estadoDestino: 'RECHAZADO'
  },
  EXONERAR: {
    label: 'Exonerar',
    color: 'purple',
    icon: Shield,
    descripcion: 'Liberar al responsable (el cargo era válido pero se perdona)',
    endpoint: 'exonerar',
    estadoDestino: 'EXONERADO'
  },
  DISPUTAR: {
    label: 'Disputar',
    color: 'amber',
    icon: AlertTriangle,
    descripcion: 'Iniciar una disputa sobre el monto',
    endpoint: 'disputar',
    estadoDestino: 'EN_DISPUTA'
  },
  RESOLVER_DISPUTA: {
    label: 'Resolver Disputa',
    color: 'blue',
    icon: ArrowRight,
    descripcion: 'Devolver a estado PROPUESTO para revisión',
    endpoint: 'resolver-disputa',
    estadoDestino: 'PROPUESTO'
  }
};

// Roles disponibles
const ROLES = [
  { value: 'AFECTADO', label: 'Afectado' },
  { value: 'SUPERVISOR', label: 'Supervisor' },
  { value: 'GERENTE_OPS', label: 'Gerente de Operaciones' },
  { value: 'DIRECCION', label: 'Dirección' }
];

// Formateador de moneda
const formatMXN = (valor) => {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN'
  }).format(valor || 0);
};

const ResponsabilidadAccionesModal = ({ 
  isOpen, 
  onClose, 
  responsabilidad, 
  accion, 
  onSuccess 
}) => {
  const [comentario, setComentario] = useState('');
  const [usuarioId, setUsuarioId] = useState('');
  const [usuarioRol, setUsuarioRol] = useState('SUPERVISOR');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !responsabilidad || !accion) return null;

  const config = ACCIONES_CONFIG[accion];
  if (!config) return null;

  const Icon = config.icon;

  const colorClasses = {
    blue: { bg: 'bg-blue-100', text: 'text-blue-700', btn: 'bg-blue-600 hover:bg-blue-700' },
    green: { bg: 'bg-green-100', text: 'text-green-700', btn: 'bg-green-600 hover:bg-green-700' },
    red: { bg: 'bg-red-100', text: 'text-red-700', btn: 'bg-red-600 hover:bg-red-700' },
    purple: { bg: 'bg-purple-100', text: 'text-purple-700', btn: 'bg-purple-600 hover:bg-purple-700' },
    amber: { bg: 'bg-amber-100', text: 'text-amber-700', btn: 'bg-amber-600 hover:bg-amber-700' }
  };

  const colors = colorClasses[config.color];

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (comentario.trim().length < 10) {
      setError('El comentario debe tener al menos 10 caracteres');
      return;
    }

    if (!usuarioId.trim()) {
      setError('El ID de usuario es requerido');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await authedFetch(
        `${API_BASE}/api/v2/responsabilidad/${responsabilidad.id}/${config.endpoint}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            usuario_id: usuarioId.trim(),
            usuario_rol: usuarioRol,
            comentario: comentario.trim()
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error al ejecutar la acción');
      }

      if (onSuccess) {
        onSuccess(data);
      }
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" data-testid="acciones-modal">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className={`p-4 border-b flex items-center justify-between ${colors.bg}`}>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-white/50`}>
              <Icon className={`h-5 w-5 ${colors.text}`} />
            </div>
            <div>
              <h3 className={`font-semibold ${colors.text}`}>{config.label}</h3>
              <p className="text-xs text-zinc-600">{config.descripcion}</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1 hover:bg-white/50 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-zinc-500" />
          </button>
        </div>

        {/* Resumen del registro */}
        <div className="p-4 bg-zinc-50 border-b">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-zinc-500">Sucursal:</span>
              <p className="font-medium">{responsabilidad.sucursal_id}</p>
            </div>
            <div>
              <span className="text-zinc-500">Monto Propuesto:</span>
              <p className={`font-semibold ${responsabilidad.monto_propuesto_mxn > 0 ? 'text-red-600' : 'text-zinc-600'}`}>
                {formatMXN(responsabilidad.monto_propuesto_mxn)}
              </p>
            </div>
            <div>
              <span className="text-zinc-500">Estado Actual:</span>
              <p className="font-medium">{responsabilidad.estado}</p>
            </div>
            <div>
              <span className="text-zinc-500">Nuevo Estado:</span>
              <p className={`font-semibold ${colors.text}`}>{config.estadoDestino}</p>
            </div>
          </div>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Usuario ID */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">
              ID de Usuario *
            </label>
            <input
              type="text"
              value={usuarioId}
              onChange={(e) => setUsuarioId(e.target.value)}
              placeholder="Ej: admin-001"
              className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
              data-testid="input-usuario-id"
            />
          </div>

          {/* Rol */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">
              Rol *
            </label>
            <select
              value={usuarioRol}
              onChange={(e) => setUsuarioRol(e.target.value)}
              className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              data-testid="select-usuario-rol"
            >
              {ROLES.map(rol => (
                <option key={rol.value} value={rol.value}>{rol.label}</option>
              ))}
            </select>
          </div>

          {/* Comentario */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">
              Comentario * <span className="text-zinc-400">(mínimo 10 caracteres)</span>
            </label>
            <textarea
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
              placeholder="Explica el motivo de esta acción..."
              rows={4}
              className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              required
              minLength={10}
              data-testid="input-comentario"
            />
            <p className="text-xs text-zinc-400 mt-1">
              {comentario.length}/10 caracteres mínimos
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Botones */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-zinc-700 bg-zinc-100 hover:bg-zinc-200 rounded-lg transition-colors"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors flex items-center gap-2 ${colors.btn} disabled:opacity-50`}
              disabled={loading || comentario.length < 10 || !usuarioId.trim()}
              data-testid="btn-confirmar-accion"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Procesando...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  Confirmar {config.label}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResponsabilidadAccionesModal;
