/**
 * Portal Proveedores - Estado de Cuenta
 * FASE AUTH-SECURITY-01: Usa credentials: 'include' para cookie httpOnly
 */
import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { DollarSign, FileText, CheckCircle, Clock, TrendingUp } from 'lucide-react';
import logger from '../../services/logger';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function AccountStatusPage({ supplier, onNavigate }) {
  const [accountData, setAccountData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadAccountStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/portal/account-status`, {
        credentials: 'include'  // FASE AUTH-SECURITY-01: Cookie httpOnly
      });
      
      if (response.ok) {
        const data = await response.json();
        setAccountData(data);
      }
    } catch (error) {
      logger.error('Error cargando estado de cuenta:', error);
      toast.error('Error al cargar estado de cuenta');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadAccountStatus();
  }, [loadAccountStatus]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(value || 0);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const resumen = accountData?.resumen || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl p-6 shadow-sm border">
        <h2 className="text-2xl font-bold text-zinc-800">Estado de Cuenta</h2>
        <div className="mt-2">
          <p className="text-lg text-zinc-600">{accountData?.razon_social}</p>
          <p className="text-sm text-zinc-400">RFC: {accountData?.rfc}</p>
        </div>
      </div>

      {/* KPIs principales */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-xl p-6 shadow-lg">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-3 bg-white/20 rounded-lg">
              <TrendingUp className="h-6 w-6" />
            </div>
            <span className="text-blue-100">Total Facturado</span>
          </div>
          <p className="text-3xl font-bold">{formatCurrency(resumen.total_facturado)}</p>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white rounded-xl p-6 shadow-lg">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-3 bg-white/20 rounded-lg">
              <CheckCircle className="h-6 w-6" />
            </div>
            <span className="text-green-100">Total Pagado</span>
          </div>
          <p className="text-3xl font-bold">{formatCurrency(resumen.total_pagado)}</p>
        </div>

        <div className="bg-gradient-to-br from-orange-500 to-orange-600 text-white rounded-xl p-6 shadow-lg">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-3 bg-white/20 rounded-lg">
              <Clock className="h-6 w-6" />
            </div>
            <span className="text-orange-100">Saldo Pendiente</span>
          </div>
          <p className="text-3xl font-bold">{formatCurrency(resumen.saldo_pendiente)}</p>
        </div>
      </div>

      {/* Resumen de facturas */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-zinc-800 mb-4">Resumen de Facturas</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-zinc-50 rounded-xl">
            <FileText className="h-8 w-8 mx-auto text-zinc-400 mb-2" />
            <p className="text-2xl font-bold text-zinc-800">{resumen.facturas_subidas || 0}</p>
            <p className="text-sm text-zinc-500">Subidas</p>
          </div>
          
          <div className="text-center p-4 bg-blue-50 rounded-xl">
            <FileText className="h-8 w-8 mx-auto text-blue-500 mb-2" />
            <p className="text-2xl font-bold text-blue-800">{resumen.facturas_conciliadas || 0}</p>
            <p className="text-sm text-blue-600">Conciliadas</p>
          </div>
          
          <div className="text-center p-4 bg-green-50 rounded-xl">
            <CheckCircle className="h-8 w-8 mx-auto text-green-500 mb-2" />
            <p className="text-2xl font-bold text-green-800">{resumen.facturas_pagadas || 0}</p>
            <p className="text-sm text-green-600">Pagadas</p>
          </div>
          
          <div className="text-center p-4 bg-yellow-50 rounded-xl">
            <Clock className="h-8 w-8 mx-auto text-yellow-500 mb-2" />
            <p className="text-2xl font-bold text-yellow-800">
              {(resumen.facturas_subidas || 0) - (resumen.facturas_pagadas || 0)}
            </p>
            <p className="text-sm text-yellow-600">Pendientes</p>
          </div>
        </div>
      </div>

      {/* Datos bancarios */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-zinc-800 mb-4">Datos Bancarios Registrados</h3>
        
        {supplier?.banco || supplier?.clabe ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-zinc-500">Banco</p>
              <p className="font-medium text-zinc-800">{supplier?.banco || 'No registrado'}</p>
            </div>
            <div>
              <p className="text-sm text-zinc-500">CLABE</p>
              <p className="font-mono text-zinc-800">{supplier?.clabe || 'No registrada'}</p>
            </div>
            <div>
              <p className="text-sm text-zinc-500">Cuenta</p>
              <p className="font-mono text-zinc-800">{supplier?.cuenta || 'No registrada'}</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-6 bg-yellow-50 rounded-xl">
            <p className="text-yellow-800">No tienes datos bancarios registrados</p>
            <p className="text-sm text-yellow-600 mt-1">Contacta al administrador para actualizarlos</p>
          </div>
        )}
      </div>

      {/* Acciones */}
      <div className="flex gap-4">
        <button
          onClick={() => onNavigate('invoices')}
          className="flex-1 bg-white border border-zinc-300 text-zinc-700 py-3 rounded-xl font-semibold hover:bg-zinc-50 transition-colors"
        >
          Ver todas las facturas
        </button>
        <button
          onClick={() => onNavigate('upload')}
          className="flex-1 bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors"
        >
          Subir nueva factura
        </button>
      </div>
    </div>
  );
}
