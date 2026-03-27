import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { Loader2, ShoppingCart, Package, TrendingUp, AlertTriangle, Download, AlertCircle, Calendar, Edit3 } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
};

const formatCurrency = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(num);
};

export default function AutorizacionCompras() {
  const [servers, setServers] = useState([]);
  const [selectedServer, setSelectedServer] = useState('');
  const [serverData, setServerData] = useState(null);
  const [sucursales, setSucursales] = useState([]);
  const [almacenes, setAlmacenes] = useState([]);
  const [selectedSucursal, setSelectedSucursal] = useState('');
  const [selectedAlmacen, setSelectedAlmacen] = useState('');
  const [fechaCalculo, setFechaCalculo] = useState(new Date().toISOString().split('T')[0]);
  const [diasHistorial, setDiasHistorial] = useState(30);
  const [diasInventario, setDiasInventario] = useState(10);
  const [loading, setLoading] = useState(false);
  const [pedidoData, setPedidoData] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [infoInventario, setInfoInventario] = useState(null);
  const [editingRow, setEditingRow] = useState(null);
  const [existenciaManual, setExistenciaManual] = useState({});

  // Cargar servidores al iniciar
  useEffect(() => {
    const fetchServers = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/api/servers`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setServers(response.data);
      } catch (error) {
        console.error('Error cargando servidores:', error);
        toast.error('Error al cargar servidores');
      }
    };
    fetchServers();
  }, []);

  // Cargar sucursales cuando cambia el servidor
  useEffect(() => {
    if (selectedServer) {
      const server = servers.find(s => s.id === selectedServer);
      setServerData(server);
      fetchSucursales(selectedServer);
      setSelectedSucursal('');
      setSelectedAlmacen('');
      setPedidoData([]);
    }
  }, [selectedServer, servers]);

  // Cargar almacenes cuando cambia la sucursal
  useEffect(() => {
    if (selectedServer && selectedSucursal) {
      fetchAlmacenes(selectedServer, selectedSucursal);
      setSelectedAlmacen('');
      setPedidoData([]);
    }
  }, [selectedServer, selectedSucursal]);

  const fetchSucursales = async (serverId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/servers/${serverId}/sucursales`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSucursales(response.data);
    } catch (error) {
      console.error('Error cargando sucursales:', error);
      toast.error('Error al cargar sucursales');
    }
  };

  const fetchAlmacenes = async (serverId, sucursal) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/servers/${serverId}/almacenes?sucursal=${encodeURIComponent(sucursal)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAlmacenes(response.data);
    } catch (error) {
      console.error('Error cargando almacenes:', error);
      toast.error('Error al cargar almacenes');
    }
  };

  const calcularPedido = async () => {
    if (!selectedServer || !selectedSucursal || !selectedAlmacen) {
      toast.error('Selecciona servidor, sucursal y almacén');
      return;
    }

    setLoading(true);
    setPedidoData([]);
    setResumen(null);
    setInfoInventario(null);
    setExistenciaManual({});

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/compras/calculo-pedido`, {
        server_id: selectedServer,
        sucursal: selectedSucursal,
        almacen: selectedAlmacen,
        fecha_calculo: fechaCalculo,
        dias_historial_ventas: parseInt(diasHistorial),
        dias_inventario: parseInt(diasInventario)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setPedidoData(response.data.data);
      
      // Guardar info del inventario físico
      setInfoInventario({
        tieneInventarioFisico: response.data.tiene_inventario_fisico,
        fechaInventarioFisico: response.data.fecha_inventario_fisico,
        folioInventarioFisico: response.data.folio_inventario_fisico,
        productosSinInventario: response.data.productos_sin_inventario,
        esBodega: response.data.es_bodega
      });
      
      // Calcular resumen
      const data = response.data.data;
      const totalProductos = data.length;
      const productosAPedir = data.filter(p => p.Cantidad_Pedir > 0).length;
      const costoTotalPedido = data.reduce((sum, p) => sum + (p.Costo_Pedido || 0), 0);
      const productosStockBajo = data.filter(p => p.Dias_Inventario < 3).length;
      const productosSinInvFisico = data.filter(p => p.Sin_Inventario_Fisico).length;

      setResumen({
        totalProductos,
        productosAPedir,
        costoTotalPedido,
        productosStockBajo,
        productosSinInvFisico,
        parametros: response.data.parametros
      });

      toast.success(`Cálculo completado: ${response.data.count} productos`);
    } catch (error) {
      console.error('Error calculando pedido:', error);
      toast.error(error.response?.data?.detail || 'Error al calcular pedido');
    } finally {
      setLoading(false);
    }
  };

  // Función para actualizar existencia manual y recalcular
  const actualizarExistenciaManual = (codigo, valor) => {
    const nuevoValor = parseFloat(valor) || 0;
    setExistenciaManual(prev => ({ ...prev, [codigo]: nuevoValor }));
    
    // Recalcular el pedido para este producto
    setPedidoData(prev => prev.map(row => {
      if (row.Codigo === codigo) {
        const invTeorico = nuevoValor + row.Compras_Periodo - row.Consumos_Periodo;
        const cantidadPedir = Math.max(0, row.Consumo_Esperado - invTeorico);
        const diasInv = row.Promedio_Diario > 0 ? invTeorico / row.Promedio_Diario : 999;
        return {
          ...row,
          Inventario_Fisico: nuevoValor,
          Inventario_Teorico: invTeorico,
          Cantidad_Pedir: cantidadPedir,
          Costo_Pedido: cantidadPedir * row.Costo_Unitario,
          Dias_Inventario: diasInv < 999 ? diasInv : 999,
          Sin_Inventario_Fisico: false,
          Existencia_Manual: nuevoValor
        };
      }
      return row;
    }));
    
    setEditingRow(null);
  };

  const exportarExcel = () => {
    // TODO: Implementar exportación a Excel
    toast.info('Exportación a Excel en desarrollo');
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800 flex items-center gap-2">
            <ShoppingCart className="h-6 w-6" />
            Autorización de Compras
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Calcula el pedido sugerido basándose en inventario, ventas y parámetros configurados
          </p>
        </div>
      </div>

      {/* Filtros */}
      <Card className="border border-zinc-200 shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold">Parámetros de Cálculo</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Servidor */}
            <div className="space-y-2">
              <Label>Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger data-testid="server-select">
                  <SelectValue placeholder="Selecciona un servidor" />
                </SelectTrigger>
                <SelectContent>
                  {servers.map((server) => (
                    <SelectItem key={server.id} value={server.id}>
                      {server.name} ({server.system_type})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Sucursal */}
            <div className="space-y-2">
              <Label>Sucursal</Label>
              <Select value={selectedSucursal} onValueChange={setSelectedSucursal} disabled={!selectedServer}>
                <SelectTrigger data-testid="sucursal-select">
                  <SelectValue placeholder="Selecciona sucursal" />
                </SelectTrigger>
                <SelectContent>
                  {sucursales.map((suc, idx) => (
                    <SelectItem key={idx} value={suc.nombre}>
                      {suc.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Almacén */}
            <div className="space-y-2">
              <Label>Almacén</Label>
              <Select value={selectedAlmacen} onValueChange={setSelectedAlmacen} disabled={!selectedSucursal}>
                <SelectTrigger data-testid="almacen-select">
                  <SelectValue placeholder="Selecciona almacén" />
                </SelectTrigger>
                <SelectContent>
                  {almacenes.map((alm, idx) => (
                    <SelectItem key={idx} value={alm.nombre}>
                      {alm.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Fecha de Cálculo */}
            <div className="space-y-2">
              <Label>Fecha de Cálculo</Label>
              <Input
                type="date"
                value={fechaCalculo}
                onChange={(e) => setFechaCalculo(e.target.value)}
                data-testid="fecha-calculo"
              />
            </div>

            {/* Días Historial */}
            <div className="space-y-2">
              <Label>Días Historial Ventas</Label>
              <Input
                type="number"
                value={diasHistorial}
                onChange={(e) => setDiasHistorial(e.target.value)}
                min="7"
                max="90"
                data-testid="dias-historial"
              />
            </div>

            {/* Días Inventario */}
            <div className="space-y-2">
              <Label>Días Inventario a Comprar</Label>
              <Input
                type="number"
                value={diasInventario}
                onChange={(e) => setDiasInventario(e.target.value)}
                min="1"
                max="30"
                data-testid="dias-inventario"
              />
            </div>

            {/* Botón Calcular */}
            <div className="space-y-2 flex items-end">
              <Button 
                onClick={calcularPedido} 
                disabled={loading || !selectedAlmacen}
                className="w-full"
                data-testid="btn-calcular"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Calculando...
                  </>
                ) : (
                  <>
                    <TrendingUp className="mr-2 h-4 w-4" />
                    Calcular Pedido
                  </>
                )}
              </Button>
            </div>

            {/* Botón Exportar */}
            <div className="space-y-2 flex items-end">
              <Button 
                variant="outline"
                onClick={exportarExcel} 
                disabled={pedidoData.length === 0}
                className="w-full"
                data-testid="btn-exportar"
              >
                <Download className="mr-2 h-4 w-4" />
                Exportar Excel
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Resumen KPIs */}
      {resumen && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className="border border-zinc-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500">Total Productos</p>
                  <p className="text-2xl font-bold text-zinc-800">{resumen.totalProductos}</p>
                </div>
                <Package className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border border-zinc-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500">Productos a Pedir</p>
                  <p className="text-2xl font-bold text-green-600">{resumen.productosAPedir}</p>
                </div>
                <ShoppingCart className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border border-zinc-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500">Costo Total Pedido</p>
                  <p className="text-2xl font-bold text-zinc-800">{formatCurrency(resumen.costoTotalPedido)}</p>
                </div>
                <TrendingUp className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border border-zinc-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500">Stock Bajo (&lt;3 días)</p>
                  <p className="text-2xl font-bold text-red-600">{resumen.productosStockBajo}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card className={`border ${resumen.productosSinInvFisico > 0 ? 'border-orange-300 bg-orange-50' : 'border-zinc-200'}`}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500">Sin Inv. Físico</p>
                  <p className={`text-2xl font-bold ${resumen.productosSinInvFisico > 0 ? 'text-orange-600' : 'text-zinc-400'}`}>
                    {resumen.productosSinInvFisico}
                  </p>
                </div>
                <AlertCircle className={`h-8 w-8 ${resumen.productosSinInvFisico > 0 ? 'text-orange-500' : 'text-zinc-300'}`} />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* Alerta de información del inventario */}
      {infoInventario && (
        <Card className={`border ${infoInventario.tieneInventarioFisico ? 'border-blue-200 bg-blue-50' : 'border-orange-200 bg-orange-50'}`}>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <Calendar className={`h-5 w-5 ${infoInventario.tieneInventarioFisico ? 'text-blue-600' : 'text-orange-600'}`} />
              <div className="flex-1">
                {infoInventario.tieneInventarioFisico ? (
                  <p className="text-sm text-blue-800">
                    <span className="font-semibold">Inventario Físico:</span> Folio {infoInventario.folioInventarioFisico} 
                    {infoInventario.fechaInventarioFisico && ` del ${new Date(infoInventario.fechaInventarioFisico).toLocaleDateString('es-MX')}`}
                    {infoInventario.esBodega && <span className="ml-2 px-2 py-0.5 bg-blue-200 rounded text-xs">BODEGA</span>}
                  </p>
                ) : (
                  <p className="text-sm text-orange-800">
                    <span className="font-semibold">Sin inventario físico capturado.</span> Ingresa las existencias manualmente para calcular correctamente.
                  </p>
                )}
              </div>
              {infoInventario.productosSinInventario > 0 && (
                <span className="text-xs bg-orange-200 text-orange-800 px-2 py-1 rounded">
                  {infoInventario.productosSinInventario} productos requieren existencia manual
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabla de Resultados */}
      {pedidoData.length > 0 && (
        <Card className="border border-zinc-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold">Pedido Sugerido</CardTitle>
              <span className="text-sm text-zinc-600">
                {pedidoData.filter(p => p.Cantidad_Pedir > 0).length} productos a pedir
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border border-zinc-200 max-h-[500px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 z-10 bg-zinc-200">
                  <tr className="border-b-2 border-zinc-400">
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-left">Código</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-left">Producto</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-left">Familia</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Inv. Físico</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Compras</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Consumos</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Inv. Teórico</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Prom. Diario</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Días Inv.</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Consumo Esp.</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Cant. Pedir</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Costo Pedido</th>
                  </tr>
                </thead>
                <tbody>
                  {pedidoData.map((row, idx) => {
                    const necesitaPedir = row.Cantidad_Pedir > 0;
                    const stockCritico = row.Dias_Inventario < 3;
                    const sinInvFisico = row.Sin_Inventario_Fisico;
                    const isEditing = editingRow === row.Codigo;
                    
                    return (
                      <tr 
                        key={idx} 
                        className={`border-b hover:bg-zinc-50 
                          ${sinInvFisico ? 'bg-orange-50' : ''} 
                          ${necesitaPedir && !sinInvFisico ? 'bg-yellow-50' : ''} 
                          ${stockCritico && !sinInvFisico ? 'bg-red-50' : ''}`}
                        data-testid={`row-${row.Codigo}`}
                      >
                        <td className="py-2 px-2 font-mono text-xs">{row.Codigo}</td>
                        <td className="py-2 px-2 text-sm max-w-[200px] truncate" title={row.Producto}>{row.Producto}</td>
                        <td className="py-2 px-2 text-sm">{row.Familia}</td>
                        <td className="py-2 px-2 text-right">
                          {sinInvFisico ? (
                            isEditing ? (
                              <Input
                                type="number"
                                step="0.01"
                                className="w-20 h-7 text-xs text-right"
                                defaultValue={existenciaManual[row.Codigo] || ''}
                                autoFocus
                                onBlur={(e) => actualizarExistenciaManual(row.Codigo, e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') {
                                    actualizarExistenciaManual(row.Codigo, e.target.value);
                                  } else if (e.key === 'Escape') {
                                    setEditingRow(null);
                                  }
                                }}
                                data-testid={`input-existencia-${row.Codigo}`}
                              />
                            ) : (
                              <button
                                onClick={() => setEditingRow(row.Codigo)}
                                className="flex items-center gap-1 text-orange-600 hover:text-orange-800 font-mono text-xs"
                                title="Clic para ingresar existencia"
                                data-testid={`btn-edit-${row.Codigo}`}
                              >
                                <Edit3 className="h-3 w-3" />
                                {row.Existencia_Manual !== null ? formatNumber(row.Existencia_Manual) : 'Ingresar'}
                              </button>
                            )
                          ) : (
                            <span className="font-mono">{formatNumber(row.Inventario_Fisico)}</span>
                          )}
                        </td>
                        <td className="py-2 px-2 text-right font-mono text-green-700">{formatNumber(row.Compras_Periodo)}</td>
                        <td className="py-2 px-2 text-right font-mono text-red-600">{formatNumber(row.Consumos_Periodo)}</td>
                        <td className="py-2 px-2 text-right font-mono font-semibold">{formatNumber(row.Inventario_Teorico)}</td>
                        <td className="py-2 px-2 text-right font-mono">{formatNumber(row.Promedio_Diario)}</td>
                        <td className={`py-2 px-2 text-right font-mono font-semibold ${stockCritico ? 'text-red-600' : ''}`}>
                          {row.Dias_Inventario >= 999 ? '∞' : formatNumber(row.Dias_Inventario)}
                        </td>
                        <td className="py-2 px-2 text-right font-mono">{formatNumber(row.Consumo_Esperado)}</td>
                        <td className={`py-2 px-2 text-right font-mono font-bold ${necesitaPedir ? 'text-green-700' : 'text-zinc-400'}`}>
                          {formatNumber(row.Cantidad_Pedir)}
                        </td>
                        <td className="py-2 px-2 text-right font-mono">{formatCurrency(row.Costo_Pedido)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Mensaje cuando no hay datos */}
      {!loading && pedidoData.length === 0 && selectedAlmacen && (
        <Card className="border border-zinc-200">
          <CardContent className="py-12 text-center">
            <ShoppingCart className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
            <p className="text-zinc-500">Selecciona los parámetros y haz clic en "Calcular Pedido"</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
