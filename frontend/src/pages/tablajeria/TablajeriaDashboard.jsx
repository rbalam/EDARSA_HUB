import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Beef, FileText, Layers, Activity, TrendingUp, TrendingDown, 
  AlertTriangle, CheckCircle, Clock, RefreshCw 
} from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';

export default function TablajeriaDashboard() {
  const [stats, setStats] = useState(null);
  const [ordenesStats, setOrdenesStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const [plantillasRes, ordenesRes] = await Promise.all([
        api.get('/tablajeria/stats'),
        api.get('/tablajeria/ordenes-stats')
      ]);
      setStats(plantillasRes.data);
      setOrdenesStats(ordenesRes.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching stats:', err);
      setError('Error cargando estadísticas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const getEstatusColor = (estatus) => {
    const colors = {
      'BORRADOR': 'bg-gray-100 text-gray-700',
      'EN_EJECUCION': 'bg-blue-100 text-blue-700',
      'PENDIENTE_AUTORIZACION': 'bg-yellow-100 text-yellow-700',
      'CERRADA': 'bg-green-100 text-green-700',
      'CANCELADA': 'bg-red-100 text-red-700'
    };
    return colors[estatus] || 'bg-gray-100 text-gray-700';
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="tablajeria-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800 flex items-center gap-2">
            <Beef className="h-7 w-7 text-red-600" />
            Tablajería
          </h1>
          <p className="text-zinc-500">Gestión de plantillas y órdenes de producción</p>
        </div>
        <Button onClick={fetchStats} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-4">
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Plantillas Activas</p>
                <p className="text-2xl font-bold">{stats?.plantillas?.total || 0}</p>
              </div>
              <Layers className="h-8 w-8 text-blue-500" />
            </div>
            <div className="mt-2 text-xs text-zinc-400">
              {stats?.plantillas?.por_estatus?.PUBLICADA || 0} publicadas
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Órdenes Hoy</p>
                <p className="text-2xl font-bold">{ordenesStats?.total_ordenes || 0}</p>
              </div>
              <FileText className="h-8 w-8 text-green-500" />
            </div>
            <div className="mt-2 text-xs text-zinc-400">
              {ordenesStats?.ordenes_por_estatus?.CERRADA || 0} cerradas
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Rendimiento Promedio</p>
                <p className="text-2xl font-bold">
                  {ordenesStats?.metricas?.rendimiento_promedio?.toFixed(1) || '--'}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Merma Promedio</p>
                <p className="text-2xl font-bold">
                  {ordenesStats?.metricas?.merma_promedio?.toFixed(1) || '--'}%
                </p>
              </div>
              <TrendingDown className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Acciones rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/produccion/tablajeria/plantillas">
          <Card className="hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-blue-500">
            <CardContent className="py-6 flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Layers className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold">Plantillas</h3>
                <p className="text-sm text-zinc-500">Ver y gestionar plantillas</p>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link to="/produccion/tablajeria/ordenes">
          <Card className="hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-green-500">
            <CardContent className="py-6 flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <FileText className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold">Órdenes de Tablaje</h3>
                <p className="text-sm text-zinc-500">Crear y ejecutar órdenes</p>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="py-6 flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Activity className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold">Sincronización</h3>
              <p className="text-sm text-zinc-500">
                {stats?.ultima_sincronizacion?.ServidorNombre || 'Sin sincronización'}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Órdenes recientes */}
      {ordenesStats?.ordenes_recientes?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Órdenes Recientes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {ordenesStats.ordenes_recientes.map((orden, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 text-xs rounded ${getEstatusColor(orden.EstatusOrden)}`}>
                      {orden.EstatusOrden}
                    </span>
                    <span className="font-medium">{orden.FolioOrden}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-zinc-500">
                    <span>{orden.FechaOperacionMexico}</span>
                    {orden.RendimientoRealPorcentaje && (
                      <span className="font-medium text-emerald-600">
                        {orden.RendimientoRealPorcentaje.toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Plantillas por estatus */}
      {stats?.plantillas?.por_estatus && Object.keys(stats.plantillas.por_estatus).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Plantillas por Estatus</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(stats.plantillas.por_estatus).map(([estatus, count]) => (
                <div key={estatus} className="text-center p-3 bg-zinc-50 rounded-lg">
                  <p className="text-2xl font-bold">{count}</p>
                  <p className="text-xs text-zinc-500 uppercase">{estatus}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
