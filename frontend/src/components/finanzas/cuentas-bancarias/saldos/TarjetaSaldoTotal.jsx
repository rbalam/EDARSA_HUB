import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../../ui/card';
import { Wallet, TrendingUp, AlertCircle } from 'lucide-react';
import { Skeleton } from '../../../ui/skeleton';

/**
 * Tarjeta que muestra el saldo total bancario consolidado
 */
export function TarjetaSaldoTotal({ saldoTotal, loading }) {
  // Formatear moneda
  const formatCurrency = (value, moneda = 'MXN') => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: moneda,
      minimumFractionDigits: 2,
    }).format(value || 0);
  };

  // Formatear fecha
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-12 w-12 rounded-lg" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-[150px]" />
              <Skeleton className="h-8 w-[200px]" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const tieneSaldo = saldoTotal && saldoTotal.saldo_total > 0;
  const cuentasConSaldo = saldoTotal?.cuentas_con_saldo || 0;

  return (
    <Card className="bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200" data-testid="tarjeta-saldo-total">
      <CardContent className="pt-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-emerald-100 rounded-xl">
              <Wallet className="h-8 w-8 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600 font-medium">Saldo Bancario Total</p>
              <p className="text-3xl font-bold text-emerald-700">
                {tieneSaldo 
                  ? formatCurrency(saldoTotal.saldo_total, saldoTotal.moneda || 'MXN')
                  : '$0.00'
                }
              </p>
            </div>
          </div>

          <div className="flex flex-col lg:items-end gap-1 text-sm">
            <div className="flex items-center gap-2 text-gray-500">
              <TrendingUp className="h-4 w-4" />
              <span>
                {cuentasConSaldo} cuenta{cuentasConSaldo !== 1 ? 's' : ''} con saldo
              </span>
            </div>
            {saldoTotal?.fecha_calculo && (
              <span className="text-gray-400 text-xs">
                Calculado: {formatDate(saldoTotal.fecha_calculo)}
              </span>
            )}
          </div>
        </div>

        {!tieneSaldo && (
          <div className="mt-4 flex items-center gap-2 text-gray-500 text-sm">
            <AlertCircle className="h-4 w-4" />
            <span>No hay saldos registrados. Capture el saldo de las cuentas bancarias.</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default TarjetaSaldoTotal;
