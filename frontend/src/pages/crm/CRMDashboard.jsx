import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Target, Users, TrendingUp, DollarSign, UserPlus, Briefcase, Activity } from 'lucide-react';
import api from '@/lib/api';

const EMPRESA_ID = '00000000-0000-0000-0000-000000000001';

export default function CRMDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/crm/native/dashboard?empresa_id=${EMPRESA_ID}`);
      setDashboard(response.data);
    } catch (err) {
      setError('Error cargando dashboard');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-600 rounded-lg">
        {error}
      </div>
    );
  }

  const formatMoney = (amount) => {
    return new Intl.NumberFormat('es-MX', { 
      style: 'currency', 
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  return (
    <div className="space-y-6" data-testid="crm-dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Target className="h-6 w-6 text-blue-600" />
            CRM Dashboard
          </h1>
          <p className="text-gray-500">Métricas y KPIs de ventas</p>
        </div>
      </div>

      {/* KPIs principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Leads</p>
                <p className="text-2xl font-bold">{dashboard?.leads?.total || 0}</p>
                <p className="text-xs text-green-600">+{dashboard?.leads?.nuevos_mes || 0} este mes</p>
              </div>
              <UserPlus className="h-10 w-10 text-blue-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Oportunidades Abiertas</p>
                <p className="text-2xl font-bold">{dashboard?.oportunidades?.abiertas || 0}</p>
                <p className="text-xs text-gray-500">de {dashboard?.oportunidades?.total || 0} total</p>
              </div>
              <Briefcase className="h-10 w-10 text-purple-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Pipeline Total</p>
                <p className="text-2xl font-bold">{formatMoney(dashboard?.oportunidades?.monto_pipeline)}</p>
                <p className="text-xs text-gray-500">Valor total</p>
              </div>
              <DollarSign className="h-10 w-10 text-green-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Monto Ponderado</p>
                <p className="text-2xl font-bold">{formatMoney(dashboard?.oportunidades?.monto_ponderado)}</p>
                <p className="text-xs text-gray-500">Forecast ajustado</p>
              </div>
              <TrendingUp className="h-10 w-10 text-amber-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tasa de conversión y Leads por estatus */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Users className="h-5 w-5" />
              Leads por Estatus
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboard?.leads?.por_estatus?.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: item.ColorHex || '#6B7280' }}
                    ></div>
                    <span className="text-sm">{item.Nombre}</span>
                  </div>
                  <span className="font-semibold">{item.count || 0}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Tasa de Conversión</span>
                <span className="text-lg font-bold text-green-600">
                  {dashboard?.conversion?.tasa_conversion || 0}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Briefcase className="h-5 w-5" />
              Oportunidades por Etapa
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboard?.oportunidades?.por_etapa?.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: item.ColorHex || '#6B7280' }}
                    ></div>
                    <span className="text-sm">{item.Nombre}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-semibold">{item.count || 0}</span>
                    <span className="text-xs text-gray-500 ml-2">
                      {formatMoney(item.monto)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Actividad Reciente */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Actividad Reciente
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {dashboard?.actividad_reciente?.length > 0 ? (
              dashboard.actividad_reciente.map((item, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-sm">
                      {item.FolioOportunidad} - {item.NombreOportunidad}
                    </p>
                    <p className="text-xs text-gray-500">
                      {item.EtapaAnterior ? `${item.EtapaAnterior} → ` : ''}{item.EtapaNueva}
                    </p>
                  </div>
                  <div className="text-right text-xs text-gray-400">
                    {item.Usuario && <p>{item.Usuario}</p>}
                    <p>{new Date(item.FechaCambio).toLocaleDateString('es-MX')}</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-4">Sin actividad reciente</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
