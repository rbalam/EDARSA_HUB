import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { Loader2, TrendingUp, TrendingDown, RefreshCw, Building2, Users, Receipt, DollarSign } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatCurrency = (num) => {
  if (num === null || num === undefined) return '-';
  if (num >= 1000000) return `$${(num/1000000).toFixed(2)}M`;
  if (num >= 1000) return `$${(num/1000).toFixed(0)}K`;
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 }).format(num);
};

const formatPercent = (num) => {
  if (num === null || num === undefined || num === 0) return '-';
  const prefix = num > 0 ? '+' : '';
  return `${prefix}${num.toFixed(1)}%`;
};

const VariacionBadge = ({ valor }) => {
  if (valor === 0 || valor === null || valor === undefined) return <span className="text-zinc-400">-</span>;
  const isPositive = valor > 0;
  return (
    <span className={`inline-flex items-center gap-1 text-sm font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
      {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
      {formatPercent(valor)}
    </span>
  );
};

export default function TableroEjecutivo() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [mes, setMes] = useState(0);
  const [anio, setAnio] = useState(0);

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

  return (
    <div className="space-y-4" data-testid="tablero-ejecutivo">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800">Tablero Ejecutivo</h1>
          <p className="text-sm text-zinc-500">KPIs consolidados de todas las unidades</p>
        </div>
      </div>

      {/* Filtros */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="w-40">
              <Select value={String(mes)} onValueChange={(v) => setMes(parseInt(v))}>
                <SelectTrigger><SelectValue placeholder="Mes" /></SelectTrigger>
                <SelectContent>{meses.map(m => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="w-32">
              <Select value={String(anio)} onValueChange={(v) => setAnio(parseInt(v))}>
                <SelectTrigger><SelectValue placeholder="Año" /></SelectTrigger>
                <SelectContent>{anios.map(a => <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <Button onClick={cargarDatos} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Actualizar
            </Button>
            {data?.periodo && (
              <span className="text-sm text-zinc-500 ml-auto">
                Días: {data.periodo.dias_transcurridos} / {data.periodo.dias_mes} 
                {data.periodo.dias_transcurridos < data.periodo.dias_mes && ' (Proyección disponible)'}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Totales Consolidados */}
      {data?.totales && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card className="border bg-gradient-to-br from-green-50 to-white">
            <CardContent className="py-4">
              <div className="flex items-center gap-2 mb-1">
                <DollarSign className="h-4 w-4 text-green-600" />
                <span className="text-xs text-zinc-500">Ventas Totales</span>
              </div>
              <p className="text-2xl font-bold text-green-600">{formatCurrency(data.totales.ventas)}</p>
              <div className="flex gap-3 mt-1">
                <span className="text-xs">vs Mes Ant: <VariacionBadge valor={data.totales.var_vs_mes_ant} /></span>
                <span className="text-xs">vs Año Ant: <VariacionBadge valor={data.totales.var_vs_año_ant} /></span>
              </div>
            </CardContent>
          </Card>

          <Card className="border bg-gradient-to-br from-blue-50 to-white">
            <CardContent className="py-4">
              <div className="flex items-center gap-2 mb-1">
                <Users className="h-4 w-4 text-blue-600" />
                <span className="text-xs text-zinc-500">PAX Total</span>
              </div>
              <p className="text-2xl font-bold text-blue-600">{data.totales.pax?.toLocaleString()}</p>
              <p className="text-xs text-zinc-500 mt-1">Ticket Prom: {formatCurrency(data.totales.ticket_prom)}</p>
            </CardContent>
          </Card>

          <Card className="border bg-gradient-to-br from-purple-50 to-white">
            <CardContent className="py-4">
              <div className="flex items-center gap-2 mb-1">
                <Receipt className="h-4 w-4 text-purple-600" />
                <span className="text-xs text-zinc-500">Cheques</span>
              </div>
              <p className="text-2xl font-bold text-purple-600">{data.totales.cheques?.toLocaleString()}</p>
              <p className="text-xs text-zinc-500 mt-1">Cheque Prom: {formatCurrency(data.totales.cheque_prom)}</p>
            </CardContent>
          </Card>

          <Card className="border bg-gradient-to-br from-orange-50 to-white">
            <CardContent className="py-4">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="h-4 w-4 text-orange-600" />
                <span className="text-xs text-zinc-500">Proyección Mes</span>
              </div>
              <p className="text-2xl font-bold text-orange-600">{formatCurrency(data.totales.proyeccion)}</p>
              <p className="text-xs text-zinc-500 mt-1">Si mantiene ritmo actual</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabla por Unidad */}
      {data?.unidades && data.unidades.length > 0 && (
        <Card className="border">
          <CardHeader className="py-3 bg-zinc-800 text-white rounded-t-lg">
            <CardTitle className="text-sm flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              Detalle por Unidad - {data.comparativo_con?.mes_anterior} | {data.comparativo_con?.año_anterior}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-zinc-100 sticky top-0">
                  <tr>
                    <th className="py-2 px-3 text-left font-semibold">Unidad</th>
                    <th className="py-2 px-3 text-right font-semibold">Ventas</th>
                    <th className="py-2 px-3 text-right font-semibold">vs Mes</th>
                    <th className="py-2 px-3 text-right font-semibold">vs Año</th>
                    <th className="py-2 px-3 text-right font-semibold">PAX</th>
                    <th className="py-2 px-3 text-right font-semibold">vs Mes</th>
                    <th className="py-2 px-3 text-right font-semibold">Cheques</th>
                    <th className="py-2 px-3 text-right font-semibold">Ticket Prom</th>
                    <th className="py-2 px-3 text-right font-semibold">Cheque Prom</th>
                    <th className="py-2 px-3 text-right font-semibold">Proyección</th>
                  </tr>
                </thead>
                <tbody>
                  {data.unidades.map((u, idx) => (
                    <tr key={idx} className="border-b hover:bg-zinc-50">
                      <td className="py-2 px-3 font-medium">{u.unidad}</td>
                      <td className="py-2 px-3 text-right font-semibold text-green-600">{formatCurrency(u.ventas)}</td>
                      <td className="py-2 px-3 text-right"><VariacionBadge valor={u.var_vs_mes_ant} /></td>
                      <td className="py-2 px-3 text-right"><VariacionBadge valor={u.var_vs_año_ant} /></td>
                      <td className="py-2 px-3 text-right">{u.pax?.toLocaleString()}</td>
                      <td className="py-2 px-3 text-right"><VariacionBadge valor={u.var_pax_mes} /></td>
                      <td className="py-2 px-3 text-right">{u.cheques?.toLocaleString()}</td>
                      <td className="py-2 px-3 text-right">{formatCurrency(u.ticket_prom)}</td>
                      <td className="py-2 px-3 text-right">{formatCurrency(u.cheque_prom)}</td>
                      <td className="py-2 px-3 text-right text-orange-600">{formatCurrency(u.proyeccion)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-zinc-800 text-white font-semibold">
                  <tr>
                    <td className="py-2 px-3">TOTAL</td>
                    <td className="py-2 px-3 text-right">{formatCurrency(data.totales.ventas)}</td>
                    <td className="py-2 px-3 text-right"><span className={data.totales.var_vs_mes_ant >= 0 ? 'text-green-400' : 'text-red-400'}>{formatPercent(data.totales.var_vs_mes_ant)}</span></td>
                    <td className="py-2 px-3 text-right"><span className={data.totales.var_vs_año_ant >= 0 ? 'text-green-400' : 'text-red-400'}>{formatPercent(data.totales.var_vs_año_ant)}</span></td>
                    <td className="py-2 px-3 text-right">{data.totales.pax?.toLocaleString()}</td>
                    <td className="py-2 px-3 text-right">-</td>
                    <td className="py-2 px-3 text-right">{data.totales.cheques?.toLocaleString()}</td>
                    <td className="py-2 px-3 text-right">{formatCurrency(data.totales.ticket_prom)}</td>
                    <td className="py-2 px-3 text-right">{formatCurrency(data.totales.cheque_prom)}</td>
                    <td className="py-2 px-3 text-right">{formatCurrency(data.totales.proyeccion)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {loading && !data && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          <span className="ml-2 text-zinc-500">Consultando todas las unidades...</span>
        </div>
      )}
    </div>
  );
}
