import logger from '../services/logger';
// FASE AUTH-SECURITY-01 / FASE 4.1: getToken eliminado, auth viaja en cookie httpOnly
import React, { useState, useEffect, useCallback } from 'react';
// AUDITORIA-TABLEROS-KPIS-FILTROS-01: Migrado de axios directo a api centralizado
import api from '../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Loader2, ShoppingCart, Package, TrendingUp, AlertTriangle, Download, AlertCircle, Calendar, Edit3, RefreshCw, Search } from 'lucide-react';
import { getDiferenciaClass } from '../utils/styleHelpers';
import {
  useAutorizacionComprasData,
  AlmacenesSelector,
  ResumenPedido,
  InfoInventario,
  LoadingSkeleton,
  EmptyState
} from '../components/compras';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const STORAGE_KEY = 'compras_params';

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
};

const formatCurrency = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(num);
};

// Guardar parámetros en localStorage
const saveParams = (params) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(params));
  } catch (e) { logger.error('Error saving params', e); }
};

// Cargar parámetros de localStorage
const loadParams = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch (e) { return null; }
};

export default function AutorizacionCompras() {
  // Hook para datos (extraído)
  const {
    unidadesNegocio,
    selectedUnidad,
    setSelectedUnidad,
    loadingUnidades,
    almacenes,
    selectedAlmacenes,
    todosAlmacenes,
    inventariosFisicos,
    inventariosFiltrados,
    setInventariosFiltrados,
    pedidosVigentes,
    selectedServer,
    serverData,
    selectedSucursal,
    fetchInventariosFisicos,
    fetchPedidosVigentes,
    toggleAlmacen,
    toggleTodosAlmacenes
  } = useAutorizacionComprasData();
  
  // Fechas y período
  const [fechaInvFisico, setFechaInvFisico] = useState('');
  const [fechaFinPeriodo, setFechaFinPeriodo] = useState(new Date().toISOString().split('T')[0]);
  const [diasInventario, setDiasInventario] = useState(10);
  const [metodoCalculo, setMetodoCalculo] = useState('consumo');
  
  // Folios
  const [folioInvFisico, setFolioInvFisico] = useState('');
  const [folioPedidoComparar, setFolioPedidoComparar] = useState('');
  const [folioManual, setFolioManual] = useState('');
  const [usarFolioManual, setUsarFolioManual] = useState(false);
  
  // Resultados
  const [loading, setLoading] = useState(false);
  const [pedidoData, setPedidoData] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [infoInventario, setInfoInventario] = useState(null);
  const [editingRow, setEditingRow] = useState(null);
  const [editingFinal, setEditingFinal] = useState(null);
  
  // Modal de detalle
  const [detalleModal, setDetalleModal] = useState({ open: false, tipo: '', data: [], titulo: '', loading: false });
  
  // Flag para restaurar params
  const [paramsRestored, setParamsRestored] = useState(false);

  // Restaurar parámetros guardados
  useEffect(() => {
    if (unidadesNegocio.length > 0 && !paramsRestored) {
      const saved = loadParams();
      if (saved) {
        const unidadMatch = unidadesNegocio.find(u => u.server_id === saved.server);
        if (unidadMatch) {
          setSelectedUnidad(unidadMatch.id);
          setMetodoCalculo(saved.metodo || 'consumo');
          setDiasInventario(saved.dias || 10);
        }
      }
      setParamsRestored(true);
    }
  }, [unidadesNegocio, paramsRestored, setSelectedUnidad]);

  // Cargar almacenes e inventarios cuando cambia la unidad
  useEffect(() => {
    if (selectedServer && selectedSucursal) {
      fetchInventariosFisicos();
      fetchPedidosVigentes();
    }
  }, [selectedServer, selectedSucursal, fetchInventariosFisicos, fetchPedidosVigentes]);

  // Filtrar inventarios cuando cambian los almacenes seleccionados
  useEffect(() => {
    if (todosAlmacenes) {
      // Mostrar todos agrupados por fecha
      const grouped = {};
      inventariosFisicos.forEach(inv => {
        const key = inv.fecha?.split('T')[0] || inv.fecha;
        if (!grouped[key]) grouped[key] = { fecha: inv.fecha, almacenes: [], comentario: inv.comentario };
        grouped[key].almacenes.push(inv.almacen);
      });
      const consolidated = Object.entries(grouped).map(([fecha, data]) => ({
        folio: `TODOS-${fecha}`,
        fecha: data.fecha,
        almacen: `${data.almacenes.length} almacenes`,
        comentario: data.comentario || '',
        isTodos: true
      }));
      setInventariosFiltrados(consolidated.slice(0, 30));
    } else if (selectedAlmacenes.length === 1) {
      // Filtrar por almacén seleccionado
      const filtered = inventariosFisicos.filter(inv => 
        inv.almacen?.toLowerCase().includes(selectedAlmacenes[0]?.toLowerCase())
      );
      setInventariosFiltrados(filtered.slice(0, 50));
    } else if (selectedAlmacenes.length > 1) {
      // Múltiples almacenes - mostrar todos de esos almacenes
      const filtered = inventariosFisicos.filter(inv => 
        selectedAlmacenes.some(a => inv.almacen.toLowerCase().includes(a.toLowerCase()))
      );
      setInventariosFiltrados(filtered.slice(0, 50));
    } else {
      setInventariosFiltrados(inventariosFisicos.slice(0, 50));
    }
  }, [selectedAlmacenes, todosAlmacenes, inventariosFisicos]);

  // MIGRACIÓN: Guardar params usando unidad_id en lugar de server
  useEffect(() => {
    if (selectedUnidad && selectedServer && selectedSucursal) {
      saveParams({
        server: selectedServer, // Mantener server para compatibilidad
        unidad: selectedUnidad,
        sucursal: selectedSucursal,
        almacenes: selectedAlmacenes,
        folio: folioInvFisico,
        fechaIni: fechaInvFisico,
        fechaFin: fechaFinPeriodo,
        metodo: metodoCalculo,
        dias: diasInventario
      });
    }
  }, [selectedUnidad, selectedServer, selectedSucursal, selectedAlmacenes, folioInvFisico, fechaInvFisico, fechaFinPeriodo, metodoCalculo, diasInventario]);

  // Handlers que usan funciones del hook
  const handleAlmacenToggle = (almacenNombre) => {
    toggleAlmacen(almacenNombre);
    setFolioInvFisico(''); // Reset folio al cambiar almacén
  };

  const handleTodosAlmacenes = (checked) => {
    toggleTodosAlmacenes();
    setFolioInvFisico(''); // Reset folio
  };

  const buscarFolioManual = async () => {
    if (!folioManual.trim()) {
      toast.error('Ingresa un folio de pedido');
      return;
    }
    try {
      const response = await api.get(`/compras/detalle-pedido-manual/${selectedServer}?folio=${encodeURIComponent(folioManual)}`);
      toast.success(`Folio ${folioManual} encontrado (${response.data.tipo})`);
      setUsarFolioManual(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Folio no encontrado');
      setUsarFolioManual(false);
    }
  };

  const calcularPedido = async () => {
    if (!selectedUnidad || !selectedServer || !selectedSucursal || (selectedAlmacenes.length === 0 && !todosAlmacenes)) {
      toast.error('Selecciona unidad de negocio y al menos un almacén');
      return;
    }

    if (!fechaInvFisico || !fechaFinPeriodo) {
      toast.error('Selecciona las fechas del período de análisis');
      return;
    }

    setLoading(true);
    setPedidoData([]);
    setResumen(null);
    setInfoInventario(null);

    try {
      const folioComparar = usarFolioManual ? folioManual : (folioPedidoComparar && folioPedidoComparar !== '__none__' ? folioPedidoComparar : null);
      
      // Si es TODOS, no enviar folio específico
      const folioEnviar = (todosAlmacenes || folioInvFisico?.startsWith('TODOS-')) ? null : folioInvFisico;
      
      const response = await api.post(`/compras/calculo-pedido`, {
        server_id: selectedServer,
        sucursal: selectedSucursal,
        almacenes: todosAlmacenes ? ['TODOS'] : selectedAlmacenes,
        fecha_inventario_fisico: fechaInvFisico,
        fecha_fin_periodo: fechaFinPeriodo,
        dias_inventario: parseInt(diasInventario),
        metodo_calculo: metodoCalculo,
        folio_inventario_fisico: folioEnviar,
        folio_pedido_comparar: folioComparar
      });

      setPedidoData(response.data.data);
      
      setInfoInventario({
        tieneInventarioFisico: response.data.tiene_inventario_fisico,
        fechaInventarioFisico: response.data.fecha_inventario_fisico,
        folioInventarioFisico: response.data.folio_inventario_fisico,
        tieneInventarioFinal: response.data.tiene_inventario_final,
        fechaInventarioFinal: response.data.fecha_inventario_final,
        folioInventarioFinal: response.data.folio_inventario_final,
        productosSinInventario: response.data.productos_sin_inventario,
        esBodega: response.data.es_bodega,
        almacenes: response.data.almacenes,
        almacenCodigos: response.data.almacen_codigos,
        sucursalCodigo: response.data.sucursal_codigo,
        diasPeriodo: response.data.dias_periodo,
        comparandoConPedido: response.data.comparando_con_pedido,
        metodoCalculo: response.data.metodo_calculo
      });
      
      const data = response.data.data;
      setResumen({
        totalProductos: data.length,
        productosAPedir: data.filter(p => p.Cantidad_Pedir > 0).length,
        costoTotalPedido: data.reduce((sum, p) => sum + (p.Costo_Pedido || 0), 0),
        productosStockBajo: data.filter(p => p.Dias_Inventario < 3 && p.Dias_Inventario !== 999).length,
        productosSinInvInicial: data.filter(p => p.Sin_Inventario_Inicial).length,
        productosSinInvFinal: data.filter(p => p.Sin_Inventario_Final).length,
        productosConDiferencia: data.filter(p => p.Diferencia_Pedido !== null && p.Diferencia_Pedido !== 0).length
      });

      toast.success(`Cálculo completado: ${response.data.count} productos`);
    } catch (error) {
      logger.error('Error calculando pedido:', error);
      toast.error(error.response?.data?.detail || 'Error al calcular pedido');
    } finally {
      setLoading(false);
    }
  };

  const verDetalleMovimientos = async (codigo, producto) => {
    if (!infoInventario?.almacenCodigos) return;
    setDetalleModal({ open: true, tipo: 'movimientos', data: [], titulo: `Movimientos: ${producto}`, loading: true });
    try {
      const response = await api.get(`/compras/detalle-movimientos/${selectedServer}?codigo_producto=${codigo}&almacenes=${infoInventario.almacenCodigos.join(',')}&fecha_ini=${fechaInvFisico}&fecha_fin=${fechaFinPeriodo}`);
      setDetalleModal(prev => ({ ...prev, data: response.data, loading: false }));
    } catch (error) {
      toast.error('Error cargando detalle');
      setDetalleModal(prev => ({ ...prev, loading: false }));
    }
  };

  const verDetalleConsumos = async (codigo, producto) => {
    if (!infoInventario?.sucursalCodigo) return;
    setDetalleModal({ open: true, tipo: 'consumos', data: [], titulo: `Consumos: ${producto}`, loading: true });
    try {
      const response = await api.get(`/compras/detalle-consumos/${selectedServer}?codigo_producto=${codigo}&sucursal_codigo=${infoInventario.sucursalCodigo}&fecha_ini=${fechaInvFisico}&fecha_fin=${fechaFinPeriodo}`);
      setDetalleModal(prev => ({ ...prev, data: response.data, loading: false }));
    } catch (error) {
      toast.error('Error cargando detalle');
      setDetalleModal(prev => ({ ...prev, loading: false }));
    }
  };

  const actualizarInvInicial = (codigo, valor) => {
    const nuevoValor = parseFloat(valor) || 0;
    setPedidoData(prev => prev.map(row => {
      if (row.Codigo === codigo) {
        const invTeorico = nuevoValor + row.Movimientos_Periodo - row.Consumos_Periodo;
        const promedioD = row.Consumos_Periodo / (infoInventario?.diasPeriodo || 1);
        const consumoEsp = promedioD * diasInventario;
        const cantPedir = Math.max(0, consumoEsp - invTeorico);
        const diasInv = promedioD > 0 ? invTeorico / promedioD : 999;
        return { ...row, Inventario_Inicial: nuevoValor, Inventario_Teorico: invTeorico, Promedio_Diario: promedioD, Cantidad_Pedir: cantPedir, Costo_Pedido: cantPedir * row.Costo_Unitario, Dias_Inventario: diasInv < 999 ? diasInv : 999, Sin_Inventario_Inicial: false };
      }
      return row;
    }));
    setEditingRow(null);
  };

  const actualizarInvFinal = (codigo, valor) => {
    const nuevoValor = parseFloat(valor) || 0;
    setPedidoData(prev => prev.map(row => {
      if (row.Codigo === codigo) {
        return { ...row, Inventario_Final: nuevoValor, Sin_Inventario_Final: false };
      }
      return row;
    }));
    setEditingFinal(null);
  };

  return (
    <div className="space-y-4" data-testid="compras-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800">Autorización de Compras</h1>
          <p className="text-sm text-zinc-500">Calcula pedidos sugeridos y compara con requisiciones</p>
        </div>
      </div>

      {/* Parámetros de Cálculo */}
      <Card className="border border-zinc-200 shadow-sm">
        <CardHeader className="py-3">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <ShoppingCart className="h-5 w-5 text-blue-600" />
            Parámetros del Cálculo
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Fila 1: MIGRACIÓN - Selector de Unidad de Negocio (reemplaza Servidor + Sucursal) */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Unidad de Negocio</Label>
              <Select value={selectedUnidad} onValueChange={setSelectedUnidad} disabled={loadingUnidades}>
                <SelectTrigger data-testid="unidad-select" className="h-9">
                  <SelectValue placeholder={loadingUnidades ? "Cargando..." : "Seleccionar"} />
                </SelectTrigger>
                <SelectContent>
                  {unidadesNegocio.map(unidad => (
                    <SelectItem key={unidad.id} value={unidad.id}>{unidad.nombre}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {/* ELIMINADO: Selector de Sucursal - Ahora se deriva automáticamente de la Unidad */}
            <div className="space-y-1">
              <Label className="text-xs">Folio Inv. Inicial {todosAlmacenes && <span className="text-orange-500">(Consolidado)</span>}</Label>
              <Select value={folioInvFisico} onValueChange={(val) => { 
                setFolioInvFisico(val); 
                const inv = inventariosFiltrados.find(i => i.folio === val); 
                if (inv) setFechaInvFisico(inv.fecha.split('T')[0]); 
              }} disabled={todosAlmacenes || !selectedUnidad}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder={todosAlmacenes ? "Todos los folios" : (selectedUnidad ? "Seleccionar" : "Selecciona unidad")} />
                </SelectTrigger>
                <SelectContent className="max-h-72 overflow-y-auto">
                  {inventariosFiltrados.map(inv => (
                    <SelectItem key={inv.folio} value={inv.folio}>
                      {inv.folio} ({new Date(inv.fecha).toLocaleDateString('es-MX')}) - {inv.comentario || inv.almacen || ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Método Cálculo</Label>
              <Select value={metodoCalculo} onValueChange={setMetodoCalculo}>
                <SelectTrigger className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="consumo">Por Consumo</SelectItem>
                  <SelectItem value="stock">Por Stock Máx</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Días Inventario</Label>
              <Input 
                type="number" 
                value={diasInventario} 
                onChange={(e) => setDiasInventario(e.target.value)} 
                min={1} 
                max={90} 
                className="h-9"
              />
            </div>
          </div>

          {/* Fila 2: Almacenes */}
          {almacenes.length > 0 && selectedUnidad && (
            <div className="space-y-1">
              <Label className="text-xs">Almacenes</Label>
              <div className="flex flex-wrap gap-2 p-2 border rounded-md bg-zinc-50 text-sm max-h-20 overflow-y-auto">
                <div className="flex items-center gap-1">
                  <Checkbox id="todos" checked={todosAlmacenes} onCheckedChange={handleTodosAlmacenes} />
                  <label htmlFor="todos" className="font-medium">TODOS</label>
                </div>
                <div className="w-px h-5 bg-zinc-300" />
                {almacenes.map(alm => (
                  <div key={alm.nombre} className="flex items-center gap-1">
                    <Checkbox id={`a-${alm.nombre}`} checked={selectedAlmacenes.includes(alm.nombre)} onCheckedChange={() => handleAlmacenToggle(alm.nombre)} disabled={todosAlmacenes} />
                    <label htmlFor={`a-${alm.nombre}`}>{alm.nombre}</label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fila 3: Fechas y días */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Fecha Inv. Inicial</Label>
              <Input type="date" value={fechaInvFisico} onChange={(e) => setFechaInvFisico(e.target.value)} className="h-9" data-testid="fecha-inv-fisico" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Fecha Fin Período</Label>
              <Input type="date" value={fechaFinPeriodo} onChange={(e) => setFechaFinPeriodo(e.target.value)} className="h-9" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Días Inv. a Comprar</Label>
              <Input type="number" min="1" max="90" value={diasInventario} onChange={(e) => setDiasInventario(e.target.value)} className="h-9" />
            </div>
            <div className="space-y-1 col-span-2">
              <Label className="text-xs">Comparar con Pedido/Requisición</Label>
              <div className="flex gap-2">
                <Select value={folioPedidoComparar} onValueChange={(v) => { setFolioPedidoComparar(v); setUsarFolioManual(false); }} disabled={usarFolioManual}>
                  <SelectTrigger className="h-9 flex-1">
                    <SelectValue placeholder="Requisiciones sin autorizar" />
                  </SelectTrigger>
                  <SelectContent className="max-h-72 overflow-y-auto">
                    <SelectItem value="__none__">Sin comparar (todos los productos)</SelectItem>
                    {pedidosVigentes.map(p => (
                      <SelectItem key={`${p.tipo}-${p.folio}`} value={p.folio}>
                        {p.folio} - {p.comentario || p.comprador || 'Sin desc.'}
                      </SelectItem>
                    ))}
                    {pedidosVigentes.length === 0 && (
                      <div className="px-2 py-1 text-xs text-zinc-500">No hay requisiciones sin autorizar</div>
                    )}
                  </SelectContent>
                </Select>
                <Input placeholder="Folio manual" value={folioManual} onChange={(e) => setFolioManual(e.target.value)} className="h-9 w-28" />
                <Button variant="outline" size="sm" onClick={buscarFolioManual} className="h-9 px-2"><Search className="h-4 w-4" /></Button>
              </div>
            </div>
          </div>

          {/* Botones */}
          <div className="flex gap-2 pt-2">
            <Button onClick={calcularPedido} disabled={loading || !selectedUnidad || (selectedAlmacenes.length === 0 && !todosAlmacenes)} data-testid="btn-calcular">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Calcular Pedido
            </Button>
            <Button variant="outline" disabled={pedidoData.length === 0}>
              <Download className="h-4 w-4 mr-2" />Excel
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* KPIs */}
      {resumen && (
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">Total</p><p className="text-lg font-bold">{resumen.totalProductos}</p></CardContent></Card>
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">A Pedir</p><p className="text-lg font-bold text-green-600">{resumen.productosAPedir}</p></CardContent></Card>
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">Costo</p><p className="text-base font-bold">{formatCurrency(resumen.costoTotalPedido)}</p></CardContent></Card>
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">Stock Bajo</p><p className="text-lg font-bold text-red-600">{resumen.productosStockBajo}</p></CardContent></Card>
          <Card className={`border ${resumen.productosSinInvInicial > 0 ? 'bg-orange-50' : ''}`}><CardContent className="py-3"><p className="text-xs text-zinc-500">Sin Inv.Ini</p><p className="text-lg font-bold text-orange-600">{resumen.productosSinInvInicial}</p></CardContent></Card>
          <Card className={`border ${resumen.productosSinInvFinal > 0 ? 'bg-yellow-50' : ''}`}><CardContent className="py-3"><p className="text-xs text-zinc-500">Sin Inv.Fin</p><p className="text-lg font-bold text-yellow-600">{resumen.productosSinInvFinal}</p></CardContent></Card>
        </div>
      )}

      {/* Info período */}
      {infoInventario && (
        <Card className="border border-blue-200 bg-blue-50">
          <CardContent className="py-2 text-sm">
            <span className="font-semibold">Período:</span> {infoInventario.fechaInventarioFisico} → {fechaFinPeriodo} ({infoInventario.diasPeriodo} días) | 
            <span className="ml-2">Folio Ini: {infoInventario.folioInventarioFisico || (todosAlmacenes ? 'Consolidado' : 'N/A')}</span>
            {infoInventario.tieneInventarioFinal && <span className="ml-2 text-green-700">| Folio Fin: {infoInventario.folioInventarioFinal}</span>}
            {!infoInventario.tieneInventarioFinal && <span className="ml-2 text-orange-600">| Sin inv. final capturado</span>}
            {infoInventario.comparandoConPedido && <span className="ml-2 px-2 py-0.5 bg-green-200 rounded text-xs">vs {infoInventario.comparandoConPedido}</span>}
          </CardContent>
        </Card>
      )}

      {/* Tabla */}
      {pedidoData.length > 0 && (
        <Card className="border shadow-sm">
          <CardHeader className="py-2">
            <CardTitle className="text-base">Pedido Sugerido <span className="text-sm font-normal text-zinc-500">({pedidoData.filter(p => p.Cantidad_Pedir > 0).length} a pedir)</span></CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="rounded-b-md border-t max-h-[450px] overflow-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 z-10 bg-zinc-200">
                  <tr>
                    <th className="py-2 px-1 text-left font-semibold">Código</th>
                    <th className="py-2 px-1 text-left font-semibold">Producto</th>
                    <th className="py-2 px-1 text-right font-semibold">Inv.Ini</th>
                    <th className="py-2 px-1 text-right font-semibold cursor-help" title="Doble click para ver detalle">Movim.</th>
                    <th className="py-2 px-1 text-right font-semibold cursor-help" title="Doble click para ver detalle">Consumos</th>
                    <th className="py-2 px-1 text-right font-semibold">Inv.Fin</th>
                    <th className="py-2 px-1 text-right font-semibold">Teórico</th>
                    <th className="py-2 px-1 text-right font-semibold">Prom/Día</th>
                    <th className="py-2 px-1 text-right font-semibold">Días</th>
                    <th className="py-2 px-1 text-right font-semibold text-green-700">Pedir</th>
                    <th className="py-2 px-1 text-right font-semibold">Costo</th>
                    {infoInventario?.comparandoConPedido && <th className="py-2 px-1 text-right font-semibold text-blue-600">Pedido</th>}
                    {infoInventario?.comparandoConPedido && <th className="py-2 px-1 text-right font-semibold">Dif.</th>}
                  </tr>
                </thead>
                <tbody>
                  {pedidoData.map((row, idx) => {
                    const stockBajo = row.Dias_Inventario < 3 && row.Dias_Inventario !== 999;
                    return (
                      <tr key={row.Codigo || `pedido-row-${idx}`} className={`border-b hover:bg-zinc-50 ${row.Sin_Inventario_Inicial ? 'bg-orange-50' : ''} ${stockBajo ? 'bg-red-50' : ''}`}>
                        <td className="py-1 px-1 font-mono">{row.Codigo}</td>
                        <td className="py-1 px-1 max-w-[150px] truncate" title={row.Producto}>{row.Producto}</td>
                        <td className="py-1 px-1 text-right">
                          {row.Sin_Inventario_Inicial ? (
                            editingRow === row.Codigo ? (
                              <Input type="number" className="w-16 h-6 text-xs text-right" autoFocus onBlur={(e) => actualizarInvInicial(row.Codigo, e.target.value)} onKeyDown={(e) => e.key === 'Enter' && actualizarInvInicial(row.Codigo, e.target.value)} />
                            ) : (
                              <button onClick={() => setEditingRow(row.Codigo)} className="text-orange-600 hover:underline"><Edit3 className="h-3 w-3 inline" /> Ing.</button>
                            )
                          ) : formatNumber(row.Inventario_Inicial)}
                        </td>
                        <td className="py-1 px-1 text-right cursor-pointer hover:text-blue-600" onDoubleClick={() => verDetalleMovimientos(row.Codigo, row.Producto)}>
                          <span className={getDiferenciaClass(row.Movimientos_Periodo)}>{formatNumber(row.Movimientos_Periodo)}</span>
                        </td>
                        <td className="py-1 px-1 text-right text-red-600 cursor-pointer hover:text-blue-600" onDoubleClick={() => verDetalleConsumos(row.Codigo, row.Producto)}>{formatNumber(row.Consumos_Periodo)}</td>
                        <td className="py-1 px-1 text-right">
                          {row.Inventario_Final === null ? (
                            row.Sin_Inventario_Final ? (
                              editingFinal === row.Codigo ? (
                                <Input type="number" className="w-16 h-6 text-xs text-right" autoFocus onBlur={(e) => actualizarInvFinal(row.Codigo, e.target.value)} onKeyDown={(e) => e.key === 'Enter' && actualizarInvFinal(row.Codigo, e.target.value)} />
                              ) : (
                                <button onClick={() => setEditingFinal(row.Codigo)} className="text-yellow-600 hover:underline"><Edit3 className="h-3 w-3 inline" /> Ing.</button>
                              )
                            ) : <span className="text-zinc-400">-</span>
                          ) : formatNumber(row.Inventario_Final)}
                        </td>
                        <td className="py-1 px-1 text-right font-semibold">{formatNumber(row.Inventario_Teorico)}</td>
                        <td className="py-1 px-1 text-right">{formatNumber(row.Promedio_Diario)}</td>
                        <td className={`py-1 px-1 text-right font-semibold ${stockBajo ? 'text-red-600' : ''}`}>{row.Dias_Inventario >= 999 ? '∞' : formatNumber(row.Dias_Inventario)}</td>
                        <td className={`py-1 px-1 text-right font-bold ${row.Cantidad_Pedir > 0 ? 'text-green-700' : 'text-zinc-400'}`}>{formatNumber(row.Cantidad_Pedir)}</td>
                        <td className="py-1 px-1 text-right">{formatCurrency(row.Costo_Pedido)}</td>
                        {infoInventario?.comparandoConPedido && <td className="py-1 px-1 text-right text-blue-600">{row.Cantidad_Pedido_Existente !== null ? formatNumber(row.Cantidad_Pedido_Existente) : '-'}</td>}
                        {infoInventario?.comparandoConPedido && <td className={`py-1 px-1 text-right font-semibold ${getDiferenciaClass(row.Diferencia_Pedido)}`}>{row.Diferencia_Pedido !== null ? (row.Diferencia_Pedido > 0 ? '+' : '') + formatNumber(row.Diferencia_Pedido) : '-'}</td>}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal Detalle */}
      <Dialog open={detalleModal.open} onOpenChange={(open) => !open && setDetalleModal({ ...detalleModal, open: false })}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>{detalleModal.titulo}</DialogTitle>
          </DialogHeader>
          {detalleModal.loading ? (
            <div className="flex justify-center py-8"><Loader2 className="h-8 w-8 animate-spin" /></div>
          ) : detalleModal.data.length === 0 ? (
            <p className="text-center text-zinc-500 py-8">Sin movimientos en el período</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-zinc-100">
                <tr>
                  <th className="py-2 px-2 text-left">Fecha</th>
                  <th className="py-2 px-2 text-left">Documento</th>
                  {detalleModal.tipo === 'movimientos' && <th className="py-2 px-2 text-left">Tipo</th>}
                  {detalleModal.tipo === 'consumos' && <th className="py-2 px-2 text-left">Producto Vendido</th>}
                  <th className="py-2 px-2 text-right">Cantidad</th>
                </tr>
              </thead>
              <tbody>
                {detalleModal.data.map((item) => (
                  <tr key={`det-${item.fecha}-${item.documento}`} className="border-b">
                    <td className="py-1 px-2">{new Date(item.fecha).toLocaleDateString('es-MX')}</td>
                    <td className="py-1 px-2 font-mono text-xs">{item.documento}</td>
                    {detalleModal.tipo === 'movimientos' && <td className="py-1 px-2 text-xs">{item.tipo}</td>}
                    {detalleModal.tipo === 'consumos' && <td className="py-1 px-2 text-xs">{item.producto_vendido}</td>}
                    <td className={`py-1 px-2 text-right font-mono ${detalleModal.tipo === 'movimientos' ? (item.cantidad > 0 ? 'text-green-600' : 'text-red-600') : 'text-red-600'}`}>
                      {formatNumber(detalleModal.tipo === 'consumos' ? item.consumo : item.cantidad)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
