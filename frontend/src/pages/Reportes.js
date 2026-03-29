import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { FileDown, Mail, Search, AlertCircle, TrendingUp, TrendingDown, X, Loader2, ChevronDown, Filter } from 'lucide-react';
import { toast } from 'sonner';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

// Estilos para los selectores nativos
const selectStyle = "w-full h-10 px-3 py-2 text-sm border border-zinc-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-zinc-100 disabled:cursor-not-allowed";

const Reportes = () => {
  const [servers, setServers] = useState([]);
  const [sucursales, setSucursales] = useState([]);
  const [almacenes, setAlmacenes] = useState([]);
  const [inventarios, setInventarios] = useState([]);
  const [reportData, setReportData] = useState(() => {
    // Recuperar datos del reporte desde sessionStorage
    try {
      const saved = sessionStorage.getItem('reportData');
      if (saved) {
        const parsed = JSON.parse(saved);
        // Validar que sea un array
        if (Array.isArray(parsed)) {
          return parsed;
        }
      }
    } catch (e) {
      console.error('Error parsing reportData from sessionStorage:', e);
      sessionStorage.removeItem('reportData');
    }
    return [];
  });
  const [erroresCaptura, setErroresCaptura] = useState([]); // Errores de captura de inventario (MPRO)
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState(() => {
    // Recuperar filtros desde sessionStorage
    try {
      const saved = sessionStorage.getItem('reportFilters');
      if (saved) {
        const parsed = JSON.parse(saved);
        // Validar que tenga la estructura correcta
        if (parsed && typeof parsed === 'object' && parsed.server_id !== undefined) {
          return parsed;
        }
      }
    } catch (e) {
      console.error('Error parsing reportFilters from sessionStorage:', e);
      sessionStorage.removeItem('reportFilters');
    }
    return {
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
    };
  });

  const [selectedServer, setSelectedServer] = useState(null);
  
  // Estado para el modal de detalle
  const [detailModal, setDetailModal] = useState({
    open: false,
    type: '', // 'movimientos' o 'ventas'
    producto: null,
    data: [],
    loading: false
  });

  // Estados para filtros de categoría/familia/subfamilia
  const [filterOptions, setFilterOptions] = useState({
    categorias: [],
    familias: [],
    subfamilias: []
  });
  const [selectedCategorias, setSelectedCategorias] = useState(() => {
    const saved = sessionStorage.getItem('selectedCategorias');
    return saved ? JSON.parse(saved) : [];
  });
  const [selectedFamilias, setSelectedFamilias] = useState(() => {
    const saved = sessionStorage.getItem('selectedFamilias');
    return saved ? JSON.parse(saved) : [];
  });
  const [selectedSubfamilias, setSelectedSubfamilias] = useState(() => {
    const saved = sessionStorage.getItem('selectedSubfamilias');
    return saved ? JSON.parse(saved) : [];
  });
  const [loadingFilters, setLoadingFilters] = useState(false);
  
  // Estados para búsqueda en filtros
  const [searchCategorias, setSearchCategorias] = useState('');
  const [searchFamilias, setSearchFamilias] = useState('');
  const [searchSubfamilias, setSearchSubfamilias] = useState('');
  
  // Estados para selección múltiple de almacenes e inventarios
  const [selectedAlmacenes, setSelectedAlmacenes] = useState([]);
  const [selectedInventariosIni, setSelectedInventariosIni] = useState([]);
  const [selectedInventariosFin, setSelectedInventariosFin] = useState([]);

  // Guardar estado en sessionStorage cuando cambie
  useEffect(() => {
    sessionStorage.setItem('reportFilters', JSON.stringify(filters));
  }, [filters]);

  useEffect(() => {
    sessionStorage.setItem('reportData', JSON.stringify(reportData));
  }, [reportData]);

  useEffect(() => {
    sessionStorage.setItem('selectedCategorias', JSON.stringify(selectedCategorias));
  }, [selectedCategorias]);

  useEffect(() => {
    sessionStorage.setItem('selectedFamilias', JSON.stringify(selectedFamilias));
  }, [selectedFamilias]);

  useEffect(() => {
    sessionStorage.setItem('selectedSubfamilias', JSON.stringify(selectedSubfamilias));
  }, [selectedSubfamilias]);

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
      
      // Si es SoftRestaurant, cargar almacenes directamente (no tiene sucursales)
      if (server?.system_type === 'SoftRestaurant') {
        loadAlmacenesSoftRestaurant();
      }
    }
  }, [filters.server_id, servers]);

  // Cargar almacenes para SoftRestaurant (no requiere sucursal)
  const loadAlmacenesSoftRestaurant = async () => {
    try {
      const response = await api.get(`/servers/${filters.server_id}/almacenes-softrestaurant`);
      setAlmacenes(response.data);
      // Establecer una sucursal "ficticia" para que el flujo continúe
      setFilters(prev => ({
        ...prev,
        sucursal_id: 'default',
        sucursal: 'SoftRestaurant'
      }));
    } catch (error) {
      console.error('Error al cargar almacenes SoftRestaurant:', error);
      setAlmacenes([]);
    }
  };

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
      // Solo cargar almacenes si NO es SoftRestaurant (que ya los carga directamente)
      if (selectedServer?.system_type !== 'SoftRestaurant') {
        loadAlmacenes();
      }
    }
  }, [filters.server_id, filters.sucursal_id, selectedServer]);

  useEffect(() => {
    // Cargar inventarios cuando hay almacén(es) seleccionado(s)
    const loadAllInventarios = async () => {
      if (selectedAlmacenes.length === 0) {
        setInventarios([]);
        return;
      }
      
      try {
        let allInventarios = [];
        for (const almacen of selectedAlmacenes) {
          const response = await api.get(`/compras/inventarios-fisicos/${filters.server_id}`, {
            params: { 
              almacen_id: almacen.id,
              sucursal_id: filters.sucursal_id || ''
            }
          });
          // Agregar el nombre del almacén a cada inventario
          const inventariosConAlmacen = (response.data.inventarios || []).map(inv => ({
            ...inv,
            almacen: almacen.nombre,
            almacen_id: almacen.id
          }));
          allInventarios = [...allInventarios, ...inventariosConAlmacen];
        }
        setInventarios(allInventarios);
      } catch (error) {
        console.error('Error cargando inventarios:', error);
        setInventarios([]);
      }
    };
    
    if (filters.server_id && selectedAlmacenes.length > 0) {
      if (selectedServer?.system_type === 'SoftRestaurant' || filters.sucursal_id) {
        loadAllInventarios();
      }
    }
  }, [filters.server_id, filters.sucursal_id, selectedAlmacenes, selectedServer]);

  // AUTO-CALCULAR fechas cuando ambos inventarios estén seleccionados
  useEffect(() => {
    if (filters.inventario_inicial && filters.inventario_final && selectedServer && inventarios.length > 0) {
      const invInicial = inventarios.find(inv => String(inv.folio) === String(filters.inventario_inicial));
      const invFinal = inventarios.find(inv => String(inv.folio) === String(filters.inventario_final));
      
      if (invInicial?.fecha && invFinal?.fecha) {
        const dates = calculateDates(invInicial.fecha, invFinal.fecha, selectedServer.system_type);
        
        // Solo actualizar si las fechas son diferentes
        if (dates.fecha_ini !== filters.fecha_ini || dates.fecha_fin !== filters.fecha_fin) {
          console.log('Auto-calculando fechas:', dates);
          setFilters(prev => ({
            ...prev,
            inventario_inicial_fecha: invInicial.fecha,
            inventario_final_fecha: invFinal.fecha,
            fecha_ini: dates.fecha_ini,
            fecha_fin: dates.fecha_fin
          }));
        }
      }
    }
  }, [filters.inventario_inicial, filters.inventario_final, inventarios, selectedServer]);

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
        // Log para debugging
        console.log('Filtros a enviar:', {
          categorias: selectedCategorias,
          familias: selectedFamilias,
          subfamilias: selectedSubfamilias
        });
        
        // Llamar al endpoint de análisis completo con filtros adicionales
        response = await api.post('/reports/inventory-analysis', {
          server_id: filters.server_id,
          sucursal: filters.sucursal,
          almacen: filters.almacen,
          fecha_ini: filters.fecha_ini,
          fecha_fin: filters.fecha_fin,
          folio_inicial: filters.inventario_inicial,
          folio_final: filters.inventario_final,
          // Filtros adicionales
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
      
      console.log('Respuesta del reporte:', response.data);
      console.log('Primer producto:', response.data.data[0]);
      setReportData(response.data.data);
      
      // Manejar errores de captura de inventario (MPRO)
      if (response.data.errores_captura && response.data.errores_captura.length > 0) {
        setErroresCaptura(response.data.errores_captura);
        toast.warning(`Atención: ${response.data.errores_captura.length} error(es) de captura detectados`);
      } else {
        setErroresCaptura([]);
      }
      
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

  // Función auxiliar para parsear fechas SIN conversión de zona horaria
  // Siempre interpreta la fecha como hora local
  const parseDateString = (dateStr) => {
    if (!dateStr) return null;
    
    const str = String(dateStr).trim();
    
    // Parsing manual para evitar problemas de zona horaria
    // Formato esperado: "YYYY-MM-DD HH:MM:SS" o "YYYY-MM-DDTHH:MM:SS"
    const match = str.match(/(\d{4})-(\d{1,2})-(\d{1,2})[\sT](\d{1,2}):(\d{1,2}):(\d{1,2})/);
    
    if (match) {
      const [, year, month, day, hour, min, sec] = match;
      // Crear fecha usando componentes locales (NO UTC)
      return new Date(
        parseInt(year), 
        parseInt(month) - 1,  // Mes es 0-indexado
        parseInt(day), 
        parseInt(hour), 
        parseInt(min), 
        parseInt(sec)
      );
    }
    
    // Si no tiene hora, asumir 00:00:00
    const dateOnlyMatch = str.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (dateOnlyMatch) {
      const [, year, month, day] = dateOnlyMatch;
      return new Date(parseInt(year), parseInt(month) - 1, parseInt(day), 0, 0, 0);
    }
    
    return null;
  };

  // Función para formatear fecha como "YYYY-MM-DD HH:MM:SS" (hora local)
  const formatDateForSQL = (date) => {
    if (!date) return '';
    const pad = (n) => String(n).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
  };

  const calculateDates = (inicialFecha, finalFecha, systemType) => {
    if (!inicialFecha || !finalFecha) return { fecha_ini: '', fecha_fin: '' };

    let fecha_ini, fecha_fin;

    if (systemType === 'MPRO') {
      // Para MPRO: usar las fechas exactas de los inventarios (solo fecha)
      fecha_ini = String(inicialFecha).split(/[T\s]/)[0]; // Solo fecha, sin hora
      fecha_fin = String(finalFecha).split(/[T\s]/)[0];
    } else if (systemType === 'SoftRestaurant') {
      // Para SoftRestaurant: fecha inicial + 1 segundo, fecha final - 1 segundo
      const fechaInicialDate = parseDateString(inicialFecha);
      const fechaFinalDate = parseDateString(finalFecha);
      
      console.log('Fechas parseadas (hora local):', {
        original_ini: inicialFecha,
        original_fin: finalFecha,
        parsed_ini: fechaInicialDate?.toString(),
        parsed_fin: fechaFinalDate?.toString()
      });
      
      if (!fechaInicialDate || !fechaFinalDate) {
        console.error('Error parseando fechas:', { inicialFecha, finalFecha });
        // Fallback: usar las fechas tal cual + ajuste manual
        fecha_ini = String(inicialFecha).replace(/(\d{2}:\d{2}:)(\d{2})/, (m, p1, p2) => p1 + String(parseInt(p2) + 1).padStart(2, '0'));
        fecha_fin = String(finalFecha).replace(/(\d{2}:\d{2}:)(\d{2})/, (m, p1, p2) => p1 + String(parseInt(p2) - 1).padStart(2, '0'));
      } else {
        // Sumar/restar 1 segundo
        fechaInicialDate.setSeconds(fechaInicialDate.getSeconds() + 1);
        fechaFinalDate.setSeconds(fechaFinalDate.getSeconds() - 1);
        
        fecha_ini = formatDateForSQL(fechaInicialDate);
        fecha_fin = formatDateForSQL(fechaFinalDate);
      }
    } else {
      // Default: usar las fechas exactas (solo fecha)
      fecha_ini = String(inicialFecha).split(/[T\s]/)[0];
      fecha_fin = String(finalFecha).split(/[T\s]/)[0];
    }

    console.log('Fechas calculadas FINAL:', { inicialFecha, finalFecha, fecha_ini, fecha_fin, systemType });
    return { fecha_ini, fecha_fin };
  };

  const handleInventarioInicialChange = (value) => {
    const inventario = inventarios.find(inv => inv.folio === value);
    const nuevaFechaInicial = inventario?.fecha || '';
    
    console.log('Inventario inicial seleccionado:', { value, fecha: nuevaFechaInicial, inventario });
    
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
    const nuevaFechaFinal = inventario?.fecha || '';
    
    console.log('Inventario final seleccionado:', { value, fecha: nuevaFechaFinal, inventario });
    
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

  const handleExportExcel = async () => {
    console.log('handleExportExcel llamado, reportData:', reportData.length);
    if (reportData.length === 0) {
      toast.error('No hay datos para exportar');
      return;
    }

    try {
      toast.info('Generando archivo Excel...');
      
      // Obtener nombre del servidor seleccionado
      const selectedServer = servers.find(s => s.id === filters.server_id);
      const serverName = selectedServer ? selectedServer.name : 'N/A';
      
      // Llamar al backend para generar el Excel con formato profesional
      const response = await api.post('/reports/export/excel', {
        data: reportData,
        filename: `reporte_inventario_${new Date().toISOString().split('T')[0]}.xlsx`,
        servidor_nombre: serverName,
        sucursal: filters.sucursal || 'N/A',
        almacen: filters.almacen || 'N/A',
        fecha_inicio: filters.fecha_ini || filters.inventario_inicial_fecha || 'N/A',
        fecha_fin: filters.fecha_fin || filters.inventario_final_fecha || 'N/A'
      }, {
        responseType: 'blob'
      });
      
      // Descargar el archivo
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const fileName = `reporte_inventario_${new Date().toISOString().split('T')[0]}.xlsx`;
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success(`Archivo "${fileName}" descargado correctamente.`);
    } catch (error) {
      console.error('Error al exportar Excel:', error);
      toast.error('Error al exportar a Excel: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleExportPDF = () => {
    console.log('handleExportPDF llamado, reportData:', reportData.length);
    if (reportData.length === 0) {
      toast.error('No hay datos para exportar');
      return;
    }

    try {
      console.log('Creando documento PDF...');
      const doc = new jsPDF('landscape');
      
      doc.setFontSize(18);
      doc.text('Reporte de Inventario', 14, 20);
      
      doc.setFontSize(10);
      doc.text(`Fecha: ${new Date().toLocaleDateString()}`, 14, 28);
      doc.text(`Sucursal: ${filters.sucursal || 'N/A'}`, 14, 34);
      doc.text(`Almacén: ${filters.almacen || 'N/A'}`, 14, 40);
      doc.text(`Período: ${filters.fecha_ini || 'N/A'} a ${filters.fecha_fin || 'N/A'}`, 14, 46);
      
      // Columnas más relevantes para el PDF
      const columns = ['Codigo', 'Producto', 'Inv_Inicial_Cantidad', 'Movimientos', 'Ventas', 'Inv_Teorico_Cantidad', 'Inv_Final_Cantidad', 'Diferencia_Cantidad'];
      const headers = ['Código', 'Producto', 'Inv. Inicial', 'Movimientos', 'Ventas', 'Inv. Teórico', 'Inv. Final', 'Diferencia'];
      
      console.log('Preparando datos para tabla...');
      const data = reportData.map(row => columns.map(col => {
        const val = row[col];
        if (typeof val === 'number') return val.toLocaleString('es-MX', { maximumFractionDigits: 2 });
        return val || '';
      }));
      
      console.log('Generando tabla autoTable...');
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
      console.log('Guardando PDF:', fileName);
      
      // Método alternativo: crear blob y descargar
      const pdfBlob = doc.output('blob');
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success(`Archivo "${fileName}" descargado correctamente.`);
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

  // Función para cargar el detalle de movimientos
  const loadMovementDetails = async (producto) => {
    setDetailModal({
      open: true,
      type: 'movimientos',
      producto: producto,
      data: [],
      loading: true
    });

    try {
      const response = await api.post('/reports/movement-details', {
        server_id: filters.server_id,
        producto_codigo: producto.Codigo,
        sucursal: filters.sucursal,
        almacen: filters.almacen,
        fecha_ini: filters.fecha_ini,
        fecha_fin: filters.fecha_fin
      });
      
      setDetailModal(prev => ({
        ...prev,
        data: response.data.data,
        loading: false
      }));
    } catch (error) {
      console.error('Error al cargar detalle de movimientos:', error);
      toast.error('Error al cargar detalle de movimientos');
      setDetailModal(prev => ({ ...prev, loading: false }));
    }
  };

  // Función para cargar el detalle de ventas
  const loadSalesDetails = async (producto) => {
    console.log('loadSalesDetails llamado con producto:', producto);
    setDetailModal({
      open: true,
      type: 'ventas',
      producto: producto,
      data: [],
      loading: true
    });

    try {
      console.log('Enviando request a /reports/sales-details con:', {
        server_id: filters.server_id,
        producto_codigo: producto.Codigo,
        sucursal: filters.sucursal,
        almacen: filters.almacen,
        fecha_ini: filters.fecha_ini,
        fecha_fin: filters.fecha_fin
      });
      const response = await api.post('/reports/sales-details', {
        server_id: filters.server_id,
        producto_codigo: producto.Codigo,
        sucursal: filters.sucursal,
        almacen: filters.almacen,
        fecha_ini: filters.fecha_ini,
        fecha_fin: filters.fecha_fin
      });
      
      console.log('Respuesta de sales-details:', response.data);
      setDetailModal(prev => ({
        ...prev,
        data: response.data.data,
        loading: false
      }));
    } catch (error) {
      console.error('Error al cargar detalle de ventas:', error);
      toast.error('Error al cargar detalle de ventas');
      setDetailModal(prev => ({ ...prev, loading: false }));
    }
  };

  // Cerrar modal
  const closeDetailModal = () => {
    setDetailModal({
      open: false,
      type: '',
      producto: null,
      data: [],
      loading: false
    });
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
              <select 
                className={selectStyle}
                data-testid="server-select"
                value={filters.server_id}
                onChange={(e) => setFilters({...filters, server_id: e.target.value, sucursal_id: '', almacen_id: '', sucursal: '', almacen: ''})}
              >
                <option value="">{servers.length === 0 ? "Cargando servidores..." : "Selecciona un servidor"}</option>
                {servers.map((server) => (
                  <option key={server.id} value={server.id}>
                    {server.name} ({server.system_type})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label>Tipo de Consulta</Label>
              <select 
                className={selectStyle}
                data-testid="query-type-select"
                value={filters.query_type}
                onChange={(e) => setFilters({...filters, query_type: e.target.value})}
              >
                <option value="analisis">Análisis Completo de Inventario</option>
                <option value="ventas">Ventas</option>
                <option value="movimientos">Movimientos</option>
                <option value="productos">Productos</option>
                <option value="inventarios">Inventarios Físicos</option>
              </select>
            </div>

            {/* Sucursal - Solo mostrar si NO es SoftRestaurant */}
            {selectedServer?.system_type !== 'SoftRestaurant' && (
              <div className="space-y-2">
                <Label>Sucursal</Label>
                <select 
                  className={selectStyle}
                  data-testid="sucursal-select"
                  value={filters.sucursal_id}
                  onChange={(e) => handleSucursalChange(e.target.value)}
                  disabled={!filters.server_id || sucursales.length === 0}
                >
                  <option value="">{!filters.server_id ? "Selecciona servidor primero" : "Selecciona una sucursal"}</option>
                  {sucursales.map((sucursal) => (
                    <option key={sucursal.id} value={sucursal.id}>
                      {sucursal.nombre}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="space-y-2">
              <Label>Almacén(es)</Label>
              <details className="relative">
                <summary 
                  className={`${selectStyle} cursor-pointer list-none flex items-center justify-between`}
                  data-testid="almacen-multiselect"
                >
                  <span className="truncate">
                    {selectedAlmacenes.length === 0 
                      ? (selectedServer?.system_type === 'SoftRestaurant'
                          ? (!filters.server_id ? "Selecciona servidor primero" : (almacenes.length === 0 ? "Cargando..." : "Selecciona almacén(es)"))
                          : (!filters.sucursal_id ? "Selecciona sucursal primero" : "Selecciona almacén(es)"))
                      : `${selectedAlmacenes.length} seleccionado(s)`}
                  </span>
                  <ChevronDown className="h-4 w-4 opacity-50" />
                </summary>
                <div className="absolute z-50 w-full mt-1 bg-white border border-zinc-300 rounded-md shadow-lg max-h-72 overflow-hidden">
                  <div className="max-h-60 overflow-y-auto">
                    {selectedAlmacenes.length > 0 && (
                      <button
                        type="button"
                        className="w-full px-3 py-2 text-xs text-left hover:bg-zinc-100 border-b flex items-center"
                        onClick={() => {
                          setSelectedAlmacenes([]);
                          setSelectedInventariosIni([]);
                          setSelectedInventariosFin([]);
                          setFilters({...filters, almacen_id: '', almacen: '', inventario_inicial: '', inventario_final: ''});
                        }}
                      >
                        <X className="h-3 w-3 mr-1" /> Limpiar selección
                      </button>
                    )}
                    {almacenes.map((almacen) => (
                      <label key={almacen.id} className="flex items-center space-x-2 py-2 px-3 hover:bg-zinc-50 cursor-pointer">
                        <input
                          type="checkbox"
                          className="rounded border-zinc-300"
                          checked={selectedAlmacenes.some(a => a.id === almacen.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              const newSelected = [...selectedAlmacenes, almacen];
                              setSelectedAlmacenes(newSelected);
                              // Si es el primero, actualizar filters para compatibilidad
                              if (newSelected.length === 1) {
                                setFilters({...filters, almacen_id: almacen.id, almacen: almacen.nombre});
                              }
                            } else {
                              const newSelected = selectedAlmacenes.filter(a => a.id !== almacen.id);
                              setSelectedAlmacenes(newSelected);
                              // Limpiar inventarios si se deselecciona un almacén
                              setSelectedInventariosIni([]);
                              setSelectedInventariosFin([]);
                              if (newSelected.length === 1) {
                                setFilters({...filters, almacen_id: newSelected[0].id, almacen: newSelected[0].nombre});
                              } else if (newSelected.length === 0) {
                                setFilters({...filters, almacen_id: '', almacen: '', inventario_inicial: '', inventario_final: ''});
                              }
                            }
                          }}
                        />
                        <span className="text-sm">{almacen.nombre} {almacen.tipo === 1 ? '(Consumo)' : almacen.tipo === 2 ? '(Presentaciones)' : ''}</span>
                      </label>
                    ))}
                    {almacenes.length === 0 && (
                      <p className="text-xs text-zinc-400 text-center py-2">No hay almacenes disponibles</p>
                    )}
                  </div>
                </div>
              </details>
            </div>

            <div className="space-y-2">
              <Label>Inventario Inicial {selectedAlmacenes.length > 1 ? '(múltiple)' : ''}</Label>
              {selectedAlmacenes.length <= 1 ? (
                <select 
                  className={selectStyle}
                  data-testid="inventario-inicial-select"
                  value={filters.inventario_inicial}
                  onChange={(e) => handleInventarioInicialChange(e.target.value)}
                  disabled={selectedAlmacenes.length === 0 || inventarios.length === 0}
                >
                  <option value="">{selectedAlmacenes.length === 0 ? "Selecciona almacén primero" : "Selecciona inventario inicial"}</option>
                  {inventarios.map((inv) => (
                    <option key={inv.folio} value={inv.folio}>
                      {inv.folio} - {inv.fecha ? inv.fecha.split(' ')[0] : 'Sin fecha'} - {inv.comentario || inv.almacen || ''}
                    </option>
                  ))}
                </select>
              ) : (
                <details className="relative">
                  <summary className={`${selectStyle} cursor-pointer list-none flex items-center justify-between`}>
                    <span className="truncate">
                      {selectedInventariosIni.length === 0 
                        ? "Selecciona inventarios iniciales" 
                        : `${selectedInventariosIni.length} seleccionado(s)`}
                    </span>
                    <ChevronDown className="h-4 w-4 opacity-50" />
                  </summary>
                  <div className="absolute z-50 w-full mt-1 bg-white border border-zinc-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                    {selectedInventariosIni.length > 0 && (
                      <button
                        type="button"
                        className="w-full px-3 py-2 text-xs text-left hover:bg-zinc-100 border-b flex items-center"
                        onClick={() => setSelectedInventariosIni([])}
                      >
                        <X className="h-3 w-3 mr-1" /> Limpiar selección
                      </button>
                    )}
                    {inventarios.map((inv) => (
                      <label key={inv.folio} className="flex items-center space-x-2 py-2 px-3 hover:bg-zinc-50 cursor-pointer">
                        <input
                          type="checkbox"
                          className="rounded border-zinc-300"
                          checked={selectedInventariosIni.some(i => i.folio === inv.folio)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedInventariosIni([...selectedInventariosIni, inv]);
                            } else {
                              setSelectedInventariosIni(selectedInventariosIni.filter(i => i.folio !== inv.folio));
                            }
                          }}
                        />
                        <span className="text-sm">{inv.folio} - {inv.fecha ? inv.fecha.split(' ')[0] : ''} - {inv.almacen || ''}</span>
                      </label>
                    ))}
                  </div>
                </details>
              )}
            </div>

            <div className="space-y-2">
              <Label>Inventario Final {selectedAlmacenes.length > 1 ? '(múltiple)' : ''}</Label>
              {selectedAlmacenes.length <= 1 ? (
                <select 
                  className={selectStyle}
                  data-testid="inventario-final-select"
                  value={filters.inventario_final}
                  onChange={(e) => handleInventarioFinalChange(e.target.value)}
                  disabled={selectedAlmacenes.length === 0 || inventarios.length === 0}
                >
                  <option value="">{selectedAlmacenes.length === 0 ? "Selecciona almacén primero" : "Selecciona inventario final"}</option>
                  {inventarios.map((inv) => (
                    <option key={inv.folio} value={inv.folio}>
                      {inv.folio} - {inv.fecha ? inv.fecha.split(' ')[0] : 'Sin fecha'} - {inv.comentario || inv.almacen || ''}
                    </option>
                  ))}
                </select>
              ) : (
                <details className="relative">
                  <summary className={`${selectStyle} cursor-pointer list-none flex items-center justify-between`}>
                    <span className="truncate">
                      {selectedInventariosFin.length === 0 
                        ? "Selecciona inventarios finales" 
                        : `${selectedInventariosFin.length} seleccionado(s)`}
                    </span>
                    <ChevronDown className="h-4 w-4 opacity-50" />
                  </summary>
                  <div className="absolute z-50 w-full mt-1 bg-white border border-zinc-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                    {selectedInventariosFin.length > 0 && (
                      <button
                        type="button"
                        className="w-full px-3 py-2 text-xs text-left hover:bg-zinc-100 border-b flex items-center"
                        onClick={() => setSelectedInventariosFin([])}
                      >
                        <X className="h-3 w-3 mr-1" /> Limpiar selección
                      </button>
                    )}
                    {inventarios.map((inv) => (
                      <label key={inv.folio} className="flex items-center space-x-2 py-2 px-3 hover:bg-zinc-50 cursor-pointer">
                        <input
                          type="checkbox"
                          className="rounded border-zinc-300"
                          checked={selectedInventariosFin.some(i => i.folio === inv.folio)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedInventariosFin([...selectedInventariosFin, inv]);
                            } else {
                              setSelectedInventariosFin(selectedInventariosFin.filter(i => i.folio !== inv.folio));
                            }
                          }}
                        />
                        <span className="text-sm">{inv.folio} - {inv.fecha ? inv.fecha.split(' ')[0] : ''} - {inv.almacen || ''}</span>
                      </label>
                    ))}
                  </div>
                </details>
              )}
            </div>

            <div className="space-y-2">
              <Label>
                Fecha Inicio de Movimientos
                {selectedServer && (
                  <span className="text-xs text-zinc-500 ml-2">
                    ({selectedServer.system_type === 'MPRO' ? 'Fecha inv. inicial' : 'Fecha inv. inicial + 1 seg'})
                  </span>
                )}
              </Label>
              <Input
                type="text"
                value={filters.fecha_ini}
                onChange={(e) => setFilters({...filters, fecha_ini: e.target.value})}
                className={filters.fecha_ini ? "bg-white" : "bg-zinc-50"}
                placeholder="Auto-calculado o ingrese: YYYY-MM-DD HH:MM:SS"
                data-testid="fecha-inicio-input"
              />
            </div>

            <div className="space-y-2">
              <Label>
                Fecha Fin de Movimientos
                {selectedServer && (
                  <span className="text-xs text-zinc-500 ml-2">
                    ({selectedServer.system_type === 'MPRO' ? 'Fecha inv. final' : 'Fecha inv. final - 1 seg'})
                  </span>
                )}
              </Label>
              <Input
                type="text"
                value={filters.fecha_fin}
                onChange={(e) => setFilters({...filters, fecha_fin: e.target.value})}
                className={filters.fecha_fin ? "bg-white" : "bg-zinc-50"}
                placeholder="Auto-calculado o ingrese: YYYY-MM-DD HH:MM:SS"
                data-testid="fecha-fin-input"
              />
            </div>
          </div>

          {/* Filtros adicionales (Categoría, Familia, SubFamilia) - Para MPRO y SoftRestaurant */}
          {filters.query_type === 'analisis' && (selectedServer?.system_type === 'MPRO' || selectedServer?.system_type === 'SoftRestaurant') && (
            <div className="mt-6 pt-4 border-t border-zinc-200">
              <div className="flex items-center gap-2 mb-4">
                <Filter className="h-4 w-4 text-zinc-500" />
                <h3 className="text-sm font-semibold text-zinc-700">Filtros Adicionales (Opcional)</h3>
                {loadingFilters && <span className="text-xs text-zinc-400">Cargando...</span>}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Multiselect Categorías - Con búsqueda */}
                <div className="space-y-2">
                  <Label>{selectedServer?.system_type === 'SoftRestaurant' ? 'Clasificación' : 'Categorías'}</Label>
                  <details className="relative">
                    <summary 
                      className={`${selectStyle} cursor-pointer list-none flex items-center justify-between`}
                      data-testid="categorias-multiselect"
                    >
                      <span className="truncate">
                        {selectedCategorias.length === 0 
                          ? 'Todas las categorías' 
                          : `${selectedCategorias.length} seleccionada(s)`}
                      </span>
                      <ChevronDown className="h-4 w-4 opacity-50" />
                    </summary>
                    <div className="absolute z-50 w-full mt-1 bg-white border border-zinc-300 rounded-md shadow-lg max-h-72 overflow-hidden">
                      {/* Campo de búsqueda */}
                      <div className="sticky top-0 bg-white border-b p-2">
                        <input
                          type="text"
                          placeholder="Buscar..."
                          value={searchCategorias}
                          onChange={(e) => setSearchCategorias(e.target.value)}
                          className="w-full px-2 py-1 text-sm border border-zinc-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                          onClick={(e) => e.stopPropagation()}
                        />
                      </div>
                      <div className="max-h-52 overflow-y-auto">
                        {selectedCategorias.length > 0 && (
                          <button
                            type="button"
                            className="w-full px-3 py-2 text-xs text-left hover:bg-zinc-100 border-b flex items-center"
                            onClick={() => setSelectedCategorias([])}
                          >
                            <X className="h-3 w-3 mr-1" /> Limpiar selección
                          </button>
                        )}
                        {filterOptions.categorias
                          .filter(cat => cat.nombre.toLowerCase().includes(searchCategorias.toLowerCase()))
                          .map((cat) => (
                          <label key={cat.id} className="flex items-center space-x-2 py-2 px-3 hover:bg-zinc-50 cursor-pointer">
                            <input
                              type="checkbox"
                              className="rounded border-zinc-300"
                              checked={selectedCategorias.includes(cat.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedCategorias([...selectedCategorias, cat.id]);
                                } else {
                                  setSelectedCategorias(selectedCategorias.filter(c => c !== cat.id));
                                }
                              }}
                            />
                            <span className="text-sm">{cat.nombre}</span>
                          </label>
                        ))}
                        {filterOptions.categorias.filter(cat => cat.nombre.toLowerCase().includes(searchCategorias.toLowerCase())).length === 0 && (
                          <p className="text-xs text-zinc-400 text-center py-2">No hay coincidencias</p>
                        )}
                      </div>
                    </div>
                  </details>
                </div>

                {/* Multiselect Familias - Con búsqueda */}
                <div className="space-y-2">
                  <Label>{selectedServer?.system_type === 'SoftRestaurant' ? 'Grupos' : 'Familias'}</Label>
                  <details className="relative">
                    <summary 
                      className={`${selectStyle} cursor-pointer list-none flex items-center justify-between`}
                      data-testid="familias-multiselect"
                    >
                      <span className="truncate">
                        {selectedFamilias.length === 0 
                          ? 'Todas las familias' 
                          : `${selectedFamilias.length} seleccionada(s)`}
                      </span>
                      <ChevronDown className="h-4 w-4 opacity-50" />
                    </summary>
                    <div className="absolute z-50 w-full mt-1 bg-white border border-zinc-300 rounded-md shadow-lg max-h-72 overflow-hidden">
                      {/* Campo de búsqueda */}
                      <div className="sticky top-0 bg-white border-b p-2">
                        <input
                          type="text"
                          placeholder="Buscar..."
                          value={searchFamilias}
                          onChange={(e) => setSearchFamilias(e.target.value)}
                          className="w-full px-2 py-1 text-sm border border-zinc-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                          onClick={(e) => e.stopPropagation()}
                        />
                      </div>
                      <div className="max-h-52 overflow-y-auto">
                        {selectedFamilias.length > 0 && (
                          <button
                            type="button"
                            className="w-full px-3 py-2 text-xs text-left hover:bg-zinc-100 border-b flex items-center"
                            onClick={() => setSelectedFamilias([])}
                          >
                            <X className="h-3 w-3 mr-1" /> Limpiar selección
                          </button>
                        )}
                        {filterOptions.familias
                          .filter(fam => fam.nombre.toLowerCase().includes(searchFamilias.toLowerCase()))
                          .map((fam) => (
                          <label key={fam.id} className="flex items-center space-x-2 py-2 px-3 hover:bg-zinc-50 cursor-pointer">
                            <input
                              type="checkbox"
                              className="rounded border-zinc-300"
                              checked={selectedFamilias.includes(fam.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedFamilias([...selectedFamilias, fam.id]);
                                } else {
                                  setSelectedFamilias(selectedFamilias.filter(f => f !== fam.id));
                                }
                              }}
                            />
                            <span className="text-sm">{fam.nombre}</span>
                          </label>
                        ))}
                        {filterOptions.familias.filter(fam => fam.nombre.toLowerCase().includes(searchFamilias.toLowerCase())).length === 0 && (
                          <p className="text-xs text-zinc-400 text-center py-2">No hay coincidencias</p>
                        )}
                      </div>
                    </div>
                  </details>
                </div>

                {/* Multiselect SubFamilias - Con búsqueda */}
                <div className="space-y-2">
                  <Label>{selectedServer?.system_type === 'SoftRestaurant' ? 'SubGrupos' : 'SubFamilias'}</Label>
                  <details className="relative">
                    <summary 
                      className={`${selectStyle} cursor-pointer list-none flex items-center justify-between`}
                      data-testid="subfamilias-multiselect"
                    >
                      <span className="truncate">
                        {selectedSubfamilias.length === 0 
                          ? 'Todas las subfamilias' 
                          : `${selectedSubfamilias.length} seleccionada(s)`}
                      </span>
                      <ChevronDown className="h-4 w-4 opacity-50" />
                    </summary>
                    <div className="absolute z-50 w-full mt-1 bg-white border border-zinc-300 rounded-md shadow-lg max-h-72 overflow-hidden">
                      {/* Campo de búsqueda */}
                      <div className="sticky top-0 bg-white border-b p-2">
                        <input
                          type="text"
                          placeholder="Buscar..."
                          value={searchSubfamilias}
                          onChange={(e) => setSearchSubfamilias(e.target.value)}
                          className="w-full px-2 py-1 text-sm border border-zinc-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                          onClick={(e) => e.stopPropagation()}
                        />
                      </div>
                      <div className="max-h-52 overflow-y-auto">
                        {selectedSubfamilias.length > 0 && (
                          <button
                            type="button"
                            className="w-full px-3 py-2 text-xs text-left hover:bg-zinc-100 border-b flex items-center"
                            onClick={() => setSelectedSubfamilias([])}
                          >
                            <X className="h-3 w-3 mr-1" /> Limpiar selección
                          </button>
                        )}
                        {filterOptions.subfamilias
                          .filter(sf => sf.nombre.toLowerCase().includes(searchSubfamilias.toLowerCase()))
                          .map((sf) => (
                          <label key={sf.id} className="flex items-center space-x-2 py-2 px-3 hover:bg-zinc-50 cursor-pointer">
                            <input
                              type="checkbox"
                              className="rounded border-zinc-300"
                              checked={selectedSubfamilias.includes(sf.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedSubfamilias([...selectedSubfamilias, sf.id]);
                                } else {
                                  setSelectedSubfamilias(selectedSubfamilias.filter(s => s !== sf.id));
                                }
                              }}
                            />
                            <span className="text-sm">{sf.nombre}</span>
                          </label>
                        ))}
                        {filterOptions.subfamilias.filter(sf => sf.nombre.toLowerCase().includes(searchSubfamilias.toLowerCase())).length === 0 && (
                          <p className="text-xs text-zinc-400 text-center py-2">No hay coincidencias</p>
                        )}
                      </div>
                    </div>
                  </details>
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
            {/* Errores de captura de inventario (MPRO) */}
            {erroresCaptura.length > 0 && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="h-5 w-5 text-red-600" />
                  <span className="font-semibold text-red-800">
                    ⚠️ Errores de Captura de Inventario Detectados ({erroresCaptura.length})
                  </span>
                </div>
                <p className="text-sm text-red-700 mb-2">
                  Los siguientes productos fueron capturados incorrectamente en el inventario físico:
                </p>
                <ul className="text-sm text-red-700 space-y-1 ml-4">
                  {erroresCaptura.map((error, idx) => (
                    <li key={idx} className="list-disc">
                      {error.mensaje}
                    </li>
                  ))}
                </ul>
                <p className="text-xs text-red-600 mt-2 italic">
                  Nota: No se debe capturar una presentación si el insumo ya existe. Revise los datos del inventario.
                </p>
              </div>
            )}
            <p className="text-xs text-zinc-500 mb-2 italic">
              💡 Doble clic en las columnas Movimientos o Ventas para ver el detalle
            </p>
            <div className="rounded-md border border-zinc-200 max-h-[600px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 z-10 bg-zinc-200">
                  <tr className="border-b-2 border-zinc-400">
                    {Object.keys(reportData[0]).map((key) => (
                      <th key={key} className="text-xs uppercase tracking-wider font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-left">
                        {key.replace(/_/g, ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {reportData.slice(0, 2000).map((row, idx) => (
                    <tr key={idx} className="border-b hover:bg-zinc-50/50">
                      {Object.entries(row).map(([key, value], cellIdx) => {
                        // Special formatting for analysis report
                        const isDiferencia = key.toLowerCase().includes('diferencia');
                        const isCosto = key.toLowerCase().includes('costo');
                        const isPorcentaje = key.toLowerCase().includes('porcentaje');
                        const isMovimientos = key === 'Movimientos';
                        const isVentas = key === 'Ventas';
                        
                        let displayValue = value;
                        let className = "text-sm font-data text-zinc-700 p-2";
                        let onDoubleClick = null;
                        
                        // Columnas clickeables para ver detalle
                        if (isMovimientos && value !== null && value !== undefined && parseFloat(value) !== 0) {
                          onDoubleClick = () => loadMovementDetails(row);
                          className = "text-sm font-data text-blue-600 cursor-pointer hover:underline p-2";
                          displayValue = formatNumber(value);
                        } else if (isVentas && value !== null && value !== undefined && parseFloat(value) !== 0) {
                          onDoubleClick = () => loadSalesDetails(row);
                          className = "text-sm font-data text-blue-600 cursor-pointer hover:underline p-2";
                          displayValue = formatNumber(value);
                        } else if (isPorcentaje && value !== null && value !== undefined) {
                          displayValue = `${formatNumber(value)}%`;
                          className = `text-sm font-data font-semibold p-2 ${getDifferenceColor(parseFloat(value))}`;
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
                          <td 
                            key={cellIdx} 
                            className={className}
                            onDoubleClick={onDoubleClick}
                            title={onDoubleClick ? 'Doble clic para ver detalle' : ''}
                          >
                            {displayValue}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
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

      {/* Modal de Detalle - Simple HTML/CSS sin Radix */}
      {detailModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Overlay */}
          <div 
            className="fixed inset-0 bg-black/50"
            onClick={closeDetailModal}
          />
          
          {/* Modal Content */}
          <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h2 className="text-lg font-semibold">
                  {detailModal.type === 'movimientos' ? 'Detalle de Movimientos' : 'Detalle de Ventas'}
                </h2>
                {detailModal.producto && (
                  <p className="text-sm text-zinc-600">
                    Producto: <strong>{detailModal.producto.Codigo}</strong> - {detailModal.producto.Producto}
                  </p>
                )}
              </div>
              <button
                onClick={closeDetailModal}
                className="p-2 hover:bg-zinc-100 rounded-full"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            {/* Body */}
            <div className="p-4 overflow-y-auto max-h-[60vh]">
              {detailModal.loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
                  <span className="ml-2 text-zinc-500">Cargando detalle...</span>
                </div>
              ) : detailModal.data.length === 0 ? (
                <div className="text-center py-8 text-zinc-500">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2 text-zinc-400" />
                  <p>No se encontraron registros</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-zinc-50">
                        {detailModal.type === 'movimientos' ? (
                          <>
                            <TableHead className="text-xs uppercase font-medium">Folio</TableHead>
                            <TableHead className="text-xs uppercase font-medium">Fecha</TableHead>
                            <TableHead className="text-xs uppercase font-medium text-right">Cantidad</TableHead>
                            <TableHead className="text-xs uppercase font-medium">Tipo</TableHead>
                            <TableHead className="text-xs uppercase font-medium">Descripción</TableHead>
                            <TableHead className="text-xs uppercase font-medium">Almacén</TableHead>
                            <TableHead className="text-xs uppercase font-medium">Observaciones</TableHead>
                          </>
                        ) : (
                          <>
                            <TableHead className="text-xs uppercase font-medium">Folio</TableHead>
                            <TableHead className="text-xs uppercase font-medium">Fecha</TableHead>
                            <TableHead className="text-xs uppercase font-medium text-right">Cantidad</TableHead>
                            <TableHead className="text-xs uppercase font-medium">Tipo</TableHead>
                            <TableHead className="text-xs uppercase font-medium">Producto Vendido</TableHead>
                            <TableHead className="text-xs uppercase font-medium text-right">Precio Unit.</TableHead>
                            <TableHead className="text-xs uppercase font-medium">Sucursal</TableHead>
                          </>
                        )}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {detailModal.data.map((item, idx) => (
                        <TableRow key={idx} className="hover:bg-zinc-50/50">
                          {detailModal.type === 'movimientos' ? (
                            <>
                              <TableCell className="font-mono text-sm">{item.folio}</TableCell>
                              <TableCell className="text-sm">{item.fecha}</TableCell>
                              <TableCell className={`text-sm text-right font-semibold ${item.cantidad >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {formatNumber(item.cantidad)}
                              </TableCell>
                              <TableCell className="text-sm">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${item.tipo_movimiento === 'Entrada' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                  {item.tipo_movimiento}
                                </span>
                              </TableCell>
                              <TableCell className="text-sm">{item.tipo_descripcion}</TableCell>
                              <TableCell className="text-sm">{item.almacen}</TableCell>
                              <TableCell className="text-sm text-zinc-500 max-w-xs truncate">{item.observaciones}</TableCell>
                            </>
                          ) : (
                            <>
                              <TableCell className="font-mono text-sm">{item.folio}</TableCell>
                              <TableCell className="text-sm">{item.fecha}</TableCell>
                              <TableCell className="text-sm text-right font-semibold">{formatNumber(item.cantidad)}</TableCell>
                              <TableCell className="text-sm">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${item.tipo_venta === 'DIRECTA' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}`}>
                                  {item.tipo_venta}
                                </span>
                              </TableCell>
                              <TableCell className="text-sm">{item.producto_vendido || item.producto}</TableCell>
                              <TableCell className="text-sm text-right">{formatCurrency(item.precio_unitario)}</TableCell>
                              <TableCell className="text-sm">{item.sucursal}</TableCell>
                            </>
                          )}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>
            
            {/* Footer con totales */}
            {detailModal.data.length > 0 && (
              <div className="p-4 border-t text-sm text-zinc-500">
                <div className="flex justify-between items-center">
                  <span>Total: {detailModal.data.length} registro(s)</span>
                  {detailModal.type === 'movimientos' && (
                    <span className="font-semibold text-zinc-700">
                      Total Cantidad: <span className={detailModal.data.reduce((sum, row) => sum + (parseFloat(row.cantidad) || 0), 0) >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {detailModal.data.reduce((sum, row) => sum + (parseFloat(row.cantidad) || 0), 0).toFixed(2)}
                      </span>
                    </span>
                  )}
                  {detailModal.type === 'ventas' && (
                    <span className="font-semibold text-zinc-700">
                      Total Cantidad: {detailModal.data.reduce((sum, row) => sum + (parseFloat(row.cantidad) || 0), 0).toFixed(2)}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Reportes;