import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Beef, FileText, Layers, Activity, TrendingUp, TrendingDown, 
  AlertTriangle, CheckCircle, Clock, RefreshCw, Package,
  Calculator, BarChart3, PieChart, AlertCircle, FilePlus
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export default function TablajeriaDashboard() {
  const navigate = useNavigate();
  const [kpis, setKpis] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [rendimientosPorPlantilla, setRendimientosPorPlantilla] = useState([]);
  const [topMermas, setTopMermas] = useState([]);
  const [resumenCosteo, setResumenCosteo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [kpisRes, alertasRes, rendimientosRes, mermasRes, costeoRes] = await Promise.all([
        api.get('/tablajeria/dashboard/kpis'),
        api.get('/tablajeria/dashboard/alertas?umbral=5'),
        api.get('/tablajeria/dashboard/rendimientos-plantilla?limit=5'),
        api.get('/tablajeria/dashboard/top-mermas?limit=5'),
        api.get('/tablajeria/dashboard/resumen-costeo')
      ]);
      
      setKpis(kpisRes.data);
      setAlertas(alertasRes.data || []);
      setRendimientosPorPlantilla(rendimientosRes.data || []);
      setTopMermas(mermasRes.data || []);
      setResumenCosteo(costeoRes.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard:', err);
      setError('Error cargando dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const getEstadoColor = (estado) => {
    const colors = {
      'OPTIMO': 'text-green-600 bg-green-50',
      'ALERTA': 'text-yellow-600 bg-yellow-50',
      'CRITICO': 'text-red-600 bg-red-50'
    };
    return colors[estado] || 'text-gray-600 bg-gray-50';
  };

  const getSeveridadColor = (severidad) => {
    const colors = {
      'ALTA': 'text-red-600 bg-red-50 border-red-200',
      'MEDIA': 'text-yellow-600 bg-yellow-50 border-yellow-200',
      'BAJA': 'text-blue-600 bg-blue-50 border-blue-200'
    };
    return colors[severidad] || 'text-gray-600 bg-gray-50';
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
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Beef className="h-7 w-7" />
            Dashboard Tablajería
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Control de producción y transformación de insumos
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchDashboardData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </Button>
          <Button size="sm" onClick={() => navigate('/tablajeria/captura-directa')}>
            <FilePlus className="h-4 w-4 mr-2" />
            Nueva Orden
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 text-red-700 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          {error}
        </div>
      )}

      {/* KPIs Principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Órdenes Totales
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{kpis?.ordenes?.total || 0}</div>
            <div className="flex gap-2 mt-2 text-xs">
              <span className="text-green-600">{kpis?.ordenes?.cerradas || 0} cerradas</span>
              <span className="text-yellow-600">{kpis?.ordenes?.pendientes_autorizacion || 0} pendientes</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Rendimiento Promedio
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold flex items-center gap-2">
              {(kpis?.rendimiento?.promedio_porcentaje || 0).toFixed(1)}%
              {(kpis?.rendimiento?.desviacion_promedio || 0) >= 0 ? (
                <TrendingUp className="h-5 w-5 text-green-500" />
              ) : (
                <TrendingDown className="h-5 w-5 text-red-500" />
              )}
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              Desviación: {(kpis?.rendimiento?.desviacion_promedio || 0).toFixed(2)}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Merma Total
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">
              {(kpis?.mermas?.total_kg || 0).toFixed(1)} kg
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              Promedio: {(kpis?.mermas?.porcentaje_promedio || 0).toFixed(1)}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Costo Total Producción
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              ${(kpis?.costeo?.costo_total || 0).toLocaleString('es-MX', {minimumFractionDigits: 2})}
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              {kpis?.costeo?.total_costeos || 0} costeos registrados
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alertas */}
      {alertas.length > 0 && (
        <Card className="border-orange-200 bg-orange-50/50">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-orange-700">
              <AlertTriangle className="h-5 w-5" />
              Alertas de Rendimiento ({alertas.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alertas.slice(0, 3).map((alerta, idx) => (
                <div 
                  key={idx}
                  className={`p-3 rounded-lg border ${getSeveridadColor(alerta.severidad)}`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-medium">{alerta.folio}</span>
                      <span className="text-sm ml-2">- {alerta.insumo}</span>
                    </div>
                    <span className={`text-sm px-2 py-0.5 rounded ${getSeveridadColor(alerta.severidad)}`}>
                      {alerta.severidad}
                    </span>
                  </div>
                  <div className="text-sm mt-1">
                    Esperado: {alerta.rendimiento_esperado?.toFixed(1)}% | 
                    Real: {alerta.rendimiento_real?.toFixed(1)}% | 
                    <span className={alerta.desviacion < 0 ? 'text-red-600' : 'text-green-600'}>
                      Desviación: {alerta.desviacion?.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Rendimientos por Plantilla */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Rendimientos por Plantilla
            </CardTitle>
            <CardDescription>Top 5 plantillas más utilizadas</CardDescription>
          </CardHeader>
          <CardContent>
            {rendimientosPorPlantilla.length > 0 ? (
              <div className="space-y-4">
                {rendimientosPorPlantilla.map((plantilla, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-sm truncate max-w-[200px]">
                        {plantilla.nombre_plantilla}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded ${getEstadoColor(plantilla.estado)}`}>
                        {plantilla.estado}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress 
                        value={plantilla.rendimiento_real_promedio} 
                        className="flex-1 h-2"
                      />
                      <span className="text-sm font-medium w-16 text-right">
                        {plantilla.rendimiento_real_promedio?.toFixed(1)}%
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {plantilla.total_ordenes} órdenes | {plantilla.kg_procesados?.toFixed(0)} kg procesados
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Sin datos de rendimientos
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Mermas */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              Top Mermas
            </CardTitle>
            <CardDescription>Productos con mayor merma</CardDescription>
          </CardHeader>
          <CardContent>
            {topMermas.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Producto</TableHead>
                    <TableHead className="text-right">Total (kg)</TableHead>
                    <TableHead className="text-right">%</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topMermas.map((merma, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-medium">{merma.producto}</TableCell>
                      <TableCell className="text-right text-orange-600">
                        {merma.total_kg?.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right">
                        {merma.porcentaje_promedio?.toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Sin datos de mermas
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Resumen de Costeo */}
      {resumenCosteo && resumenCosteo.total_costeos > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5" />
              Resumen de Costeo
            </CardTitle>
            <CardDescription>Distribución de costos de producción</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="p-4 rounded-lg bg-blue-50">
                <div className="text-sm text-blue-700">Insumos</div>
                <div className="text-xl font-bold text-blue-900">
                  ${resumenCosteo.desglose?.insumos?.toFixed(2) || 0}
                </div>
                <div className="text-xs text-blue-600">
                  {resumenCosteo.porcentajes?.insumos?.toFixed(1)}%
                </div>
              </div>
              <div className="p-4 rounded-lg bg-green-50">
                <div className="text-sm text-green-700">Mano de Obra</div>
                <div className="text-xl font-bold text-green-900">
                  ${resumenCosteo.desglose?.mano_obra?.toFixed(2) || 0}
                </div>
                <div className="text-xs text-green-600">
                  {resumenCosteo.porcentajes?.mano_obra?.toFixed(1)}%
                </div>
              </div>
              <div className="p-4 rounded-lg bg-purple-50">
                <div className="text-sm text-purple-700">Indirectos</div>
                <div className="text-xl font-bold text-purple-900">
                  ${resumenCosteo.desglose?.indirectos?.toFixed(2) || 0}
                </div>
                <div className="text-xs text-purple-600">
                  {resumenCosteo.porcentajes?.indirectos?.toFixed(1)}%
                </div>
              </div>
              <div className="p-4 rounded-lg bg-yellow-50">
                <div className="text-sm text-yellow-700">Energía</div>
                <div className="text-xl font-bold text-yellow-900">
                  ${resumenCosteo.desglose?.energia?.toFixed(2) || 0}
                </div>
                <div className="text-xs text-yellow-600">
                  {resumenCosteo.porcentajes?.energia?.toFixed(1)}%
                </div>
              </div>
              <div className="p-4 rounded-lg bg-gray-50">
                <div className="text-sm text-gray-700">Otros</div>
                <div className="text-xl font-bold text-gray-900">
                  ${resumenCosteo.desglose?.otros?.toFixed(2) || 0}
                </div>
                <div className="text-xs text-gray-600">
                  {resumenCosteo.porcentajes?.otros?.toFixed(1)}%
                </div>
              </div>
            </div>
            <div className="mt-4 p-4 rounded-lg bg-zinc-100 flex justify-between items-center">
              <span className="font-medium">Costo Total de Producción</span>
              <span className="text-2xl font-bold">
                ${resumenCosteo.totales?.costo_total?.toLocaleString('es-MX', {minimumFractionDigits: 2})}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link to="/tablajeria/ordenes">
          <Card className="hover:bg-zinc-50 transition-colors cursor-pointer">
            <CardContent className="p-4 flex items-center gap-3">
              <FileText className="h-8 w-8 text-blue-500" />
              <div>
                <div className="font-medium">Órdenes</div>
                <div className="text-xs text-muted-foreground">Ver todas</div>
              </div>
            </CardContent>
          </Card>
        </Link>
        <Link to="/tablajeria/captura-directa">
          <Card className="hover:bg-zinc-50 transition-colors cursor-pointer">
            <CardContent className="p-4 flex items-center gap-3">
              <FilePlus className="h-8 w-8 text-green-500" />
              <div>
                <div className="font-medium">Captura Directa</div>
                <div className="text-xs text-muted-foreground">Nueva orden</div>
              </div>
            </CardContent>
          </Card>
        </Link>
        <Link to="/tablajeria/plantillas">
          <Card className="hover:bg-zinc-50 transition-colors cursor-pointer">
            <CardContent className="p-4 flex items-center gap-3">
              <Layers className="h-8 w-8 text-purple-500" />
              <div>
                <div className="font-medium">Plantillas</div>
                <div className="text-xs text-muted-foreground">Configurar</div>
              </div>
            </CardContent>
          </Card>
        </Link>
        <Link to="/produccion/tablajeria">
          <Card className="hover:bg-zinc-50 transition-colors cursor-pointer">
            <CardContent className="p-4 flex items-center gap-3">
              <Activity className="h-8 w-8 text-orange-500" />
              <div>
                <div className="font-medium">Reportes</div>
                <div className="text-xs text-muted-foreground">Exportar</div>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
