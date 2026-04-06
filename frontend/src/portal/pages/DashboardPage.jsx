/**
 * SupplierHub - Dashboard con KPIs y Saldos por Sucursal
 * Conectado a datos reales de MPRO y SoftRestaurant
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { 
  FileText, DollarSign, Clock, CheckCircle, RefreshCw, 
  ChevronDown, ChevronRight, Upload, Download, FileSpreadsheet,
  AlertCircle, Server
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function DashboardPage({ supplier, token, onNavigate }) {
  const [stats, setStats] = useState(null);
  const [recentInvoices, setRecentInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingSaldos, setLoadingSaldos] = useState(false);
  const [selectedSystem, setSelectedSystem] = useState('all');
  const [selectedUnit, setSelectedUnit] = useState('all');
  const [expandedSucursal, setExpandedSucursal] = useState(null);

  // Datos reales de saldos desde SQL Server
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
      const statsRes = await fetch(`${API_URL}/api/portal/account-status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData.resumen);
      }

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
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Error cargando saldos');
      }
    } catch (error) {
      console.error('Error cargando saldos:', error);
      toast.error('Error de conexión al cargar saldos');
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

  const toggleSucursalDetails = (sucursalId) => {
    setExpandedSucursal(expandedSucursal === sucursalId ? null : sucursalId);
  };

  // Obtener facturas de una sucursal específica
  const getFacturasSucursal = (sucursalName, sistemaId) => {
    return saldosData.facturas_pendientes.filter(
      f => f.sucursal === sucursalName && f.sistema_id === sistemaId
    );
  };

  // Agrupar facturas por sucursal para la sección de pendientes
  const facturasAgrupadas = saldosData.sucursales
    .filter(s => s.saldo > 0)
    .map(suc => ({
      ...suc,
      facturas_detalle: getFacturasSucursal(suc.name, suc.sistema_id)
    }))
    .sort((a, b) => b.saldo - a.saldo);

  // Filtrar sistemas y sucursales según selección
  const sistemasFiltrados = selectedSystem === 'all' 
    ? saldosData.sistemas 
    : saldosData.sistemas.filter(s => s.id === selectedSystem);
  
  const sucursalesFiltradas = selectedUnit === 'all'
    ? (selectedSystem === 'all' 
        ? saldosData.sucursales 
        : saldosData.sucursales.filter(s => s.sistema_id === selectedSystem))
    : saldosData.sucursales.filter(s => s.id === selectedUnit);

  const getStatusBadge = (status) => {
    const badges = {
      'Pendiente': { bg: 'bg-yellow-100', text: 'text-yellow-700' },
      'Validada': { bg: 'bg-green-100', text: 'text-green-700' }
    };
    const badge = badges[status] || badges['Pendiente'];
    return <span className={`px-2 py-0.5 rounded text-xs ${badge.bg} ${badge.text}`}>{status}</span>;
  };

  const getPaymentBadge = (status) => {
    return <span className="px-2 py-0.5 rounded text-xs bg-orange-100 text-orange-700">{status}</span>;
  };

  const getSystemBadge = (systemType) => {
    return systemType === 'MPRO' 
      ? <span className="px-2 py-0.5 rounded text-xs bg-orange-100 text-orange-700">Management Pro</span>
      : <span className="px-2 py-0.5 rounded text-xs bg-green-100 text-green-700">Soft Restaurant</span>;
  };

  const getStatusIcon = (status) => {
    if (status === 'connected') return <span className="w-2 h-2 bg-green-500 rounded-full"></span>;
    if (status === 'not_found') return <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>;
    return <span className="w-2 h-2 bg-red-500 rounded-full"></span>;
  };

  // Totales para KPIs
  const totalFacturado = saldosData.totales.importe;
  const totalPagado = saldosData.totales.pagado;
  const totalSaldo = saldosData.totales.saldo;
  const totalFacturas = saldosData.totales.facturas;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-zinc-800"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Mi Dashboard</h1>
          <p className="text-zinc-500">Bienvenido, {supplier?.razon_social}</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-zinc-50 text-sm">
            <FileSpreadsheet className="h-4 w-4" />
            Excel
          </button>
          <button className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-zinc-50 text-sm">
            <Download className="h-4 w-4" />
            PDF
          </button>
          <button 
            onClick={() => onNavigate('upload')}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 text-sm"
          >
            <Upload className="h-4 w-4" />
            Subir Factura
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-zinc-500">Total Facturado</p>
              <p className="text-2xl font-bold text-zinc-900">{formatCurrency(stats?.total_facturado || totalFacturado)}</p>
            </div>
            <FileText className="h-10 w-10 text-zinc-300" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-5 border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-zinc-500">Total Pagado</p>
              <p className="text-2xl font-bold text-zinc-900">{formatCurrency(stats?.total_pagado || (totalFacturado - totalSaldo))}</p>
            </div>
            <CheckCircle className="h-10 w-10 text-zinc-300" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-5 border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-zinc-500">Saldo Pendiente</p>
              <p className="text-2xl font-bold text-orange-500">{formatCurrency(stats?.saldo_pendiente || totalSaldo)}</p>
            </div>
            <Clock className="h-10 w-10 text-zinc-300" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-5 border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-zinc-500">Facturas Pendientes</p>
              <p className="text-2xl font-bold text-zinc-900">{totalFacturas}</p>
            </div>
            <DollarSign className="h-10 w-10 text-zinc-300" />
          </div>
        </div>
      </div>

      {/* Fuente de Datos */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Server className="h-5 w-5 text-zinc-400" />
            <h2 className="font-semibold text-zinc-900">Fuente de Datos</h2>
            {loadingSaldos && <RefreshCw className="h-4 w-4 animate-spin text-zinc-400" />}
          </div>
          <button 
            onClick={loadSaldosReales}
            disabled={loadingSaldos}
            className="flex items-center gap-2 text-sm text-zinc-500 hover:text-zinc-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loadingSaldos ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>

        {/* Filtros por Sistema */}
        <div className="mb-4">
          <p className="text-xs text-zinc-500 mb-2">Por Sistema</p>
          <div className="flex gap-2 flex-wrap">
            <button 
              onClick={() => { setSelectedSystem('all'); setSelectedUnit('all'); }}
              className={`px-3 py-1.5 rounded text-sm ${selectedSystem === 'all' ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'}`}
            >
              Todos los Sistemas
            </button>
            {saldosData.sistemas.map(s => (
              <button 
                key={s.id}
                onClick={() => { setSelectedSystem(s.id); setSelectedUnit('all'); }}
                className={`px-3 py-1.5 rounded text-sm flex items-center gap-2 ${selectedSystem === s.id ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'}`}
              >
                {getStatusIcon(s.status)}
                {s.name}
              </button>
            ))}
          </div>
        </div>

        {/* Filtros por Unidad */}
        {saldosData.sucursales.length > 0 && (
          <div className="mb-6">
            <p className="text-xs text-zinc-500 mb-2">Por Unidad / Empresa</p>
            <div className="flex gap-2 flex-wrap">
              <button 
                onClick={() => setSelectedUnit('all')}
                className={`px-3 py-1.5 rounded text-sm ${selectedUnit === 'all' ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'}`}
              >
                Todas las Unidades
              </button>
              {(selectedSystem === 'all' ? saldosData.sucursales : saldosData.sucursales.filter(s => s.sistema_id === selectedSystem)).map(s => (
                <button 
                  key={s.id}
                  onClick={() => setSelectedUnit(s.id)}
                  className={`px-3 py-1.5 rounded text-sm ${selectedUnit === s.id ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'}`}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Resumen por Sistema */}
        <div className="mb-4">
          <p className="text-sm font-medium text-zinc-700 mb-3">Resumen por Sistema</p>
          {saldosData.sistemas.length === 0 ? (
            <div className="text-center py-8 text-zinc-500">
              <AlertCircle className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>No se encontró tu RFC en ningún sistema configurado</p>
              <p className="text-sm mt-2">Contacta al administrador para verificar tu registro</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {sistemasFiltrados.map(s => (
                  <div key={s.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-zinc-900">{s.name}</h3>
                      {getStatusIcon(s.status)}
                    </div>
                    {s.status === 'not_found' ? (
                      <p className="text-sm text-zinc-500">RFC no encontrado en este sistema</p>
                    ) : s.status === 'error' ? (
                      <p className="text-sm text-red-500">Error de conexión</p>
                    ) : (
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-zinc-500">Facturas</span>
                          <span className="font-medium">{s.facturas}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-zinc-500">Importe</span>
                          <span className="font-medium">{formatCurrency(s.importe)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-zinc-500">Pagado</span>
                          <span className="font-medium text-green-600">{formatCurrency(s.pagado)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-zinc-500">Saldo</span>
                          <span className="font-medium text-orange-500">{formatCurrency(s.saldo)}</span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="flex gap-4 mt-3 text-xs text-zinc-500 flex-wrap">
                {saldosData.sistemas.map(s => (
                  <span key={s.id} className="flex items-center gap-1">
                    {getStatusIcon(s.status)}
                    {s.name}: {s.facturas} registros
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Saldo por Sucursal */}
      {sucursalesFiltradas.length > 0 && (
        <div className="bg-white rounded-xl border p-5">
          <h2 className="font-semibold text-zinc-900 mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5 text-zinc-400" />
            Saldo por Sucursal
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sucursalesFiltradas.map(s => (
              <div key={s.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-semibold text-zinc-900">{s.name}</h3>
                </div>
                {getSystemBadge(s.system_type)}
                <div className="space-y-2 text-sm mt-3">
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Facturas:</span>
                    <span className="font-medium">{s.facturas}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Importe:</span>
                    <span className="font-medium">{formatCurrency(s.importe)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Pagado:</span>
                    <span className="font-medium text-green-600">{formatCurrency(s.pagado)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Saldo:</span>
                    <span className="font-medium text-orange-500">{formatCurrency(s.saldo)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Facturas Pendientes de Pago */}
      {facturasAgrupadas.length > 0 && (
        <div className="bg-white rounded-xl border p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-zinc-900">Facturas Pendientes de Pago ({saldosData.facturas_pendientes.length})</h2>
            <div className="flex gap-2">
              <input 
                type="text" 
                placeholder="Buscar folio, documento..." 
                className="px-3 py-1.5 border rounded-lg text-sm w-64"
              />
            </div>
          </div>

          <div className="space-y-2">
            {facturasAgrupadas.map((suc, idx) => (
              <div key={idx} className="border rounded-lg">
                <button 
                  onClick={() => toggleSucursalDetails(suc.id)}
                  className="w-full flex items-center justify-between p-4 hover:bg-zinc-50"
                >
                  <div className="flex items-center gap-3">
                    {expandedSucursal === suc.id ? (
                      <ChevronDown className="h-4 w-4 text-zinc-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-zinc-400" />
                    )}
                    <div className="text-left">
                      <span className="font-medium text-zinc-900">{suc.name}</span>
                      <span className="ml-2">{getSystemBadge(suc.system_type)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-8 text-sm">
                    <span>Facturas: <strong>{suc.facturas_detalle.length || suc.facturas}</strong></span>
                    <span>Importe: <strong>{formatCurrency(suc.importe)}</strong></span>
                    <span>Saldo: <strong className="text-orange-500">{formatCurrency(suc.saldo)}</strong></span>
                  </div>
                </button>
                
                {expandedSucursal === suc.id && suc.facturas_detalle.length > 0 && (
                  <div className="border-t bg-zinc-50 p-4 overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-zinc-500">
                          <th className="py-2">Folio</th>
                          <th className="py-2">Ref (8)</th>
                          <th className="py-2">Documento</th>
                          <th className="py-2">Fecha</th>
                          <th className="py-2">Vencimiento</th>
                          <th className="py-2">Días Venc.</th>
                          <th className="py-2 text-right">Importe</th>
                          <th className="py-2 text-right">Saldo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {suc.facturas_detalle.map((det, i) => (
                          <tr key={i} className="border-t">
                            <td className="py-2">{det.folio}</td>
                            <td className="py-2">{det.referencia}</td>
                            <td className="py-2">{det.documento}</td>
                            <td className="py-2">{det.fecha}</td>
                            <td className="py-2">{det.vencimiento}</td>
                            <td className={`py-2 ${det.dias_vencido > 0 ? 'text-red-500 font-medium' : 'text-green-600'}`}>
                              {det.dias_vencido > 0 ? `+${det.dias_vencido}` : det.dias_vencido}
                            </td>
                            <td className="py-2 text-right">{formatCurrency(det.importe)}</td>
                            <td className="py-2 text-right text-orange-500">{formatCurrency(det.saldo)}</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr className="border-t font-medium">
                          <td colSpan={6} className="py-2 text-right">Sub-total {suc.name}:</td>
                          <td className="py-2 text-right">{formatCurrency(suc.importe)}</td>
                          <td className="py-2 text-right text-orange-500">{formatCurrency(suc.saldo)}</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Total General */}
          <div className="mt-4 p-4 bg-zinc-100 rounded-lg flex items-center justify-between">
            <span className="font-semibold">TOTAL GENERAL ({saldosData.facturas_pendientes.length} facturas)</span>
            <div className="flex gap-8 text-sm">
              <span>Importe: <strong>{formatCurrency(totalFacturado)}</strong></span>
              <span>Saldo: <strong className="text-orange-500">{formatCurrency(totalSaldo)}</strong></span>
            </div>
          </div>
        </div>
      )}

      {/* Facturas Recientes */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-zinc-900">Facturas Recientes</h2>
          <button onClick={() => onNavigate('invoices')} className="text-sm text-zinc-500 hover:text-zinc-700">
            Ver todas →
          </button>
        </div>
        
        {recentInvoices.length === 0 ? (
          <div className="text-center py-8 text-zinc-500">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>No tienes facturas subidas</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-500 border-b">
                <th className="py-3">FOLIO</th>
                <th className="py-3">FECHA</th>
                <th className="py-3">TOTAL</th>
                <th className="py-3">VALIDACIÓN</th>
                <th className="py-3">PAGO</th>
              </tr>
            </thead>
            <tbody>
              {recentInvoices.map((inv, idx) => (
                <tr key={idx} className="border-b hover:bg-zinc-50">
                  <td className="py-3">{inv.serie}{inv.folio || inv.uuid?.substring(0, 8)}</td>
                  <td className="py-3">{new Date(inv.fecha_emision).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })}</td>
                  <td className="py-3">{formatCurrency(inv.total)}</td>
                  <td className="py-3">{getStatusBadge(inv.status === 'validated' ? 'Validada' : 'Pendiente')}</td>
                  <td className="py-3">{getPaymentBadge('Sin Pagar')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
