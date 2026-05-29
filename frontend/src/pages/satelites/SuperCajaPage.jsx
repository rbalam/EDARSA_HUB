import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CreditCard, RefreshCw, DollarSign, Receipt, TrendingUp } from 'lucide-react';

const SuperCajaPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Super Caja</h1>
          <p className="text-zinc-500">Módulo Satélite - Punto de Venta Centralizado</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500">Ventas del Día</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <DollarSign className="h-8 w-8 text-green-500" />
              <span className="text-2xl font-bold">$0.00</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500">Tickets Hoy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Receipt className="h-8 w-8 text-blue-500" />
              <span className="text-2xl font-bold">0</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500">Ticket Promedio</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-8 w-8 text-amber-500" />
              <span className="text-2xl font-bold">$0.00</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500">Estado Caja</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CreditCard className="h-8 w-8 text-zinc-400" />
              <span className="text-lg font-medium text-zinc-500">Sin Turno</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="py-16 text-center">
          <CreditCard className="h-16 w-16 mx-auto text-zinc-300 mb-4" />
          <h3 className="text-xl font-semibold text-zinc-700 mb-2">Módulo Super Caja</h3>
          <p className="text-zinc-500 max-w-md mx-auto">
            Sistema de punto de venta centralizado. Conectando con la infraestructura Edge de EDARSA HUB.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default SuperCajaPage;
