/**
 * Portal Proveedores - Dashboard Principal
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { FileText, Upload, DollarSign, Clock, CheckCircle, XCircle } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function DashboardPage({ supplier, token, onNavigate }) {
  const [stats, setStats] = useState(null);
  const [recentInvoices, setRecentInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // Cargar estado de cuenta
      const statsRes = await fetch(`${API_URL}/api/portal/account-status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData.resumen);
      }

      // Cargar facturas recientes
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

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(value || 0);
  };

  const getStatusBadge = (status) => {
    const badges = {
      uploaded: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Subida' },
      validated: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Validada' },
      matched: { bg: 'bg-green-100', text: 'text-green-700', label: 'Conciliada' },
      rejected: { bg: 'bg-red-100', text: 'text-red-700', label: 'Rechazada' },
      paid: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Pagada' }
    };
    const badge = badges[status] || badges.uploaded;
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Bienvenida */}
      <div className="bg-white rounded-xl p-6 shadow-sm border">
        <h2 className="text-2xl font-bold text-zinc-800">
          Bienvenido, {supplier?.nombre_contacto}
        </h2>
        <p className="text-zinc-500 mt-1">{supplier?.razon_social}</p>
        <p className="text-sm text-zinc-400">RFC: {supplier?.rfc}</p>
      </div>

      {/* KPIs */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl p-5 shadow-sm border">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 rounded-lg">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-zinc-500">Facturas Subidas</p>
                <p className="text-2xl font-bold text-zinc-800">{stats.facturas_subidas}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-5 shadow-sm border">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-zinc-500">Conciliadas</p>
                <p className="text-2xl font-bold text-zinc-800">{stats.facturas_conciliadas}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-5 shadow-sm border">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-emerald-100 rounded-lg">
                <DollarSign className="h-6 w-6 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-zinc-500">Total Facturado</p>
                <p className="text-xl font-bold text-zinc-800">{formatCurrency(stats.total_facturado)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-5 shadow-sm border">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-orange-100 rounded-lg">
                <Clock className="h-6 w-6 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-zinc-500">Saldo Pendiente</p>
                <p className="text-xl font-bold text-orange-600">{formatCurrency(stats.saldo_pendiente)}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Acciones rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={() => onNavigate('upload')}
          className="bg-blue-600 text-white rounded-xl p-6 shadow-sm hover:bg-blue-700 transition-colors text-left"
        >
          <Upload className="h-8 w-8 mb-3" />
          <h3 className="text-lg font-semibold">Subir Factura</h3>
          <p className="text-blue-200 text-sm mt-1">Carga tu XML y PDF de factura</p>
        </button>

        <button
          onClick={() => onNavigate('account')}
          className="bg-white border rounded-xl p-6 shadow-sm hover:bg-zinc-50 transition-colors text-left"
        >
          <DollarSign className="h-8 w-8 mb-3 text-green-600" />
          <h3 className="text-lg font-semibold text-zinc-800">Estado de Cuenta</h3>
          <p className="text-zinc-500 text-sm mt-1">Consulta tus pagos y saldos</p>
        </button>
      </div>

      {/* Facturas recientes */}
      <div className="bg-white rounded-xl shadow-sm border">
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="font-semibold text-zinc-800">Facturas Recientes</h3>
          <button
            onClick={() => onNavigate('invoices')}
            className="text-blue-600 text-sm hover:underline"
          >
            Ver todas →
          </button>
        </div>
        
        {recentInvoices.length === 0 ? (
          <div className="p-8 text-center text-zinc-500">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>No tienes facturas subidas</p>
            <button
              onClick={() => onNavigate('upload')}
              className="text-blue-600 mt-2 hover:underline"
            >
              Subir primera factura
            </button>
          </div>
        ) : (
          <div className="divide-y">
            {recentInvoices.map((invoice) => (
              <div key={invoice.id} className="p-4 hover:bg-zinc-50 flex items-center justify-between">
                <div>
                  <p className="font-medium text-zinc-800">
                    {invoice.serie || ''}{invoice.folio || invoice.uuid?.substring(0, 8)}
                  </p>
                  <p className="text-sm text-zinc-500">
                    {new Date(invoice.fecha_emision).toLocaleDateString('es-MX')}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-zinc-800">{formatCurrency(invoice.total)}</p>
                  {getStatusBadge(invoice.status)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sucursales asignadas */}
      {supplier?.sucursales_asignadas?.length > 0 && (
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <h3 className="font-semibold text-zinc-800 mb-3">Sucursales Asignadas</h3>
          <div className="flex flex-wrap gap-2">
            {supplier.sucursales_asignadas.map((suc, idx) => (
              <span key={idx} className="px-3 py-1 bg-zinc-100 rounded-full text-sm">
                {suc}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
