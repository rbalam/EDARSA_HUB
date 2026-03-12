import { useEffect, useState, useCallback } from 'react';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingDown, 
  TrendingUp, 
  Package, 
  DollarSign, 
  AlertTriangle,
  CheckCircle2,
  Warehouse,
  RefreshCw,
  Loader2,
  BarChart3,
  PieChart as PieChartIcon
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  ComposedChart,
  Line,
  Area,
  Brush,
  ReferenceLine
} from 'recharts';
import { toast } from 'sonner';

const COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f43f5e'];

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '$0';
  return new Intl.NumberFormat('es-MX', { 
    style: 'currency', 
    currency: 'MXN',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

const formatNumber = (value) => {
  if (value === null || value === undefined) return '0';
  return new Intl.NumberFormat('es-MX').format(value);
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-zinc-200 rounded-lg shadow-lg">
        <p className="font-medium text-zinc-900">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ color: entry.color }} className="text-sm">
            {entry.name}: {entry.name.includes('Costo') ? formatCurrency(entry.value) : formatNumber(entry.value)}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [servers, setServers] = useState([]);
  const [selectedServer, setSelectedServer] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [error, setError] = useState(null);

  // Cargar servidores configurados
  useEffect(() => {
    loadServers();
  }, []);

  // Cargar datos cuando se selecciona un servidor
  useEffect(() => {
    if (selectedServer) {
      loadDashboardData(selectedServer);
    }
  }, [selectedServer]);

  const loadServers = async () => {
    try {
      const response = await api.get('/dashboard/servers-configured');
      setServers(response.data);
      if (response.data.length > 0) {
        setSelectedServer(response.data[0].id);
      } else {
        setLoading(false);
      }
    } catch (error) {
      console.error('Error loading servers:', error);
      setError('Error al cargar servidores');
      setLoading(false);
    }
  };

  const loadDashboardData = async (serverId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/dashboard/inventory-summary?server_id=${serverId}`);
      if (response.data.success) {
        setDashboardData(response.data.data);
      } else {
        setError(response.data.message);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError('Error al cargar datos del dashboard');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    if (selectedServer) {
      loadDashboardData(selectedServer);
    }
  };

  // Si no hay servidores configurados
  if (!loading && servers.length === 0) {
    return (
      <div className="space-y-6" data-testid="dashboard-page">
        <div>
          <h1 className="text-3xl font-extrabold text-zinc-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Dashboard de Inventarios
          </h1>
          <p className="text-zinc-600 mt-1">Analisis de diferencias de inventario</p>
        </div>
        
        <Card className="border border-orange-200 bg-orange-50">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-orange-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-orange-800 mb-2">No hay servidores configurados</h2>
            <p className="text-orange-700 mb-4">
              Para ver el dashboard de inventarios, primero debes configurar las consultas SQL en al menos un servidor.
            </p>
            <a 
              href="/servidores" 
              className="inline-flex items-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              Ir a Servidores
            </a>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Loading state
  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-96" data-testid="dashboard-loading">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-zinc-400 mx-auto mb-4" />
          <p className="text-zinc-600">Cargando datos de inventario...</p>
        </div>
      </div>
    );
  }

  // Preparar datos para gráficos
  const topFaltantesCostoData = dashboardData?.top_faltantes_costo?.map(item => ({
    name: item.descripcion?.substring(0, 25) + (item.descripcion?.length > 25 ? '...' : '') || item.codigo,
    codigo: item.codigo,
    almacen: item.almacen_nombre,
    diferencia: Math.abs(item.diferencia || 0),
    costo: Math.abs(item.costo_diferencia || 0)
  })) || [];

  const topFaltantesCantidadData = dashboardData?.top_faltantes_cantidad?.map(item => ({
    name: item.descripcion?.substring(0, 25) + (item.descripcion?.length > 25 ? '...' : '') || item.codigo,
    codigo: item.codigo,
    almacen: item.almacen_nombre,
    diferencia: Math.abs(item.diferencia || 0),
    costo: Math.abs(item.costo_diferencia || 0)
  })) || [];

  const comparativoAlmacenData = dashboardData?.comparativo_almacen?.map(item => ({
    name: item.almacen_nombre?.substring(0, 15) || item.almacen,
    inicial: Math.abs(item.diferencia_inicial || 0),
    final: Math.abs(item.diferencia_final || 0),
    cambio: (item.diferencia_final || 0) - (item.diferencia_inicial || 0)
  })) || [];

  const resumenGrupoData = dashboardData?.resumen_por_grupo?.map(item => ({
    name: item.grupo?.substring(0, 20) || 'Sin grupo',
    value: Math.abs(item.total_costo_diferencia || 0),
    items: item.total_items
  })) || [];

  const resumenAlmacenData = dashboardData?.resumen_por_almacen?.map(item => ({
    name: item.almacen?.substring(0, 20) || item.idalmacen,
    faltante: item.total_costo_diferencia < 0 ? Math.abs(item.total_costo_diferencia) : 0,
    sobrante: item.total_costo_diferencia > 0 ? item.total_costo_diferencia : 0,
    items: item.total_items
  })) || [];

  const kpis = dashboardData?.kpis || {};

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-zinc-900" style={{ fontFamily: 'Manrope, sans-serif' }} data-testid="dashboard-title">
            Dashboard de Inventarios
          </h1>
          <p className="text-zinc-600 mt-1">
            Analisis de diferencias - {dashboardData?.server_name || 'Selecciona un servidor'}
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={selectedServer} onValueChange={setSelectedServer}>
            <SelectTrigger className="w-[250px]" data-testid="server-selector">
              <SelectValue placeholder="Seleccionar servidor" />
            </SelectTrigger>
            <SelectContent>
              {servers.map(server => (
                <SelectItem key={server.id} value={server.id}>
                  {server.name} ({server.system_type})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 rounded-lg border border-zinc-200 hover:bg-zinc-50 transition-colors disabled:opacity-50"
            data-testid="refresh-button"
          >
            <RefreshCw className={`h-5 w-5 text-zinc-600 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <Card className="border border-red-200 bg-red-50">
          <CardContent className="p-4">
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card className="border border-red-200 bg-gradient-to-br from-red-50 to-white" data-testid="kpi-diferencia">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="h-4 w-4 text-red-500" />
              <span className="text-xs font-medium text-red-600">Costo Diferencias</span>
            </div>
            <p className="text-xl font-bold text-red-700">{formatCurrency(kpis.total_diferencia_costo)}</p>
          </CardContent>
        </Card>

        <Card className="border border-orange-200 bg-gradient-to-br from-orange-50 to-white" data-testid="kpi-faltantes">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="h-4 w-4 text-orange-500" />
              <span className="text-xs font-medium text-orange-600">Faltantes</span>
            </div>
            <p className="text-xl font-bold text-orange-700">{formatNumber(kpis.total_faltantes)}</p>
          </CardContent>
        </Card>

        <Card className="border border-green-200 bg-gradient-to-br from-green-50 to-white" data-testid="kpi-sobrantes">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-xs font-medium text-green-600">Sobrantes</span>
            </div>
            <p className="text-xl font-bold text-green-700">{formatNumber(kpis.total_sobrantes)}</p>
          </CardContent>
        </Card>

        <Card className="border border-blue-200 bg-gradient-to-br from-blue-50 to-white" data-testid="kpi-items">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Package className="h-4 w-4 text-blue-500" />
              <span className="text-xs font-medium text-blue-600">Items Revisados</span>
            </div>
            <p className="text-xl font-bold text-blue-700">{formatNumber(kpis.total_items)}</p>
          </CardContent>
        </Card>

        <Card className="border border-yellow-200 bg-gradient-to-br from-yellow-50 to-white" data-testid="kpi-diferencias">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              <span className="text-xs font-medium text-yellow-600">Con Diferencia</span>
            </div>
            <p className="text-xl font-bold text-yellow-700">{formatNumber(kpis.total_items_con_diferencia)}</p>
          </CardContent>
        </Card>

        <Card className="border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white" data-testid="kpi-precision">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span className="text-xs font-medium text-emerald-600">Precision</span>
            </div>
            <p className="text-xl font-bold text-emerald-700">{kpis.precision_inventario?.toFixed(1)}%</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top 10 Faltantes por Costo */}
        <Card className="border border-zinc-200 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-red-500" />
                  Top 10 Faltantes por Costo
                </CardTitle>
                <CardDescription>Productos con mayor perdida economica</CardDescription>
              </div>
              <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                {formatCurrency(topFaltantesCostoData.reduce((sum, item) => sum + item.costo, 0))}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={topFaltantesCostoData} layout="vertical" margin={{ left: 20, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" horizontal={true} vertical={false} />
                <XAxis type="number" tickFormatter={(value) => formatCurrency(value)} stroke="#71717a" fontSize={11} />
                <YAxis type="category" dataKey="name" width={150} stroke="#71717a" fontSize={11} tick={{ fill: '#3f3f46' }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="costo" name="Costo Diferencia" fill="#ef4444" radius={[0, 4, 4, 0]} />
                <Brush dataKey="name" height={20} stroke="#d4d4d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Top 10 Faltantes por Cantidad */}
        <Card className="border border-zinc-200 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <Package className="h-5 w-5 text-orange-500" />
                  Top 10 Faltantes por Cantidad
                </CardTitle>
                <CardDescription>Productos con mayor diferencia en unidades</CardDescription>
              </div>
              <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
                {formatNumber(topFaltantesCantidadData.reduce((sum, item) => sum + item.diferencia, 0))} uds
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={topFaltantesCantidadData} layout="vertical" margin={{ left: 20, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" horizontal={true} vertical={false} />
                <XAxis type="number" tickFormatter={(value) => formatNumber(value)} stroke="#71717a" fontSize={11} />
                <YAxis type="category" dataKey="name" width={150} stroke="#71717a" fontSize={11} tick={{ fill: '#3f3f46' }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="diferencia" name="Diferencia (uds)" fill="#f97316" radius={[0, 4, 4, 0]} />
                <Brush dataKey="name" height={20} stroke="#d4d4d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Comparativo Inicial vs Final por Almacen */}
        <Card className="border border-zinc-200 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Warehouse className="h-5 w-5 text-blue-500" />
              Comparativo: Inicio vs Fin de Mes por Almacen
            </CardTitle>
            <CardDescription>Diferencias en costo del primer inventario vs el ultimo del mes</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart data={comparativoAlmacenData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                <XAxis dataKey="name" stroke="#71717a" fontSize={11} angle={-45} textAnchor="end" height={80} />
                <YAxis tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`} stroke="#71717a" fontSize={11} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="inicial" name="Costo Dif. Inicial" fill="#93c5fd" radius={[4, 4, 0, 0]} />
                <Bar dataKey="final" name="Costo Dif. Final" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Line type="monotone" dataKey="cambio" name="Cambio" stroke="#ef4444" strokeWidth={2} dot={{ fill: '#ef4444' }} />
                <ReferenceLine y={0} stroke="#71717a" strokeDasharray="3 3" />
                <Brush dataKey="name" height={20} stroke="#d4d4d8" />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Distribucion por Grupo/Categoria */}
        <Card className="border border-zinc-200 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <PieChartIcon className="h-5 w-5 text-purple-500" />
              Diferencias por Grupo/Categoria
            </CardTitle>
            <CardDescription>Distribucion del costo de diferencias por categoria</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={resumenGrupoData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {resumenGrupoData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 3 - Resumen por Almacen (Full Width) */}
      <Card className="border border-zinc-200 shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Warehouse className="h-5 w-5 text-emerald-500" />
            Resumen Acumulado por Almacen
          </CardTitle>
          <CardDescription>Faltantes vs sobrantes por almacen (valores absolutos en costo)</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={resumenAlmacenData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
              <XAxis dataKey="name" stroke="#71717a" fontSize={11} angle={-45} textAnchor="end" height={80} />
              <YAxis tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`} stroke="#71717a" fontSize={11} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="faltante" name="Faltante ($)" stackId="a" fill="#ef4444" />
              <Bar dataKey="sobrante" name="Sobrante ($)" stackId="a" fill="#22c55e" />
              <Brush dataKey="name" height={20} stroke="#d4d4d8" y={260} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Tabla de Almacenes */}
      <Card className="border border-zinc-200 shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg font-semibold">Detalle por Almacen</CardTitle>
          <CardDescription>Resumen de diferencias del ultimo inventario por almacen</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-200 bg-zinc-50">
                  <th className="text-left p-3 font-semibold text-zinc-700">Almacen</th>
                  <th className="text-right p-3 font-semibold text-zinc-700">Items</th>
                  <th className="text-right p-3 font-semibold text-zinc-700">Diferencia Total</th>
                  <th className="text-right p-3 font-semibold text-zinc-700">Costo Diferencia</th>
                  <th className="text-center p-3 font-semibold text-zinc-700">Estado</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData?.resumen_por_almacen?.map((item, index) => (
                  <tr key={index} className="border-b border-zinc-100 hover:bg-zinc-50">
                    <td className="p-3 font-medium text-zinc-900">{item.almacen || item.idalmacen}</td>
                    <td className="p-3 text-right text-zinc-600">{formatNumber(item.total_items)}</td>
                    <td className="p-3 text-right font-mono">
                      <span className={item.total_diferencia < 0 ? 'text-red-600' : item.total_diferencia > 0 ? 'text-green-600' : 'text-zinc-600'}>
                        {formatNumber(item.total_diferencia)}
                      </span>
                    </td>
                    <td className="p-3 text-right font-mono">
                      <span className={item.total_costo_diferencia < 0 ? 'text-red-600 font-semibold' : item.total_costo_diferencia > 0 ? 'text-green-600' : 'text-zinc-600'}>
                        {formatCurrency(item.total_costo_diferencia)}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      {item.total_costo_diferencia < -10000 ? (
                        <Badge className="bg-red-100 text-red-700">Critico</Badge>
                      ) : item.total_costo_diferencia < 0 ? (
                        <Badge className="bg-yellow-100 text-yellow-700">Atencion</Badge>
                      ) : (
                        <Badge className="bg-green-100 text-green-700">OK</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
