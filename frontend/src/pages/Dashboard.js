import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Server, Users, Bell, FileText } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Dashboard = () => {
  const [metrics, setMetrics] = useState({
    total_servers: 0,
    total_users: 0,
    total_alerts: 0,
    total_queries: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const response = await api.get('/dashboard/metrics');
      setMetrics(response.data);
    } catch (error) {
      console.error('Error loading metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const statsCards = [
    {
      title: 'Servidores Activos',
      value: metrics.total_servers,
      icon: Server,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      testId: 'metric-servers'
    },
    {
      title: 'Usuarios',
      value: metrics.total_users,
      icon: Users,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      testId: 'metric-users'
    },
    {
      title: 'Alertas Activas',
      value: metrics.total_alerts,
      icon: Bell,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      testId: 'metric-alerts'
    },
    {
      title: 'Consultas Configuradas',
      value: metrics.total_queries,
      icon: FileText,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      testId: 'metric-queries'
    }
  ];

  const chartData = [
    { name: 'Servidores', value: metrics.total_servers },
    { name: 'Usuarios', value: metrics.total_users },
    { name: 'Alertas', value: metrics.total_alerts },
    { name: 'Consultas', value: metrics.total_queries }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96" data-testid="dashboard-loading">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      <div>
        <h1 className="text-3xl font-extrabold text-zinc-900" style={{ fontFamily: 'Manrope, sans-serif' }} data-testid="dashboard-title">
          Dashboard
        </h1>
        <p className="text-zinc-600 mt-1">Resumen general del sistema</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title} className="border border-zinc-200 shadow-sm hover:border-zinc-300 transition-colors" data-testid={stat.testId}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-zinc-600">{stat.title}</p>
                    <p className="text-3xl font-bold text-zinc-900 mt-2 font-data">{stat.value}</p>
                  </div>
                  <div className={`${stat.bgColor} p-3 rounded-lg`}>
                    <Icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Chart */}
      <Card className="border border-zinc-200 shadow-sm">
        <CardHeader>
          <CardTitle className="font-semibold" style={{ fontFamily: 'Manrope, sans-serif' }}>Estadísticas del Sistema</CardTitle>
          <CardDescription>Visualización de métricas principales</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
              <XAxis dataKey="name" stroke="#52525b" />
              <YAxis stroke="#52525b" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#ffffff', 
                  border: '1px solid #e4e4e7',
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="value" fill="#18181b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card className="border border-zinc-200 shadow-sm">
        <CardHeader>
          <CardTitle className="font-semibold" style={{ fontFamily: 'Manrope, sans-serif' }}>Acciones Rápidas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a 
              href="/reportes" 
              className="p-4 border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors"
              data-testid="quick-action-reports"
            >
              <FileText className="h-6 w-6 text-zinc-700 mb-2" />
              <h3 className="font-semibold text-zinc-900">Generar Reporte</h3>
              <p className="text-sm text-zinc-600 mt-1">Crear un nuevo reporte de inventario</p>
            </a>
            
            <a 
              href="/servidores" 
              className="p-4 border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors"
              data-testid="quick-action-servers"
            >
              <Server className="h-6 w-6 text-zinc-700 mb-2" />
              <h3 className="font-semibold text-zinc-900">Gestionar Servidores</h3>
              <p className="text-sm text-zinc-600 mt-1">Administrar conexiones SQL</p>
            </a>
            
            <a 
              href="/alertas" 
              className="p-4 border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors"
              data-testid="quick-action-alerts"
            >
              <Bell className="h-6 w-6 text-zinc-700 mb-2" />
              <h3 className="font-semibold text-zinc-900">Configurar Alertas</h3>
              <p className="text-sm text-zinc-600 mt-1">Establecer notificaciones automáticas</p>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;