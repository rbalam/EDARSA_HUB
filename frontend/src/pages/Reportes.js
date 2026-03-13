import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { FileDown, Mail, Search, AlertCircle, TrendingUp, TrendingDown, ChevronDown, X, Filter } from 'lucide-react';
import { toast } from 'sonner';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

const Reportes = () => {
  const [servers, setServers] = useState([]);
  const [sucursales, setSucursales] = useState([]);
  const [almacenes, setAlmacenes] = useState([]);
  const [inventarios, setInventarios] = useState([]);
  const [reportData, setReportData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    server_id: '',
    query_type: 'analisis',
    sucursal_id: '',
    sucursal: '',
    almacen_id: '',
    almacen: '',
    inventario_inicial: '',
    inventario_inicial_fecha: '',
    inventario_final: '',
    inventario_final_fecha: '',
    fecha_ini: '',
    fecha_fin: ''
  });

  const [selectedServer, setSelectedServer] = useState(null);
  
  // Estados para filtros de categoría/familia/subfamilia
  const [filterOptions, setFilterOptions] = useState({
    categorias: [],
    familias: [],
    subfamilias: []
  });
  const [selectedCategorias, setSelectedCategorias] = useState([]);
  const [selectedFamilias, setSelectedFamilias] = useState([]);
  const [selectedSubfamilias, setSelectedSubfamilias] = useState([]);
  const [loadingFilters, setLoadingFilters] = useState(false);

  useEffect(() => {
    loadServers();
  }, []);

  useEffect(() => {
    if (filters.server_id) {
      loadSucursales();
      loadReportFilters();
      // Guardar el servidor seleccionado
      const server = servers.find(s => s.id === filters.server_id);
      setSelectedServer(server);
    }
  }, [filters.server_id, servers]);

  // Cargar opciones de filtros (categorías, familias, subfamilias)
  const loadReportFilters = async () => {
    if (!filters.server_id) return;
    
    setLoadingFilters(true);
    try {
      const response = await api.get(`/servers/${filters.server_id}/report-filters`);
      setFilterOptions({
        categorias: response.data.categorias || [],
        familias: response.data.familias || [],
        subfamilias: response.data.subfamilias || []
      });
    } catch (error) {
      console.error('Error al cargar filtros:', error);
      setFilterOptions({ categorias: [], familias: [], subfamilias: [] });
    } finally {
      setLoadingFilters(false);
    }
  };

  useEffect(() => {
    if (filters.server_id && filters.sucursal_id) {
      loadAlmacenes();
    }
  }, [filters.server_id, filters.sucursal_id]);

  useEffect(() => {
    if (filters.server_id && filters.sucursal_id && filters.almacen_id) {
      loadInventarios();
    }
  }, [filters.server_id, filters.sucursal_id, filters.almacen_id]);

  const loadServers = async () => {
    try {
      console.log('Cargando servidores...');
      const response = await api.get('/servers');
      console.log('Respuesta servers:', response.status, response.data);
      const data = Array.isArray(response.data) ? response.data : [];
      console.log('Servidores cargados:', data.length);
      setServers(data);
      if (data.length === 0) {
        console.warn('No se recibieron servidores');
      }
    } catch (error) {
      console.error('Error al cargar servidores:', error.response?.status, error.response?.data);
      toast.error('Error al cargar servidores: ' + (error.response?.data?.detail || error.message));
      setServers([]);
    }
  };

  const loadSucursales = async () => {
    try {
      const response = await api.get(`/servers/${filters.server_id}/sucursales`);
      const data = Array.isArray(response.data) ? response.data : [];
      setSucursales(data);
    } catch (error) {
      console.error('Error al cargar sucursales:', error);
      setSucursales([]);
    }
  };

  const loadAlmacenes = async () => {
    try {
      const response = await api.get(`/servers/${filters.server_id}/almacenes`, {
        params: { sucursal_id: filters.sucursal_id }
      });
      setAlmacenes(response.data);
    } catch (error) {
      console.error('Error al cargar almacenes:', error);
      setAlmacenes([]);
    }
  };

  const loadInventarios = async () => {
    try {
      const response = await api.get(`/servers/${filters.server_id}/inventarios`, {
        params: { 
          sucursal_id: filters.sucursal_id,
          almacen_id: filters.almacen_id
        }
      });
      setInventarios(response.data);
    } catch (error) {
      console.error('Error al cargar inventarios:', error);
      setInventarios([]);
    }
  };

  const handleGenerateReport = async () => {
    if (!filters.server_id) {
      toast.error('Selecciona un servidor');
      return;
    }

    // Validar campos requeridos para análisis completo
    if (filters.query_type === 'analisis') {
      if (!filters.sucursal) {
        toast.error('Selecciona una sucursal');
        return;
      }
      if (!filters.almacen) {
        toast.error('Selecciona un almacén');
        return;
      }
      if (!filters.fecha_ini || !filters.fecha_fin) {
        toast.error('Selecciona fechas de inicio y fin');
        return;
      }
      if (!filters.inventario_inicial || !filters.inventario_final) {
        toast.error('Selecciona inventario inicial y final');
        return;
      }
    }

    setLoading(true);
    try {
      let response;
      
      if (filters.query_type === 'analisis') {
        // Llamar al endpoint de análisis completo con filtros adicionales
        response = await api.post('/reports/inventory-analysis', {
          server_id: filters.server_id,
          sucursal: filters.sucursal,
          almacen: filters.almacen,
          fecha_ini: filters.fecha_ini,
          fecha_fin: filters.fecha_fin,
          folio_inicial: filters.inventario_inicial,
          folio_final: filters.inventario_final,
          // Enviar filtros de categoría/familia/subfamilia
          categorias: selectedCategorias,
          familias: selectedFamilias,
          subfamilias: selectedSubfamilias
        });
      } else {
        // Llamar al endpoint normal de reportes
        response = await api.post('/reports/inventory', {
          server_id: filters.server_id,
          query_type: filters.query_type,
          params: {
            sucursal: filters.sucursal,
            almacen: filters.almacen,
            fecha_ini: filters.fecha_ini,
            fecha_fin: filters.fecha_fin
          }
        });
      }
      
      setReportData(response.data.data);
      toast.success(`Reporte generado: ${response.data.count} registros`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al generar reporte');
    } finally {
      setLoading(false);
    }
  };

  const handleSucursalChange = (value) => {
    const sucursal = sucursales.find(s => s.id === value);
    setFilters({
      ...filters, 
      sucursal_id: value,
      sucursal: sucursal?.nombre || '',
      almacen_id: '',
      almacen: '',
      inventario_inicial: '',
      inventario_final: ''
    });
    setAlmacenes([]);
    setInventarios([]);
  };

  const handleAlmacenChange = (value) => {
    const almacen = almacenes.find(a => a.id === value);
    setFilters({
      ...filters, 
      almacen_id: value,
      almacen: almacen?.nombre || '',
      inventario_inicial: '',
      inventario_inicial_fecha: '',
      inventario_final: '',
      inventario_final_fecha: '',
      fecha_ini: '',
      fecha_fin: ''
    });
  };

  const calculateDates = (inicialFecha, finalFecha, systemType) => {
    if (!inicialFecha || !finalFecha) return { fecha_ini: '', fecha_fin: '' };

    let fecha_ini, fecha_fin;

    if (systemType === 'MPRO') {
      // Para MPRO: usar las fechas exactas de los inventarios
      fecha_ini = inicialFecha.split(' ')[0]; // Solo fecha, sin hora
      fecha_fin = finalFecha.split(' ')[0];
    } else if (systemType === 'SoftRestaurant') {
      // Para SoftRestaurant: fecha inicial + 1 segundo, fecha final - 1 segundo
      const fechaInicialDate = new Date(inicialFecha);
      const fechaFinalDate = new Date(finalFecha);
      
      fechaInicialDate.setSeconds(fechaInicialDate.getSeconds() + 1);
      fechaFinalDate.setSeconds(fechaFinalDate.getSeconds() - 1);
      
      fecha_ini = fechaInicialDate.toISOString().slice(0, 19).replace('T', ' ');
      fecha_fin = fechaFinalDate.toISOString().slice(0, 19).replace('T', ' ');
    } else {
      // Default: usar las fechas exactas
      fecha_ini = inicialFecha.split(' ')[0];
      fecha_fin = finalFecha.split(' ')[0];
    }

    return { fecha_ini, fecha_fin };
  };

  const handleInventarioInicialChange = (value) => {
    const inventario = inventarios.find(inv => inv.folio === value);
    const nuevaFechaInicial = inventario?.fecha_completa || inventario?.fecha || '';
    
    const newFilters = {
      ...filters,
      inventario_inicial: value,
      inventario_inicial_fecha: nuevaFechaInicial
    };

    // Si ya hay inventario final, recalcular fechas
    if (filters.inventario_final_fecha && selectedServer) {
      const dates = calculateDates(nuevaFechaInicial, filters.inventario_final_fecha, selectedServer.system_type);
      newFilters.fecha_ini = dates.fecha_ini;
      newFilters.fecha_fin = dates.fecha_fin;
    }

    setFilters(newFilters);
  };

  const handleInventarioFinalChange = (value) => {
    const inventario = inventarios.find(inv => inv.folio === value);
    const nuevaFechaFinal = inventario?.fecha_completa || inventario?.fecha || '';
    
    const newFilters = {
      ...filters,
      inventario_final: value,
      inventario_final_fecha: nuevaFechaFinal
    };

    // Si ya hay inventario inicial, recalcular fechas
    if (filters.inventario_inicial_fecha && selectedServer) {
      const dates = calculateDates(filters.inventario_inicial_fecha, nuevaFechaFinal, selectedServer.system_type);
      newFilters.fecha_ini = dates.fecha_ini;
      newFilters.fecha_fin = dates.fecha_fin;
    }

    setFilters(newFilters);
  };

  const handleExportExcel = () => {
    if (reportData.length === 0) {
      toast.error('No hay datos para exportar');
      return;
    }

    try {
      const worksheet = XLSX.utils.json_to_sheet(reportData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Reporte');
      
      const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const fileName = `reporte_inventario_${new Date().toISOString().split('T')[0]}.xlsx`;
      
      saveAs(blob, fileName);
      
      toast.success(`Archivo "${fileName}" descargado correctamente. Revisa tu carpeta de Descargas.`);
    } catch (error) {
      console.error('Error al exportar Excel:', error);
      toast.error('Error al exportar a Excel: ' + error.message);
    }
  };

  const handleExportPDF = () => {
    if (reportData.length === 0) {
      toast.error('No hay datos para exportar');
      return;
    }

    try {
      const doc = new jsPDF('landscape');
      
      doc.setFontSize(18);
      doc.text('Reporte de Inventario', 14, 20);
      
      doc.setFontSize(10);
      doc.text(`Fecha: ${new Date().toLocaleDateString()}`, 14, 28);
      doc.text(`Sucursal: ${filters.sucursal}`, 14, 34);
      doc.text(`Almacén: ${filters.almacen}`, 14, 40);
      doc.text(`Período: ${filters.fecha_ini} a ${filters.fecha_fin}`, 14, 46);
      
      // Columnas más relevantes para el PDF
      const columns = ['Codigo', 'Producto', 'Inv_Inicial_Cantidad', 'Movimientos', 'Ventas', 'Inv_Teorico_Cantidad', 'Inv_Final_Cantidad', 'Diferencia_Cantidad'];
      const headers = ['Código', 'Producto', 'Inv. Inicial', 'Movimientos', 'Ventas', 'Inv. Teórico', 'Inv. Final', 'Diferencia'];
      
      const data = reportData.map(row => columns.map(col => {
        const val = row[col];
        if (typeof val === 'number') return val.toLocaleString('es-MX', { maximumFractionDigits: 2 });
        return val || '';
      }));
      
      autoTable(doc, {
        head: [headers],
        body: data,
        startY: 52,
        styles: { fontSize: 7, cellPadding: 2 },
        headStyles: { fillColor: [24, 24, 27], fontSize: 8 },
        columnStyles: {
          0: { cellWidth: 25 },
          1: { cellWidth: 60 },
          2: { cellWidth: 25, halign: 'right' },
          3: { cellWidth: 25, halign: 'right' },
          4: { cellWidth: 25, halign: 'right' },
          5: { cellWidth: 25, halign: 'right' },
          6: { cellWidth: 25, halign: 'right' },
          7: { cellWidth: 25, halign: 'right' }
        }
      });
      
      const fileName = `reporte_inventario_${new Date().toISOString().split('T')[0]}.pdf`;
      doc.save(fileName);
      
      toast.success(`Archivo "${fileName}" descargado correctamente. Revisa tu carpeta de Descargas.`);
    } catch (error) {
      console.error('Error al exportar PDF:', error);
      toast.error('Error al exportar a PDF: ' + error.message);
    }
  };

  const getDifferenceColor = (value) => {
    if (value > 0) return 'text-red-600';
    if (value < 0) return 'text-green-600';
    return 'text-zinc-600';
  };

  const getDifferenceIcon = (value) => {
    if (value > 0) return <TrendingUp className="h-4 w-4 inline mr-1" />;
    if (value < 0) return <TrendingDown className="h-4 w-4 inline mr-1" />;
    return null;
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('es-MX', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    }).format(num);
  };

  const formatCurrency = (num) => {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('es-MX', { 
      style: 'currency', 
      currency: 'MXN' 
    }).format(num);
  };

  return (
    <div className="space-y-6" data-testid="reportes-page">
      <div>
        <h1 className="text-3xl font-extrabold text-zinc-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Reportes de Inventario
        </h1>
        <p className="text-zinc-600 mt-1">Genera y analiza reportes de inventario</p>
      </div>

      {/* Filters */}
      <Card className="border border-zinc-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Servidor {servers.length === 0 && <span className="text-red-500 text-xs">(Cargando...)</span>}</Label>
              <Select value={filters.server_id} onValueChange={(value) => setFilters({...filters, server_id: value, sucursal_id: '', almacen_id: '', sucursal: '', almacen: ''})}>
                <SelectTrigger data-testid="server-select">
                  <SelectValue placeholder={servers.length === 0 ? "Cargando servidores..." : "Selecciona un servidor"} />
                </SelectTrigger>
                <SelectContent>
                  {servers.length === 0 ? (
                    <SelectItem value="loading" disabled>No hay servidores disponibles</SelectItem>
                  ) : (
                    servers.map((server) => (
                      <SelectItem key={server.id} value={server.id}>
                        {server.name} ({server.system_type})
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Tipo de Consulta</Label>
              <Select value={filters.query_type} onValueChange={(value) => setFilters({...filters, query_type: value})}>
                <SelectTrigger data-testid="query-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="analisis">Análisis de Inventarios</SelectItem>
                  <SelectItem value="ventas">Ventas</SelectItem>
                  <SelectItem value="movimientos">Movimientos</SelectItem>
                  <SelectItem value="productos">Productos</SelectItem>
                  <SelectItem value="inventarios">Inventarios Físicos</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Sucursal</Label>
              <Select 
                value={filters.sucursal_id} 
                onValueChange={handleSucursalChange}
                disabled={!filters.server_id || sucursales.length === 0}
              >
                <SelectTrigger data-testid="sucursal-select">
                  <SelectValue placeholder={!filters.server_id ? "Selecciona servidor primero" : "Selecciona una sucursal"} />
                </SelectTrigger>
                <SelectContent>
                  {sucursales.map((sucursal) => (
                    <SelectItem key={sucursal.id} value={sucursal.id}>
                      {sucursal.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Almacén</Label>
              <Select 
                value={filters.almacen_id} 
                onValueChange={handleAlmacenChange}
                disabled={!filters.sucursal_id || almacenes.length === 0}
              >
                <SelectTrigger data-testid="almacen-select">
                  <SelectValue placeholder={!filters.sucursal_id ? "Selecciona sucursal primero" : "Selecciona un almacén"} />
                </SelectTrigger>
                <SelectContent>
                  {almacenes.map((almacen) => (
                    <SelectItem key={almacen.id} value={almacen.id}>
                      {almacen.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Inventario Inicial</Label>
              <Select 
                value={filters.inventario_inicial} 
                onValueChange={handleInventarioInicialChange}
                disabled={!filters.almacen_id || inventarios.length === 0}
              >
                <SelectTrigger data-testid="inventario-inicial-select">
                  <SelectValue placeholder={!filters.almacen_id ? "Selecciona almacén primero" : "Selecciona inventario inicial"} />
                </SelectTrigger>
                <SelectContent>
                  {inventarios.map((inv) => (
                    <SelectItem key={inv.folio} value={inv.folio}>
                      Folio: {inv.folio} - {inv.fecha ? new Date(inv.fecha).toLocaleDateString('es-MX') : 'Sin fecha'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Inventario Final</Label>
              <Select 
                value={filters.inventario_final} 
                onValueChange={handleInventarioFinalChange}
                disabled={!filters.almacen_id || inventarios.length === 0}
              >
                <SelectTrigger data-testid="inventario-final-select">
                  <SelectValue placeholder={!filters.almacen_id ? "Selecciona almacén primero" : "Selecciona inventario final"} />
                </SelectTrigger>
                <SelectContent>
                  {inventarios.map((inv) => (
                    <SelectItem key={inv.folio} value={inv.folio}>
                      Folio: {inv.folio} - {inv.fecha ? new Date(inv.fecha).toLocaleDateString('es-MX') : 'Sin fecha'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>
                Fecha Inicio de Ventas 
                {selectedServer && (
                  <span className="text-xs text-zinc-500 ml-2">
                    ({selectedServer.system_type === 'MPRO' ? 'Fecha inv. inicial' : 'Fecha inv. inicial + 1 seg'})
                  </span>
                )}
              </Label>
              <Input
                type="text"
                value={filters.fecha_ini}
                readOnly
                disabled
                className="bg-zinc-50 cursor-not-allowed"
                placeholder="Auto-calculado al seleccionar inventarios"
                data-testid="fecha-inicio-input"
              />
            </div>

            <div className="space-y-2">
              <Label>
                Fecha Fin de Ventas
                {selectedServer && (
                  <span className="text-xs text-zinc-500 ml-2">
                    ({selectedServer.system_type === 'MPRO' ? 'Fecha inv. final' : 'Fecha inv. final - 1 seg'})
                  </span>
                )}
              </Label>
              <Input
                type="text"
                value={filters.fecha_fin}
                readOnly
                disabled
                className="bg-zinc-50 cursor-not-allowed"
                placeholder="Auto-calculado al seleccionar inventarios"
                data-testid="fecha-fin-input"
              />
            </div>
          </div>

          {/* Filtros adicionales (Categoría, Familia, SubFamilia) - Solo para MPRO */}
          {filters.query_type === 'analisis' && selectedServer?.system_type === 'MPRO' && (
            <div className="mt-6 pt-4 border-t border-zinc-200">
              <div className="flex items-center gap-2 mb-4">
                <Filter className="h-4 w-4 text-zinc-500" />
                <h3 className="text-sm font-semibold text-zinc-700">Filtros Adicionales (Opcional)</h3>
                {loadingFilters && <span className="text-xs text-zinc-400">Cargando...</span>}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Multiselect Categorías */}
                <div className="space-y-2">
                  <Label>Categorías</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button 
                        variant="outline" 
                        className="w-full justify-between font-normal"
                        data-testid="categorias-multiselect"
                        disabled={filterOptions.categorias.length === 0}
                      >
                        <span className="truncate">
                          {selectedCategorias.length === 0 
                            ? 'Todas las categorías' 
                            : `${selectedCategorias.length} seleccionada(s)`}
                        </span>
                        <ChevronDown className="h-4 w-4 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-64 p-2 max-h-64 overflow-y-auto">
                      {selectedCategorias.length > 0 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="w-full mb-2 text-xs"
                          onClick={() => setSelectedCategorias([])}
                        >
                          <X className="h-3 w-3 mr-1" /> Limpiar selección
                        </Button>
                      )}
                      {filterOptions.categorias.map((cat) => (
                        <div key={cat.id} className="flex items-center space-x-2 py-1.5 px-2 hover:bg-zinc-50 rounded">
                          <Checkbox
                            id={`cat-${cat.id}`}
                            checked={selectedCategorias.includes(cat.id)}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setSelectedCategorias([...selectedCategorias, cat.id]);
                              } else {
                                setSelectedCategorias(selectedCategorias.filter(c => c !== cat.id));
                              }
                            }}
                          />
                          <label htmlFor={`cat-${cat.id}`} className="text-sm cursor-pointer flex-1">
                            {cat.nombre}
                          </label>
                        </div>
                      ))}
                      {filterOptions.categorias.length === 0 && (
                        <p className="text-xs text-zinc-400 text-center py-2">No hay categorías disponibles</p>
                      )}
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Multiselect Familias */}
                <div className="space-y-2">
                  <Label>Familias</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button 
                        variant="outline" 
                        className="w-full justify-between font-normal"
                        data-testid="familias-multiselect"
                        disabled={filterOptions.familias.length === 0}
                      >
                        <span className="truncate">
                          {selectedFamilias.length === 0 
                            ? 'Todas las familias' 
                            : `${selectedFamilias.length} seleccionada(s)`}
                        </span>
                        <ChevronDown className="h-4 w-4 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-64 p-2 max-h-64 overflow-y-auto">
                      {selectedFamilias.length > 0 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="w-full mb-2 text-xs"
                          onClick={() => setSelectedFamilias([])}
                        >
                          <X className="h-3 w-3 mr-1" /> Limpiar selección
                        </Button>
                      )}
                      {filterOptions.familias.map((fam) => (
                        <div key={fam.id} className="flex items-center space-x-2 py-1.5 px-2 hover:bg-zinc-50 rounded">
                          <Checkbox
                            id={`fam-${fam.id}`}
                            checked={selectedFamilias.includes(fam.id)}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setSelectedFamilias([...selectedFamilias, fam.id]);
                              } else {
                                setSelectedFamilias(selectedFamilias.filter(f => f !== fam.id));
                              }
                            }}
                          />
                          <label htmlFor={`fam-${fam.id}`} className="text-sm cursor-pointer flex-1">
                            {fam.nombre}
                          </label>
                        </div>
                      ))}
                      {filterOptions.familias.length === 0 && (
                        <p className="text-xs text-zinc-400 text-center py-2">No hay familias disponibles</p>
                      )}
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Multiselect SubFamilias */}
                <div className="space-y-2">
                  <Label>SubFamilias</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button 
                        variant="outline" 
                        className="w-full justify-between font-normal"
                        data-testid="subfamilias-multiselect"
                        disabled={filterOptions.subfamilias.length === 0}
                      >
                        <span className="truncate">
                          {selectedSubfamilias.length === 0 
                            ? 'Todas las subfamilias' 
                            : `${selectedSubfamilias.length} seleccionada(s)`}
                        </span>
                        <ChevronDown className="h-4 w-4 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-64 p-2 max-h-64 overflow-y-auto">
                      {selectedSubfamilias.length > 0 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="w-full mb-2 text-xs"
                          onClick={() => setSelectedSubfamilias([])}
                        >
                          <X className="h-3 w-3 mr-1" /> Limpiar selección
                        </Button>
                      )}
                      {filterOptions.subfamilias.map((sf) => (
                        <div key={sf.id} className="flex items-center space-x-2 py-1.5 px-2 hover:bg-zinc-50 rounded">
                          <Checkbox
                            id={`sf-${sf.id}`}
                            checked={selectedSubfamilias.includes(sf.id)}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setSelectedSubfamilias([...selectedSubfamilias, sf.id]);
                              } else {
                                setSelectedSubfamilias(selectedSubfamilias.filter(s => s !== sf.id));
                              }
                            }}
                          />
                          <label htmlFor={`sf-${sf.id}`} className="text-sm cursor-pointer flex-1">
                            {sf.nombre}
                          </label>
                        </div>
                      ))}
                      {filterOptions.subfamilias.length === 0 && (
                        <p className="text-xs text-zinc-400 text-center py-2">No hay subfamilias disponibles</p>
                      )}
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
              
              {/* Resumen de filtros seleccionados */}
              {(selectedCategorias.length > 0 || selectedFamilias.length > 0 || selectedSubfamilias.length > 0) && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {selectedCategorias.map(id => {
                    const cat = filterOptions.categorias.find(c => c.id === id);
                    return cat && (
                      <span key={id} className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full">
                        {cat.nombre}
                        <X 
                          className="h-3 w-3 cursor-pointer hover:text-blue-900" 
                          onClick={() => setSelectedCategorias(selectedCategorias.filter(c => c !== id))}
                        />
                      </span>
                    );
                  })}
                  {selectedFamilias.map(id => {
                    const fam = filterOptions.familias.find(f => f.id === id);
                    return fam && (
                      <span key={id} className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 text-xs rounded-full">
                        {fam.nombre}
                        <X 
                          className="h-3 w-3 cursor-pointer hover:text-green-900" 
                          onClick={() => setSelectedFamilias(selectedFamilias.filter(f => f !== id))}
                        />
                      </span>
                    );
                  })}
                  {selectedSubfamilias.map(id => {
                    const sf = filterOptions.subfamilias.find(s => s.id === id);
                    return sf && (
                      <span key={id} className="inline-flex items-center gap-1 px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded-full">
                        {sf.nombre}
                        <X 
                          className="h-3 w-3 cursor-pointer hover:text-purple-900" 
                          onClick={() => setSelectedSubfamilias(selectedSubfamilias.filter(s => s !== id))}
                        />
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          <div className="flex gap-2 mt-4">
            <Button 
              onClick={handleGenerateReport}
              disabled={loading}
              className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
              data-testid="generate-report-button"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Generando...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Generar Reporte
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      {reportData.length > 0 && (
        <div className="flex gap-2">
          <Button 
            onClick={handleExportExcel}
            variant="outline"
            data-testid="export-excel-button"
          >
            <FileDown className="h-4 w-4 mr-2" />
            Exportar a Excel
          </Button>
          <Button 
            onClick={handleExportPDF}
            variant="outline"
            data-testid="export-pdf-button"
          >
            <FileDown className="h-4 w-4 mr-2" />
            Exportar a PDF
          </Button>
        </div>
      )}

      {/* Results */}
      {reportData.length > 0 && (
        <Card className="border border-zinc-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold">Resultados</CardTitle>
              <span className="text-sm text-zinc-600">
                Total: <span className="font-data font-semibold">{reportData.length}</span> registros
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border border-zinc-200 overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-zinc-50">
                    {Object.keys(reportData[0]).map((key) => (
                      <TableHead key={key} className="text-xs uppercase tracking-wider font-medium text-zinc-500 whitespace-nowrap">
                        {key.replace(/_/g, ' ')}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reportData.slice(0, 2000).map((row, idx) => (
                    <TableRow key={idx} className="hover:bg-zinc-50/50">
                      {Object.entries(row).map(([key, value], cellIdx) => {
                        // Special formatting for analysis report
                        const isDiferencia = key.toLowerCase().includes('diferencia');
                        const isCosto = key.toLowerCase().includes('costo');
                        const isPorcentaje = key.toLowerCase().includes('porcentaje');
                        
                        let displayValue = value;
                        let className = "text-sm font-data text-zinc-700";
                        
                        if (isPorcentaje && value !== null && value !== undefined) {
                          displayValue = `${formatNumber(value)}%`;
                          className = `text-sm font-data font-semibold ${getDifferenceColor(parseFloat(value))}`;
                        } else if (isCosto && value !== null && value !== undefined) {
                          displayValue = formatCurrency(value);
                        } else if ((key.toLowerCase().includes('cantidad') || key.toLowerCase().includes('ventas') || key.toLowerCase().includes('movimientos')) && value !== null && value !== undefined && typeof value === 'number') {
                          displayValue = formatNumber(value);
                        } else if (isDiferencia && value !== null && value !== undefined) {
                          const numValue = parseFloat(value);
                          displayValue = (
                            <span className={`font-semibold ${getDifferenceColor(numValue)}`}>
                              {getDifferenceIcon(numValue)}
                              {isCosto ? formatCurrency(numValue) : formatNumber(numValue)}
                            </span>
                          );
                        } else if (value === null || value === undefined) {
                          displayValue = '-';
                        } else {
                          displayValue = String(value);
                        }
                        
                        return (
                          <TableCell key={cellIdx} className={className}>
                            {displayValue}
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {reportData.length > 2000 && (
              <p className="text-sm text-zinc-600 mt-4 text-center">
                Mostrando 2000 de {reportData.length} registros. Exporta para ver todos.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {reportData.length === 0 && !loading && (
        <Card className="border border-zinc-200 shadow-sm">
          <CardContent className="py-12">
            <div className="text-center text-zinc-500">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-zinc-400" />
              <p>No hay datos para mostrar</p>
              <p className="text-sm mt-2">Configura los filtros y genera un reporte</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Reportes;