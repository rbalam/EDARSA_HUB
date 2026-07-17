/**
 * Subcomponentes para TesoreriaCorteZ
 */
import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import {
  Building2, Calendar, DollarSign, CheckCircle2, AlertCircle,
  Clock, Upload, RefreshCw, ChevronRight, ChevronDown, FileText,
  Banknote, Coins, Eye, Edit2, X, Check
} from 'lucide-react';

// ============================================================================
// Utilidades
// ============================================================================

export const formatCurrency = (amount) => {
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(amount || 0);
};

export const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  try {
    return new Date(dateStr).toLocaleDateString('es-MX', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  } catch {
    return dateStr;
  }
};

// ============================================================================
// ConteoEfectivo - Componente para conteo de billetes y monedas
// ============================================================================

export function ConteoEfectivo({ conteo, onChange, readOnly = false }) {
  const billetes = conteo?.billetes || {};
  const monedas = conteo?.monedas || {};
  
  const calcularTotal = () => {
    return (
      (billetes.b1000 || 0) * 1000 +
      (billetes.b500 || 0) * 500 +
      (billetes.b200 || 0) * 200 +
      (billetes.b100 || 0) * 100 +
      (billetes.b50 || 0) * 50 +
      (billetes.b20 || 0) * 20 +
      (monedas.m20 || 0) * 20 +
      (monedas.m10 || 0) * 10 +
      (monedas.m5 || 0) * 5 +
      (monedas.m2 || 0) * 2 +
      (monedas.m1 || 0) * 1 +
      (monedas.m050 || 0) * 0.50
    );
  };
  
  const handleBilleteChange = (key, value) => {
    const newBilletes = { ...billetes, [key]: parseInt(value) || 0 };
    onChange({ billetes: newBilletes, monedas });
  };
  
  const handleMonedaChange = (key, value) => {
    const newMonedas = { ...monedas, [key]: parseInt(value) || 0 };
    onChange({ billetes, monedas: newMonedas });
  };
  
  const BILLETES = [
    { key: 'b1000', label: '$1,000', value: 1000, color: 'bg-purple-100 border-purple-300' },
    { key: 'b500', label: '$500', value: 500, color: 'bg-blue-100 border-blue-300' },
    { key: 'b200', label: '$200', value: 200, color: 'bg-green-100 border-green-300' },
    { key: 'b100', label: '$100', value: 100, color: 'bg-red-100 border-red-300' },
    { key: 'b50', label: '$50', value: 50, color: 'bg-pink-100 border-pink-300' },
    { key: 'b20', label: '$20', value: 20, color: 'bg-cyan-100 border-cyan-300' }
  ];
  
  const MONEDAS = [
    { key: 'm20', label: '$20', value: 20 },
    { key: 'm10', label: '$10', value: 10 },
    { key: 'm5', label: '$5', value: 5 },
    { key: 'm2', label: '$2', value: 2 },
    { key: 'm1', label: '$1', value: 1 },
    { key: 'm050', label: '$0.50', value: 0.50 }
  ];
  
  return (
    <div className="space-y-4">
      {/* Billetes */}
      <div>
        <h4 className="text-sm font-medium text-zinc-700 mb-2 flex items-center gap-2">
          <Banknote className="h-4 w-4" />
          Billetes
        </h4>
        <div className="grid grid-cols-3 gap-2">
          {BILLETES.map(b => (
            <div key={b.key} className={`p-2 rounded border ${b.color}`}>
              <label className="text-xs font-medium text-zinc-600">{b.label}</label>
              <div className="flex items-center gap-1 mt-1">
                <Input
                  type="number"
                  min="0"
                  value={billetes[b.key] || ''}
                  onChange={(e) => handleBilleteChange(b.key, e.target.value)}
                  disabled={readOnly}
                  className="h-8 text-sm"
                  placeholder="0"
                />
                <span className="text-xs text-zinc-500 whitespace-nowrap">
                  = {formatCurrency((billetes[b.key] || 0) * b.value)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Monedas */}
      <div>
        <h4 className="text-sm font-medium text-zinc-700 mb-2 flex items-center gap-2">
          <Coins className="h-4 w-4" />
          Monedas
        </h4>
        <div className="grid grid-cols-3 gap-2">
          {MONEDAS.map(m => (
            <div key={m.key} className="p-2 rounded border bg-amber-50 border-amber-200">
              <label className="text-xs font-medium text-zinc-600">{m.label}</label>
              <div className="flex items-center gap-1 mt-1">
                <Input
                  type="number"
                  min="0"
                  value={monedas[m.key] || ''}
                  onChange={(e) => handleMonedaChange(m.key, e.target.value)}
                  disabled={readOnly}
                  className="h-8 text-sm"
                  placeholder="0"
                />
                <span className="text-xs text-zinc-500 whitespace-nowrap">
                  = {formatCurrency((monedas[m.key] || 0) * m.value)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Total */}
      <div className="bg-zinc-800 text-white rounded-lg p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm">TOTAL CONTADO:</span>
          <span className="text-2xl font-bold">{formatCurrency(calcularTotal())}</span>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// ResumenCards - Tarjetas de resumen de estados
// ============================================================================

export function ResumenCards({ resumen }) {
  if (!resumen) return null;
  
  const cards = [
    { key: 'PENDIENTE', label: 'Pendientes', color: 'yellow', icon: Clock, field: 'total_esperado' },
    { key: 'EN_PROCESO', label: 'En Proceso', color: 'blue', icon: RefreshCw, field: 'total_esperado' },
    { key: 'CUADRADO', label: 'Cuadrados', color: 'green', icon: CheckCircle2, field: 'total_depositado' },
    { key: 'DESCUADRE', label: 'Descuadre', color: 'red', icon: AlertCircle, field: 'total_diferencia' }
  ];
  
  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      {cards.map(({ key, label, color, icon: Icon, field }) => (
        <Card key={key} className={`border-l-4 border-l-${color}-500`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-zinc-500">{label}</p>
                <p className={`text-2xl font-bold text-${color}-600`}>{resumen[key]?.count || 0}</p>
                <p className="text-xs text-zinc-400">{formatCurrency(resumen[key]?.[field])}</p>
              </div>
              <Icon className={`h-8 w-8 text-${color}-500`} />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ============================================================================
// CorteCard - Tarjeta individual de corte pendiente
// ============================================================================

export function CorteCard({ corte, onIniciarCuadre }) {
  return (
    <Card className="hover:shadow-md transition">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-2 rounded-lg ${
              corte.fuente === 'SOFTRESTAURANT' ? 'bg-emerald-100' : 'bg-indigo-100'
            }`}>
              <Building2 className={`h-5 w-5 ${
                corte.fuente === 'SOFTRESTAURANT' ? 'text-emerald-600' : 'text-indigo-600'
              }`} />
            </div>
            <div>
              <p className="font-medium">{corte.sucursal_nombre}</p>
              <p className="text-xs text-zinc-500">Folio: {corte.folio_corte}</p>
            </div>
            <div className="text-center px-4 border-l">
              <p className="text-xs text-zinc-500">Fecha Corte</p>
              <p className="font-medium">{formatDate(corte.fecha_corte)}</p>
            </div>
            <div className="text-center px-4 border-l">
              <p className="text-xs text-zinc-500">Efectivo Ventas</p>
              <p className="font-medium text-green-600">{formatCurrency(corte.efectivo_ventas)}</p>
            </div>
            <div className="text-center px-4 border-l">
              <p className="text-xs text-zinc-500">Propinas Pagadas</p>
              <p className="font-medium text-orange-600">{formatCurrency(corte.propinas_pagadas)}</p>
            </div>
            <div className="text-center px-4 border-l bg-zinc-100 rounded p-2">
              <p className="text-xs text-zinc-500">A Depositar</p>
              <p className="font-bold text-lg">{formatCurrency(corte.monto_a_depositar)}</p>
            </div>
            <div className="text-center px-4 border-l">
              <p className="text-xs text-zinc-500">Depósito Esperado</p>
              <p className="font-medium text-blue-600">{formatDate(corte.fecha_deposito_esperada)}</p>
            </div>
          </div>
          {typeof onIniciarCuadre === 'function' && (
            <Button
              onClick={() => onIniciarCuadre(corte)}
              className="bg-amber-500 hover:bg-amber-600"
            >
              <DollarSign className="h-4 w-4 mr-1" />
              Cuadrar
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// CuadreCard - Tarjeta de cuadre completado
// ============================================================================

export function CuadreCard({ cuadre, onVerDetalle, onEditar }) {
  const getEstadoBadge = (estado) => {
    const estilos = {
      'CUADRADO': 'bg-green-100 text-green-700',
      'DESCUADRE': 'bg-red-100 text-red-700',
      'EN_PROCESO': 'bg-blue-100 text-blue-700',
      'PENDIENTE': 'bg-yellow-100 text-yellow-700'
    };
    return estilos[estado] || 'bg-zinc-100 text-zinc-700';
  };
  
  return (
    <Card className={`hover:shadow-md transition ${cuadre.estado === 'DESCUADRE' ? 'border-l-4 border-l-red-500' : ''}`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-2 rounded-lg bg-zinc-100">
              <Building2 className="h-5 w-5 text-zinc-600" />
            </div>
            <div>
              <p className="font-medium">{cuadre.sucursal_nombre}</p>
              <p className="text-xs text-zinc-500">Folio Corte: {cuadre.folio_corte}</p>
            </div>
            <div className="text-center px-4 border-l">
              <p className="text-xs text-zinc-500">Fecha Corte</p>
              <p className="font-medium">{formatDate(cuadre.fecha_corte)}</p>
            </div>
            <div className="text-center px-4 border-l">
              <p className="text-xs text-zinc-500">Esperado</p>
              <p className="font-medium">{formatCurrency(cuadre.monto_esperado)}</p>
            </div>
            <div className="text-center px-4 border-l">
              <p className="text-xs text-zinc-500">Depositado</p>
              <p className="font-medium text-green-600">{formatCurrency(cuadre.monto_depositado)}</p>
            </div>
            <div className="text-center px-4 border-l">
              <p className="text-xs text-zinc-500">Diferencia</p>
              <p className={`font-bold ${cuadre.diferencia !== 0 ? 'text-red-600' : 'text-green-600'}`}>
                {formatCurrency(cuadre.diferencia)}
              </p>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getEstadoBadge(cuadre.estado)}`}>
              {cuadre.estado}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => onVerDetalle(cuadre)}>
              <Eye className="h-4 w-4" />
            </Button>
            {cuadre.estado !== 'CUADRADO' && (
              <Button variant="outline" size="sm" onClick={() => onEditar(cuadre)}>
                <Edit2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// EmptyState - Estado vacío genérico
// ============================================================================

export function EmptyState({ icon: Icon = CheckCircle2, message, iconColor = 'text-green-300' }) {
  return (
    <Card className="border-2 border-dashed">
      <CardContent className="py-8 text-center">
        <Icon className={`h-12 w-12 ${iconColor} mx-auto mb-3`} />
        <p className="text-zinc-500">{message}</p>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// FichaDepositoForm - Formulario de ficha de depósito
// ============================================================================

export function FichaDepositoForm({ fichaDeposito, onUpdate }) {
  return (
    <div>
      <h3 className="font-medium mb-3 flex items-center gap-2">
        <FileText className="h-5 w-5 text-blue-600" />
        Ficha de Depósito Bancario
      </h3>
      <div className="space-y-3">
        <div className="border-2 border-dashed rounded-lg p-6 text-center">
          <Upload className="h-8 w-8 text-zinc-400 mx-auto mb-2" />
          <p className="text-sm text-zinc-500">Arrastra o haz clic para subir la ficha</p>
          <input type="file" className="hidden" accept="image/*,.pdf" />
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-zinc-500">Fecha Depósito</label>
            <Input
              type="date"
              value={fichaDeposito.fecha_deposito || ''}
              onChange={(e) => onUpdate('fecha_deposito', e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-zinc-500">Banco</label>
            <Input
              value={fichaDeposito.banco || ''}
              onChange={(e) => onUpdate('banco', e.target.value)}
              placeholder="BBVA, Santander..."
            />
          </div>
          <div>
            <label className="text-xs text-zinc-500">Referencia</label>
            <Input
              value={fichaDeposito.referencia || ''}
              onChange={(e) => onUpdate('referencia', e.target.value)}
              placeholder="Número de referencia"
            />
          </div>
          <div>
            <label className="text-xs text-zinc-500">Cuenta</label>
            <Input
              value={fichaDeposito.cuenta || ''}
              onChange={(e) => onUpdate('cuenta', e.target.value)}
              placeholder="Número de cuenta"
            />
          </div>
          <div className="col-span-2">
            <label className="text-xs text-zinc-500">Importe Depositado</label>
            <Input
              type="number"
              step="0.01"
              value={fichaDeposito.importe || ''}
              onChange={(e) => onUpdate('importe', parseFloat(e.target.value) || 0)}
              placeholder="0.00"
              className="text-lg font-bold"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// ComparativaCard - Card de comparativa en modal
// ============================================================================

export function ComparativaCard({ esperado, contado, depositado }) {
  const diferencia = (depositado || 0) - esperado;
  const esCuadrado = Math.abs(diferencia) <= 1;
  
  return (
    <Card className="bg-zinc-800 text-white">
      <CardContent className="p-4">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-xs text-zinc-400">Esperado (Corte Z)</p>
            <p className="text-xl font-bold">{formatCurrency(esperado)}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-400">Contado</p>
            <p className="text-xl font-bold text-cyan-400">{formatCurrency(contado)}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-400">Depositado</p>
            <p className="text-xl font-bold text-green-400">{formatCurrency(depositado || 0)}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-400">Diferencia</p>
            <p className={`text-xl font-bold ${esCuadrado ? 'text-green-400' : 'text-red-400'}`}>
              {formatCurrency(diferencia)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
