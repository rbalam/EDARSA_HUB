/**
 * ResponsabilidadPendientesPanel.jsx - Panel de Pendientes de Aprobación
 * CAB-003 | Fase 2C.2
 * EDARSA HUB
 * 
 * Panel que muestra responsabilidades pendientes de aprobación y permite ejecutar acciones.
 */

import { useState, useEffect } from 'react';
import {
  Clock,
  AlertCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  CheckCircle,
  XCircle,
  Shield,
  AlertTriangle,
  History
} from 'lucide-react';
import ResponsabilidadAccionesModal from './ResponsabilidadAccionesModal';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

// Formateador de moneda
const formatMXN = (valor) => {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN'
  }).format(valor || 0);
};

// Colores por estado
const ESTADO_CONFIG = {
  CALCULADO: { color: 'zinc', label: 'Calculado', icon: Clock },
  PROPUESTO: { color: 'blue', label: 'Propuesto', icon: ArrowRight },
  EN_DISPUTA: { color: 'amber', label: 'En Disputa', icon: AlertTriangle },
  APROBADO: { color: 'green', label: 'Aprobado', icon: CheckCircle },
  RECHAZADO: { color: 'red', label: 'Rechazado', icon: XCircle },
  EXONERADO: { color: 'purple', label: 'Exonerado', icon: Shield }
};

// Acciones permitidas por estado
const ACCIONES_POR_ESTADO = {
  CALCULADO: ['PROPONER'],
  PROPUESTO: ['APROBAR', 'RECHAZAR', 'EXONERAR', 'DISPUTAR'],
  EN_DISPUTA: ['RESOLVER_DISPUTA', 'EXONERAR', 'RECHAZAR'],
  APROBADO: [],
  RECHAZADO: [],
  EXONERADO: []
};

// Fila de responsabilidad
const ResponsabilidadRow = ({ item, onAccion, onVerHistorial }) => {
  const [expandido, setExpandido] = useState(false);
  const estadoConfig = ESTADO_CONFIG[item.estado] || ESTADO_CONFIG.CALCULADO;
  const IconEstado = estadoConfig.icon;
  const accionesDisponibles = ACCIONES_POR_ESTADO[item.estado] || [];

  const colorClasses = {
    zinc: 'bg-zinc-100 text-zinc-700',
    blue: 'bg-blue-100 text-blue-700',
    amber: 'bg-amber-100 text-amber-700',
    green: 'bg-green-100 text-green-700',
    red: 'bg-red-100 text-red-700',
    purple: 'bg-purple-100 text-purple-700'
  };

  const fechaCalculo = item.fecha_calculo
    ? new Date(item.fecha_calculo).toLocaleDateString('es-MX', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      })
    : '-';

  return (
    <div className="border border-zinc-200 rounded-lg overflow-hidden mb-2" data-testid={`pendiente-row-${item.id}`}>
      {/* Fila principal */}
      <div 
        className="flex items-center justify-between p-3 bg-white hover:bg-zinc-50 cursor-pointer"
        onClick={() => setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${colorClasses[estadoConfig.color]}`}>
            <IconEstado className="h-3 w-3" />
            {estadoConfig.label}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-zinc-800 truncate">{item.sucursal_id}</p>
            <p className="text-xs text-zinc-500">{fechaCalculo} · {item.dias_pendiente} días</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className={`text-sm font-semibold ${item.monto_propuesto_mxn > 0 ? 'text-red-600' : 'text-zinc-500'}`}>
              {formatMXN(item.monto_propuesto_mxn)}
            </p>
            {item.excede_minimo && (
              <span className="text-xs text-amber-600">Excede mínimo</span>
            )}
          </div>
          {expandido ? (
            <ChevronUp className="h-4 w-4 text-zinc-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-zinc-400" />
          )}
        </div>
      </div>

      {/* Panel expandido con acciones */}
      {expandido && (
        <div className="p-3 bg-zinc-50 border-t border-zinc-200">
          <div className="flex flex-wrap gap-2">
            {accionesDisponibles.map(accion => {
              const btnConfig = {
                PROPONER: { label: 'Proponer', color: 'bg-blue-500 hover:bg-blue-600', icon: ArrowRight },
                APROBAR: { label: 'Aprobar', color: 'bg-green-500 hover:bg-green-600', icon: CheckCircle },
                RECHAZAR: { label: 'Rechazar', color: 'bg-red-500 hover:bg-red-600', icon: XCircle },
                EXONERAR: { label: 'Exonerar', color: 'bg-purple-500 hover:bg-purple-600', icon: Shield },
                DISPUTAR: { label: 'Disputar', color: 'bg-amber-500 hover:bg-amber-600', icon: AlertTriangle },
                RESOLVER_DISPUTA: { label: 'Resolver', color: 'bg-blue-500 hover:bg-blue-600', icon: ArrowRight }
              };
              const cfg = btnConfig[accion];
              const Icon = cfg.icon;

              return (
                <button
                  key={accion}
                  onClick={(e) => {
                    e.stopPropagation();
                    onAccion(item, accion);
                  }}
                  className={`px-3 py-1.5 text-xs font-medium text-white rounded-lg flex items-center gap-1.5 transition-colors ${cfg.color}`}
                  data-testid={`btn-${accion.toLowerCase()}-${item.id}`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {cfg.label}
                </button>
              );
            })}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onVerHistorial(item);
              }}
              className="px-3 py-1.5 text-xs font-medium text-zinc-700 bg-zinc-200 hover:bg-zinc-300 rounded-lg flex items-center gap-1.5 transition-colors"
              data-testid={`btn-historial-${item.id}`}
            >
              <History className="h-3.5 w-3.5" />
              Historial
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Panel de Historial
const HistorialPanel = ({ responsabilidadId, onClose }) => {
  const [historial, setHistorial] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const cargar = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v2/responsabilidad/${responsabilidadId}/historial`);
        const data = await res.json();
        setHistorial(data);
      } catch (err) {
        console.error('Error cargando historial:', err);
      } finally {
        setLoading(false);
      }
    };
    cargar();
  }, [responsabilidadId]);

  if (loading) {
    return (
      <div className="p-4 text-center text-zinc-500">
        <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2" />
        Cargando historial...
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b flex items-center justify-between bg-zinc-50">
          <h3 className="font-semibold text-zinc-800">Historial de Transiciones</h3>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-700">×</button>
        </div>
        <div className="p-4 max-h-96 overflow-y-auto">
          {historial?.items?.length === 0 ? (
            <p className="text-zinc-500 text-sm text-center py-4">Sin transiciones registradas</p>
          ) : (
            <div className="space-y-3">
              {historial?.items?.map((t, idx) => (
                <div key={t.id || idx} className="border-l-2 border-zinc-200 pl-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-zinc-800">{t.accion}</span>
                    <span className="text-xs text-zinc-400">
                      {t.estado_anterior} → {t.estado_nuevo}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500">{t.usuario_id} ({t.usuario_rol})</p>
                  <p className="text-xs text-zinc-600 mt-1 italic">"{t.comentario}"</p>
                  <p className="text-xs text-zinc-400 mt-1">
                    {new Date(t.fecha).toLocaleString('es-MX')}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ResponsabilidadPendientesPanel = () => {
  const [pendientes, setPendientes] = useState(null);
  const [enDisputa, setEnDisputa] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('pendientes'); // 'pendientes' | 'disputa'
  
  // Modal de acciones
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedAccion, setSelectedAccion] = useState(null);
  
  // Panel de historial
  const [historialId, setHistorialId] = useState(null);

  const cargarDatos = async () => {
    setLoading(true);
    setError(null);
    try {
      const [resPendientes, resDisputa] = await Promise.all([
        fetch(`${API_BASE}/api/v2/responsabilidad/pendientes-aprobacion`),
        fetch(`${API_BASE}/api/v2/responsabilidad/en-disputa`)
      ]);
      
      if (!resPendientes.ok || !resDisputa.ok) {
        throw new Error('Error al cargar datos');
      }
      
      const [dataPendientes, dataDisputa] = await Promise.all([
        resPendientes.json(),
        resDisputa.json()
      ]);
      
      setPendientes(dataPendientes);
      setEnDisputa(dataDisputa);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  const handleAccion = (item, accion) => {
    setSelectedItem(item);
    setSelectedAccion(accion);
    setModalOpen(true);
  };

  const handleAccionSuccess = () => {
    cargarDatos();
    setModalOpen(false);
  };

  const items = tab === 'pendientes' ? pendientes?.items : enDisputa?.items;
  const total = tab === 'pendientes' ? pendientes?.total : enDisputa?.total;
  const montoTotal = tab === 'pendientes' 
    ? pendientes?.monto_total_pendiente 
    : enDisputa?.monto_total_en_disputa;

  return (
    <div className="rounded-xl border border-zinc-200 bg-white" data-testid="pendientes-panel">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-zinc-600" />
          <h3 className="font-semibold text-zinc-800">Aprobaciones</h3>
        </div>
        <button
          onClick={cargarDatos}
          className="p-2 text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
          title="Actualizar"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        <button
          onClick={() => setTab('pendientes')}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
            tab === 'pendientes'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
              : 'text-zinc-600 hover:text-zinc-800 hover:bg-zinc-50'
          }`}
        >
          Pendientes ({pendientes?.total || 0})
        </button>
        <button
          onClick={() => setTab('disputa')}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
            tab === 'disputa'
              ? 'text-amber-600 border-b-2 border-amber-600 bg-amber-50'
              : 'text-zinc-600 hover:text-zinc-800 hover:bg-zinc-50'
          }`}
        >
          En Disputa ({enDisputa?.total || 0})
        </button>
      </div>

      {/* Resumen */}
      {!loading && !error && (
        <div className="p-3 bg-zinc-50 border-b">
          <div className="flex justify-between text-sm">
            <span className="text-zinc-600">Total: {total || 0} registros</span>
            <span className={`font-semibold ${montoTotal > 0 ? 'text-red-600' : 'text-zinc-600'}`}>
              {formatMXN(montoTotal)}
            </span>
          </div>
        </div>
      )}

      {/* Contenido */}
      <div className="p-4 max-h-96 overflow-y-auto">
        {loading ? (
          <div className="text-center py-8 text-zinc-500">
            <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
            Cargando...
          </div>
        ) : error ? (
          <div className="text-center py-8 text-red-500">
            <AlertCircle className="h-6 w-6 mx-auto mb-2" />
            {error}
          </div>
        ) : items?.length === 0 ? (
          <div className="text-center py-8 text-zinc-400">
            <CheckCircle className="h-8 w-8 mx-auto mb-2" />
            <p>No hay {tab === 'pendientes' ? 'pendientes' : 'disputas'}</p>
          </div>
        ) : (
          items?.map(item => (
            <ResponsabilidadRow
              key={item.id}
              item={item}
              onAccion={handleAccion}
              onVerHistorial={(item) => setHistorialId(item.id)}
            />
          ))
        )}
      </div>

      {/* Modal de Acciones */}
      <ResponsabilidadAccionesModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        responsabilidad={selectedItem}
        accion={selectedAccion}
        onSuccess={handleAccionSuccess}
      />

      {/* Panel de Historial */}
      {historialId && (
        <HistorialPanel
          responsabilidadId={historialId}
          onClose={() => setHistorialId(null)}
        />
      )}
    </div>
  );
};

export default ResponsabilidadPendientesPanel;
