/**
 * SupplierHub - Dashboard con KPIs y Saldos por Sucursal
 * Diseño exacto según mockups proporcionados
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { 
  FileText, DollarSign, Clock, CheckCircle, RefreshCw, 
  ChevronDown, ChevronUp, Upload, Download, FileSpreadsheet,
  AlertCircle, Building2, Search
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
  const [searchTerm, setSearchTerm] = useState('');
  const [resumenExpanded, setResumenExpanded] = useState(true);

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
  
  const sucursalesFiltradas = (selectedUnit === 'all'
    ? (selectedSystem === 'all' 
        ? saldosData.sucursales 
        : saldosData.sucursales.filter(s => s.sistema_id === selectedSystem))
    : saldosData.sucursales.filter(s => s.id === selectedUnit))
    .sort((a, b) => b.saldo - a.saldo);

  // Totales para KPIs
  const totalFacturado = saldosData.totales.importe;
  const totalPagado = saldosData.totales.pagado;
  const totalSaldo = saldosData.totales.saldo;
  const totalFacturasPendientes = facturasAgrupadas.reduce((acc, s) => acc + (s.facturas_detalle?.length || s.facturas || 0), 0);

  // Sistema badge con colores específicos
  const SystemBadge = ({ type }) => {
    if (type === 'MPRO') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
          Management Pro
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-50 text-orange-600 border border-orange-200">
        Soft Restaurant
      </span>
    );
  };

  // Sistema badge pequeño para facturas
  const SystemBadgeSmall = ({ type }) => {
    if (type === 'MPRO') {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700">
          MPro
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-600">
        SR
      </span>
    );
  };

  // Status icon
  const StatusIcon = ({ status }) => {
    if (status === 'connected') return <span className="w-2 h-2 bg-green-500 rounded-full inline-block"></span>;
    if (status === 'not_found') return <span className="w-2 h-2 bg-yellow-500 rounded-full inline-block"></span>;
    return <span className="w-2 h-2 bg-red-500 rounded-full inline-block"></span>;
  };

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
          <p className="text-gray-500 text-sm">Bienvenido, {supplier?.razon_social}</p>
        </div>
        <div className="flex gap-2">
          <button 
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium text-gray-700"
            data-testid="btn-excel"
          >
            <FileSpreadsheet className="h-4 w-4" />
            Excel
          </button>
          <button 
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium text-gray-700"
            data-testid="btn-pdf"
          >
            <Download className="h-4 w-4" />
            PDF
          </button>
          <button 
            onClick={() => onNavigate('upload')}
            className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 text-sm font-medium"
            data-testid="btn-subir-factura"
          >
            <Upload className="h-4 w-4" />
            Subir Factura
          </button>
        </div>
      </div>

      {/* KPIs Cards */}
      <div className="grid grid-cols-4 gap-4">
        {/* Total Facturado */}
        <div className="bg-gray-50 rounded-xl p-5 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Total Facturado</p>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(stats?.total_facturado || totalFacturado)}</p>
            </div>
            <div className="h-12 w-12 flex items-center justify-center">
              <FileText className="h-8 w-8 text-gray-300" />
            </div>
          </div>
        </div>
        
        {/* Total Pagado */}
        <div className="bg-gray-50 rounded-xl p-5 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Total Pagado</p>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(stats?.total_pagado || totalPagado)}</p>
            </div>
            <div className="h-12 w-12 flex items-center justify-center">
              <CheckCircle className="h-8 w-8 text-gray-300" />
            </div>
          </div>
        </div>
        
        {/* Saldo Pendiente */}
        <div className="bg-gray-50 rounded-xl p-5 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Saldo Pendiente</p>
              <p className="text-2xl font-bold text-orange-500">{formatCurrency(stats?.saldo_pendiente || totalSaldo)}</p>
            </div>
            <div className="h-12 w-12 flex items-center justify-center">
              <Clock className="h-8 w-8 text-gray-300" />
            </div>
          </div>
        </div>
        
        {/* Facturas Pendientes */}
        <div className="bg-gray-50 rounded-xl p-5 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Facturas Pendientes</p>
              <p className="text-2xl font-bold text-gray-900">{totalFacturasPendientes || saldosData.totales.facturas}</p>
            </div>
            <div className="h-12 w-12 flex items-center justify-center">
              <DollarSign className="h-8 w-8 text-gray-300" />
            </div>
          </div>
        </div>
      </div>

      {/* Fuente de Datos */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-gray-400" />
            <h2 className="font-semibold text-gray-900">Fuente de Datos</h2>
            {loadingSaldos && <RefreshCw className="h-4 w-4 animate-spin text-gray-400 ml-2" />}
          </div>
          <button 
            onClick={loadSaldosReales}
            disabled={loadingSaldos}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 disabled:opacity-50"
            data-testid="btn-actualizar"
          >
            <RefreshCw className={`h-4 w-4 ${loadingSaldos ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>

        {/* Filtros por Sistema */}
        <div className="mb-4">
          <p className="text-xs text-gray-400 mb-2">Por Sistema</p>
          <div className="flex gap-2 flex-wrap">
            <button 
              onClick={() => { setSelectedSystem('all'); setSelectedUnit('all'); }}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selectedSystem === 'all' 
                  ? 'bg-gray-900 text-white' 
                  : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
              }`}
              data-testid="filter-todos-sistemas"
            >
              Todos los Sistemas
            </button>
            {saldosData.sistemas.filter(s => s.facturas > 0 || s.status === 'connected').map(s => (
              <button 
                key={s.id}
                onClick={() => { setSelectedSystem(s.id); setSelectedUnit('all'); }}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
                  selectedSystem === s.id 
                    ? 'bg-gray-900 text-white' 
                    : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                <StatusIcon status={s.status} />
                {s.name}
              </button>
            ))}
          </div>
        </div>

        {/* Filtros por Unidad */}
        {saldosData.sucursales.filter(s => s.facturas > 0).length > 0 && (
          <div className="mb-6">
            <p className="text-xs text-gray-400 mb-2">Por Unidad / Empresa</p>
            <div className="flex gap-2 flex-wrap">
              <button 
                onClick={() => setSelectedUnit('all')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  selectedUnit === 'all' 
                    ? 'bg-gray-900 text-white' 
                    : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
                }`}
                data-testid="filter-todas-unidades"
              >
                Todas las Unidades
              </button>
              {(selectedSystem === 'all' 
                ? saldosData.sucursales.filter(s => s.facturas > 0) 
                : saldosData.sucursales.filter(s => s.sistema_id === selectedSystem && s.facturas > 0)
              ).map(s => (
                <button 
                  key={s.id}
                  onClick={() => setSelectedUnit(s.id)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    selectedUnit === s.id 
                      ? 'bg-gray-900 text-white' 
                      : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Resumen por Sistema - Collapsible */}
        <div className="border-t pt-4">
          <button 
            onClick={() => setResumenExpanded(!resumenExpanded)}
            className="flex items-center justify-between w-full text-left mb-4"
          >
            <p className="text-sm font-medium text-gray-700">Resumen por Sistema</p>
            {resumenExpanded ? (
              <ChevronUp className="h-4 w-4 text-gray-400" />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-400" />
            )}
          </button>
          
          {resumenExpanded && (
            <>
              {saldosData.sistemas.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <AlertCircle className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>No se encontró tu RFC en ningún sistema configurado</p>
                  <p className="text-sm mt-2">Contacta al administrador para verificar tu registro</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {sistemasFiltrados.map(s => (
                    <div key={s.id} className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-semibold text-gray-900">{s.name}</h3>
                        <StatusIcon status={s.status} />
                      </div>
                      {s.status === 'not_found' ? (
                        <p className="text-sm text-gray-500">RFC no encontrado en este sistema</p>
                      ) : s.status === 'error' ? (
                        <p className="text-sm text-red-500">Error de conexión</p>
                      ) : (
                        <div className="space-y-1.5 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Facturas</span>
                            <span className="font-medium text-gray-900">{s.facturas}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Importe</span>
                            <span className="font-medium text-gray-900">{formatCurrency(s.importe)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Saldo</span>
                            <span className="font-semibold text-orange-500">{formatCurrency(s.saldo)}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              
              {/* Status indicators */}
              <div className="flex gap-4 mt-4 text-xs text-gray-500 flex-wrap border-t pt-3">
                {saldosData.sistemas.map(s => (
                  <span key={s.id} className="flex items-center gap-1.5">
                    <StatusIcon status={s.status} />
                    {s.name}: {s.facturas} registros
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Saldo por Sucursal */}
      {sucursalesFiltradas.filter(s => s.facturas > 0).length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5 text-gray-400" />
            Saldo por Sucursal
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sucursalesFiltradas.filter(s => s.facturas > 0).map(s => (
              <div key={s.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                <div className="mb-2">
                  <h3 className="font-semibold text-gray-900 text-lg">{s.name}</h3>
                  <div className="mt-1">
                    <SystemBadge type={s.system_type} />
                  </div>
                </div>
                <div className="space-y-2 text-sm mt-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">Facturas:</span>
                    <span className="font-medium text-gray-900">{s.facturas}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">Importe:</span>
                    <span className="font-medium text-gray-900">{formatCurrency(s.importe)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">Pagado:</span>
                    <span className="font-medium text-green-600">{formatCurrency(s.pagado)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">Saldo:</span>
                    <span className="font-semibold text-orange-500">{formatCurrency(s.saldo)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Facturas Pendientes de Pago */}
      {facturasAgrupadas.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">
              Facturas Pendientes de Pago ({totalFacturasPendientes})
            </h2>
            <div className="flex gap-2">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input 
                  type="text" 
                  placeholder="Buscar folio, documento..." 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-gray-200"
                  data-testid="search-facturas"
                />
              </div>
              <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium text-gray-700">
                <FileText className="h-4 w-4" />
                Conciliar
              </button>
            </div>
          </div>

          <div className="space-y-2">
            {facturasAgrupadas.map((suc, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg overflow-hidden">
                <button 
                  onClick={() => toggleSucursalDetails(suc.id)}
                  className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${expandedSucursal === suc.id ? '' : '-rotate-90'}`} />
                    <span className="font-medium text-gray-900">{suc.name}</span>
                    <SystemBadgeSmall type={suc.system_type} />
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    <span className="text-gray-600">Facturas: <strong className="text-gray-900">{suc.facturas_detalle?.length || suc.facturas}</strong></span>
                    <span className="text-gray-600">Importe: <strong className="text-gray-900">{formatCurrency(suc.importe)}</strong></span>
                    <span className="text-gray-600">Saldo: <strong className="text-orange-500">{formatCurrency(suc.saldo)}</strong></span>
                  </div>
                </button>
                
                {expandedSucursal === suc.id && suc.facturas_detalle?.length > 0 && (
                  <div className="border-t border-gray-200 bg-gray-50 p-4 overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-gray-500">
                          <th className="py-2 font-medium">Folio</th>
                          <th className="py-2 font-medium">Referencia</th>
                          <th className="py-2 font-medium">Documento</th>
                          <th className="py-2 font-medium">Fecha</th>
                          <th className="py-2 font-medium">Vencimiento</th>
                          <th className="py-2 font-medium">Días Venc.</th>
                          <th className="py-2 font-medium text-right">Importe</th>
                          <th className="py-2 font-medium text-right">Saldo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {suc.facturas_detalle.map((det, i) => (
                          <tr key={i} className="border-t border-gray-200">
                            <td className="py-2 text-gray-900">{det.folio}</td>
                            <td className="py-2 text-gray-600">{det.referencia}</td>
                            <td className="py-2 text-gray-600">{det.documento}</td>
                            <td className="py-2 text-gray-600">{det.fecha}</td>
                            <td className="py-2 text-gray-600">{det.vencimiento}</td>
                            <td className={`py-2 font-medium ${det.dias_vencido > 0 ? 'text-red-500' : 'text-green-600'}`}>
                              {det.dias_vencido > 0 ? `+${det.dias_vencido}` : det.dias_vencido}
                            </td>
                            <td className="py-2 text-right text-gray-900">{formatCurrency(det.importe)}</td>
                            <td className="py-2 text-right font-medium text-orange-500">{formatCurrency(det.saldo)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Total General */}
          <div className="mt-4 p-4 bg-gray-900 text-white rounded-lg flex items-center justify-between">
            <span className="font-semibold">TOTAL GENERAL ({totalFacturasPendientes} facturas)</span>
            <div className="flex gap-8 text-sm">
              <span>Importe: <strong>{formatCurrency(totalFacturado)}</strong></span>
              <span>Saldo: <strong className="text-orange-400">{formatCurrency(totalSaldo)}</strong></span>
            </div>
          </div>
        </div>
      )}

      {/* Facturas Recientes */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Facturas Recientes</h2>
          <button 
            onClick={() => onNavigate('invoices')} 
            className="text-sm text-gray-500 hover:text-gray-700 font-medium"
            data-testid="ver-todas-facturas"
          >
            Ver todas &rarr;
          </button>
        </div>
        
        {recentInvoices.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-600">No tienes facturas subidas</p>
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
                  <td className="py-3 text-gray-900">{inv.serie}{inv.folio || inv.uuid?.substring(0, 8)}</td>
                  <td className="py-3 text-gray-600">{new Date(inv.fecha_emision).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })}</td>
                  <td className="py-3 text-gray-900 font-medium">{formatCurrency(inv.total)}</td>
                  <td className="py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      inv.status === 'validated' 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {inv.status === 'validated' ? 'Validada' : 'Pendiente'}
                    </span>
                  </td>
                  <td className="py-3">
                    <span className="px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-700">
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
