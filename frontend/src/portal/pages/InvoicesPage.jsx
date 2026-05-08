/**
 * Portal Proveedores - Lista de Facturas
 * FASE AUTH-SECURITY-01: Usa credentials: 'include' para cookie httpOnly
 */
import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import logger from '../../services/logger';
import { FileText, Search, Filter, Download, Eye } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function InvoicesPage({ supplier, onNavigate }) {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const loadInvoices = useCallback(async () => {
    setLoading(true);
    try {
      let url = `${API_URL}/api/portal/invoices`;
      if (filterStatus !== 'all') {
        url += `?status=${filterStatus}`;
      }
      
      const response = await fetch(url, {
        credentials: 'include'  // FASE AUTH-SECURITY-01: Cookie httpOnly
      });
      
      if (response.ok) {
        const data = await response.json();
        setInvoices(data);
      }
    } catch (error) {
      logger.error('Error cargando facturas:', error);
      toast.error('Error al cargar facturas');
    } finally {
      setLoading(false);
    }
  }, [filterStatus]);

  useEffect(() => {
    loadInvoices();
  }, [loadInvoices]);

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
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  const filteredInvoices = invoices.filter(inv => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      inv.uuid?.toLowerCase().includes(term) ||
      inv.folio?.toLowerCase().includes(term) ||
      inv.serie?.toLowerCase().includes(term) ||
      inv.receptor_nombre?.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-zinc-800">Mis Facturas</h2>
        <button
          onClick={() => onNavigate('upload')}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <FileText className="h-4 w-4" />
          Subir Factura
        </button>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-xl p-4 shadow-sm border flex flex-wrap gap-4 items-center">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
            <input
              type="text"
              placeholder="Buscar por UUID, folio, receptor..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-zinc-400" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="border border-zinc-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">Todos los estados</option>
            <option value="uploaded">Subidas</option>
            <option value="validated">Validadas</option>
            <option value="matched">Conciliadas</option>
            <option value="paid">Pagadas</option>
            <option value="rejected">Rechazadas</option>
          </select>
        </div>
      </div>

      {/* Tabla de facturas */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-zinc-500 mt-2">Cargando facturas...</p>
          </div>
        ) : filteredInvoices.length === 0 ? (
          <div className="p-8 text-center text-zinc-500">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>No se encontraron facturas</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-50 border-b">
                <tr>
                  <th className="text-left py-3 px-4 font-semibold text-zinc-600">Folio</th>
                  <th className="text-left py-3 px-4 font-semibold text-zinc-600">UUID</th>
                  <th className="text-left py-3 px-4 font-semibold text-zinc-600">Fecha</th>
                  <th className="text-left py-3 px-4 font-semibold text-zinc-600">Receptor</th>
                  <th className="text-right py-3 px-4 font-semibold text-zinc-600">Total</th>
                  <th className="text-center py-3 px-4 font-semibold text-zinc-600">Estado</th>
                  <th className="text-center py-3 px-4 font-semibold text-zinc-600">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredInvoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-zinc-50">
                    <td className="py-3 px-4">
                      <span className="font-medium">
                        {invoice.serie || ''}{invoice.folio || '-'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-mono text-xs text-zinc-500">
                        {invoice.uuid?.substring(0, 8)}...
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {new Date(invoice.fecha_emision).toLocaleDateString('es-MX')}
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-zinc-800">{invoice.receptor_nombre || '-'}</p>
                        <p className="text-xs text-zinc-400">{invoice.receptor_rfc}</p>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right font-semibold">
                      {formatCurrency(invoice.total)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {getStatusBadge(invoice.status)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        className="p-2 hover:bg-zinc-100 rounded-lg"
                        title="Ver detalle"
                      >
                        <Eye className="h-4 w-4 text-zinc-500" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Resumen */}
      {!loading && filteredInvoices.length > 0 && (
        <div className="bg-zinc-50 rounded-xl p-4 border flex items-center justify-between">
          <span className="text-zinc-600">
            Mostrando {filteredInvoices.length} factura(s)
          </span>
          <span className="font-semibold text-zinc-800">
            Total: {formatCurrency(filteredInvoices.reduce((sum, inv) => sum + (inv.total || 0), 0))}
          </span>
        </div>
      )}
    </div>
  );
}
