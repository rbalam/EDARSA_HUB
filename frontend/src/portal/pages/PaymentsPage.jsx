/**
 * PaymentsPage - Mis Pagos
 * FASE AUTH-SECURITY-01: Ya no recibe token, usa cookie httpOnly
 */
import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import logger from '../../services/logger';
import { 
  CreditCard, DollarSign, Calendar, CheckCircle, 
  Clock, Download, Filter, Search
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function PaymentsPage({ supplier, onNavigate }) {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const loadPayments = useCallback(async () => {
    try {
      // Por ahora mostramos datos de ejemplo
      // TODO: Implementar endpoint de pagos reales
      setPayments([]);
    } catch (error) {
      logger.error('Error cargando pagos:', error);
      toast.error('Error al cargar los pagos');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPayments();
  }, [loadPayments]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(value || 0);
  };

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
          <h1 className="text-2xl font-bold text-zinc-900">Mis Pagos</h1>
          <p className="text-zinc-500">Historial de pagos recibidos</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-zinc-50 text-sm">
            <Download className="h-4 w-4" />
            Exportar
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-zinc-500">Total Pagado</p>
              <p className="text-2xl font-bold text-green-600">{formatCurrency(0)}</p>
            </div>
            <CheckCircle className="h-10 w-10 text-zinc-300" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-5 border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-zinc-500">Pagos del Mes</p>
              <p className="text-2xl font-bold text-zinc-900">0</p>
            </div>
            <Calendar className="h-10 w-10 text-zinc-300" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-5 border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-zinc-500">Pendiente de Pago</p>
              <p className="text-2xl font-bold text-orange-500">{formatCurrency(0)}</p>
            </div>
            <Clock className="h-10 w-10 text-zinc-300" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-5 border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-zinc-500">Facturas Pagadas</p>
              <p className="text-2xl font-bold text-zinc-900">0</p>
            </div>
            <CreditCard className="h-10 w-10 text-zinc-300" />
          </div>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-xl border p-4">
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg text-sm ${filter === 'all' ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'}`}
            >
              Todos
            </button>
            <button
              onClick={() => setFilter('month')}
              className={`px-4 py-2 rounded-lg text-sm ${filter === 'month' ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'}`}
            >
              Este mes
            </button>
            <button
              onClick={() => setFilter('year')}
              className={`px-4 py-2 rounded-lg text-sm ${filter === 'year' ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'}`}
            >
              Este año
            </button>
          </div>
          <div className="relative">
            <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              placeholder="Buscar pago..."
              className="pl-10 pr-4 py-2 border rounded-lg text-sm w-64"
            />
          </div>
        </div>
      </div>

      {/* Lista de pagos */}
      <div className="bg-white rounded-xl border p-6">
        {payments.length === 0 ? (
          <div className="text-center py-12 text-zinc-500">
            <DollarSign className="h-16 w-16 mx-auto mb-4 opacity-30" />
            <h3 className="text-lg font-medium text-zinc-700 mb-2">No hay pagos registrados</h3>
            <p className="text-sm">
              Los pagos recibidos aparecerán aquí cuando sean procesados
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-500 border-b">
                <th className="py-3">REFERENCIA</th>
                <th className="py-3">FECHA</th>
                <th className="py-3">FACTURAS</th>
                <th className="py-3">MONTO</th>
                <th className="py-3">MÉTODO</th>
                <th className="py-3">ESTADO</th>
                <th className="py-3">ACCIONES</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((payment) => (
                <tr key={payment.referencia || payment.id} className="border-b hover:bg-zinc-50">
                  <td className="py-3 font-medium">{payment.referencia}</td>
                  <td className="py-3">{payment.fecha}</td>
                  <td className="py-3">{payment.facturas}</td>
                  <td className="py-3 font-medium text-green-600">{formatCurrency(payment.monto)}</td>
                  <td className="py-3">{payment.metodo}</td>
                  <td className="py-3">
                    <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-700">
                      {payment.estado}
                    </span>
                  </td>
                  <td className="py-3">
                    <button className="text-zinc-500 hover:text-zinc-700">
                      <Download className="h-4 w-4" />
                    </button>
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
