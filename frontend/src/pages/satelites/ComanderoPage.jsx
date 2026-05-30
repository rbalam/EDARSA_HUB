import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChefHat, RefreshCw, Utensils, Clock, Users } from 'lucide-react';

const ComanderoPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Comandero</h1>
          <p className="text-zinc-500">Módulo Satélite - Sistema de Comandas y Gestión de Piso</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500">Comensales Hoy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Users className="h-8 w-8 text-blue-500" />
              <span className="text-2xl font-bold">0</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500">Platillos Servidos</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Utensils className="h-8 w-8 text-green-500" />
              <span className="text-2xl font-bold">0</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500">Turno Actual</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Clock className="h-8 w-8 text-amber-500" />
              <span className="text-lg font-medium text-zinc-500">--:--</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500">Estado Cocina</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <ChefHat className="h-8 w-8 text-zinc-400" />
              <span className="text-lg font-medium text-zinc-500">Inactivo</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="py-16 text-center">
          <ChefHat className="h-16 w-16 mx-auto text-zinc-300 mb-4" />
          <h3 className="text-xl font-semibold text-zinc-700 mb-2">Módulo Comandero</h3>
          <p className="text-zinc-500 max-w-md mx-auto">
            Sistema de comandas y gestión de piso de ventas. Integración con KDS y control de mesas de EDARSA HUB.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ComanderoPage;
