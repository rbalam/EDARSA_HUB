/**
 * SupplierHub - Dashboard del Portal de Proveedores
 * Diseño EXACTO según mockups proporcionados
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { 
  FileText, Clock, CheckCircle, RefreshCw, 
  ChevronDown, ChevronRight, Upload, Download, FileSpreadsheet,
  Search, DollarSign, Building2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function DashboardPage({ supplier, token, onNavigate }) {
  const [loading, setLoading] = useState(true);
  const [loadingSaldos, setLoadingSaldos] = useState(false);
  const [selectedSystem, setSelectedSystem] = useState('all');
  const [selectedUnit, setSelectedUnit] = useState('all');
  const [expandedSucursales, setExpandedSucursales] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [recentInvoices, setRecentInvoices] = useState([]);

  const [saldosData, setSaldosData] = useState({
    sistemas: [],
    sucursales: [],
    facturas_pendientes: [],
    totales: { importe: 0, pagado: 0, saldo: 0, facturas: 0 }
  });

  useEffect(() => {
    loadDashboardData();
    loadSaldosReales();
  }, []);

  const loadDashboardData = async () => {
    try {
      const invoicesRes = await fetch(`${API_URL}/api/portal/invoices`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (invoicesRes.ok) {
        const invoicesData = await invoicesRes.json();
        setRecentInvoices(invoicesData.slice(0, 5));
      }
    } catch (error) {
      console.error('Error cargando dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSaldosReales = async () => {
    setLoadingSaldos(true);
    try {
      const res = await fetch(`${API_URL}/api/portal/saldos`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSaldosData(data);
      }
    } catch (error) {
      console.error('Error cargando saldos:', error);
    } finally {
      setLoadingSaldos(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(value || 0);
  };

  const toggleSucursal = (id) => {
    setExpandedSucursales(prev => ({ ...prev, [id]: !prev[id] }));
  };

  // Filtrar datos
  const sistemasFiltrados = selectedSystem === 'all' 
    ? saldosData.sistemas 
    : saldosData.sistemas.filter(s => s.id === selectedSystem);

  const sucursalesFiltradas = (selectedUnit === 'all'
    ? (selectedSystem === 'all' 
        ? saldosData.sucursales 
        : saldosData.sucursales.filter(s => s.sistema_id === selectedSystem))
    : saldosData.sucursales.filter(s => s.id === selectedUnit))
    .filter(s => s.facturas > 0)
    .sort((a, b) => b.saldo - a.saldo);

  // Totales
  const totalFacturado = saldosData.totales.importe;
  const totalPagado = saldosData.totales.pagado;
  const totalSaldo = saldosData.totales.saldo;
  const totalFacturas = saldosData.totales.facturas;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-gray-800"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900" data-testid="dashboard-title">Mi Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Bienvenido, {supplier?.razon_social}</p>
        </div>
        <div className="flex gap-3">
          <button className="inline-flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium text-gray-600">
            <FileSpreadsheet className="h-4 w-4" />
            Excel
          </button>
          <button className="inline-flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium text-gray-600">
            <Download className="h-4 w-4" />
            PDF
          </button>
          <button 
            onClick={() => onNavigate('upload')}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-gray-900 text-white rounded-lg hover:bg-gray-800 text-sm font-medium"
          >
            <Upload className="h-4 w-4" />
            Subir Factura
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-2">Total Facturado</p>
              <p className="text-3xl font-bold text-gray-900">{formatCurrency(totalFacturado)}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <FileText className="h-6 w-6 text-gray-400" />
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-2">Total Pagado</p>
              <p className="text-3xl font-bold text-gray-900">{formatCurrency(totalPagado)}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <CheckCircle className="h-6 w-6 text-gray-400" />
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-2">Saldo Pendiente</p>
              <p className="text-3xl font-bold text-orange-500">{formatCurrency(totalSaldo)}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <Clock className="h-6 w-6 text-gray-400" />
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-2">Facturas Pendientes</p>
              <p className="text-3xl font-bold text-gray-900">{totalFacturas}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <DollarSign className="h-6 w-6 text-gray-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Fuente de Datos */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Building2 className="h-5 w-5 text-gray-700" />
              <h2 className="text-lg font-semibold text-gray-900">Fuente de Datos</h2>
            </div>
            <button 
              onClick={loadSaldosReales}
              disabled={loadingSaldos}
              className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
            >
              <RefreshCw className={`h-4 w-4 ${loadingSaldos ? 'animate-spin' : ''}`} />
              Actualizar
            </button>
          </div>

          {/* Por Sistema */}
          <div className="mb-5">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Por Sistema</p>
            <div className="flex gap-2 flex-wrap">
              <button 
                onClick={() => { setSelectedSystem('all'); setSelectedUnit('all'); }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedSystem === 'all' 
                    ? 'bg-gray-900 text-white' 
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                Todos los Sistemas
              </button>
              {saldosData.sistemas.filter(s => s.facturas > 0 || s.status === 'connected').map(s => (
                <button 
                  key={s.id}
                  onClick={() => { setSelectedSystem(s.id); setSelectedUnit('all'); }}
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedSystem === s.id 
                      ? 'bg-gray-900 text-white' 
                      : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${s.status === 'connected' ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
                  {s.name}
                </button>
              ))}
            </div>
          </div>

          {/* Por Unidad */}
          {sucursalesFiltradas.length > 0 && (
            <div className="mb-6">
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Por Unidad / Empresa</p>
              <div className="flex gap-2 flex-wrap">
                <button 
                  onClick={() => setSelectedUnit('all')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedUnit === 'all' 
                      ? 'bg-gray-900 text-white' 
                      : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  Todas las Unidades
                </button>
                {sucursalesFiltradas.map(s => (
                  <button 
                    key={s.id}
                    onClick={() => setSelectedUnit(s.id)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      selectedUnit === s.id 
                        ? 'bg-gray-900 text-white' 
                        : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    {s.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Resumen por Sistema */}
          <div className="border-t border-gray-100 pt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-gray-900">Resumen por Sistema</h3>
              <ChevronDown className="h-4 w-4 text-gray-400" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              {sistemasFiltrados.map((s) => {
                // AZUL para MPRO, VIOLETA para SoftRestaurant
                const isMPRO = s.system_type === 'MPRO';
                return (
                  <div 
                    key={s.id} 
                    className="rounded-xl p-5"
                    style={{ 
                      backgroundColor: isMPRO ? '#E8F4FD' : '#F3E8FF',
                      borderLeft: `4px solid ${isMPRO ? '#93C5FD' : '#D8B4FE'}`
                    }}
                  >
                    <h4 className="font-semibold text-gray-900 text-base mb-4">{s.name}</h4>
                    {s.status === 'not_found' || s.facturas === 0 ? (
                      <p className="text-sm text-gray-400">RFC no encontrado en este sistema</p>
                    ) : (
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <p className="text-sm text-gray-500 mb-1">Facturas</p>
                          <p className="text-xl font-bold text-gray-900">{s.facturas}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500 mb-1">Importe</p>
                          <p className="text-lg font-semibold text-gray-900">{formatCurrency(s.importe)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500 mb-1">Saldo</p>
                          <p className="text-lg font-semibold text-orange-500">{formatCurrency(s.saldo)}</p>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            
            {/* Footer resumen */}
            <div className="flex gap-6 mt-4 pt-3 text-xs text-gray-500 border-t border-gray-100">
              {saldosData.sistemas.map(s => (
                <span key={s.id} className="inline-flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${s.facturas > 0 ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
                  {s.name}: {s.facturas} registros
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Saldo por Sucursal */}
      {sucursalesFiltradas.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <FileText className="h-5 w-5 text-gray-700" />
            <h2 className="text-lg font-semibold text-gray-900">Saldo por Sucursal</h2>
          </div>
          <div className="grid grid-cols-3 gap-4">
            {sucursalesFiltradas.map(s => (
              <div 
                key={s.id} 
                className="rounded-xl p-5 border"
                style={s.system_type === 'MPRO' 
                  ? {backgroundColor: '#EFF6FF', borderColor: '#BFDBFE', borderLeftWidth: '4px', borderLeftColor: '#3B82F6'} 
                  : {backgroundColor: '#F5F3FF', borderColor: '#DDD6FE', borderLeftWidth: '4px', borderLeftColor: '#8B5CF6'}
                }
              >
                <h3 className="font-bold text-lg text-gray-900 mb-2">{s.name}</h3>
                <span 
                  className="inline-block px-2.5 py-1 rounded text-xs font-medium mb-4"
                  style={s.system_type === 'MPRO' 
                    ? {backgroundColor: '#DBEAFE', color: '#1D4ED8'} 
                    : {backgroundColor: '#EDE9FE', color: '#7C3AED'}
                  }
                >
                  {s.system_type === 'MPRO' ? 'Management Pro' : 'Soft Restaurant'}
                </span>
                <div className="space-y-2.5 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Facturas:</span>
                    <span className="font-semibold text-gray-900">{s.facturas}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Importe:</span>
                    <span className="font-semibold text-gray-900">{formatCurrency(s.importe)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Pagado:</span>
                    <span className="font-semibold text-green-600">{formatCurrency(s.pagado)}</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-gray-200">
                    <span className="text-gray-500">Saldo:</span>
                    <span className="font-bold text-orange-500">{formatCurrency(s.saldo)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Facturas Pendientes de Pago */}
      {sucursalesFiltradas.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-gray-700" />
              <h2 className="text-lg font-semibold text-gray-900">
                Facturas Pendientes de Pago ({totalFacturas})
              </h2>
            </div>
            <div className="flex gap-3">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input 
                  type="text" 
                  placeholder="Buscar folio, documento..." 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-gray-200"
                />
              </div>
              <button className="inline-flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium text-gray-600">
                <CheckCircle className="h-4 w-4" />
                Conciliar
              </button>
            </div>
          </div>

          <div className="space-y-2">
            {sucursalesFiltradas.map(suc => (
              <div key={suc.id} className="border border-gray-200 rounded-lg overflow-hidden">
                <button 
                  onClick={() => toggleSucursal(suc.id)}
                  className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {expandedSucursales[suc.id] ? (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    )}
                    <span className="font-semibold text-gray-900">{suc.name}</span>
                    <span 
                      className="px-2 py-0.5 rounded text-xs font-medium"
                      style={suc.system_type === 'MPRO' 
                        ? {backgroundColor: '#DBEAFE', color: '#1D4ED8'} 
                        : {backgroundColor: '#EDE9FE', color: '#7C3AED'}
                      }
                    >
                      {suc.system_type === 'MPRO' ? 'MPro' : 'SR'}
                    </span>
                  </div>
                  <div className="flex items-center gap-8 text-sm">
                    <span className="text-gray-500">Facturas: <strong className="text-gray-900">{suc.facturas}</strong></span>
                    <span className="text-gray-500">Importe: <strong className="text-gray-900">{formatCurrency(suc.importe)}</strong></span>
                    <span className="text-gray-500">Saldo: <strong className="text-orange-500">{formatCurrency(suc.saldo)}</strong></span>
                  </div>
                </button>
                
                {expandedSucursales[suc.id] && saldosData.facturas_pendientes.filter(f => f.sucursal === suc.name).length > 0 && (
                  <div className="border-t border-gray-200 bg-gray-50 p-4">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-gray-500 text-xs uppercase">
                          <th className="py-2 font-medium">Folio</th>
                          <th className="py-2 font-medium">Referencia</th>
                          <th className="py-2 font-medium">Fecha</th>
                          <th className="py-2 font-medium">Vencimiento</th>
                          <th className="py-2 font-medium">Días</th>
                          <th className="py-2 font-medium text-right">Importe</th>
                          <th className="py-2 font-medium text-right">Saldo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {saldosData.facturas_pendientes
                          .filter(f => f.sucursal === suc.name)
                          .map((f, i) => (
                          <tr key={i} className="border-t border-gray-200">
                            <td className="py-2.5 text-gray-900 font-medium">{f.folio}</td>
                            <td className="py-2.5 text-gray-600">{f.referencia}</td>
                            <td className="py-2.5 text-gray-600">{f.fecha}</td>
                            <td className="py-2.5 text-gray-600">{f.vencimiento}</td>
                            <td className={`py-2.5 font-medium ${f.dias_vencido > 0 ? 'text-red-500' : 'text-green-600'}`}>
                              {f.dias_vencido > 0 ? `+${f.dias_vencido}` : f.dias_vencido}
                            </td>
                            <td className="py-2.5 text-right text-gray-900">{formatCurrency(f.importe)}</td>
                            <td className="py-2.5 text-right font-semibold text-orange-500">{formatCurrency(f.saldo)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Total General - Fondo gris claro con borde */}
          <div className="mt-4 p-4 rounded-lg flex items-center justify-between border border-gray-200" style={{backgroundColor: '#F1F5F9'}}>
            <span className="font-semibold text-gray-700">TOTAL GENERAL ({totalFacturas} facturas)</span>
            <div className="flex gap-8 text-sm text-gray-600">
              <span>Importe: <strong className="text-gray-900">{formatCurrency(totalFacturado)}</strong></span>
              <span>Saldo: <strong className="text-orange-500">{formatCurrency(totalSaldo)}</strong></span>
            </div>
          </div>
        </div>
      )}

      {/* Facturas Recientes */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-gray-900">Facturas Recientes</h2>
          <button 
            onClick={() => onNavigate('invoices')} 
            className="text-sm text-gray-500 hover:text-gray-700 font-medium"
          >
            Ver todas &rarr;
          </button>
        </div>
        
        {recentInvoices.length === 0 ? (
          <div className="text-center py-16">
            <FileText className="h-16 w-16 mx-auto mb-4 text-gray-200" />
            <p className="text-gray-500">No tienes facturas subidas</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-200">
                <th className="py-3 font-medium">FOLIO</th>
                <th className="py-3 font-medium">FECHA</th>
                <th className="py-3 font-medium">TOTAL</th>
                <th className="py-3 font-medium">VALIDACIÓN</th>
                <th className="py-3 font-medium">PAGO</th>
              </tr>
            </thead>
            <tbody>
              {recentInvoices.map((inv, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 text-gray-900 font-medium">{inv.serie}{inv.folio || inv.uuid?.substring(0, 8)}</td>
                  <td className="py-3 text-gray-600">{new Date(inv.fecha_emision).toLocaleDateString('es-MX')}</td>
                  <td className="py-3 text-gray-900 font-medium">{formatCurrency(inv.total)}</td>
                  <td className="py-3">
                    <span className={`px-2.5 py-1 rounded text-xs font-medium ${
                      inv.status === 'validated' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {inv.status === 'validated' ? 'Validada' : 'Pendiente'}
                    </span>
                  </td>
                  <td className="py-3">
                    <span className="px-2.5 py-1 rounded text-xs font-medium bg-orange-100 text-orange-700">
                      Sin Pagar
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
