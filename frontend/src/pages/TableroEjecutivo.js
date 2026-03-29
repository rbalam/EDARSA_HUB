import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import { 
  Loader2, TrendingUp, TrendingDown, RefreshCw, Building2, Users, Receipt, 
  DollarSign, ArrowLeft, ChevronRight, Target, Clock, Utensils, X
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatCurrency = (num) => {
  if (num === null || num === undefined) return '-';
  if (num >= 1000000) return `$${(num/1000000).toFixed(2)}M`;
  if (num >= 1000) return `$${(num/1000).toFixed(0)}K`;
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 }).format(num);
};

const formatPercent = (num) => {
  if (num === null || num === undefined) return '0%';
  if (num === 0) return '0%';
  const prefix = num > 0 ? '+' : '';
  return `${prefix}${num.toFixed(1)}%`;
};

const VariacionBadge = ({ valor, size = 'sm' }) => {
  if (valor === 0 || valor === null || valor === undefined) return <span className="text-zinc-400">-</span>;
  const isPositive = valor > 0;
  const sizeClass = size === 'lg' ? 'text-lg font-bold' : 'text-sm font-semibold';
  return (
    <span className={`inline-flex items-center gap-1 ${sizeClass} ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
      {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
      {formatPercent(valor)}
    </span>
  );
};

// Tarjeta de Unidad clickeable
const UnidadCard = ({ unidad, onClick }) => {
  const isPositive = unidad.var_vs_mes_ant >= 0;
  
  return (
    <Card 
      className={`cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02] border-2 ${
        isPositive ? 'hover:border-green-400' : 'hover:border-red-400'
      }`}
      onClick={() => onClick(unidad)}
      data-testid={`unidad-card-${unidad.server_id}`}
    >
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-3">
          <h3 className="font-bold text-zinc-800 text-sm truncate max-w-[180px]">{unidad.unidad}</h3>
          <ChevronRight className="h-4 w-4 text-zinc-400" />
        </div>
        
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-xs text-zinc-500">Ventas</span>
            <span className="font-bold text-green-600">{formatCurrency(unidad.ventas)}</span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-xs text-zinc-500">vs Mes Ant</span>
            <VariacionBadge valor={unidad.var_vs_mes_ant} />
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-xs text-zinc-500">vs Año Ant</span>
            <VariacionBadge valor={unidad.var_vs_año_ant} />
          </div>
          
          <div className="border-t pt-2 mt-2 grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-zinc-500">PAX</span>
              <p className="font-semibold">{unidad.pax?.toLocaleString()}</p>
            </div>
            <div>
              <span className="text-zinc-500">Cheques</span>
              <p className="font-semibold">{unidad.cheques?.toLocaleString()}</p>
            </div>
            <div>
              <span className="text-zinc-500">Ticket</span>
              <p className="font-semibold">{formatCurrency(unidad.ticket_prom)}</p>
            </div>
            <div>
              <span className="text-zinc-500">Proyección</span>
              <p className="font-semibold text-orange-600">{formatCurrency(unidad.proyeccion)}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Detalle de Unidad (Drill-down)
const DetalleUnidad = ({ unidad, onClose, mes, anio }) => {
  const [detalleData, setDetalleData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const cargarDetalle = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');
        const headers = { Authorization: `Bearer ${token}` };
        
        // Parámetros con sucursal (si existe)
        const params = unidad.sucursal ? `?sucursal=${encodeURIComponent(unidad.sucursal)}` : '';
        const periodParams = unidad.sucursal ? `?periodo=mes&sucursal=${encodeURIComponent(unidad.sucursal)}` : '?periodo=mes';
        
        // Cargar datos adicionales de la unidad
        const [dashboard, ventasTiempo, mesas] = await Promise.all([
          axios.get(`${API_URL}/api/comercial/dashboard/${unidad.server_id}${periodParams}`, { headers }),
          axios.get(`${API_URL}/api/comercial/ventas-tiempo/${unidad.server_id}${params}`, { headers }),
          axios.get(`${API_URL}/api/comercial/mesas/${unidad.server_id}${params}`, { headers })
        ]);
        
        setDetalleData({
          dashboard: dashboard.data,
          ventasTiempo: ventasTiempo.data,
          mesas: mesas.data
        });
      } catch (error) {
        console.error('Error cargando detalle:', error);
        toast.error('Error al cargar detalle de unidad');
      } finally {
        setLoading(false);
      }
    };
    
    if (unidad?.server_id) {
      cargarDetalle();
    }
  }, [unidad]);

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            {unidad.unidad}
          </DialogTitle>
        </DialogHeader>
        
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* KPIs principales */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Card className="bg-green-50 border-green-200">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <span className="text-xs text-zinc-600">Ventas</span>
                  </div>
                  <p className="text-xl font-bold text-green-600">{formatCurrency(unidad.ventas)}</p>
                  <div className="flex gap-2 mt-1">
                    <span className="text-xs">Mes: <VariacionBadge valor={unidad.var_vs_mes_ant} /></span>
                    <span className="text-xs">Año: <VariacionBadge valor={unidad.var_vs_año_ant} /></span>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Users className="h-4 w-4 text-blue-600" />
                    <span className="text-xs text-zinc-600">PAX</span>
                  </div>
                  <p className="text-xl font-bold text-blue-600">{unidad.pax?.toLocaleString()}</p>
                  <p className="text-xs text-zinc-500">Ticket: {formatCurrency(unidad.ticket_prom)}</p>
                </CardContent>
              </Card>
              
              <Card className="bg-purple-50 border-purple-200">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Receipt className="h-4 w-4 text-purple-600" />
                    <span className="text-xs text-zinc-600">Cheques</span>
                  </div>
                  <p className="text-xl font-bold text-purple-600">{unidad.cheques?.toLocaleString()}</p>
                  <p className="text-xs text-zinc-500">Promedio: {formatCurrency(unidad.cheque_prom)}</p>
                </CardContent>
              </Card>
              
              <Card className="bg-orange-50 border-orange-200">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Target className="h-4 w-4 text-orange-600" />
                    <span className="text-xs text-zinc-600">Proyección</span>
                  </div>
                  <p className="text-xl font-bold text-orange-600">{formatCurrency(unidad.proyeccion)}</p>
                  <p className="text-xs text-zinc-500">Mes completo</p>
                </CardContent>
              </Card>
            </div>

            {/* Comparativo */}
            <Card>
              <CardHeader className="py-2 bg-zinc-100">
                <CardTitle className="text-sm">Comparativo</CardTitle>
              </CardHeader>
              <CardContent className="p-3">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-xs text-zinc-500">Mes Actual</p>
                    <p className="font-bold text-lg">{formatCurrency(unidad.ventas)}</p>
                    <p className="text-xs">{unidad.cheques} cheques</p>
                    <p className="text-xs text-purple-600">{unidad.pax || 0} pax</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500">Mes Anterior</p>
                    <p className="font-bold text-lg">{formatCurrency(unidad.ventas_ant)}</p>
                    <p className="text-xs">{unidad.cheques_ant} cheques</p>
                    <p className="text-xs text-purple-600">{unidad.pax_ant || 0} pax</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500">Año Anterior</p>
                    <p className="font-bold text-lg">{formatCurrency(unidad.ventas_año)}</p>
                    <p className="text-xs">{unidad.cheques_año} cheques</p>
                    <p className="text-xs text-purple-600">{unidad.pax_año || 0} pax</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Ventas por Hora */}
            {detalleData?.ventasTiempo?.por_hora?.length > 0 && (
              <Card>
                <CardHeader className="py-2 bg-zinc-100">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Ventas por Hora (Top 6)
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3">
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                    {detalleData.ventasTiempo.por_hora.slice(0, 6).map((h, i) => (
                      <div key={i} className="text-center p-2 bg-zinc-50 rounded">
                        <p className="font-bold text-sm">{h.hora}</p>
                        <p className="text-xs text-green-600">{formatCurrency(h.ventas)}</p>
                        <p className="text-xs text-zinc-500">{h.pax} pax</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Ventas por Día */}
            {detalleData?.ventasTiempo?.por_dia?.length > 0 && (
              <Card>
                <CardHeader className="py-2 bg-zinc-100">
                  <CardTitle className="text-sm">Ventas por Día de Semana</CardTitle>
                </CardHeader>
                <CardContent className="p-3">
                  <div className="grid grid-cols-7 gap-1">
                    {(() => {
                      // Asegurar que siempre tengamos los 7 días de la semana
                      const diasSemana = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
                      const diasMap = {};
                      detalleData.ventasTiempo.por_dia.forEach(d => {
                        const diaKey = d.dia.substring(0, 3);
                        diasMap[diaKey] = d;
                      });
                      
                      const diasCompletos = diasSemana.map(dia => ({
                        dia: dia,
                        ventas: diasMap[dia]?.ventas || 0,
                        pax: diasMap[dia]?.pax || 0
                      }));
                      
                      const maxVenta = Math.max(...diasCompletos.map(x => x.ventas), 1);
                      
                      return diasCompletos.map((d, i) => {
                        const height = (d.ventas / maxVenta * 60) + 20;
                        return (
                          <div key={i} className="text-center">
                            <div 
                              className={`rounded-t mx-auto w-8 transition-all ${d.ventas > 0 ? 'bg-blue-500' : 'bg-zinc-200'}`}
                              style={{ height: `${height}px` }}
                            />
                            <p className="text-xs font-medium mt-1">{d.dia}</p>
                            <p className="text-xs text-zinc-500">{formatCurrency(d.ventas)}</p>
                          </div>
                        );
                      });
                    })()}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default function TableroEjecutivo() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [mes, setMes] = useState(0);
  const [anio, setAnio] = useState(0);
  const [unidadSeleccionada, setUnidadSeleccionada] = useState(null);

  const meses = [
    { value: '0', label: 'Mes Actual' },
    { value: '1', label: 'Enero' }, { value: '2', label: 'Febrero' }, { value: '3', label: 'Marzo' },
    { value: '4', label: 'Abril' }, { value: '5', label: 'Mayo' }, { value: '6', label: 'Junio' },
    { value: '7', label: 'Julio' }, { value: '8', label: 'Agosto' }, { value: '9', label: 'Septiembre' },
    { value: '10', label: 'Octubre' }, { value: '11', label: 'Noviembre' }, { value: '12', label: 'Diciembre' }
  ];

  const anios = [
    { value: '0', label: 'Año Actual' },
    { value: '2026', label: '2026' }, { value: '2025', label: '2025' }, { value: '2024', label: '2024' }
  ];

  const cargarDatos = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/comercial/tablero-ejecutivo`, {
        params: { mes, anio },
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(response.data);
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al cargar tablero ejecutivo');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  const nombreMes = data?.periodo?.mes ? meses.find(m => m.value === String(data.periodo.mes))?.label : '';

  return (
    <div className="space-y-4" data-testid="tablero-ejecutivo">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800">Tablero de Dirección</h1>
          <p className="text-sm text-zinc-500">Vista consolidada de todas las unidades • Clic para ver detalle</p>
        </div>
      </div>

      {/* Filtros */}
      <Card className="border bg-white">
        <CardContent className="py-3">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="w-36">
              <Select value={String(mes)} onValueChange={(v) => setMes(parseInt(v))}>
                <SelectTrigger className="h-9"><SelectValue placeholder="Mes" /></SelectTrigger>
                <SelectContent>{meses.map(m => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="w-28">
              <Select value={String(anio)} onValueChange={(v) => setAnio(parseInt(v))}>
                <SelectTrigger className="h-9"><SelectValue placeholder="Año" /></SelectTrigger>
                <SelectContent>{anios.map(a => <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <Button onClick={cargarDatos} disabled={loading} size="sm">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Actualizar
            </Button>
            {data?.periodo && (
              <span className="text-xs text-zinc-500 ml-auto bg-zinc-100 px-2 py-1 rounded">
                {nombreMes} {data.periodo.anio} • Día {data.periodo.dias_transcurridos} de {data.periodo.dias_mes}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* TOTALES - Vista Ejecutiva Grande */}
      {data?.totales && (
        <Card className="border-2 border-zinc-300 bg-gradient-to-br from-zinc-900 to-zinc-800 text-white">
          <CardContent className="py-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
              {/* Ventas Consolidadas */}
              <div className="col-span-2 md:col-span-1 flex flex-col">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">Ventas Consolidadas</p>
                <p className="text-3xl font-bold text-green-400">{formatCurrency(data.totales.ventas)}</p>
                <p className="text-xs text-zinc-400 mt-1">&nbsp;</p>
                <div className="flex gap-4 mt-auto pt-2">
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Mes</span>
                    <p className={`font-bold ${data.totales.var_vs_mes_ant >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_vs_mes_ant)}
                    </p>
                  </div>
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Año</span>
                    <p className={`font-bold ${data.totales.var_vs_año_ant >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_vs_año_ant)}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* PAX Total */}
              <div className="flex flex-col">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">PAX Total</p>
                <p className="text-2xl font-bold">{data.totales.pax?.toLocaleString()}</p>
                <p className="text-xs text-zinc-400 mt-1">Ticket: {formatCurrency(data.totales.ticket_prom)}</p>
                <div className="flex gap-4 mt-auto pt-2">
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Mes</span>
                    <p className={`text-sm font-bold ${(data.totales.var_pax_mes || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_pax_mes || 0)}
                    </p>
                  </div>
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Año</span>
                    <p className={`text-sm font-bold ${(data.totales.var_pax_año || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_pax_año || 0)}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Cheques */}
              <div className="flex flex-col">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">Cheques</p>
                <p className="text-2xl font-bold">{data.totales.cheques?.toLocaleString()}</p>
                <p className="text-xs text-zinc-400 mt-1">Promedio: {formatCurrency(data.totales.cheque_prom)}</p>
                <div className="flex gap-4 mt-auto pt-2">
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Mes</span>
                    <p className={`text-sm font-bold ${(data.totales.var_cheques_mes || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_cheques_mes || 0)}
                    </p>
                  </div>
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Año</span>
                    <p className={`text-sm font-bold ${(data.totales.var_cheques_año || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_cheques_año || 0)}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Proyección Mes */}
              <div className="flex flex-col">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">Proyección Mes</p>
                <p className="text-2xl font-bold text-orange-400">{formatCurrency(data.totales.proyeccion)}</p>
                <p className="text-xs text-zinc-400 mt-1">Si mantiene ritmo</p>
                <div className="flex gap-4 mt-auto pt-2">
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Año Ant.</span>
                    <p className={`text-sm font-bold ${(data.totales.var_proy_vs_año || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_proy_vs_año || 0)}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Unidades */}
              <div className="flex flex-col">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">Unidades</p>
                <p className="text-2xl font-bold">{data.unidades?.length || 0}</p>
                <p className="text-xs text-zinc-400 mt-1">Conectadas</p>
                <div className="flex gap-4 mt-auto pt-2">
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">Año Ant.</span>
                    <p className="text-sm font-bold text-zinc-300">
                      {data.totales.unidades_año_ant || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Grid de Unidades - Clickeables */}
      {data?.unidades && data.unidades.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Unidades ({data.unidades.length})
            <span className="text-xs font-normal text-zinc-500">• Clic para ver detalle</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.unidades.map((unidad, idx) => (
              <UnidadCard 
                key={idx} 
                unidad={unidad} 
                onClick={setUnidadSeleccionada}
              />
            ))}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && !data && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          <span className="ml-2 text-zinc-500">Consultando todas las unidades...</span>
        </div>
      )}

      {/* Modal de Detalle */}
      {unidadSeleccionada && (
        <DetalleUnidad 
          unidad={unidadSeleccionada} 
          onClose={() => setUnidadSeleccionada(null)}
          mes={mes}
          anio={anio}
        />
      )}
    </div>
  );
}
