import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import {
  Building2, Calendar, RefreshCw, ChevronUp, ChevronDown,
  BarChart3, PieChart, AlertCircle, FileText
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, PieChart as RechartsPie, Pie, Cell
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FF6B6B', '#4ECDC4'];

/**
 * FinanzasDashboard
 * 
 * Componente presentacional para el dashboard de finanzas: KPIs,
 * graficos comparativos y tabla por sucursal.
 * 
 * ACTUALIZADO: Filtro de sucursal eliminado. Solo se filtra por Unidad de Negocio.
 * Los datos por sucursal se muestran en la tabla sin filtro individual.
 * 
 * @param {Object} props
 * @param {Object} props.dashboard - Datos del dashboard (kpis, por_sucursal)
 * @param {Array} props.unidadesNegocio - Unidades de negocio disponibles (filtradas por permisos)
 * @param {string} props.selectedUnidad - Unidad seleccionada
 * @param {boolean} props.loadingUnidades - Estado de carga de unidades
 * @param {number} props.filtroMes - Mes seleccionado
 * @param {number} props.filtroAnio - Ano seleccionado
 * @param {Array} props.meses - Array de nombres de meses
 * @param {boolean} props.loading - Estado de carga general
 * @param {Function} props.onUnidadChange - Callback cambio unidad
 * @param {Function} props.onMesChange - Callback cambio mes
 * @param {Function} props.onAnioChange - Callback cambio ano
 * @param {Function} props.onActualizar - Callback boton actualizar
 * @param {Function} props.onVerScript - Callback ver script SQL
 * @param {Function} props.formatCurrency - Funcion para formatear moneda
 */
export default function FinanzasDashboard({
  dashboard,
  unidadesNegocio,
  selectedUnidad,
  loadingUnidades,
  filtroMes,
  filtroAnio,
  meses,
  loading,
  onUnidadChange,
  onMesChange,
  onAnioChange,
  onActualizar,
  onVerScript,
  formatCurrency
}) {
  const kpis = dashboard?.kpis || {};
  
  // Memoized: porSucursal (evita que la referencia cambie en cada render)
  const porSucursal = useMemo(() => dashboard?.por_sucursal || [], [dashboard?.por_sucursal]);

  // Memoized: Datos para gráfico de Pie (evita recálculo en cada render)
  const pieChartData = useMemo(() => 
    porSucursal.map(s => ({
      name: s.Nombre_Sucursal || 'N/A',
      value: s.Egresos || 0
    })).filter(d => d.value > 0),
    [porSucursal]
  );

  // Memoized: Sucursales con sobregiro (evita recálculo en cada render)
  const sucursalesConSobregiro = useMemo(() => 
    porSucursal
      .filter(s => (s.Egresos || 0) > (s.Egresos_Pres || 0))
      .map(s => ({
        ...s,
        exceso: (s.Egresos || 0) - (s.Egresos_Pres || 0),
        porcExceso: s.Egresos_Pres > 0 ? Math.round(((s.Egresos || 0) - (s.Egresos_Pres || 0)) / s.Egresos_Pres * 100) : 0
      })),
    [porSucursal]
  );

  // Check if tables don't exist
  if (dashboard?.nota) {
    return (
      <div className="space-y-6" data-testid="dashboard-no-tables">
        <Card className="border-2 border-dashed border-amber-300 bg-amber-50">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-16 w-16 text-amber-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-amber-700 mb-2">Tablas no configuradas</h2>
            <p className="text-amber-600 mb-4">
              Las tablas de finanzas aun no han sido creadas en la base de datos EDARSA HUB.
            </p>
            <Button onClick={onVerScript} className="bg-amber-600 hover:bg-amber-700 text-white">
              <FileText className="h-4 w-4 mr-2" />
              Ver Script de Inicializacion
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="finanzas-dashboard">
      {/* Filtros */}
      <div className="flex flex-wrap gap-3 items-center" data-testid="dashboard-filtros">
        {/* Selector de Unidad de Negocio */}
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-zinc-400" />
          {unidadesNegocio.length === 1 ? (
            <div className="px-3 py-2 border rounded-lg text-sm bg-zinc-50 flex items-center gap-2">
              <span>{unidadesNegocio[0].nombre}</span>
            </div>
          ) : (
            <select
              value={selectedUnidad}
              onChange={(e) => onUnidadChange(e.target.value)}
              className="px-3 py-2 border rounded-lg text-sm"
              disabled={loadingUnidades}
              data-testid="dashboard-unidad-select"
            >
              <option value="">{loadingUnidades ? "Cargando..." : "Todas las unidades"}</option>
              {unidadesNegocio.map(u => (
                <option key={u.id} value={u.id}>{u.nombre}</option>
              ))}
            </select>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-zinc-400" />
          <select
            value={filtroMes}
            onChange={(e) => onMesChange(parseInt(e.target.value))}
            className="px-3 py-2 border rounded-lg text-sm"
            data-testid="dashboard-mes-select"
          >
            {meses.map((m, i) => (
              <option key={`mes-${i + 1}`} value={i + 1}>{m}</option>
            ))}
          </select>
          <select
            value={filtroAnio}
            onChange={(e) => onAnioChange(parseInt(e.target.value))}
            className="px-3 py-2 border rounded-lg text-sm"
            data-testid="dashboard-anio-select"
          >
            {[2024, 2025, 2026, 2027].map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
        <Button variant="outline" size="sm" onClick={onActualizar} disabled={loading} data-testid="dashboard-actualizar-btn">
          <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>
      
      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="dashboard-kpis">
        {/* Ingresos */}
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-zinc-500 uppercase tracking-wide">Ingresos</p>
                <p className="text-2xl font-bold text-green-600">{formatCurrency(kpis.ingresos_ejecutados)}</p>
                <p className="text-xs text-zinc-400">de {formatCurrency(kpis.ingresos_presupuestados)}</p>
              </div>
              <div className={`flex items-center gap-1 text-sm ${kpis.ingresos_var_mes_ant >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {kpis.ingresos_var_mes_ant >= 0 ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                {Math.abs(kpis.ingresos_var_mes_ant || 0)}%
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Egresos */}
        <Card className="border-l-4 border-l-red-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-zinc-500 uppercase tracking-wide">Egresos</p>
                <p className="text-2xl font-bold text-red-600">{formatCurrency(kpis.egresos_ejecutados)}</p>
                <p className="text-xs text-zinc-400">de {formatCurrency(kpis.egresos_presupuestados)}</p>
              </div>
              <div className={`flex items-center gap-1 text-sm ${kpis.egresos_var_mes_ant <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {kpis.egresos_var_mes_ant >= 0 ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                {Math.abs(kpis.egresos_var_mes_ant || 0)}%
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Utilidad */}
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-4">
            <div>
              <p className="text-xs text-zinc-500 uppercase tracking-wide">Utilidad</p>
              <p className={`text-2xl font-bold ${kpis.utilidad_real >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                {formatCurrency(kpis.utilidad_real)}
              </p>
              <p className="text-xs text-zinc-400">Presupuestada: {formatCurrency(kpis.utilidad_presupuestada)}</p>
            </div>
          </CardContent>
        </Card>
        
        {/* Margen */}
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="pt-4">
            <div>
              <p className="text-xs text-zinc-500 uppercase tracking-wide">Margen de Utilidad</p>
              <p className={`text-2xl font-bold ${kpis.margen_utilidad >= 0 ? 'text-purple-600' : 'text-red-600'}`}>
                {kpis.margen_utilidad || 0}%
              </p>
              <p className="text-xs text-zinc-400">{meses[filtroMes - 1]} {filtroAnio}</p>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Graficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" data-testid="dashboard-charts">
        {/* Grafico de Barras - Comparativo Presupuesto vs Real */}
        <Card>
          <CardHeader className="py-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Presupuesto vs Ejecutado por Sucursal
            </CardTitle>
          </CardHeader>
          <CardContent>
            {porSucursal.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={porSucursal.map(s => ({
                  name: s.Nombre_Sucursal?.substring(0, 10) || 'N/A',
                  Presupuesto: (s.Ingresos_Pres || 0) - (s.Egresos_Pres || 0),
                  Ejecutado: (s.Ingresos || 0) - (s.Egresos || 0)
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => formatCurrency(v)} />
                  <Legend />
                  <Bar dataKey="Presupuesto" fill="#94a3b8" name="Presupuesto" />
                  <Bar dataKey="Ejecutado" fill="#3b82f6" name="Ejecutado" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-zinc-400">
                Sin datos para graficar
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Grafico de Pie - Distribucion de Egresos */}
        <Card>
          <CardHeader className="py-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <PieChart className="h-4 w-4" />
              Distribucion de Egresos por Sucursal
            </CardTitle>
          </CardHeader>
          <CardContent>
            {pieChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <RechartsPie>
                  <Pie
                    data={pieChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name.substring(0, 8)} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieChartData.map((entry, index) => (
                      <Cell key={`cell-${entry.name}-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => formatCurrency(v)} />
                </RechartsPie>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-zinc-400">
                Sin datos para graficar
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Alertas de Sobregiro */}
      {sucursalesConSobregiro.length > 0 && (
        <Card className="border-red-200 bg-red-50" data-testid="dashboard-alertas">
          <CardHeader className="py-2">
            <CardTitle className="text-sm text-red-700 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Alertas de Sobregiro
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-1">
              {sucursalesConSobregiro.map((s) => (
                <div key={`alerta-${s.Codigo_Sucursal || s.Nombre_Sucursal}`} className="flex items-center justify-between text-sm">
                  <span className="text-red-700">{s.Nombre_Sucursal}</span>
                  <span className="font-medium text-red-600">
                    Exceso: {formatCurrency(s.exceso)} (+{s.porcExceso}%)
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Por Sucursal */}
      <Card data-testid="dashboard-tabla-sucursales">
        <CardHeader className="py-3 bg-zinc-800 text-white rounded-t-lg">
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Comparativo por Sucursal
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-100">
                <tr>
                  <th className="text-left p-3 font-medium">Sucursal</th>
                  <th className="text-right p-3 font-medium">Ingresos Pres.</th>
                  <th className="text-right p-3 font-medium">Ingresos Real</th>
                  <th className="text-right p-3 font-medium">Egresos Pres.</th>
                  <th className="text-right p-3 font-medium">Egresos Real</th>
                  <th className="text-right p-3 font-medium">Utilidad</th>
                  <th className="text-center p-3 font-medium">Cumplimiento</th>
                </tr>
              </thead>
              <tbody>
                {porSucursal.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-zinc-400">
                      No hay datos para el periodo seleccionado
                    </td>
                  </tr>
                ) : (
                  porSucursal.map((suc, i) => {
                    const utilidad = (suc.Ingresos || 0) - (suc.Egresos || 0);
                    const cumplimiento = suc.Ingresos_Pres > 0 
                      ? Math.round((suc.Ingresos / suc.Ingresos_Pres) * 100) 
                      : 0;
                    
                    return (
                      <tr key={suc.SucursalID || i} className="border-b hover:bg-zinc-50">
                        <td className="p-3 font-medium">{suc.Nombre_Sucursal}</td>
                        <td className="p-3 text-right text-zinc-500">{formatCurrency(suc.Ingresos_Pres)}</td>
                        <td className="p-3 text-right text-green-600 font-medium">{formatCurrency(suc.Ingresos)}</td>
                        <td className="p-3 text-right text-zinc-500">{formatCurrency(suc.Egresos_Pres)}</td>
                        <td className="p-3 text-right text-red-600 font-medium">{formatCurrency(suc.Egresos)}</td>
                        <td className={`p-3 text-right font-bold ${utilidad >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                          {formatCurrency(utilidad)}
                        </td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            cumplimiento >= 100 ? 'bg-green-100 text-green-700' :
                            cumplimiento >= 80 ? 'bg-amber-100 text-amber-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {cumplimiento}%
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
