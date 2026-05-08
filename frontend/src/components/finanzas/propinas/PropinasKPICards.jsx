/**
 * KPI Cards de resumen de propinas
 */

import { Card, CardContent } from '@/components/ui/card';
import { formatCurrency } from './utils';

export default function PropinasKPICards({ totales }) {
  return (
    <div className="grid grid-cols-4 gap-4" data-testid="propinas-kpis">
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-4">
          <p className="text-xs text-blue-600 font-medium">Propinas TPV</p>
          <p className="text-2xl font-bold text-blue-700">{formatCurrency(totales.propinas_tpv)}</p>
        </CardContent>
      </Card>
      <Card className="bg-amber-50 border-amber-200">
        <CardContent className="pt-4">
          <p className="text-xs text-amber-600 font-medium">Comisión (2%)</p>
          <p className="text-2xl font-bold text-amber-700">{formatCurrency(totales.comision)}</p>
        </CardContent>
      </Card>
      <Card className="bg-green-50 border-green-200">
        <CardContent className="pt-4">
          <p className="text-xs text-green-600 font-medium">A Pagar Meseros</p>
          <p className="text-2xl font-bold text-green-700">{formatCurrency(totales.a_pagar)}</p>
        </CardContent>
      </Card>
      <Card className="bg-purple-50 border-purple-200">
        <CardContent className="pt-4">
          <p className="text-xs text-purple-600 font-medium">Pagado</p>
          <p className="text-2xl font-bold text-purple-700">{formatCurrency(totales.pagado)}</p>
        </CardContent>
      </Card>
    </div>
  );
}
