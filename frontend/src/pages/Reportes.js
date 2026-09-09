import { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import logger from '@/services/logger';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { fetchUnidadesNegocio, getServerIdFromUnidad } from '@/services/unidadesNegocioService';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FileDown, Mail, Search, AlertCircle, TrendingUp, TrendingDown, X, Loader2, ChevronDown, Filter, FileSpreadsheet, LayoutDashboard, ClipboardList, FileText, FolderOpen, Upload, Trash2, Eye, Download, CheckCircle, FileImage, File, Maximize2, Minimize2, Building2 } from 'lucide-react';
import { toast } from 'sonner';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import DashboardInventarios from './Dashboard'; // Importar el Dashboard de Inventarios
import { OperativoDashboard } from '@/components/fase2_operativo'; // Dashboard Operativo Fase 2A
import { Activity } from 'lucide-react';
import { getAlmacenTipoText } from '../utils/styleHelpers';
// Componentes/lógica CANÓNICOS compartidos con Auditoría (Compras.js) — regla de centralización
import DetalleProductoModal from '@/components/compras/DetalleProductoModal';
import { useDetalleProducto } from '@/hooks/useDetalleProducto';


const fmtCantidadReceta = (value) => {
  const n = Number(value ?? 0);
  if (!Number.isFinite(n)) return '-';
  if (n === 0) return 'Sin consumo';

  const abs = Math.abs(n);
  const maxDecimals = abs < 1 ? 6 : 4;

  return n.toLocaleString('es-MX', {
    minimumFractionDigits: 0,
    maximumFractionDigits: maxDecimals
  });
};
import {
  fechaMinimaInventarios,
  filtrarInventariosFinales,
  getInventarioKey,
  getInventarioTimestamp
} from '@/lib/inventarioSelectorUtils';

// Estilos para los selectores nativos
const selectStyle = "w-full h-10 px-3 py-2 text-sm border border-zinc-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-zinc-100 disabled:cursor-not-allowed";

const normalizeReportQueryType = (queryType) => {
  const normalized = String(queryType || '').trim();
  return normalized === 'pendientes' ? 'pendientes' : 'analisis';
};

// Helper: Texto para selector de almacén según estado
const getAlmacenPlaceholder = (selectedAlmacenes, selectedServer, selectedUnidad, almacenes, filters) => {
  if (selectedAlmacenes.length > 0) {
    return `${selectedAlmacenes.length} seleccionado(s)`;
  }
  
  if (!selectedUnidad) {
    return "Selecciona unidad primero";
  }
  
  if (selectedServer?.system_type === 'SoftRestaurant') {
    return almacenes.length === 0 ? "Cargando..." : "Selecciona almacén(es)";
  }
  
  // MPRO
  if (almacenes.length === 0 && !filters.sucursal_id) {
    return "Cargando almacenes...";
  }
  if (almacenes.length === 0) {
    return "No hay almacenes disponibles";
  }
  return "Selecciona almacén(es)";
};

const UsoRecetaModal = ({ detalle, onClose, formatNumber }) => {
  if (!detalle?.open) return null;

  const fmt = formatNumber || ((n) => Number(n || 0).toLocaleString('es-MX'));
  const usos = detalle.data?.usos || [];
  const base = detalle.data?.base;
  const presentacion = detalle.data?.presentacion;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[82vh] overflow-hidden">
        <div className="px-4 py-3 border-b flex items-center justify-between bg-zinc-50">
          <div>
            <h3 className="font-semibold">Uso en recetas</h3>
            <p className="text-sm text-zinc-500">
              {detalle.codigo} - {detalle.producto}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-zinc-200 rounded"
            aria-label="Cerrar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-4 overflow-auto max-h-[66vh]">
          {detalle.loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : detalle.error ? (
            <p className="text-red-600 text-center py-4">{detalle.error}</p>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                {presentacion && (
                  <div className="rounded border border-zinc-200 bg-zinc-50 p-3">
                    <p className="text-xs uppercase tracking-wide text-zinc-500">Presentación seleccionada</p>
                    <p className="font-semibold">{presentacion.codigo} - {presentacion.nombre}</p>
                    <p className="text-zinc-600">
                      Unidad: {presentacion.unidad || '-'} · Rendimiento: {fmt(presentacion.rendimiento || 1)}
                    </p>
                  </div>
                )}
                <div className="rounded border border-zinc-200 bg-blue-50 p-3">
                  <p className="text-xs uppercase tracking-wide text-blue-600">Insumo base consultado</p>
                  <p className="font-semibold text-blue-900">{base?.codigo || detalle.codigo} - {base?.nombre || detalle.producto}</p>
                  <p className="text-blue-700">Unidad: {base?.unidad || '-'}</p>
                </div>
              </div>

              {usos.length > 0 ? (
                <table className="w-full text-sm">
                  <thead className="bg-zinc-100">
                    <tr>
                      <th className="py-2 px-3 text-left">CODIGO</th>
                      <th className="py-2 px-3 text-left">PRODUCTO / PRODUCCION</th>
                      <th className="py-2 px-3 text-left">TIPO</th>
                      <th className="py-2 px-3 text-left">CANTIDAD RECETA</th>
                      <th className="py-2 px-3 text-left">UNIDAD</th>
                      <th className="py-2 px-3 text-left">LINEAS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usos.map((uso, idx) => (
                      <tr key={`${uso.codigo_destino}-${idx}`} className="border-b hover:bg-zinc-50">
                        <td className="py-1.5 px-3 font-mono">{uso.codigo_destino}</td>
                        <td className="py-1.5 px-3 font-medium">{uso.producto_destino}</td>
                        <td className="py-1.5 px-3">
                          <span className="rounded bg-zinc-100 px-2 py-0.5 text-xs">
                            {uso.tipo_destino}
                          </span>
                        </td>
                        <td className="py-1.5 px-3 font-mono">{fmtCantidadReceta(uso.cantidad_receta)}</td>
                        <td className="py-1.5 px-3">{uso.unidad_receta || '-'}</td>
                        <td className="py-1.5 px-3">{uso.lineas || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-center text-zinc-500 py-8">
                  No se encontraron productos de venta o producciones que usen este insumo.
                </p>
              )}
            </div>
          )}
        </div>

        <div className="px-4 py-3 border-t bg-zinc-50 flex justify-end">
          <Button variant="outline" onClick={onClose}>Cerrar</Button>
        </div>
      </div>
    </div>
  );
};

const Reportes = () => {
  // FASE AUTH-FIX: Usar AuthContext para esperar a que el usuario esté autenticado
  const { user, loading: authLoading } = useAuth();
  
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') || 'analisis';
  const [activeTab, setActiveTab] = useState(initialTab);
  
  // FASE 3.2: Unidades de Negocio reemplazan servidores como filtro visible
  const [unidadesNegocio, setUnidadesNegocio] = useState([]);
  const [selectedUnidad, setSelectedUnidad] = useState('');
  const [loadingUnidades, setLoadingUnidades] = useState(true);
  
  // servers se deriva de unidadesNegocio para compatibilidad interna
  const servers = useMemo(() => {
    return unidadesNegocio.map(u => ({
      id: String(u.server_id || '').trim(),
      name: u.nombre,
      system_type: u.system_type,
      unidad_id: u.id,
      sucursal_origen_id: u.sucursal_origen_id,
      active: true
    }));
  }, [unidadesNegocio]);
  
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
      logger.error('Error parsing reportData from sessionStorage:', e);
      sessionStorage.removeItem('reportData');
    }
    return [];
  });

  const [inventorySearchTerm, setInventorySearchTerm] = useState('');
  const [inventorySortConfig, setInventorySortConfig] = useState({
    key: null,
    direction: 'asc'
  });

  const handleInventorySort = (columnKey) => {
    setInventorySortConfig(prev => {
      if (prev?.key === columnKey) {
        return {
          key: columnKey,
          direction: prev.direction === 'asc' ? 'desc' : 'asc'
        };
      }

      return {
        key: columnKey,
        direction: 'asc'
      };
    });
  };

  const getInventorySortLabel = (columnKey) => {
    if (inventorySortConfig?.key !== columnKey) return '';
    return inventorySortConfig.direction === 'asc' ? ' ↑' : ' ↓';
  };

  const [erroresCaptura, setErroresCaptura] = useState([]); // Errores de captura de inventario (MPRO)
  const [loading, setLoading] = useState(false);
  
  // Estados para Insumos Pendientes de Descargar
  const [pendientesData, setPendientesData] = useState({ items: [], totales: { cantidad: 0, valor: 0, items: 0 }, almacenes: [] });
  const [loadingPendientes, setLoadingPendientes] = useState(false);
  const [almacenesPendientesSeleccionados, setAlmacenesPendientesSeleccionados] = useState([]);
  
  const [filters, setFilters] = useState(() => {
    // Recuperar filtros desde sessionStorage
    try {
      const saved = sessionStorage.getItem('reportFilters');
      if (saved) {
        const parsed = JSON.parse(saved);
        // Validar que tenga la estructura correcta
        if (parsed && typeof parsed === 'object' && parsed.server_id !== undefined) {
          return {
            ...parsed,
            query_type: normalizeReportQueryType(parsed.query_type)
          };
        }
      }
    } catch (e) {
      logger.error('Error parsing reportFilters from sessionStorage:', e);
      sessionStorage.removeItem('reportFilters');
    }
    return {
      server_id: '',
      unidad_id: '', // FASE 3.2: Agregar unidad_id
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
  // Modal detalle de movimientos / consumos (hook + componente CANÓNICO compartido con Auditoría)
  const {
    detalle: detalleProducto,
    abrirMovimientos,
    abrirConsumos,
    cerrar: cerrarDetalleProducto,
  } = useDetalleProducto();
  const [usoRecetaDetalle, setUsoRecetaDetalle] = useState({
    open: false,
    loading: false,
    codigo: '',
    producto: '',
    data: null,
    error: null
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
  const [loadingComparativo, setLoadingComparativo] = useState(false);
  
  // Estados para búsqueda en filtros
  const [searchCategorias, setSearchCategorias] = useState('');
  const [searchFamilias, setSearchFamilias] = useState('');
  const [searchSubfamilias, setSearchSubfamilias] = useState('');
  
  // Estados para controlar dropdowns (para mejor compatibilidad con Windows)
  const [dropdownInvIni, setDropdownInvIni] = useState(false);
  const [dropdownInvFin, setDropdownInvFin] = useState(false);
  
  // Estados para selección múltiple de almacenes e inventarios
  const [selectedAlmacenes, setSelectedAlmacenes] = useState(() => {
    try {
      const saved = sessionStorage.getItem('selectedAlmacenes');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [selectedInventariosIni, setSelectedInventariosIni] = useState(() => {
    try {
      const saved = sessionStorage.getItem('selectedInventariosIni');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [selectedInventariosFin, setSelectedInventariosFin] = useState(() => {
    try {
      const saved = sessionStorage.getItem('selectedInventariosFin');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  
  // Calcular fecha mínima de inventarios iniciales para filtrar finales (util CANÓNICO)
  const fechaMinimaInvInicial = useMemo(
    () => fechaMinimaInventarios(selectedInventariosIni),
    [selectedInventariosIni]
  );

  // Filtrar inventarios finales: posterior al inicial y nunca el mismo folio.
  const inventariosFinalesFiltrados = useMemo(
    () => filtrarInventariosFinales(inventarios, fechaMinimaInvInicial, {
      inventariosIniciales: selectedInventariosIni,
      strictAfterInitial: true
    }),
    [inventarios, fechaMinimaInvInicial, selectedInventariosIni]
  );

  const validarInventariosFinales = useCallback((finales, iniciales = selectedInventariosIni) => {
    if (!Array.isArray(finales) || finales.length === 0) return true;
    if (!Array.isArray(iniciales) || iniciales.length === 0) return true;

    const inicialKeys = new Set(iniciales.map(getInventarioKey).filter(Boolean));
    const inicialTimestamps = iniciales
      .map(getInventarioTimestamp)
      .filter((timestamp) => timestamp != null);
    const latestInitialTimestamp = inicialTimestamps.length > 0 ? Math.max(...inicialTimestamps) : null;

    return finales.every((inv) => {
      const key = getInventarioKey(inv);
      if (key && inicialKeys.has(key)) return false;
      if (latestInitialTimestamp == null) return true;
      const finalTimestamp = getInventarioTimestamp(inv);
      return finalTimestamp != null && finalTimestamp > latestInitialTimestamp;
    });
  }, [selectedInventariosIni]);

  useEffect(() => {
    if (selectedInventariosFin.length === 0) return;
    if (validarInventariosFinales(selectedInventariosFin)) return;

    setSelectedInventariosFin((prev) => prev.filter((inv) => validarInventariosFinales([inv])));
    toast.warning('Se quitaron inventarios finales no posteriores al inicial');
  }, [selectedInventariosIni, selectedInventariosFin, validarInventariosFinales]);
  
  // Estado para agrupar insumos de múltiples inventarios (MPRO)
  const [agruparInsumos, setAgruparInsumos] = useState(false);

  // EDARSAHUB-PATCH-ANALISIS-CONVERSION-AGRUPACION
  // Vista de cantidades para Análisis de Inventarios.
  // La data base del backend se conserva; esto solo cambia la vista.
  const [unidadAnalisisInventarios, setUnidadAnalisisInventarios] = useState('insumos');
  const [agruparProductosAnalisis, setAgruparProductosAnalisis] = useState(false);
  const [agruparPorAnalisis, setAgruparPorAnalisis] = useState('categoria');
  const [expandedAnalisisGroups, setExpandedAnalisisGroups] = useState({});
  
  // Estado para mostrar/ocultar columnas de costos (oculto por defecto)
  const [mostrarCostos, setMostrarCostos] = useState(false);

  // ============================================================================
  // ESTADOS PARA INFORMES DE AUDITORÍA
  // ============================================================================
  const [modalInforme, setModalInforme] = useState(false);
  const [informeData, setInformeData] = useState({
    comentarios: '',
    conclusiones: '',
    recomendaciones: '',
    auditor: '',
    cargo_auditor: '',
    incluir_comparativo: false
  });
  const [savingInforme, setSavingInforme] = useState(false);
  const [informesList, setInformesList] = useState([]);
  const [loadingInformes, setLoadingInformes] = useState(false);
  const [evidenciasTemp, setEvidenciasTemp] = useState([]); // Archivos seleccionados antes de guardar
  const [uploadingEvidencia, setUploadingEvidencia] = useState(false);
  
  // Estado para ver informe completo
  const [viewInformeModal, setViewInformeModal] = useState(false);
  const [selectedInforme, setSelectedInforme] = useState(null);
  
  // Estado para pantalla completa de resultados
  const [showFullscreenResultados, setShowFullscreenResultados] = useState(false);

  // Cargar informes de auditoría
  const loadInformesAuditoria = async () => {
    try {
      setLoadingInformes(true);
      const response = await api.get('/auditoria/informes');
      setInformesList(response.data.informes || []);
    } catch (error) {
      logger.error('Error cargando informes:', error);
    } finally {
      setLoadingInformes(false);
    }
  };

  // Cargar informes cuando se abre el tab
  useEffect(() => {
    if (activeTab === 'informes') {
      loadInformesAuditoria();
    }
  }, [activeTab]);

  // Abrir modal para generar informe
  const handleAbrirModalInforme = () => {
    // Pre-llenar datos del reporte actual
    const rowsVistaAnalisis = getAnalisisVistaRows();
    const totalProductos = rowsVistaAnalisis.length;
    const productosConDiferencia = rowsVistaAnalisis.filter(p => Math.abs(getAnalisisDiferenciaQty(p)) > 0).length;
    const valorDiferencias = rowsVistaAnalisis.reduce((sum, p) => sum + Math.abs(getAnalisisDiferenciaValor(p)), 0);
    const precision = totalProductos > 0 ? ((totalProductos - productosConDiferencia) / totalProductos * 100) : 0;
    
    setInformeData({
      comentarios: '',
      conclusiones: `El análisis de inventarios para ${filters.sucursal || 'la sucursal seleccionada'} muestra un total de ${totalProductos} productos analizados, de los cuales ${productosConDiferencia} presentan diferencias con un valor total de $${valorDiferencias.toLocaleString('es-MX', { minimumFractionDigits: 2 })}. El porcentaje de precisión es del ${precision.toFixed(1)}%.`,
      recomendaciones: '',
      auditor: '',
      cargo_auditor: '',
      incluir_comparativo: false,
      // Datos calculados
      total_productos: totalProductos,
      productos_con_diferencia: productosConDiferencia,
      valor_total_diferencias: valorDiferencias,
      porcentaje_precision: precision
    });
    setEvidenciasTemp([]);
    setModalInforme(true);
  };

  // Guardar informe de auditoría
  const handleGuardarInforme = async () => {
    if (!informeData.comentarios && !informeData.conclusiones) {
      toast.error('Agrega al menos comentarios o conclusiones');
      return;
    }
    
    try {
      setSavingInforme(true);
      
      // Preparar productos con diferencias (top 50)
      const productosConDif = rowsVistaAnalisis
        .filter(p => Math.abs(p.DIFERENCIA_QTY || 0) > 0)
        .sort((a, b) => Math.abs(b.DIFERENCIA_VALOR || 0) - Math.abs(a.DIFERENCIA_VALOR || 0))
        .slice(0, 50)
        .map(p => ({
          codigo: p.CODIGO_INSUMO || p.ID_PRODUCTO || '',
          producto: p.PRODUCTO || p.NOMBRE || '',
          inv_inicial: p.Inv_Inicial_Cantidad ?? p.INV_INICIAL ?? p.inv_inicial ?? 0,
          inv_final: p.Inv_Final_Cantidad ?? p.INV_FINAL ?? p.inv_final ?? 0,
          diferencia: getAnalisisDiferenciaQty(p),
          valor_diferencia: Math.abs(getAnalisisDiferenciaValor(p))
        }));
      
      const payload = {
        sucursal_id: filters.sucursal_id,
        sucursal_nombre: filters.sucursal || sucursales.find(s => s.id === filters.sucursal_id)?.nombre || '',
        almacen_id: selectedAlmacenes[0]?.id || filters.almacen_id,
        almacen_nombre: selectedAlmacenes[0]?.nombre || filters.almacen || '',
        servidor_id: filters.server_id,
        servidor_nombre: selectedServer?.name || '',
        inventario_inicial_id: selectedInventariosIni[0]?.id || filters.inventario_inicial,
        inventario_inicial_fecha: selectedInventariosIni[0]?.fecha?.split('T')[0] || filters.inventario_inicial_fecha,
        inventario_final_id: selectedInventariosFin[0]?.id || filters.inventario_final,
        inventario_final_fecha: selectedInventariosFin[0]?.fecha?.split('T')[0] || filters.inventario_final_fecha,
        fecha_inicio_movimientos: filters.fecha_ini,
        fecha_fin_movimientos: filters.fecha_fin,
        total_productos: informeData.total_productos,
        productos_con_diferencia: informeData.productos_con_diferencia,
        valor_total_diferencias: informeData.valor_total_diferencias,
        porcentaje_precision: informeData.porcentaje_precision,
        comentarios: informeData.comentarios,
        conclusiones: informeData.conclusiones,
        recomendaciones: informeData.recomendaciones,
        auditor: informeData.auditor,
        cargo_auditor: informeData.cargo_auditor,
        incluir_comparativo_4_cortes: informeData.incluir_comparativo,
        productos_diferencias: productosConDif,
        // Errores de captura detectados
        errores_captura: erroresCaptura.map(e => ({
          codigo: e.CODIGO_INSUMO || e.codigo || '',
          producto: e.PRODUCTO || e.producto || '',
          tipo_error: e.TIPO_ERROR || e.tipo || 'Error de captura',
          inv_capturado: e.INV_CAPTURADO || e.cantidad || 0,
          detalle: e.DETALLE || e.mensaje || ''
        }))
      };
      
      const response = await api.post('/auditoria/informes', payload);
      
      if (response.data.success) {
        const informeId = response.data.informe_id;
        
        // Subir evidencias si hay
        for (const file of evidenciasTemp) {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('descripcion', file.descripcion || '');
          
          await api.post(`/auditoria/informes/${informeId}/evidencias`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
        }
        
        toast.success('Informe guardado exitosamente');
        setModalInforme(false);
        loadInformesAuditoria();
        setActiveTab('informes'); // Ir al tab de informes
      }
    } catch (error) {
      logger.error('Error guardando informe:', error);
      toast.error('Error al guardar el informe');
    } finally {
      setSavingInforme(false);
    }
  };

  // Manejar selección de archivos de evidencia
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter(f => {
      const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
      return validTypes.includes(f.type);
    });
    
    if (validFiles.length !== files.length) {
      toast.warning('Algunos archivos no son válidos (solo imágenes, PDF, Word, Excel)');
    }
    
    setEvidenciasTemp(prev => [...prev, ...validFiles]);
    e.target.value = ''; // Reset input
  };

  // Eliminar evidencia temporal
  const handleRemoveEvidencia = (index) => {
    setEvidenciasTemp(prev => prev.filter((_, i) => i !== index));
  };

  // Ver informe completo
  const handleVerInforme = async (informeId) => {
    try {
      const response = await api.get(`/auditoria/informes/${informeId}`);
      setSelectedInforme(response.data);
      setViewInformeModal(true);
    } catch (error) {
      toast.error('Error al cargar el informe');
    }
  };

  // Descargar PDF del informe
  const handleDescargarPDF = async (informeId) => {
    try {
      toast.info('Generando PDF...');
      const response = await api.get(`/auditoria/informes/${informeId}/pdf`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Informe_Auditoria_${informeId.slice(0, 8)}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success('PDF descargado');
    } catch (error) {
      toast.error('Error al generar el PDF');
    }
  };

  // Eliminar informe
  const handleEliminarInforme = async (informeId) => {
    if (!window.confirm('¿Estás seguro de eliminar este informe?')) return;
    
    try {
      await api.delete(`/auditoria/informes/${informeId}`);
      toast.success('Informe eliminado');
      loadInformesAuditoria();
    } catch (error) {
      toast.error('Error al eliminar el informe');
    }
  };

  // ============================================================================

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

  // Guardar almacenes e inventarios seleccionados
  useEffect(() => {
    sessionStorage.setItem('selectedAlmacenes', JSON.stringify(selectedAlmacenes));
  }, [selectedAlmacenes]);

  useEffect(() => {
    if (filters.query_type !== 'analisis' || selectedAlmacenes.length === 0) return;

    const unidades = Array.from(new Set(
      selectedAlmacenes
        .map(a => a?.unidad_natural || (Number(a?.tipo ?? a?.tipo_almacen ?? a?.almacen_tipo) === 2 ? 'presentaciones' : 'insumos'))
        .filter(Boolean)
    ));

    if (unidades.length === 1) {
      setUnidadAnalisisInventarios(unidades[0]);
    }
  }, [filters.query_type, selectedAlmacenes]);

  useEffect(() => {
    sessionStorage.setItem('selectedInventariosIni', JSON.stringify(selectedInventariosIni));
  }, [selectedInventariosIni]);

  useEffect(() => {
    sessionStorage.setItem('selectedInventariosFin', JSON.stringify(selectedInventariosFin));
  }, [selectedInventariosFin]);

  useEffect(() => {
    if (!selectedServer) return;

    const normalizedQueryType = normalizeReportQueryType(filters.query_type);
    const supportedQueryType = normalizedQueryType === 'pendientes' && selectedServer.system_type !== 'SoftRestaurant'
      ? 'analisis'
      : normalizedQueryType;

    if (supportedQueryType !== filters.query_type) {
      setFilters(prev => ({
        ...prev,
        query_type: supportedQueryType
      }));
    }
  }, [filters.query_type, selectedServer]);

  // Cerrar dropdowns de inventarios al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!e.target.closest('[data-dropdown-inv]')) {
        setDropdownInvIni(false);
        setDropdownInvFin(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  useEffect(() => {
    // FASE AUTH-FIX: Esperar a que el usuario esté autenticado
    if (authLoading || !user) {
      return;
    }
    loadUnidadesNegocio();
  }, [user, authLoading]);

  // Track previous canonical business unit to detect scope changes
  const prevUnidadRef = useRef(selectedUnidad);
  
  useEffect(() => {
    if (filters.server_id) {
      // Si cambió el servidor, limpiar estados dependientes
      if (prevUnidadRef.current && prevUnidadRef.current !== selectedUnidad) {
        setSelectedAlmacenes([]);
        setSelectedInventariosIni([]);
        setSelectedInventariosFin([]);
        setSelectedCategorias([]);
        setSelectedFamilias([]);
        setSelectedSubfamilias([]);
        setInventarios([]);
        setAlmacenes([]);
        setSucursales([]);
      }
      prevUnidadRef.current = selectedUnidad;
      
      loadSucursales();
      loadReportFilters();
      // Guardar el servidor seleccionado
      const server = servers.find(s => s.id === filters.server_id);
      setSelectedServer(server);
      
      // Si es SoftRestaurant, cargar almacenes directamente (no tiene sucursales)
      if (server?.system_type === 'SoftRestaurant') {
        loadAlmacenesSoftRestaurant();
      }
      // Si es MPRO con sucursal_origen_id ya establecida, cargar almacenes
      else if (server?.system_type === 'MPRO' && filters.sucursal_id) {
        loadAlmacenes();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedUnidad, filters.server_id, servers, filters.sucursal_id]);

  // Cargar almacenes para SoftRestaurant desde EDARSAHUB SQL canónico
  const loadAlmacenesSoftRestaurant = async (soloConsumo = false) => {
    try {
      if (!selectedUnidad) return;
      const response = await api.get(`/config-asignaciones/almacenes/${selectedUnidad}`);
      const rows = Array.isArray(response.data?.data) ? response.data.data : [];

      const map = new Map();

      rows.forEach(item => {
        const almacenId = String(item.id ?? item.almacen_id ?? item.idalmacen ?? '').trim();
        const almacenNombre = String(item.nombre ?? item.almacen ?? '').trim();
        const almacenTipo = Number(item.tipo ?? item.tipo_almacen ?? item.almacen_tipo ?? 1);

        if (!almacenId && !almacenNombre) return;

        const nombreFinal = almacenNombre || almacenId;
        const key = `${almacenId}|${nombreFinal}`;

        if (!map.has(key)) {
          map.set(key, {
            id: almacenId || nombreFinal,
            almacen_id: almacenId,
            nombre: nombreFinal,
            almacen: nombreFinal,
            label: nombreFinal,
            value: nombreFinal,
            source: 'EDARSAHUB_SQL',
            tipo: almacenTipo,
            tipo_almacen: almacenTipo,
            unidad_natural: almacenTipo === 2 ? 'presentaciones' : 'insumos'
          });
        }
      });

      const almacenesCanonicos = Array.from(map.values())
        .sort((a, b) => String(a.nombre).localeCompare(String(b.nombre)));

      if (almacenesCanonicos.length > 0) {
        setAlmacenes(almacenesCanonicos);
      } else {
        setAlmacenes([]);
      }

      setFilters(prev => ({
        ...prev,
        sucursal_id: 'default',
        sucursal: 'SoftRestaurant'
      }));
    } catch (error) {
      logger.error('Error al cargar almacenes canónicos SoftRestaurant:', error);
      // Mantener el último catálogo válido ante un fallo transitorio.
    }
  };

  // Cargar opciones de filtros (categorías, familias, subfamilias)
  const loadReportFilters = async () => {
    if (!filters.server_id) return;
    
    setLoadingFilters(true);
    try {
      const response = await api.get(`/servers/${filters.server_id}/report-filters`);
      const normalizeOptions = (items) => (Array.isArray(items) ? items : [])
        .map((item) => {
          const id = item?.id ?? item?.Codigo ?? item?.codigo;
          const parent = item?.parent ?? item?.ParentCodigo ?? item?.parentCodigo;
          return {
            ...item,
            id: id === null || id === undefined ? '' : String(id),
            nombre: String(item?.nombre ?? item?.Nombre ?? item?.name ?? id ?? ''),
            parent: parent === null || parent === undefined || parent === '' ? null : String(parent)
          };
        })
        .filter((item) => item.id && item.nombre);

      setFilterOptions({
        categorias: normalizeOptions(response.data.categorias),
        familias: normalizeOptions(response.data.familias),
        subfamilias: normalizeOptions(response.data.subfamilias)
      });
    } catch (error) {
      logger.error('Error al cargar filtros:', error);
      setFilterOptions({ categorias: [], familias: [], subfamilias: [] });
    } finally {
      setLoadingFilters(false);
    }
  };

  useEffect(() => {
    if (filters.server_id && filters.sucursal_id) {
      // Buscar el servidor actual para verificar el tipo
      const currentServer = selectedServer || servers.find(s => s.id === filters.server_id);
      // Solo cargar almacenes si NO es SoftRestaurant (que ya los carga directamente)
      if (currentServer?.system_type !== 'SoftRestaurant') {
        logger.log('[loadAlmacenes useEffect] Cargando almacenes para:', filters.sucursal_id);
        loadAlmacenes();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.server_id, filters.sucursal_id, selectedServer, servers]);

  // Cargar insumos pendientes cuando se selecciona ese tipo de consulta
  useEffect(() => {
    if (filters.query_type === 'pendientes' && filters.server_id && selectedServer?.system_type === 'SoftRestaurant') {
      // Recargar almacenes solo de consumo para pendientes
      loadAlmacenesSoftRestaurant(true);
    } else if (filters.server_id && selectedServer?.system_type === 'SoftRestaurant' && filters.query_type !== 'pendientes') {
      // Recargar todos los almacenes para otros tipos de consulta
      loadAlmacenesSoftRestaurant(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.query_type, filters.server_id, selectedServer]);

  // Recargar pendientes cuando cambia selección de almacén
  useEffect(() => {
    if (filters.query_type === 'pendientes' && filters.server_id && selectedServer?.system_type === 'SoftRestaurant') {
      const almacenFiltro = almacenesPendientesSeleccionados.length === 1 ? almacenesPendientesSeleccionados[0] : null;
      loadInsumosPendientes(almacenFiltro);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [almacenesPendientesSeleccionados, filters.query_type, filters.server_id, selectedServer]);

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
          // Para MPRO usar sucursal_id, para SoftRestaurant usar 'SoftRestaurant'
          const params = {
            almacen_id: almacen.id || '',
            almacen: almacen.nombre || ''
          };
          
          if (selectedServer?.system_type === 'SoftRestaurant') {
            params.sucursal = 'SoftRestaurant';
          } else {
            // MPRO: usar sucursal_id para filtro correcto
            params.sucursal_id = filters.sucursal_id || '';
            params.sucursal = filters.sucursal || '';
          }
          
          const response = await api.get(`/compras/inventarios-fisicos/${selectedUnidad}`, { params });
          // La respuesta es un array directo, no {inventarios: [...]}
          const inventariosData = Array.isArray(response.data) ? response.data : (response.data.inventarios || []);
          // Agregar el nombre del almacén a cada inventario
          const inventariosConAlmacen = inventariosData.map(inv => ({
            ...inv,
            almacen: inv.almacen || almacen.nombre,
            almacen_id: inv.almacen_id || almacen.id
          }));
          allInventarios = [...allInventarios, ...inventariosConAlmacen];
        }
        // Ordenar todos los inventarios por fecha descendente (más reciente primero)
        allInventarios.sort((a, b) => {
          // Primero por fecha descendente
          const fechaA = a.fecha ? new Date(a.fecha) : new Date(0);
          const fechaB = b.fecha ? new Date(b.fecha) : new Date(0);
          if (fechaB.getTime() !== fechaA.getTime()) {
            return fechaB.getTime() - fechaA.getTime();
          }
          // Si misma fecha, por folio descendente
          return b.folio.localeCompare(a.folio);
        });
        setInventarios(allInventarios);
      } catch (error) {
        logger.error('Error cargando inventarios:', error);
        // Mantener la última lista válida ante un fallo transitorio.
      }
    };
    
    if (selectedUnidad && selectedAlmacenes.length > 0) {
      if (selectedServer?.system_type === 'SoftRestaurant' || filters.sucursal_id) {
        loadAllInventarios();
      }
    }
  }, [selectedUnidad, filters.sucursal_id, selectedAlmacenes, selectedServer, filters.sucursal]);

  // AUTO-CALCULAR fechas cuando ambos inventarios estén seleccionados
  useEffect(() => {
    if (filters.inventario_inicial && filters.inventario_final && selectedServer && inventarios.length > 0) {
      const invInicial = inventarios.find(inv => String(inv.folio) === String(filters.inventario_inicial));
      const invFinal = inventarios.find(inv => String(inv.folio) === String(filters.inventario_final));
      
      if (invInicial?.fecha && invFinal?.fecha) {
        const dates = calculateDates(invInicial.fecha, invFinal.fecha, selectedServer.system_type);
        
        // Solo actualizar si las fechas son diferentes
        if (dates.fecha_ini !== filters.fecha_ini || dates.fecha_fin !== filters.fecha_fin) {
          logger.log('Auto-calculando fechas:', dates);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.inventario_inicial, filters.inventario_final, inventarios, selectedServer]);

  // AUTO-CALCULAR fechas para MULTI-SELECCIÓN de inventarios
  useEffect(() => {
    if (selectedInventariosIni.length > 0 && selectedInventariosFin.length > 0 && selectedServer) {
      // Usar la fecha del primer inventario seleccionado de cada grupo
      const fechaInicial = selectedInventariosIni[0]?.fecha;
      const fechaFinal = selectedInventariosFin[0]?.fecha;
      
      if (fechaInicial && fechaFinal) {
        const dates = calculateDates(fechaInicial, fechaFinal, selectedServer.system_type);
        
        // Solo actualizar si las fechas son diferentes
        if (dates.fecha_ini !== filters.fecha_ini || dates.fecha_fin !== filters.fecha_fin) {
          logger.log('Auto-calculando fechas (multi-selección):', dates);
          setFilters(prev => ({
            ...prev,
            inventario_inicial_fecha: fechaInicial,
            inventario_final_fecha: fechaFinal,
            fecha_ini: dates.fecha_ini,
            fecha_fin: dates.fecha_fin
          }));
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedInventariosIni, selectedInventariosFin, selectedServer]);

  // FASE 3.2: Cargar unidades de negocio según RBAC
  const loadUnidadesNegocio = async () => {
    setLoadingUnidades(true);
    try {
      logger.log('[Reportes] Cargando unidades de negocio via unidadesNegocioService...');
      const unidades = await fetchUnidadesNegocio();
      logger.log('[Reportes] Unidades cargadas:', unidades.length);
      setUnidadesNegocio(unidades);
      
      // Auto-seleccionar si el usuario tiene solo una unidad
      if (unidades.length === 1) {
        const unidad = unidades[0];
        const unidadServerId = String(unidad.server_id || '').trim();
        setSelectedUnidad(unidad.id);
        
        // Si tiene sucursal_origen_id (MPRO con sucursal auto-definida), también auto-seleccionar sucursal
        if (unidad.sucursal_origen_id && unidad.system_type === 'MPRO') {
          const nombreSucursal = unidad.sucursales?.[0]?.nombre || unidad.nombre;
          setFilters(prev => ({
            ...prev,
            unidad_id: unidad.id,
            server_id: unidadServerId,
            sucursal_id: unidad.sucursal_origen_id,
            sucursal: nombreSucursal
          }));
        } else {
          setFilters(prev => ({
            ...prev,
            unidad_id: unidad.id,
            server_id: unidadServerId
          }));
        }
        
        // Establecer el servidor seleccionado para compatibilidad
        setSelectedServer({
          id: unidadServerId,
          name: unidad.nombre,
          system_type: unidad.system_type,
          sucursal_origen_id: unidad.sucursal_origen_id
        });
        logger.log(`[Reportes] Auto-seleccionada unidad única: ${unidad.nombre}`);
      } else {
        // Restaurar unidad guardada si existe
        const saved = sessionStorage.getItem('reportFilters');
        if (saved) {
          try {
            const params = JSON.parse(saved);
            if (params.unidad_id && unidades.find(u => u.id === params.unidad_id)) {
              setSelectedUnidad(params.unidad_id);
              const unidad = unidades.find(u => u.id === params.unidad_id);
              if (unidad) {
                const unidadServerId = String(unidad.server_id || '').trim();
                const serverChanged = String(params.server_id || '') !== unidadServerId;
                const usaSucursalUnidad = unidad.sucursal_origen_id && unidad.system_type === 'MPRO';
                const nombreSucursal = unidad.sucursales?.[0]?.nombre || unidad.nombre;

                setFilters(prev => ({
                  ...prev,
                  ...params,
                  unidad_id: unidad.id,
                  server_id: unidadServerId,
                  query_type: normalizeReportQueryType(params.query_type),
                  sucursal_id: usaSucursalUnidad ? unidad.sucursal_origen_id : (serverChanged ? '' : params.sucursal_id || ''),
                  sucursal: usaSucursalUnidad ? nombreSucursal : (serverChanged ? '' : params.sucursal || ''),
                  almacen_id: serverChanged ? '' : params.almacen_id || '',
                  almacen: serverChanged ? '' : params.almacen || '',
                  inventario_inicial: serverChanged ? '' : params.inventario_inicial || '',
                  inventario_final: serverChanged ? '' : params.inventario_final || '',
                  inventario_inicial_fecha: serverChanged ? '' : params.inventario_inicial_fecha || '',
                  inventario_final_fecha: serverChanged ? '' : params.inventario_final_fecha || '',
                  fecha_ini: serverChanged ? '' : params.fecha_ini || '',
                  fecha_fin: serverChanged ? '' : params.fecha_fin || ''
                }));

                if (serverChanged) {
                  setSelectedAlmacenes([]);
                  setSelectedInventariosIni([]);
                  setSelectedInventariosFin([]);
                }

                setSelectedServer({
                  id: unidadServerId,
                  name: unidad.nombre,
                  system_type: unidad.system_type,
                  sucursal_origen_id: unidad.sucursal_origen_id
                });
              }
            }
          } catch (e) {
            // Silently ignore JSON parse errors for stored preferences
            logger.warn('[Reportes] Error parsing stored filters:', e.message);
          }
        }
      }
    } catch (error) {
      logger.error('[Reportes] Error al cargar unidades de negocio:', error);
      toast.error('Error al cargar unidades de negocio: ' + (error.message || 'Error desconocido'));
      setUnidadesNegocio([]);
    } finally {
      setLoadingUnidades(false);
    }
  };

  const loadSucursales = async () => {
    try {
      logger.log('[loadSucursales] Cargando sucursales para server:', filters.server_id);
      const response = await api.get(`/servers/${filters.server_id}/sucursales`);
      const data = Array.isArray(response.data) ? response.data : [];
      logger.log('[loadSucursales] Sucursales recibidas:', data.length, data);
      setSucursales(data);
    } catch (error) {
      logger.error('[loadSucursales] Error al cargar sucursales:', error);
      setSucursales([]);
    }
  };

  const loadAlmacenes = async () => {
    if (!selectedUnidad) return;
    try {
      logger.log('[loadAlmacenes] Cargando catálogo canónico para unidad:', selectedUnidad);
      const response = await api.get(`/config-asignaciones/almacenes/${selectedUnidad}`);
      const rows = Array.isArray(response.data?.data) ? response.data.data : [];
      const canonicos = rows
        .filter(item => String(item?.id ?? item?.almacen_id ?? '').trim())
        .map(item => {
          const id = String(item.id ?? item.almacen_id).trim();
          const nombre = String(item.nombre ?? item.almacen ?? id).trim();
          return { ...item, id, almacen_id: id, nombre, almacen: nombre, label: nombre, value: nombre, source: 'EDARSAHUB_SQL' };
        });
      setAlmacenes(canonicos);
    } catch (error) {
      logger.error('Error al cargar almacenes canónicos:', error);
      // Mantener el último catálogo válido ante un fallo transitorio.
    }
  };

  const loadInventarios = async () => {
    try {
      if (!selectedUnidad) return;
      const response = await api.get(`/compras/inventarios-fisicos/${selectedUnidad}`, {
        params: { 
          sucursal_id: filters.sucursal_id,
          almacen_id: filters.almacen_id
        }
      });
      // Ordenar por fecha descendente (más reciente primero)
      const inventariosOrdenados = (response.data || []).sort((a, b) => {
        const fechaA = a.fecha ? new Date(a.fecha) : new Date(0);
        const fechaB = b.fecha ? new Date(b.fecha) : new Date(0);
        if (fechaB.getTime() !== fechaA.getTime()) {
          return fechaB.getTime() - fechaA.getTime();
        }
        return (b.folio || '').localeCompare(a.folio || '');
      });
      setInventarios(inventariosOrdenados);
    } catch (error) {
      logger.error('Error al cargar inventarios:', error);
      // Mantener la última lista válida ante un fallo transitorio.
    }
  };

  // Función para cargar Insumos Pendientes de Descargar
  const loadInsumosPendientes = async (almacenId = null) => {
    if (!filters.server_id) return;
    
    setLoadingPendientes(true);
    try {
      let url = `/inventarios/pendientes/${filters.server_id}`;
      if (almacenId) {
        url += `?almacen_id=${almacenId}`;
      }
      const response = await api.get(url);
      setPendientesData(response.data || { items: [], totales: { cantidad: 0, valor: 0, items: 0 }, almacenes: [] });
    } catch (error) {
      logger.error('Error al cargar insumos pendientes:', error);
      toast.error('Error al cargar insumos pendientes');
      setPendientesData({ items: [], totales: { cantidad: 0, valor: 0, items: 0 }, almacenes: [] });
    } finally {
      setLoadingPendientes(false);
    }
  };

  // EDARSAHUB-PATCH-ANALISIS-CONVERSION-AGRUPACION
  const analisisQtyKeys = new Set([
    'Inv_Inicial_Cantidad',
    'Movimientos',
    'Ventas',
    'Inv_Teorico_Cantidad',
    'Inv_Final_Cantidad',
    'Diferencia_Cantidad',
    'DIFERENCIA_QTY',
    'INV_INICIAL',
    'INV_FINAL'
  ]);

  const getAnalisisRendimiento = (row) => {
    const raw =
      row?.Rendimiento ??
      row?.rendimiento ??
      row?.RENDIMIENTO ??
      row?.factor_conversion ??
      1;

    const val = parseFloat(raw);
    return Number.isFinite(val) && val > 0 ? val : 1;
  };

  const isAnalisisCantidadKey = (key) => {
    const k = String(key || '').toLowerCase();

    if (analisisQtyKeys.has(key)) return true;
    if (k.includes('costo') || k.includes('valor') || k.includes('porcentaje') || k.includes('precio')) return false;

    return (
      k === 'movimientos' ||
      k === 'ventas' ||
      k.includes('cantidad') ||
      k.includes('qty') ||
      k.includes('inv_inicial') ||
      k.includes('inv_final') ||
      k.includes('inv_teorico') ||
      k.includes('diferencia')
    );
  };

  const convertirCantidadAnalisis = (row, key, value) => {
    const num = parseFloat(value);

    if (!Number.isFinite(num) || !isAnalisisCantidadKey(key)) {
      return value;
    }

    const rendimiento = getAnalisisRendimiento(row);
    return unidadAnalisisInventarios === 'presentaciones' && rendimiento > 0
      ? num / rendimiento
      : num;
  };

  const formatAnalisisHeader = (key) => {
    const labels = {
      Agrupacion: 'AGRUPACION',
      codigo_producto: 'CODIGO',
      Codigo: 'CODIGO',
      codigo: 'CODIGO',
      CODIGO: 'CODIGO',
      nombre_producto: 'NOMBRE PRODUCTO',
      Producto: 'NOMBRE PRODUCTO',
      producto: 'NOMBRE PRODUCTO',
      Nombre: 'NOMBRE PRODUCTO',
      nombre: 'NOMBRE PRODUCTO',
      unidad: 'UNIDAD',
      Unidad: 'UNIDAD',
      UNIDAD: 'UNIDAD',
      Items: 'ITEMS',
      Inv_Inicial_Cantidad: 'INV. INICIAL',
      inventario_inicial: 'INV. INICIAL',
      Movimientos: 'MOVIMIENTOS',
      movimientos: 'MOVIMIENTOS',
      Ventas: 'VENTAS',
      ventas: 'VENTAS',
      Inv_Teorico_Cantidad: 'INV. TEORICO',
      inventario_teorico: 'INV. TEORICO',
      Inv_Final_Cantidad: 'INV. FINAL',
      inventario_final: 'INV. FINAL',
      Diferencia_Cantidad: 'DIFERENCIAS',
      diferencia: 'DIFERENCIAS',
      DIFERENCIA_QTY: 'DIFERENCIAS',
      Diferencia_Costo: 'DIFERENCIA COSTO',
      DIFERENCIA_VALOR: 'DIFERENCIA COSTO'
    };

    return labels[key] || String(key || '').replace(/_/g, ' ').replace(/Cantidad/gi, '').trim().toUpperCase();
  };

  const shouldShowAnalisisColumn = (key) => {
    const normalized = String(key || '').toLowerCase();
    const hidden = new Set([
      'Rendimiento',
      'rendimiento',
      'tipo_almacen',
      'tipoAlmacen',
      'almacen_tipo',
      'source',
      'Categoria',
      'categoria',
      'Familia',
      'familia',
      'SubFamilia',
      'Subfamilia',
      'subfamilia',
      '__rowType',
      '__groupKey',
      '__rowId',
      '__detailCount'
    ]);
    return !String(key || '').startsWith('__') && !hidden.has(key) && !hidden.has(normalized);
  };

  const getProductoAgrupacionAnalisis = (row) => {
    const codigo = String(
      row?.codigo_producto ??
      row?.Codigo ??
      row?.codigo ??
      row?.CODIGO ??
      ''
    ).trim();
    const producto = String(
      row?.nombre_producto ??
      row?.Producto ??
      row?.producto ??
      row?.Nombre ??
      row?.nombre ??
      codigo
    ).trim();
    const unidad = String(
      row?.unidad ??
      row?.Unidad ??
      row?.UNIDAD ??
      ''
    ).trim();

    return {
      key: `${codigo || producto}|${producto}|${unidad}`,
      codigo,
      producto,
      unidad
    };
  };

  const isNombreProductoAnalisisColumn = (key) => {
    const normalized = String(key || '')
      .toLowerCase()
      .replace(/[\s_-]+/g, '');

    return ['nombreproducto', 'producto', 'nombre'].includes(normalized);
  };

  const getAgrupacionAnalisis = (row) => {
    const productoInfo = getProductoAgrupacionAnalisis(row);
    const rawBy = {
      producto: productoInfo.key,
      categoria: row?.Categoria ?? row?.categoria ?? row?.Grupo ?? row?.grupo,
      familia: row?.Familia ?? row?.familia,
      subfamilia: row?.SubFamilia ?? row?.subfamilia ?? row?.Subfamilia
    };
    const labelBy = {
      producto: productoInfo.producto || productoInfo.codigo || 'SIN PRODUCTO',
      categoria: rawBy.categoria,
      familia: rawBy.familia,
      subfamilia: rawBy.subfamilia
    };
    const selected = rawBy[agruparPorAnalisis] ?? rawBy.producto;
    const label = labelBy[agruparPorAnalisis] ?? labelBy.producto;
    const fallback = agruparPorAnalisis === 'producto' ? 'SIN PRODUCTO' : 'SIN CLASIFICAR';

    return {
      key: selected === null || selected === undefined || String(selected).trim() === ''
        ? fallback
        : String(selected).trim(),
      label: label === null || label === undefined || String(label).trim() === ''
        ? fallback
        : String(label).trim(),
      productoInfo
    };
  };

  const isAnalisisGroupExpanded = (groupKey) => (
    expandedAnalisisGroups[groupKey] !== false
  );

  const toggleAnalisisGroup = (groupKey) => {
    setExpandedAnalisisGroups((prev) => ({
      ...prev,
      [groupKey]: !isAnalisisGroupExpanded(groupKey)
    }));
  };

  const buildConvertedAnalisisRow = (row) => {
    const out = {};

    Object.entries(row || {}).forEach(([key, value]) => {
      out[key] = convertirCantidadAnalisis(row, key, value);
    });

    return out;
  };

  const buildAnalisisDisplayData = () => {
    const rows = Array.isArray(reportData) ? reportData : [];

    if (!agruparProductosAnalisis) {
      return rows.map((row, idx) => ({
        ...buildConvertedAnalisisRow(row),
        __rowType: 'detail',
        __rowId: `detail-${idx}`
      }));
    }

    const metricas = [
      'Inv_Inicial_Cantidad',
      'Movimientos',
      'Ventas',
      'Inv_Teorico_Cantidad',
      'Inv_Final_Cantidad',
      'Diferencia_Cantidad',
      'Diferencia_Costo',
      'DIFERENCIA_QTY',
      'DIFERENCIA_VALOR',
      'inventario_inicial',
      'movimientos',
      'ventas',
      'inventario_teorico',
      'inventario_final',
      'diferencia',
      'diferencia_costo'
    ];

    const grupos = new Map();

    rows.forEach((row) => {
      const agrupacion = getAgrupacionAnalisis(row);
      const productoInfo = agrupacion.productoInfo;

      if (!grupos.has(agrupacion.key)) {
        grupos.set(agrupacion.key, {
          summary: {
            __rowType: 'group',
            __groupKey: agrupacion.key,
            Agrupacion: agrupacion.label,
            codigo_producto: agruparPorAnalisis === 'producto' ? productoInfo.codigo : '',
            nombre_producto: agruparPorAnalisis === 'producto' ? productoInfo.producto : agrupacion.label,
            unidad: agruparPorAnalisis === 'producto' ? productoInfo.unidad : '',
            Items: 0,
            Rendimiento: getAnalisisRendimiento(row)
          },
          details: []
        });
      }

      const acc = grupos.get(agrupacion.key).summary;
      acc.Items += 1;
      acc.Rendimiento = Math.max(getAnalisisRendimiento(row), getAnalisisRendimiento(acc));

      metricas.forEach((key) => {
        if (row[key] === undefined || row[key] === null) return;

        const val = convertirCantidadAnalisis(row, key, row[key]);
        const num = parseFloat(val);

        if (!Number.isFinite(num)) return;

        acc[key] = (parseFloat(acc[key]) || 0) + num;
      });

      grupos.get(agrupacion.key).details.push({
        ...buildConvertedAnalisisRow(row),
        __rowType: 'detail',
        __groupKey: agrupacion.key,
        __rowId: `${agrupacion.key}-${grupos.get(agrupacion.key).details.length}`
      });
    });

    return Array.from(grupos.values()).flatMap(({ summary, details }) => {
      const out = {};

      Object.entries(summary).forEach(([key, value]) => {
        out[key] = typeof value === 'number'
          ? Math.round(value * 10000) / 10000
          : value;
      });

      out.__detailCount = details.length;
      const rowsForGroup = [out];

      if (isAnalisisGroupExpanded(out.__groupKey)) {
        rowsForGroup.push(...details);
      }

      return rowsForGroup;
    });
  };

  const analysisDisplayData = filters.query_type === 'analisis'
    ? buildAnalisisDisplayData()
    : (Array.isArray(reportData) ? reportData : []);

  const inventoryVisibleData = useMemo(() => {
    const sourceRows = Array.isArray(analysisDisplayData) ? analysisDisplayData : [];
    const search = inventorySearchTerm.trim().toLowerCase();

    const filtered = sourceRows.filter(row => {
      if (!search) return true;

      const haystack = [
        row.codigo_producto,
        row.codigo,
        row.Codigo,
        row.CODIGO,
        row.nombre_producto,
        row.nombre,
        row.Nombre,
        row.NOMBRE,
        row.descripcion,
        row.Descripcion,
        row.DESCRIPCION,
        row.Producto,
        row.producto
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      return haystack.includes(search);
    });

    if (agruparProductosAnalisis) {
      return filtered;
    }

    const sortKey = inventorySortConfig?.key;
    const direction = inventorySortConfig?.direction || 'asc';

    if (!sortKey) {
      return filtered;
    }

    const normalizeValue = (value) => {
      if (value === null || value === undefined) return '';

      const numeric = Number(value);
      if (value !== '' && Number.isFinite(numeric)) {
        return numeric;
      }

      return String(value)
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase();
    };

    return [...filtered].sort((a, b) => {
      const av = normalizeValue(a?.[sortKey]);
      const bv = normalizeValue(b?.[sortKey]);

      if (typeof av === 'number' && typeof bv === 'number') {
        return direction === 'asc' ? av - bv : bv - av;
      }

      const result = String(av).localeCompare(String(bv), 'es', {
        numeric: true,
        sensitivity: 'base'
      });

      return direction === 'asc' ? result : -result;
    });
  }, [analysisDisplayData, inventorySearchTerm, inventorySortConfig, agruparProductosAnalisis]);

  const inventoryVisibleColumns = useMemo(() => {
    const rows = Array.isArray(inventoryVisibleData) ? inventoryVisibleData : [];
    const preferred = [
      'Agrupacion',
      'codigo_producto',
      'nombre_producto',
      'unidad',
      'Items',
      'Inv_Inicial_Cantidad',
      'Movimientos',
      'Ventas',
      'Inv_Teorico_Cantidad',
      'Inv_Final_Cantidad',
      'Diferencia_Cantidad',
      'Diferencia_Costo'
    ];
    const found = new Set();

    rows.forEach((row) => {
      Object.keys(row || {}).forEach((key) => {
        if (!shouldShowAnalisisColumn(key)) return;
        if (!mostrarCostos && key.toLowerCase().includes('costo')) return;
        found.add(key);
      });
    });

    return [
      ...preferred.filter((key) => found.has(key)),
      ...Array.from(found).filter((key) => !preferred.includes(key))
    ];
  }, [inventoryVisibleData, mostrarCostos]);

  const selectedCategoriaSet = useMemo(
    () => new Set(selectedCategorias.map(String)),
    [selectedCategorias]
  );

  const selectedFamiliaSet = useMemo(
    () => new Set(selectedFamilias.map(String)),
    [selectedFamilias]
  );

  const familiasDisponibles = useMemo(() => {
    if (selectedCategoriaSet.size === 0) {
      return filterOptions.familias;
    }

    return filterOptions.familias.filter((familia) => (
      !familia.parent || selectedCategoriaSet.has(String(familia.parent))
    ));
  }, [filterOptions.familias, selectedCategoriaSet]);

  const subfamiliasDisponibles = useMemo(() => {
    if (selectedFamiliaSet.size > 0) {
      return filterOptions.subfamilias.filter((subfamilia) => (
        !subfamilia.parent || selectedFamiliaSet.has(String(subfamilia.parent))
      ));
    }

    if (selectedCategoriaSet.size === 0) {
      return filterOptions.subfamilias;
    }

    const familiasPermitidas = new Set(familiasDisponibles.map((familia) => String(familia.id)));
    return filterOptions.subfamilias.filter((subfamilia) => (
      !subfamilia.parent || familiasPermitidas.has(String(subfamilia.parent))
    ));
  }, [filterOptions.subfamilias, familiasDisponibles, selectedCategoriaSet, selectedFamiliaSet]);

  const pruneSelectionToOptions = useCallback((selected, options) => {
    const validIds = new Set(options.map((option) => String(option.id)));
    return selected.map(String).filter((id) => validIds.has(id));
  }, []);

  useEffect(() => {
    const prunedCategorias = pruneSelectionToOptions(selectedCategorias, filterOptions.categorias);
    if (prunedCategorias.length !== selectedCategorias.length || prunedCategorias.some((id, index) => id !== String(selectedCategorias[index]))) {
      setSelectedCategorias(prunedCategorias);
    }
  }, [filterOptions.categorias, pruneSelectionToOptions, selectedCategorias]);

  useEffect(() => {
    const prunedFamilias = pruneSelectionToOptions(selectedFamilias, familiasDisponibles);
    if (prunedFamilias.length !== selectedFamilias.length || prunedFamilias.some((id, index) => id !== String(selectedFamilias[index]))) {
      setSelectedFamilias(prunedFamilias);
    }
  }, [familiasDisponibles, pruneSelectionToOptions, selectedFamilias]);

  useEffect(() => {
    const prunedSubfamilias = pruneSelectionToOptions(selectedSubfamilias, subfamiliasDisponibles);
    if (prunedSubfamilias.length !== selectedSubfamilias.length || prunedSubfamilias.some((id, index) => id !== String(selectedSubfamilias[index]))) {
      setSelectedSubfamilias(prunedSubfamilias);
    }
  }, [pruneSelectionToOptions, selectedSubfamilias, subfamiliasDisponibles]);


  // EDARSAHUB-PATCH-ANALISIS-EXPORTS-V3
  const getAnalisisVistaRows = () => {
    if (filters.query_type !== 'analisis') {
      return Array.isArray(analysisDisplayData) ? analysisDisplayData : [];
    }

    return (Array.isArray(reportData) ? reportData : []).map(buildConvertedAnalisisRow);
  };

  const getAnalisisDiferenciaQty = (row) => {
    const value =
      row?.DIFERENCIA_QTY ??
      row?.Diferencia_Cantidad ??
      row?.DiferenciaCantidad ??
      row?.diferencia ??
      0;

    const num = parseFloat(value);
    return Number.isFinite(num) ? num : 0;
  };

  const getAnalisisDiferenciaValor = (row) => {
    const value =
      row?.DIFERENCIA_VALOR ??
      row?.Diferencia_Costo ??
      row?.DiferenciaCosto ??
      row?.importe_diferencia ??
      0;

    const num = parseFloat(value);
    return Number.isFinite(num) ? num : 0;
  };

  const handleGenerateReport = async () => {
    if (!filters.server_id) {
      toast.error('Selecciona una unidad de negocio');
      return;
    }

    const reportQueryType = normalizeReportQueryType(filters.query_type);
    if (reportQueryType !== filters.query_type) {
      setFilters(prev => ({
        ...prev,
        query_type: reportQueryType
      }));
    }

    if (reportQueryType === 'pendientes') {
      toast.info('Los insumos pendientes se cargan automáticamente');
      return;
    }

    // Validar campos requeridos para análisis completo
    if (reportQueryType === 'analisis') {
      if (!filters.sucursal) {
        toast.error('Selecciona una sucursal');
        return;
      }
      if (selectedAlmacenes.length === 0) {
        toast.error('Selecciona al menos un almacén');
        return;
      }
      if (!filters.fecha_ini || !filters.fecha_fin) {
        toast.error('Selecciona fechas de inicio y fin');
        return;
      }
      // Validar inventarios (multi o single)
      const hasInvIni = selectedInventariosIni.length > 0 || filters.inventario_inicial;
      const hasInvFin = selectedInventariosFin.length > 0 || filters.inventario_final;
      if (!hasInvIni || !hasInvFin) {
        toast.error('Selecciona inventario(s) inicial(es) y final(es)');
        return;
      }

      const inventariosIniValidacion = selectedInventariosIni.length > 0
        ? selectedInventariosIni
        : inventarios.filter((inv) => String(inv.folio) === String(filters.inventario_inicial));
      const inventariosFinValidacion = selectedInventariosFin.length > 0
        ? selectedInventariosFin
        : inventarios.filter((inv) => String(inv.folio) === String(filters.inventario_final));
      const foliosIniValidacion = new Set(
        (selectedInventariosIni.length > 0 ? selectedInventariosIni.map((inv) => inv.folio) : [filters.inventario_inicial])
          .filter(Boolean)
          .map(String)
      );
      const foliosFinValidacion = (selectedInventariosFin.length > 0 ? selectedInventariosFin.map((inv) => inv.folio) : [filters.inventario_final])
        .filter(Boolean)
        .map(String);

      if (foliosFinValidacion.some((folio) => foliosIniValidacion.has(folio))) {
        toast.error('Un mismo inventario no puede ser inicial y final al mismo tiempo');
        return;
      }

      if (!validarInventariosFinales(inventariosFinValidacion, inventariosIniValidacion)) {
        toast.error('El inventario final debe ser posterior al inventario inicial');
        return;
      }
    }

    setLoading(true);
    try {
      let response;

      // Obtener folios de inventarios (multi-select o single)
      const foliosIniciales = selectedInventariosIni.length > 0
        ? selectedInventariosIni.map(i => i.folio)
        : [filters.inventario_inicial];
      const foliosFinales = selectedInventariosFin.length > 0
        ? selectedInventariosFin.map(i => i.folio)
        : [filters.inventario_final];

      // Log para debugging
      logger.log('Filtros a enviar:', {
        categorias: selectedCategorias,
        familias: selectedFamilias,
        subfamilias: selectedSubfamilias,
        folios_iniciales: foliosIniciales,
        folios_finales: foliosFinales
      });

      // Preparar info de inventarios para MPRO (folio + comentario + almacen_id para el cache)
      const inventariosIniInfo = selectedInventariosIni.map(i => ({
        folio: i.folio,
        comentario: i.comentario || '',
        almacen_id: i.almacen_id || '',
        fecha: i.fecha || ''
      }));
      const inventariosFinInfo = selectedInventariosFin.map(i => ({
        folio: i.folio,
        comentario: i.comentario || '',
        almacen_id: i.almacen_id || '',
        fecha: i.fecha || ''
      }));

      // Llamar al endpoint de análisis completo con filtros adicionales
      const almacenesAnalisis = selectedAlmacenes
        .map((a) => {
          const almacenId = String(a.almacen_id ?? a.id ?? '').trim();
          const almacenNombre = String(a.nombre ?? a.almacen ?? a.Al_Descripcion ?? a.label ?? '').trim();
          return {
            id: almacenId,
            almacen_id: almacenId,
            nombre: almacenNombre,
            almacen: almacenNombre
          };
        })
        .filter((a) => a.almacen_id || a.nombre);

      response = await api.post('/reports/inventory-analysis', {
        server_id: String(filters.server_id || '').trim(),
        sucursal_id: filters.sucursal_id,
        sucursal: filters.sucursal,
        almacen: filters.almacen,
        almacenes: almacenesAnalisis.length > 0 ? almacenesAnalisis : undefined,
        fecha_ini: filters.fecha_ini,
        fecha_fin: filters.fecha_fin,
        folio_inicial: foliosIniciales.length === 1 ? foliosIniciales[0] : undefined,
        folio_final: foliosFinales.length === 1 ? foliosFinales[0] : undefined,
        folios_iniciales: foliosIniciales.length > 1 ? foliosIniciales : undefined,
        folios_finales: foliosFinales.length > 1 ? foliosFinales : undefined,
        // Info completa de inventarios para MPRO
        inventarios_iniciales_info: inventariosIniInfo,
        inventarios_finales_info: inventariosFinInfo,
        // Opción de agrupación
        agrupar_insumos: agruparInsumos,
        // Filtros adicionales
        categorias: selectedCategorias,
        familias: selectedFamilias,
        subfamilias: selectedSubfamilias
      }, {
        timeout: 120000
      });
      
      logger.log('Respuesta del reporte:', response.data);

      const rawRows = Array.isArray(response.data?.data)
        ? response.data.data
        : Array.isArray(response.data?.results)
          ? response.data.results
          : Array.isArray(response.data?.reportData)
            ? response.data.reportData
            : [];

      const toNumber = (value) => {
        const n = Number(value ?? 0);
        return Number.isFinite(n) ? n : 0;
      };

      const canonicalRows = rawRows.map(row => {
        const codigo = String(
          row.codigo_producto ??
          row.codigo ??
          row.Codigo ??
          row.CODIGO ??
          ''
        ).trim();

        const nombre = String(
          row.nombre_producto ??
          row.Producto ??
          row.nombre ??
          row.Nombre ??
          row.descripcion ??
          row.Descripcion ??
          row.DESCRIPCION ??
          codigo
        ).trim();

        const unidad = String(
          row.unidad ??
          row.Unidad ??
          row.UNIDAD ??
          ''
        ).trim();

        const inventarioInicial = toNumber(
          row.inventario_inicial ??
          row.Inv_Inicial_Cantidad ??
          row.inv_inicial ??
          row.Inventario_Inicial ??
          row.INV_INICIAL
        );

        const movimientos = toNumber(
          row.movimientos ??
          row.Movimientos ??
          row.MOVIMIENTOS
        );

        const ventas = toNumber(
          row.ventas ??
          row.Ventas ??
          row.VENTAS
        );

        const inventarioTeorico = toNumber(
          row.inventario_teorico ??
          row.Inv_Teorico_Cantidad ??
          row.inv_teorico ??
          row.Inventario_Teorico ??
          row.INV_TEORICO ??
          (inventarioInicial + movimientos - ventas)
        );

        const inventarioFinal = toNumber(
          row.inventario_final ??
          row.Inv_Final_Cantidad ??
          row.inv_final ??
          row.Inventario_Final ??
          row.INV_FINAL
        );

        const diferencia = toNumber(
          row.diferencia ??
          row.Diferencia_Cantidad ??
          row.Diferencia ??
          row.DIFERENCIA ??
          (inventarioFinal - inventarioTeorico)
        );

        const costoUnitario = toNumber(
          row.costo_unitario ??
          row.Costo_Unitario ??
          row.COSTO_UNITARIO
        );

        const diferenciaCosto = toNumber(
          row.diferencia_costo ??
          row.Diferencia_Costo ??
          row.DIFERENCIA_COSTO ??
          (diferencia * costoUnitario)
        );

        return {
          Categoria: row.Categoria ?? row.categoria ?? '',
          Familia: row.Familia ?? row.familia ?? '',
          SubFamilia: row.SubFamilia ?? row.subfamilia ?? '',
          codigo_producto: codigo,
          nombre_producto: nombre,
          unidad: unidad,
          inventario_inicial: inventarioInicial,
          movimientos: movimientos,
          ventas: ventas,
          inventario_teorico: inventarioTeorico,
          inventario_final: inventarioFinal,
          diferencia: diferencia,
          costo_unitario: costoUnitario,
          diferencia_costo: diferenciaCosto,
          Rendimiento: row.Rendimiento ?? row.rendimiento ?? 1,
          tipo_almacen: row.tipo_almacen ?? row.tipoAlmacen ?? row.almacen_tipo ?? row.tipo
        };
      });

      const groupedRowsMap = new Map();

      canonicalRows.forEach(row => {
        const key = `${row.nombre_producto}|${row.unidad}`;

        if (!groupedRowsMap.has(key)) {
          groupedRowsMap.set(key, { ...row });
          return;
        }

        const current = groupedRowsMap.get(key);

        current.inventario_inicial += row.inventario_inicial;
        current.movimientos += row.movimientos;
        current.ventas += row.ventas;
        current.inventario_teorico += row.inventario_teorico;
        current.inventario_final += row.inventario_final;
        current.diferencia += row.diferencia;
        current.diferencia_costo += row.diferencia_costo;

        if (row.codigo_producto && !current.codigo_producto.includes(row.codigo_producto)) {
          current.codigo_producto = `${current.codigo_producto}, ${row.codigo_producto}`;
        }
      });

      const finalRows = agruparInsumos
        ? Array.from(groupedRowsMap.values())
        : canonicalRows;

      const roundedRows = finalRows.map(row => {
        const costoUnitarioFinal =
          Math.abs(row.diferencia) > 0.000001
            ? row.diferencia_costo / row.diferencia
            : row.costo_unitario;

        return {
          Categoria: row.Categoria,
          Familia: row.Familia,
          SubFamilia: row.SubFamilia,
          codigo_producto: row.codigo_producto,
          nombre_producto: row.nombre_producto,
          unidad: row.unidad,
          inventario_inicial: Number(row.inventario_inicial.toFixed(6)),
          movimientos: Number(row.movimientos.toFixed(6)),
          ventas: Number(row.ventas.toFixed(6)),
          inventario_teorico: Number(row.inventario_teorico.toFixed(6)),
          inventario_final: Number(row.inventario_final.toFixed(6)),
          diferencia: Number(row.diferencia.toFixed(6)),
          costo_unitario: Number(costoUnitarioFinal.toFixed(6)),
          diferencia_costo: Number(row.diferencia_costo.toFixed(6)),
          Rendimiento: row.Rendimiento,
          tipo_almacen: row.tipo_almacen
        };
      });

      const responseCount =
        response.data?.count ??
        response.data?.metadata?.total_productos ??
        response.data?.resumen?.total_productos ??
        roundedRows.length;

      logger.log('Primer producto normalizado:', roundedRows[0] || null);
      setReportData(roundedRows);
      
      // Manejar errores de captura de inventario (MPRO)
      if (response.data?.errores_captura && response.data.errores_captura.length > 0) {
        setErroresCaptura(response.data.errores_captura);
        toast.warning(`Atención: ${response.data.errores_captura.length} error(es) de captura detectados`);
      } else {
        setErroresCaptura([]);
      }
      
      toast.success(`Reporte generado: ${responseCount} registros`);
    } catch (error) {
      const errorData = error.response?.data || {};
      const errorMessage =
        errorData.message ||
        errorData.detail?.message ||
        (typeof errorData.detail === 'string' ? errorData.detail : null) ||
        error.message ||
        'Error al generar reporte';

      const errorCode = errorData.error || errorData.detail?.code;

      if (errorCode === 'INVENTORY_PHYSICAL_DETAIL_MISSING') {
        setReportData([]);
        setErroresCaptura([]);
        toast.error(errorMessage, { duration: 10000 });
      } else {
        toast.error(errorMessage, { duration: 8000 });
      }
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
      // Para MPRO: movimientos y ventas inician 1 dia despues del inventario inicial.
      const fechaInicialDate = parseDateString(inicialFecha);
      if (fechaInicialDate) {
        fechaInicialDate.setDate(fechaInicialDate.getDate() + 1);
        const pad = (n) => String(n).padStart(2, '0');
        fecha_ini = `${fechaInicialDate.getFullYear()}-${pad(fechaInicialDate.getMonth() + 1)}-${pad(fechaInicialDate.getDate())}`;
      } else {
        fecha_ini = String(inicialFecha).split(/[T\s]/)[0];
      }
      fecha_fin = String(finalFecha).split(/[T\s]/)[0];
    } else if (systemType === 'SoftRestaurant') {
      // Para SoftRestaurant: fecha inicial + 1 segundo, fecha final - 1 segundo
      const fechaInicialDate = parseDateString(inicialFecha);
      const fechaFinalDate = parseDateString(finalFecha);
      
      logger.log('Fechas parseadas (hora local):', {
        original_ini: inicialFecha,
        original_fin: finalFecha,
        parsed_ini: fechaInicialDate?.toString(),
        parsed_fin: fechaFinalDate?.toString()
      });
      
      if (!fechaInicialDate || !fechaFinalDate) {
        logger.error('Error parseando fechas:', { inicialFecha, finalFecha });
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

    logger.log('Fechas calculadas FINAL:', { inicialFecha, finalFecha, fecha_ini, fecha_fin, systemType });
    return { fecha_ini, fecha_fin };
  };

  const handleInventarioInicialChange = (value) => {
    const inventario = inventarios.find(inv => inv.folio === value);
    const nuevaFechaInicial = inventario?.fecha || '';
    
    logger.log('Inventario inicial seleccionado:', { value, fecha: nuevaFechaInicial, inventario });
    
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
    
    logger.log('Inventario final seleccionado:', { value, fecha: nuevaFechaFinal, inventario });
    
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
    const exportRows = getAnalisisVistaRows();
    logger.log('handleExportExcel llamado, exportRows:', exportRows.length);
    if (exportRows.length === 0) {
      toast.error('No hay datos para exportar');
      return;
    }

    try {
      toast.info('Generando archivo Excel...');
      
      // Obtener nombre del servidor seleccionado
      const selectedServer = servers.find(s => s.id === filters.server_id);
      const serverName = selectedServer ? selectedServer.name : 'N/A';
      
      // === FILTRADO DE COLUMNAS DE COSTO SEGÚN CHECKBOX ===
      // Lista explícita de columnas de costo GENERALES a excluir cuando mostrarCostos = false
      // NOTA: Diferencia_Costo se CONSERVA siempre (es el costo de la diferencia QTY)
      const COLUMNAS_COSTO_EXCLUIR = [
        'Costo_Unitario',
        'Inv_Inicial_Costo',
        'Movimientos_Costo',
        'Ventas_Costo',
        'Inv_Teorico_Costo',
        'Inv_Final_Costo'
      ];
      
      // Crear copia filtrada para exportación (no modifica reportData original)
      const dataParaExportar = mostrarCostos 
        ? exportRows 
        : exportRows.map(row => {
            const rowFiltrada = {};
            Object.entries(row).forEach(([key, value]) => {
              // Solo excluir las columnas de la lista explícita
              if (!COLUMNAS_COSTO_EXCLUIR.includes(key)) {
                rowFiltrada[key] = value;
              }
            });
            return rowFiltrada;
          });
      
      // Llamar al backend para generar el Excel con formato profesional
      const response = await api.post('/reports/export/excel', {
        data: dataParaExportar,
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
      if (link && link.parentNode) { link.parentNode.removeChild(link); }
      window.URL.revokeObjectURL(url);
      
      toast.success(`Archivo "${fileName}" descargado correctamente.`);
    } catch (error) {
      logger.error('Error al exportar Excel:', error);
      toast.error('Error al exportar a Excel: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleExportPDF = () => {
    const exportRows = getAnalisisVistaRows();
    logger.log('handleExportPDF llamado, exportRows:', exportRows.length);
    if (exportRows.length === 0) {
      toast.error('No hay datos para exportar');
      return;
    }

    try {
      logger.log('Creando documento PDF...');
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
      
      logger.log('Preparando datos para tabla...');
      const data = exportRows.map(row => columns.map(col => {
        const val = row[col];
        if (typeof val === 'number') return val.toLocaleString('es-MX', { maximumFractionDigits: 2 });
        return val || '';
      }));
      
      logger.log('Generando tabla autoTable...');
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
      logger.log('Guardando PDF:', fileName);
      
      // Método alternativo: crear blob y descargar
      const pdfBlob = doc.output('blob');
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      if (link && link.parentNode) { link.parentNode.removeChild(link); }
      window.URL.revokeObjectURL(url);
      
      toast.success(`Archivo "${fileName}" descargado correctamente.`);
    } catch (error) {
      logger.error('Error al exportar PDF:', error);
      toast.error('Error al exportar a PDF: ' + error.message);
    }
  };

  // Exportar comparativo de últimos 4 cortes de inventario (Auditoría)
  const handleExportComparativo4Cortes = async () => {
    // Validar que tengamos los filtros necesarios
    if (!filters.server_id) {
      toast.error('Selecciona una unidad de negocio primero');
      return;
    }
    
    // Validar que haya almacenes seleccionados
    if (selectedAlmacenes.length === 0) {
      toast.error('Selecciona al menos un almacén para generar el comparativo');
      return;
    }
    
    try {
      setLoadingComparativo(true);
      
      // Construir lista de almacenes con sus comentarios
      // Para MPRO: cada almacén puede tener un comentario específico del inventario seleccionado
      const almacenesParaComparativo = selectedAlmacenes.map(almacen => {
        // Buscar si hay inventarios iniciales seleccionados para este almacén
        const invIniDeEsteAlmacen = selectedInventariosIni.find(inv => 
          (inv.almacen_id === almacen.id || inv.almacen_id === almacen.Al_Cve_Almacen) ||
          (inv.almacen === almacen.nombre || inv.almacen === almacen.Al_Descripcion)
        );
        
        return {
          id: almacen.id || almacen.Al_Cve_Almacen || '',
          nombre: almacen.nombre || almacen.Al_Descripcion || 'Almacen',
          comentario: invIniDeEsteAlmacen?.comentario || null
        };
      });
      
      // Mensaje informativo
      const almacenesMsg = almacenesParaComparativo.length === 1 
        ? almacenesParaComparativo[0].nombre + (almacenesParaComparativo[0].comentario ? ` (${almacenesParaComparativo[0].comentario})` : '')
        : `${almacenesParaComparativo.length} almacenes`;
      
      toast.info(`Generando comparativo: ${almacenesMsg}...`);
      
      // Usar fecha actual si no hay fecha seleccionada
      const fechaReferencia = filters.fecha_fin || new Date().toISOString().split('T')[0];
      
      const response = await api.post('/reports/export/comparativo-inventarios', {
        server_id: String(filters.server_id || '').trim(),
        sucursal_id: filters.sucursal_id || '',
        sucursal_nombre: filters.sucursal || '',
        almacenes: almacenesParaComparativo,
        fecha_referencia: fechaReferencia,
        categorias: selectedCategorias.length > 0 ? selectedCategorias : null
      }, {
        responseType: 'blob',
        validateStatus: function (status) {
          return status < 500; // Aceptar todas las respuestas que no sean 5xx
        }
      });
      
      // Verificar si la respuesta es un error (4xx)
      if (response.status >= 400) {
        // Leer el blob como texto para extraer el mensaje de error
        const text = await response.data.text();
        try {
          const json = JSON.parse(text);
          toast.error(json.detail || 'Error al generar el comparativo', { duration: 8000 });
        } catch {
          toast.error(text || 'Error al generar el comparativo', { duration: 8000 });
        }
        return;
      }
      
      // Descargar el archivo (respuesta exitosa)
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `comparativo_4cortes_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      if (link && link.parentNode) { link.parentNode.removeChild(link); }
      window.URL.revokeObjectURL(url);
      
      toast.success('Reporte comparativo descargado correctamente (desde cache)');
    } catch (error) {
      logger.error('Error al exportar comparativo:', error);
      toast.error(error.message || 'Error de conexión al servidor', { duration: 5000 });
    } finally {
      setLoadingComparativo(false);
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

  // Doble clic: detalle CANÓNICO de movimientos (hook + componente compartido con Auditoría).
  // Usa los endpoints canónicos /compras/detalle-movimientos (aceptan unidad o server_id legacy).
  const loadMovementDetails = (producto) => {
    const codigo = producto.Codigo ?? producto.codigo_producto ?? producto.codigo ?? producto.CODIGO;
    const nombre = producto.Producto ?? producto.nombre_producto ?? producto.nombre ?? producto.Nombre ?? codigo;

    abrirMovimientos({
      serverId: filters.server_id,
      sucursal: filters.sucursal,
      codigo,
      producto: nombre,
      fechaInicio: filters.fecha_ini,
      fechaFin: filters.fecha_fin,
      almacenes: selectedAlmacenes.length > 0 ? selectedAlmacenes.map(a => a.id || a.almacen_id || a.nombre) : filters.almacen,
    });
  };

  // Doble clic: detalle CANÓNICO de ventas/consumos (hook + componente compartido con Auditoría).
  const loadSalesDetails = (producto) => {
    const codigo = producto.Codigo ?? producto.codigo_producto ?? producto.codigo ?? producto.CODIGO;
    const nombre = producto.Producto ?? producto.nombre_producto ?? producto.nombre ?? producto.Nombre ?? codigo;
    let fechaInicioDetalle = filters.fecha_ini;
    let fechaFinDetalle = filters.fecha_fin;

    if (selectedServer?.system_type === 'SoftRestaurant') {
      const fechaInicialVentas = parseDateString(selectedInventariosIni[0]?.fecha || filters.inventario_inicial_fecha);
      const fechaFinalVentas = parseDateString(selectedInventariosFin[0]?.fecha || filters.inventario_final_fecha);

      if (fechaInicialVentas && fechaFinalVentas) {
        fechaInicialVentas.setHours(0, 0, 0, 0);
        fechaFinalVentas.setHours(0, 0, 0, 0);
        fechaFinalVentas.setSeconds(fechaFinalVentas.getSeconds() - 1);
        fechaInicioDetalle = formatDateForSQL(fechaInicialVentas);
        fechaFinDetalle = formatDateForSQL(fechaFinalVentas);
      }
    }

    abrirConsumos({
      serverId: filters.server_id,
      sucursal: filters.sucursal,
      codigo,
      producto: nombre,
      fechaInicio: fechaInicioDetalle,
      fechaFin: fechaFinDetalle,
      almacenes: selectedAlmacenes.length > 0 ? selectedAlmacenes.map(a => a.id || a.almacen_id || a.nombre) : filters.almacen,
    });
  };

  const loadRecipeUsageDetails = async (producto) => {
    const productoInfo = getProductoAgrupacionAnalisis(producto);
    const codigo = productoInfo.codigo;
    const nombre = productoInfo.producto || codigo;
    const unidad = productoInfo.unidad;
    const rendimiento = getAnalisisRendimiento(producto);

    if (!codigo) {
      toast.error('No hay código para consultar la receta inversa');
      return;
    }

    setUsoRecetaDetalle({
      open: true,
      loading: true,
      codigo,
      producto: nombre,
      data: null,
      error: null
    });

    try {
      const response = await api.post(
        '/reports/inverse-recipe-usage',
        {
          server_id: String(filters.server_id || '').trim(),
          codigo,
          producto: nombre,
          unidad,
          rendimiento,
          unidad_vista: unidadAnalisisInventarios
        },
        { timeout: 30000 }
      );

      setUsoRecetaDetalle((prev) => ({
        ...prev,
        loading: false,
        data: response.data,
        error: null
      }));
    } catch (error) {
      logger.error('[Reportes] Error uso inverso de receta:', error);
      setUsoRecetaDetalle((prev) => ({
        ...prev,
        loading: false,
        data: null,
        error: error.response?.data?.detail || 'Error al obtener uso en recetas'
      }));
    }
  };

  const closeRecipeUsageDetails = () => {
    setUsoRecetaDetalle({
      open: false,
      loading: false,
      codigo: '',
      producto: '',
      data: null,
      error: null
    });
  };

  // Cerrar modal (alias canónico)
  const closeDetailModal = cerrarDetalleProducto;

  return (
    <div className="space-y-6" data-testid="reportes-page">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-zinc-800">
          Operaciones
        </h1>
        <p className="text-sm text-zinc-500">Gestión operativa y análisis de inventarios</p>
      </div>

      {/* Tabs de Operaciones */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 mb-4">
          <TabsTrigger value="operativo" className="flex items-center gap-2" data-testid="tab-operativo">
            <Activity className="h-4 w-4" />
            Dashboard Operativo
          </TabsTrigger>
          <TabsTrigger value="dashboard" className="flex items-center gap-2" data-testid="tab-dashboard">
            <LayoutDashboard className="h-4 w-4" />
            Métricas
          </TabsTrigger>
          <TabsTrigger value="analisis" className="flex items-center gap-2" data-testid="tab-analisis">
            <ClipboardList className="h-4 w-4" />
            Análisis
          </TabsTrigger>
          <TabsTrigger value="informes" className="flex items-center gap-2" data-testid="tab-informes">
            <FolderOpen className="h-4 w-4" />
            Informes
          </TabsTrigger>
        </TabsList>

        {/* Tab: Dashboard Operativo (Fase 2A) */}
        <TabsContent value="operativo">
          <OperativoDashboard />
        </TabsContent>

        {/* Tab: Métricas de Inventarios */}
        <TabsContent value="dashboard">
          <DashboardInventarios />
        </TabsContent>

        {/* Tab: Análisis de Inventarios */}
        <TabsContent value="analisis">
          {/* Filters */}
          <Card className="border border-zinc-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-semibold">Filtros</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* FASE 3.2: Selector de Unidad de Negocio */}
                <div className="space-y-2">
                  <Label>Unidad de Negocio {loadingUnidades && <span className="text-zinc-500 text-xs">(Cargando...)</span>}</Label>
                  {unidadesNegocio.length === 1 ? (
                    <div className="flex h-10 w-full items-center rounded-md border border-zinc-300 bg-zinc-50 px-3 py-2 text-sm">
                      <Building2 className="h-4 w-4 mr-2 text-zinc-500" />
                      {unidadesNegocio[0].nombre}
                    </div>
                  ) : (
                    <select 
                      className={selectStyle}
                      data-testid="unidad-negocio-select"
                      value={selectedUnidad}
                      onChange={(e) => {
                        const unidadId = e.target.value;
                        setSelectedUnidad(unidadId);
                        const unidad = unidadesNegocio.find(u => u.id === unidadId);
                        if (unidad) {
                          const unidadServerId = String(unidad.server_id || '').trim();
                          // Establecer el servidor seleccionado
                          const newServer = {
                            id: unidadServerId,
                            name: unidad.nombre,
                            system_type: unidad.system_type,
                            sucursal_origen_id: unidad.sucursal_origen_id
                          };
                          setSelectedServer(newServer);
                          
                          // Si tiene sucursal_origen_id (MPRO con sucursal auto-definida), auto-seleccionar
                          if (unidad.sucursal_origen_id && unidad.system_type === 'MPRO') {
                            // Obtener el nombre de la sucursal desde el array de sucursales
                            const nombreSucursal = unidad.sucursales?.[0]?.nombre || unidad.nombre;
                            setFilters({
                              ...filters, 
                              unidad_id: unidadId,
                              server_id: unidadServerId,
                              sucursal_id: unidad.sucursal_origen_id, 
                              sucursal: nombreSucursal, // Nombre real de sucursal para queries SQL LIKE
                              almacen_id: '', 
                              almacen: ''
                            });
                          } else {
                            setFilters({
                              ...filters, 
                              unidad_id: unidadId,
                              server_id: unidadServerId,
                              sucursal_id: '', 
                              almacen_id: '', 
                              sucursal: '', 
                              almacen: ''
                            });
                          }
                        } else {
                          setFilters({...filters, unidad_id: '', server_id: '', sucursal_id: '', almacen_id: '', sucursal: '', almacen: ''});
                          setSelectedServer(null);
                        }
                      }}
                      disabled={loadingUnidades}
                    >
                      <option value="">{loadingUnidades ? "Cargando..." : "Selecciona una unidad"}</option>
                      {unidadesNegocio.map((unidad) => (
                        <option key={unidad.id} value={unidad.id}>
                          {unidad.nombre} ({unidad.system_type})
                        </option>
                      ))}
                    </select>
                  )}
                </div>

            <div className="space-y-2">
              <Label>Tipo de Consulta</Label>
              <select 
                className={selectStyle}
                data-testid="query-type-select"
                value={normalizeReportQueryType(filters.query_type)}
                onChange={(e) => setFilters({...filters, query_type: normalizeReportQueryType(e.target.value)})}
              >
                <option value="analisis">Análisis de Inventarios</option>
                {selectedServer?.system_type === 'SoftRestaurant' && (
                  <option value="pendientes">Insumos Pendientes de Descargar</option>
                )}
              </select>
            </div>

            {/* Sucursal - Solo mostrar si NO es SoftRestaurant y NO tiene sucursal_origen_id (auto-resolución) y hay múltiples */}
            {selectedServer?.system_type !== 'SoftRestaurant' && 
             !selectedServer?.sucursal_origen_id && 
             sucursales.length > 1 && (
              <div className="space-y-2">
                <Label>Sucursal</Label>
                <select 
                  className={selectStyle}
                  data-testid="sucursal-select"
                  value={filters.sucursal_id}
                  onChange={(e) => handleSucursalChange(e.target.value)}
                  disabled={!selectedUnidad || sucursales.length === 0}
                >
                  <option value="">{!selectedUnidad ? "Selecciona unidad primero" : "Selecciona una sucursal"}</option>
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
                    {getAlmacenPlaceholder(selectedAlmacenes, selectedServer, selectedUnidad, almacenes, filters)}
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
                        <span className="text-sm">{almacen.nombre} {getAlmacenTipoText(almacen.tipo)}</span>
                      </label>
                    ))}
                    {almacenes.length === 0 && (
                      <p className="text-xs text-zinc-400 text-center py-2">No hay almacenes disponibles</p>
                    )}
                  </div>
                </div>
              </details>
              {/* Badges de almacenes seleccionados */}
              {selectedAlmacenes.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedAlmacenes.map(alm => (
                    <span key={alm.id} className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                      {alm.nombre}
                      <X 
                        className="h-3 w-3 cursor-pointer hover:text-blue-900" 
                        onClick={() => {
                          const newSelected = selectedAlmacenes.filter(a => a.id !== alm.id);
                          setSelectedAlmacenes(newSelected);
                          setSelectedInventariosIni([]);
                          setSelectedInventariosFin([]);
                          if (newSelected.length === 0) {
                            setFilters({...filters, almacen_id: '', almacen: '', inventario_inicial: '', inventario_final: ''});
                          }
                        }}
                      />
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label>Inventario Inicial (multi-selección)</Label>
              <div className="relative" data-dropdown-inv="ini">
                <div 
                  className={`${selectStyle} cursor-pointer flex items-center justify-between ${selectedAlmacenes.length === 0 ? 'opacity-50 pointer-events-none' : ''}`}
                  onClick={() => selectedAlmacenes.length > 0 && setDropdownInvIni(!dropdownInvIni)}
                >
                  <span className="truncate">
                    {selectedAlmacenes.length === 0 
                      ? "Selecciona almacén primero"
                      : selectedInventariosIni.length === 0 
                        ? "Selecciona inventarios iniciales" 
                        : `${selectedInventariosIni.length} inventario(s) seleccionado(s)`}
                  </span>
                  <ChevronDown className={`h-4 w-4 opacity-50 transition-transform ${dropdownInvIni ? 'rotate-180' : ''}`} />
                </div>
                {dropdownInvIni && selectedAlmacenes.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-white border border-zinc-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                    {/* Buscador */}
                    <div className="sticky top-0 bg-white border-b p-2">
                      <input
                        type="text"
                        placeholder="Buscar inventario..."
                        className="w-full px-2 py-1 text-sm border rounded"
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => {
                          const searchVal = e.target.value.toLowerCase();
                          document.querySelectorAll('[data-inv-inicial]').forEach(el => {
                            const text = el.getAttribute('data-inv-inicial').toLowerCase();
                            el.style.display = text.includes(searchVal) ? '' : 'none';
                          });
                        }}
                      />
                    </div>
                    {selectedInventariosIni.length > 0 && (
                      <button
                        type="button"
                        className="w-full px-3 py-2 text-xs text-left hover:bg-zinc-100 border-b flex items-center text-red-600"
                        onClick={(e) => { e.stopPropagation(); setSelectedInventariosIni([]); }}
                      >
                        <X className="h-3 w-3 mr-1" /> Limpiar selección ({selectedInventariosIni.length})
                      </button>
                    )}
                    {/* Filtrar por fecha: solo mostrar inventarios de la misma fecha que el primero seleccionado */}
                    {inventarios
                      .filter(inv => {
                        if (selectedInventariosIni.length === 0) return true;
                        const fechaBase = selectedInventariosIni[0].fecha?.split('T')[0] || selectedInventariosIni[0].fecha?.split(' ')[0];
                        const fechaInv = inv.fecha?.split('T')[0] || inv.fecha?.split(' ')[0];
                        return fechaBase === fechaInv;
                      })
                      .map((inv) => (
                      <label 
                        key={inv.folio} 
                        data-inv-inicial={`${inv.folio} ${inv.fecha || ''} ${inv.almacen || ''} ${inv.comentario || ''}`}
                        className="flex items-center space-x-2 py-2 px-3 hover:bg-zinc-50 cursor-pointer"
                        onClick={(e) => e.stopPropagation()}
                      >
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
                        <span className="text-sm">{inv.folio} - {inv.fecha ? inv.fecha.split(' ')[0] : ''} - {inv.almacen || ''}{inv.comentario ? ` - ${inv.comentario}` : ''}</span>
                      </label>
                    ))}
                    {inventarios.length === 0 && (
                      <p className="text-xs text-zinc-400 text-center py-3">No hay inventarios disponibles</p>
                    )}
                  </div>
                )}
              </div>
              {/* Badges de inventarios iniciales seleccionados */}
              {selectedInventariosIni.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedInventariosIni.map(inv => (
                    <span key={inv.folio} className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded-full">
                      {inv.folio} - {inv.fecha?.split(' ')[0] || ''}
                      <X 
                        className="h-3 w-3 cursor-pointer hover:text-green-900" 
                        onClick={() => setSelectedInventariosIni(selectedInventariosIni.filter(i => i.folio !== inv.folio))}
                      />
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label>Inventario Final (multi-selección)</Label>
              <div className="relative" data-dropdown-inv="fin">
                <div 
                  className={`${selectStyle} cursor-pointer flex items-center justify-between ${selectedAlmacenes.length === 0 ? 'opacity-50 pointer-events-none' : ''}`}
                  onClick={() => selectedAlmacenes.length > 0 && setDropdownInvFin(!dropdownInvFin)}
                >
                  <span className="truncate">
                    {selectedAlmacenes.length === 0 
                      ? "Selecciona almacén primero"
                      : selectedInventariosFin.length === 0 
                        ? "Selecciona inventarios finales" 
                        : `${selectedInventariosFin.length} inventario(s) seleccionado(s)`}
                  </span>
                  <ChevronDown className={`h-4 w-4 opacity-50 transition-transform ${dropdownInvFin ? 'rotate-180' : ''}`} />
                </div>
                {dropdownInvFin && selectedAlmacenes.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-white border border-zinc-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                    {/* Buscador */}
                    <div className="sticky top-0 bg-white border-b p-2">
                      <input
                        type="text"
                        placeholder="Buscar inventario..."
                        className="w-full px-2 py-1 text-sm border rounded"
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => {
                          const searchVal = e.target.value.toLowerCase();
                          document.querySelectorAll('[data-inv-final]').forEach(el => {
                            const text = el.getAttribute('data-inv-final').toLowerCase();
                            el.style.display = text.includes(searchVal) ? '' : 'none';
                          });
                        }}
                      />
                    </div>
                    {selectedInventariosFin.length > 0 && (
                      <button
                        type="button"
                        className="w-full px-3 py-2 text-xs text-left hover:bg-zinc-100 border-b flex items-center text-red-600"
                        onClick={(e) => { e.stopPropagation(); setSelectedInventariosFin([]); }}
                      >
                        <X className="h-3 w-3 mr-1" /> Limpiar selección ({selectedInventariosFin.length})
                      </button>
                    )}
                    {/* Info: mostrar fecha mínima cuando hay inventarios iniciales seleccionados */}
                    {fechaMinimaInvInicial && (
                      <div className="px-3 py-1 text-xs text-zinc-500 bg-blue-50 border-b">
                        Solo inventarios posteriores al inicial: {fechaMinimaInvInicial}
                      </div>
                    )}
                    {/* Filtrar: solo mostrar inventarios posteriores al inicial y nunca el mismo folio */}
                    {inventariosFinalesFiltrados
                      .filter(inv => {
                        // Filtro adicional: si ya hay finales seleccionados, filtrar por misma fecha
                        if (selectedInventariosFin.length === 0) return true;
                        const fechaBase = selectedInventariosFin[0].fecha?.split('T')[0] || selectedInventariosFin[0].fecha?.split(' ')[0];
                        const fechaInv = inv.fecha?.split('T')[0] || inv.fecha?.split(' ')[0];
                        return fechaBase === fechaInv;
                      })
                      .map((inv) => (
                      <label 
                        key={inv.folio} 
                        data-inv-final={`${inv.folio} ${inv.fecha || ''} ${inv.almacen || ''} ${inv.comentario || ''}`}
                        className="flex items-center space-x-2 py-2 px-3 hover:bg-zinc-50 cursor-pointer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <input
                          type="checkbox"
                          className="rounded border-zinc-300"
                          checked={selectedInventariosFin.some(i => i.folio === inv.folio)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              if (!validarInventariosFinales([inv])) {
                                toast.error('El inventario final debe ser posterior al inicial y no puede ser el mismo inventario');
                                return;
                              }
                              setSelectedInventariosFin([...selectedInventariosFin, inv]);
                            } else {
                              setSelectedInventariosFin(selectedInventariosFin.filter(i => i.folio !== inv.folio));
                            }
                          }}
                        />
                        <span className="text-sm">{inv.folio} - {inv.fecha ? inv.fecha.split(' ')[0] : ''} - {inv.almacen || ''}{inv.comentario ? ` - ${inv.comentario}` : ''}</span>
                      </label>
                    ))}
                    {inventariosFinalesFiltrados.length === 0 && (
                      <p className="text-xs text-zinc-400 text-center py-3">
                        {inventarios.length === 0 
                          ? "No hay inventarios disponibles" 
                          : "No hay inventarios con fecha posterior al inicial"}
                      </p>
                    )}
                  </div>
                )}
              </div>
              {/* Badges de inventarios finales seleccionados */}
              {selectedInventariosFin.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedInventariosFin.map(inv => (
                    <span key={inv.folio} className="inline-flex items-center gap-1 px-2 py-0.5 bg-orange-50 text-orange-700 text-xs rounded-full">
                      {inv.folio} - {inv.fecha?.split(' ')[0] || ''}
                      <X 
                        className="h-3 w-3 cursor-pointer hover:text-orange-900" 
                        onClick={() => setSelectedInventariosFin(selectedInventariosFin.filter(i => i.folio !== inv.folio))}
                      />
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Fechas en la misma fila */}
            <div className="space-y-2">
              <Label>
                Fecha Inicio de Movimientos
                {selectedServer && (
                  <span className="text-xs text-zinc-500 ml-2">
                    ({selectedServer.system_type === 'MPRO' ? 'Fecha inv. inicial + 1 dia' : 'Fecha inv. inicial + 1 seg'})
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

            {/* Opción de agrupar insumos - debajo de las fechas, solo visible con multi-inventario en MPRO */}
            {selectedServer?.system_type === 'MPRO' && (selectedInventariosIni.length > 1 || selectedInventariosFin.length > 1) && (
              <div className="col-span-2 flex items-center space-x-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <input
                  type="checkbox"
                  id="agrupar-insumos"
                  checked={agruparInsumos}
                  onChange={(e) => setAgruparInsumos(e.target.checked)}
                  className="rounded border-zinc-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="agrupar-insumos" className="text-sm text-blue-800 cursor-pointer">
                  <strong>Agrupar insumos</strong> - Suma cantidades de productos que aparecen en múltiples inventarios
                </label>
              </div>
            )}
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
                          ? (selectedServer?.system_type === 'SoftRestaurant' ? 'Todas las clasificaciones' : 'Todas las categorías')
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
                          ? (selectedServer?.system_type === 'SoftRestaurant' ? 'Todos los grupos' : 'Todas las familias')
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
                        {familiasDisponibles
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
                        {familiasDisponibles.filter(fam => fam.nombre.toLowerCase().includes(searchFamilias.toLowerCase())).length === 0 && (
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
                          ? (selectedServer?.system_type === 'SoftRestaurant' ? 'Todos los subgrupos' : 'Todas las subfamilias')
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
                        {subfamiliasDisponibles
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
                        {subfamiliasDisponibles.filter(sf => sf.nombre.toLowerCase().includes(searchSubfamilias.toLowerCase())).length === 0 && (
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

          {/* Ocultar botón para pendientes (se carga automáticamente) */}
          {filters.query_type !== 'pendientes' && (
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
              
              {/* Botón para exportar comparativo de últimos 4 cortes */}
              <Button 
                onClick={handleExportComparativo4Cortes}
                disabled={loadingComparativo || !filters.server_id || selectedAlmacenes.length === 0}
                variant="outline"
                className="border-emerald-500 text-emerald-700 hover:bg-emerald-50"
                data-testid="export-comparativo-4cortes-button"
                title={`Genera Excel comparativo de los últimos 4 inventarios para ${selectedAlmacenes.length} almacén(es). Usa cache para rapidez.`}
              >
                {loadingComparativo ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generando...
                  </>
                ) : (
                  <>
                    <FileSpreadsheet className="h-4 w-4 mr-2" />
                    Comparativo 4 Cortes
                    {selectedAlmacenes.length > 0 && (
                      <span className="ml-1 text-xs bg-emerald-100 px-1 rounded">
                        {selectedAlmacenes.length}
                      </span>
                    )}
                  </>
                )}
              </Button>
              
              {/* Botón Generar Informe de Auditoría */}
              {reportData.length > 0 && (
                <Button
                  variant="default"
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                  onClick={handleAbrirModalInforme}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Generar Informe
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      {reportData.length > 0 && (
        <div className="flex gap-2 items-center">
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
          
          {/* Toggle para mostrar/ocultar costos */}
          <div className="flex items-center gap-2 ml-4 border-l pl-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={mostrarCostos}
                onChange={(e) => setMostrarCostos(e.target.checked)}
                className="rounded border-zinc-300"
              />
              <span className="text-sm text-zinc-600">Ver costos</span>
            </label>
          </div>
        </div>
      )}

      {/* Results */}
      {reportData.length > 0 && (
        <Card className="border border-zinc-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold">Resultados</CardTitle>
              <div className="flex items-center gap-3">
                <span className="text-sm text-zinc-600">
                  Total: <span className="font-data font-semibold">{analysisDisplayData.length}</span> registros
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowFullscreenResultados(true)}
                  className="h-7 px-2"
                  title="Ver en pantalla completa"
                >
                  <Maximize2 className="h-4 w-4" />
                </Button>
              </div>
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
                    <li key={error.codigo || `error-${idx}`} className="list-disc">
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

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  margin: '12px 0',
                  flexWrap: 'wrap'
                }}
              >
                <input
                  type="text"
                  value={inventorySearchTerm}
                  onChange={(e) => setInventorySearchTerm(e.target.value)}
                  placeholder="Buscar por clave o nombre..."
                  style={{
                    minWidth: '320px',
                    maxWidth: '520px',
                    flex: '1',
                    padding: '10px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px',
                    fontSize: '14px'
                  }}
                />

                {inventorySearchTerm && (
                  <button
                    type="button"
                    onClick={() => setInventorySearchTerm('')}
                    style={{
                      padding: '9px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      background: '#ffffff',
                      cursor: 'pointer'
                    }}
                  >
                    Limpiar
                  </button>
                )}

                <span style={{ fontSize: '13px', color: '#6b7280' }}>
                  Mostrando {inventoryVisibleData.length} de {analysisDisplayData.length} registros
                </span>
              </div>
              💡 Doble clic en las columnas Movimientos o Ventas para ver el detalle
            </p>
                          {filters.query_type === 'analisis' && (
                <>
              {/* EDARSAHUB-PATCH-ANALISIS-CONVERSION-AGRUPACION */}
              <div className="mb-3 flex flex-wrap items-center gap-3 rounded-md border border-zinc-200 bg-zinc-50 p-3">
                <div className="flex rounded-lg bg-zinc-200 p-1">
                  <button
                    type="button"
                    onClick={() => setUnidadAnalisisInventarios('presentaciones')}
                    className={`px-3 py-1 text-xs rounded ${unidadAnalisisInventarios === 'presentaciones' ? 'bg-white shadow font-medium' : 'text-zinc-600'}`}
                  >
                    Presentaciones
                  </button>

                  <button
                    type="button"
                    onClick={() => setUnidadAnalisisInventarios('insumos')}
                    className={`px-3 py-1 text-xs rounded ${unidadAnalisisInventarios === 'insumos' ? 'bg-white shadow font-medium' : 'text-zinc-600'}`}
                  >
                    Insumos
                  </button>
                </div>

                <label className="flex items-center gap-2 text-xs text-zinc-700">
                  <input
                    type="checkbox"
                    checked={agruparProductosAnalisis}
                    onChange={(e) => setAgruparProductosAnalisis(e.target.checked)}
                  />
                  Agrupar productos
                </label>

                {agruparProductosAnalisis && (
                  <select
                    value={agruparPorAnalisis}
                    onChange={(e) => setAgruparPorAnalisis(e.target.value)}
                    className="h-8 rounded border border-zinc-300 bg-white px-2 text-xs"
                  >
                    <option value="categoria">Categoría / Clasificación</option>
                    <option value="familia">Familia / Grupo</option>
                    <option value="subfamilia">Subfamilia / Subgrupo</option>
                  </select>
                )}

                <span className="text-xs text-zinc-500">
                  Conversión por rendimiento canónico. Sin hardcode de alimentos/bebidas.
                </span>
              </div>

                </>
              )}
<div className="rounded-md border border-zinc-200 max-h-[600px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 z-10 bg-zinc-200">
                  <tr className="border-b-2 border-zinc-400">
                    {inventoryVisibleColumns.map((key) => (
                      <th
                        key={key}
                        onClick={() => handleInventorySort(key)}
                        title="Ordenar columna"
                        className="text-xs uppercase tracking-wider font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-left"
                        style={{ textAlign: 'left' }}
                      >
                        {formatAnalisisHeader(key)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {inventoryVisibleData.slice(0, 2000).map((row, idx) => (
                    <tr
                      key={row.__rowId || row.id || row.codigo || row.folio || `row-${idx}`}
                      className={`border-b ${row.__rowType === 'group' ? 'bg-zinc-100 font-semibold' : 'hover:bg-zinc-50/50'}`}
                    >
                      {inventoryVisibleColumns.map((key, cellIdx) => {
                        const value = row[key];
                        // Special formatting for analysis report
                        const isDiferencia = key.toLowerCase().includes('diferencia');
                        const isCosto = key.toLowerCase().includes('costo');
                        const isPorcentaje = key.toLowerCase().includes('porcentaje');
                        const keyLower = key.toLowerCase();
                        const isMovimientos = keyLower === 'movimientos';
                        const isVentas = keyLower === 'ventas';
                        const isNombreProducto = isNombreProductoAnalisisColumn(key);
                        
                        const isGroupRow = row.__rowType === 'group';
                        const isDetailInGroup = agruparProductosAnalisis && row.__rowType === 'detail';
                        let displayValue = value;
                        let className = `text-sm font-data p-2 text-left ${isGroupRow ? 'text-zinc-900 bg-zinc-100' : 'text-zinc-700'}`;
                        let onDoubleClick = null;
                        
                        // Columnas clickeables para ver detalle
                        if (!isGroupRow && isNombreProducto) {
                          onDoubleClick = () => loadRecipeUsageDetails(row);
                          className = "text-sm font-data text-blue-600 cursor-pointer hover:underline p-2 text-left";
                        } else if (!isGroupRow && isMovimientos && value !== null && value !== undefined && parseFloat(value) !== 0) {
                          onDoubleClick = () => loadMovementDetails(row);
                          className = "text-sm font-data text-blue-600 cursor-pointer hover:underline p-2 text-left";
                          displayValue = formatNumber(value);
                        } else if (!isGroupRow && isVentas && value !== null && value !== undefined && parseFloat(value) !== 0) {
                          onDoubleClick = () => loadSalesDetails(row);
                          className = "text-sm font-data text-blue-600 cursor-pointer hover:underline p-2 text-left";
                          displayValue = formatNumber(value);
                        } else if (isGroupRow && key === 'Agrupacion') {
                          const expanded = isAnalisisGroupExpanded(row.__groupKey);
                          displayValue = (
                            <button
                              type="button"
                              onClick={() => toggleAnalisisGroup(row.__groupKey)}
                              className="inline-flex items-center gap-2 text-left font-semibold text-zinc-900"
                              title={expanded ? 'Contraer grupo' : 'Expandir grupo'}
                            >
                              <ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${expanded ? '' : '-rotate-90'}`} />
                              <span>{value || row.nombre_producto || 'SIN AGRUPACION'}</span>
                            </button>
                          );
                        } else if (isDetailInGroup && (key === 'Agrupacion' || key === 'Items')) {
                          displayValue = '';
                        } else if (isPorcentaje && value !== null && value !== undefined) {
                          displayValue = `${formatNumber(value)}%`;
                          className = `text-sm font-data font-semibold p-2 text-left ${getDifferenceColor(parseFloat(value))}`;
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
                            className={`${className} align-top whitespace-nowrap`}
                            style={{ textAlign: 'left' }}
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
            {inventoryVisibleData.length > 2000 && (
              <p className="text-sm text-zinc-600 mt-4 text-center">
                Mostrando 2000 de {analysisDisplayData.length} registros. Exporta para ver todos.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* ==================== SECCIÓN: INSUMOS PENDIENTES DE DESCARGAR ==================== */}
      {filters.query_type === 'pendientes' && selectedServer?.system_type === 'SoftRestaurant' && (
        <div className="space-y-4">
          {/* KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border bg-gradient-to-br from-blue-50 to-white" data-testid="kpi-total-items">
              <CardContent className="py-4">
                <p className="text-xs text-zinc-500">Total Insumos</p>
                <p className="text-2xl font-bold text-blue-600">{pendientesData.totales.items}</p>
              </CardContent>
            </Card>
            <Card className="border bg-gradient-to-br from-red-50 to-white" data-testid="kpi-total-cantidad">
              <CardContent className="py-4">
                <p className="text-xs text-zinc-500">Cantidad Total</p>
                <p className="text-2xl font-bold text-red-600">{pendientesData.totales.cantidad.toLocaleString('es-MX', {maximumFractionDigits: 2})}</p>
              </CardContent>
            </Card>
            <Card className="border bg-gradient-to-br from-green-50 to-white" data-testid="kpi-total-valor">
              <CardContent className="py-4">
                <p className="text-xs text-zinc-500">Valor Total</p>
                <p className="text-2xl font-bold text-green-600">${pendientesData.totales.valor.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
              </CardContent>
            </Card>
          </div>

          {/* Filtro por Almacén */}
          {pendientesData.almacenes.length > 0 && (
            <Card className="border">
              <CardContent className="py-3">
                <div className="flex items-center gap-4 flex-wrap">
                  <Label className="text-sm font-medium">Filtrar por Almacén:</Label>
                  <div className="flex gap-2 flex-wrap">
                    <Button
                      variant={almacenesPendientesSeleccionados.length === 0 ? "default" : "outline"}
                      size="sm"
                      onClick={() => setAlmacenesPendientesSeleccionados([])}
                    >
                      Todos
                    </Button>
                    {pendientesData.almacenes.map(alm => (
                      <Button
                        key={alm}
                        variant={almacenesPendientesSeleccionados.includes(alm) ? "default" : "outline"}
                        size="sm"
                        onClick={() => {
                          if (almacenesPendientesSeleccionados.includes(alm)) {
                            setAlmacenesPendientesSeleccionados(prev => prev.filter(a => a !== alm));
                          } else {
                            setAlmacenesPendientesSeleccionados([alm]);
                          }
                        }}
                      >
                        {alm}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Tabla de Insumos Pendientes */}
          <Card className="border">
            <CardHeader className="py-3 bg-zinc-800 text-white rounded-t-lg">
              <CardTitle className="text-base flex items-center justify-between">
                <span>INSUMOS PENDIENTES A DESCARGAR</span>
                {loadingPendientes && <Loader2 className="h-5 w-5 animate-spin" />}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {loadingPendientes ? (
                <div className="py-12 text-center">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-blue-600" />
                  <p className="text-zinc-500">Cargando insumos pendientes...</p>
                </div>
              ) : pendientesData.items.length === 0 ? (
                <div className="py-12 text-center text-zinc-500">
                  <AlertCircle className="h-10 w-10 mx-auto mb-2 opacity-40" />
                  <p>No hay insumos pendientes de descargar</p>
                </div>
              ) : (
                <div className="max-h-[600px] overflow-auto">
                  <table className="w-full text-sm" data-testid="tabla-pendientes">
                    <thead className="sticky top-0 bg-zinc-700 text-white">
                      <tr>
                        <th className="py-2 px-2 text-left w-12">No</th>
                        <th className="py-2 px-2 text-center w-16">ALM</th>
                        <th className="py-2 px-2 text-left">GRUPO</th>
                        <th className="py-2 px-2 text-left w-24">CODIGO</th>
                        <th className="py-2 px-2 text-left">INSUMO</th>
                        <th className="py-2 px-2 text-right w-24">CANTIDAD</th>
                        <th className="py-2 px-2 text-center w-16">UM</th>
                        <th className="py-2 px-2 text-right w-24">COSTO</th>
                        <th className="py-2 px-2 text-right w-28">TOTAL</th>
                        <th className="py-2 px-2 text-right w-16">80-20</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pendientesData.items
                        .filter(item => almacenesPendientesSeleccionados.length === 0 || almacenesPendientesSeleccionados.includes(item.almacen))
                        .map((item, idx) => (
                        <tr 
                          key={item.codigo || item.producto || `abc-${idx}`} 
                          className={`border-b hover:bg-zinc-50 ${item.pareto <= 80 ? 'bg-yellow-50' : ''}`}
                        >
                          <td className="py-1.5 px-2 text-zinc-500">{item.no}</td>
                          <td className="py-1.5 px-2 text-center font-mono">{item.almacen}</td>
                          <td className="py-1.5 px-2 text-xs">{item.grupo}</td>
                          <td className="py-1.5 px-2 font-mono text-xs">{item.codigo}</td>
                          <td className="py-1.5 px-2 font-medium">{item.insumo}</td>
                          <td className="py-1.5 px-2 text-right text-red-600 font-semibold">
                            {item.cantidad.toLocaleString('es-MX', {maximumFractionDigits: 2})}
                          </td>
                          <td className="py-1.5 px-2 text-center text-xs text-zinc-500">{item.unidad}</td>
                          <td className="py-1.5 px-2 text-right">
                            ${item.costo.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 4})}
                          </td>
                          <td className="py-1.5 px-2 text-right font-semibold text-green-700">
                            ${item.total.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                          </td>
                          <td className="py-1.5 px-2 text-right">
                            <span className={`px-1.5 py-0.5 rounded text-xs ${
                              item.pareto <= 80 ? 'bg-yellow-200 text-yellow-800' : 'text-zinc-500'
                            }`}>
                              {item.pareto}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-zinc-800 text-white sticky bottom-0">
                      <tr>
                        <td colSpan={5} className="py-2 px-2 font-bold">TOTALES</td>
                        <td className="py-2 px-2 text-right font-bold text-red-300">
                          {pendientesData.totales.cantidad.toLocaleString('es-MX', {maximumFractionDigits: 2})}
                        </td>
                        <td></td>
                        <td></td>
                        <td className="py-2 px-2 text-right font-bold text-green-300">
                          ${pendientesData.totales.valor.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                        </td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {reportData.length === 0 && !loading && filters.query_type !== 'pendientes' && (
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

      {/* Modal de Detalle de Movimientos/Consumos (componente CANÓNICO compartido con Auditoría) */}
      <UsoRecetaModal
        detalle={usoRecetaDetalle}
        onClose={closeRecipeUsageDetails}
        formatNumber={formatNumber}
      />
      <DetalleProductoModal
        detalle={detalleProducto}
        onClose={cerrarDetalleProducto}
        formatNumber={formatNumber}
      />
        </TabsContent>

        {/* Tab: Informes de Auditoría */}
        <TabsContent value="informes">
          <div className="space-y-6">
            {/* Header */}
            <Card className="border border-zinc-200 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <FolderOpen className="h-5 w-5" />
                  Repositorio de Informes de Auditoría
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-zinc-500 mb-4">
                  Aquí se almacenan todos los informes de auditoría generados. Los informes incluyen 
                  el análisis de inventarios, comentarios del auditor, conclusiones, recomendaciones 
                  y evidencias adjuntas (fotos, PDFs, documentos).
                </p>
                
                {/* Filtros de búsqueda */}
                <div className="flex flex-wrap gap-4 mb-6">
                  <div className="flex-1 min-w-[200px]">
                    <Label className="text-xs text-zinc-500">Sucursal</Label>
                    <select className={selectStyle}>
                      <option value="">Todas las sucursales</option>
                      {sucursales.map(s => (
                        <option key={s.id} value={s.id}>{s.nombre}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex-1 min-w-[150px]">
                    <Label className="text-xs text-zinc-500">Fecha Desde</Label>
                    <Input type="date" className="h-10" />
                  </div>
                  <div className="flex-1 min-w-[150px]">
                    <Label className="text-xs text-zinc-500">Fecha Hasta</Label>
                    <Input type="date" className="h-10" />
                  </div>
                  <div className="flex items-end">
                    <Button variant="outline">
                      <Search className="h-4 w-4 mr-2" />
                      Buscar
                    </Button>
                  </div>
                </div>

                {/* Lista de informes */}
                <div className="border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-zinc-50">
                        <TableHead className="font-semibold">Fecha</TableHead>
                        <TableHead className="font-semibold">Sucursal</TableHead>
                        <TableHead className="font-semibold">Almacén</TableHead>
                        <TableHead className="font-semibold">Productos</TableHead>
                        <TableHead className="font-semibold">Diferencias</TableHead>
                        <TableHead className="font-semibold">Auditor</TableHead>
                        <TableHead className="font-semibold">Estatus</TableHead>
                        <TableHead className="font-semibold text-right">Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {loadingInformes ? (
                        <TableRow>
                          <TableCell colSpan={8} className="text-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin mx-auto text-zinc-400" />
                          </TableCell>
                        </TableRow>
                      ) : informesList.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={8} className="text-center py-12 text-zinc-400">
                            <FolderOpen className="h-12 w-12 mx-auto mb-3 text-zinc-300" />
                            <p className="text-base font-medium">No hay informes de auditoría</p>
                            <p className="text-sm mt-1">
                              Los informes se generarán desde la pestaña "Análisis de Inventarios" 
                              usando el botón "Generar Informe"
                            </p>
                          </TableCell>
                        </TableRow>
                      ) : (
                        informesList.map((informe) => (
                          <TableRow key={informe.id} className="hover:bg-zinc-50">
                            <TableCell className="text-sm">
                              {informe.fecha_creacion?.split('T')[0]}
                            </TableCell>
                            <TableCell className="font-medium">{informe.sucursal_nombre}</TableCell>
                            <TableCell>{informe.almacen_nombre}</TableCell>
                            <TableCell>
                              <span className="font-mono">{informe.total_productos}</span>
                              {informe.productos_con_diferencia > 0 && (
                                <span className="text-red-500 text-xs ml-1">
                                  ({informe.productos_con_diferencia} dif)
                                </span>
                              )}
                            </TableCell>
                            <TableCell className="text-right font-mono">
                              ${(informe.valor_diferencias || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                            </TableCell>
                            <TableCell>{informe.auditor || '-'}</TableCell>
                            <TableCell>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                informe.estatus === 'finalizado' 
                                  ? 'bg-green-100 text-green-700' 
                                  : 'bg-amber-100 text-amber-700'
                              }`}>
                                {informe.estatus === 'finalizado' ? 'Finalizado' : 'Borrador'}
                              </span>
                              {informe.num_errores_captura > 0 && (
                                <span className="ml-2 px-1.5 py-0.5 bg-red-100 text-red-600 text-xs rounded" title="Errores de captura">
                                  {informe.num_errores_captura} err
                                </span>
                              )}
                              {informe.num_evidencias > 0 && (
                                <span className="ml-1 text-xs text-zinc-500">
                                  {informe.num_evidencias} arch
                                </span>
                              )}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex gap-1 justify-end">
                                <Button 
                                  variant="ghost" 
                                  size="sm"
                                  onClick={() => handleVerInforme(informe.id)}
                                  title="Ver informe"
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                                <Button 
                                  variant="ghost" 
                                  size="sm"
                                  onClick={() => handleDescargarPDF(informe.id)}
                                  title="Descargar PDF"
                                >
                                  <Download className="h-4 w-4" />
                                </Button>
                                <Button 
                                  variant="ghost" 
                                  size="sm"
                                  className="text-red-500 hover:text-red-700"
                                  onClick={() => handleEliminarInforme(informe.id)}
                                  title="Eliminar"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            {/* Instrucciones */}
            <Card className="border border-blue-200 bg-blue-50">
              <CardContent className="pt-4">
                <h4 className="font-medium text-blue-800 mb-2 flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  ¿Cómo generar un informe de auditoría?
                </h4>
                <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
                  <li>Ve a la pestaña "Análisis de Inventarios"</li>
                  <li>Selecciona la unidad de negocio, sucursal, almacén e inventario</li>
                  <li>Genera el reporte de análisis</li>
                  <li>Haz clic en el botón "Generar Informe"</li>
                  <li>Agrega comentarios, conclusiones y recomendaciones</li>
                  <li>Adjunta evidencias (fotos, PDFs) si lo requieres</li>
                  <li>Guarda el informe para consultarlo posteriormente</li>
                </ol>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* ================================================================= */}
      {/* MODAL: GENERAR INFORME DE AUDITORÍA */}
      {/* ================================================================= */}
      {modalInforme && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="bg-gradient-to-r from-zinc-800 to-zinc-900 text-white px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold">Generar Informe de Auditoría</h2>
                  <p className="text-zinc-300 text-sm mt-1">
                    {filters.sucursal} - {selectedAlmacenes[0]?.nombre || filters.almacen}
                  </p>
                </div>
                <button 
                  onClick={() => setModalInforme(false)}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Body - Scrollable */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Resumen del análisis */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-zinc-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-zinc-800">{informeData.total_productos}</p>
                  <p className="text-xs text-zinc-500">Total Productos</p>
                </div>
                <div className="bg-red-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-red-600">{informeData.productos_con_diferencia}</p>
                  <p className="text-xs text-zinc-500">Con Diferencia</p>
                </div>
                <div className="bg-amber-50 rounded-lg p-3 text-center">
                  <p className="text-lg font-bold text-amber-600">
                    ${(informeData.valor_total_diferencias || 0).toLocaleString('es-MX', { minimumFractionDigits: 0 })}
                  </p>
                  <p className="text-xs text-zinc-500">Valor Diferencias</p>
                </div>
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-green-600">{(informeData.porcentaje_precision || 0).toFixed(1)}%</p>
                  <p className="text-xs text-zinc-500">Precisión</p>
                </div>
              </div>

              {/* Datos del auditor */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Nombre del Auditor</Label>
                  <Input
                    value={informeData.auditor}
                    onChange={(e) => setInformeData(prev => ({ ...prev, auditor: e.target.value }))}
                    placeholder="Nombre completo del auditor"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label className="text-sm font-medium">Cargo</Label>
                  <Input
                    value={informeData.cargo_auditor}
                    onChange={(e) => setInformeData(prev => ({ ...prev, cargo_auditor: e.target.value }))}
                    placeholder="Ej: Auditor Senior, Contralor"
                    className="mt-1"
                  />
                </div>
              </div>

              {/* Comentarios */}
              <div>
                <Label className="text-sm font-medium">Comentarios del Auditor</Label>
                <textarea
                  value={informeData.comentarios}
                  onChange={(e) => setInformeData(prev => ({ ...prev, comentarios: e.target.value }))}
                  placeholder="Observaciones generales sobre el análisis de inventarios..."
                  className="mt-1 w-full h-24 px-3 py-2 border rounded-lg text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Conclusiones */}
              <div>
                <Label className="text-sm font-medium">Conclusiones</Label>
                <textarea
                  value={informeData.conclusiones}
                  onChange={(e) => setInformeData(prev => ({ ...prev, conclusiones: e.target.value }))}
                  placeholder="Conclusiones principales del análisis..."
                  className="mt-1 w-full h-24 px-3 py-2 border rounded-lg text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Recomendaciones */}
              <div>
                <Label className="text-sm font-medium">Recomendaciones</Label>
                <textarea
                  value={informeData.recomendaciones}
                  onChange={(e) => setInformeData(prev => ({ ...prev, recomendaciones: e.target.value }))}
                  placeholder="1. Primera recomendación&#10;2. Segunda recomendación&#10;3. Tercera recomendación"
                  className="mt-1 w-full h-28 px-3 py-2 border rounded-lg text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Errores de Captura Detectados - Se incluyen automáticamente */}
              {erroresCaptura.length > 0 && (
                <div className="border border-red-200 bg-red-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertCircle className="h-5 w-5 text-red-600" />
                    <span className="font-semibold text-red-800">
                      Errores de Captura Detectados ({erroresCaptura.length})
                    </span>
                    <span className="text-xs text-red-600 bg-red-100 px-2 py-0.5 rounded">
                      Se incluirán automáticamente
                    </span>
                  </div>
                  <div className="max-h-32 overflow-y-auto space-y-1">
                    {erroresCaptura.slice(0, 10).map((error, idx) => (
                      <div key={error.codigo || `cap-err-${idx}`} className="text-sm text-red-700 flex items-start gap-2">
                        <span className="text-red-400">•</span>
                        <span>
                          <strong>{error.CODIGO_INSUMO || error.codigo}</strong>: {error.PRODUCTO || error.producto}
                          {error.TIPO_ERROR && <span className="text-red-500 ml-1">({error.TIPO_ERROR})</span>}
                        </span>
                      </div>
                    ))}
                    {erroresCaptura.length > 10 && (
                      <p className="text-xs text-red-500 mt-2">
                        ... y {erroresCaptura.length - 10} errores más
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Opción de comparativo */}
              <div className="flex items-center gap-2 p-3 bg-zinc-50 rounded-lg">
                <input
                  type="checkbox"
                  id="incluir_comparativo"
                  checked={informeData.incluir_comparativo}
                  onChange={(e) => setInformeData(prev => ({ ...prev, incluir_comparativo: e.target.checked }))}
                  className="h-4 w-4 rounded border-zinc-300"
                />
                <label htmlFor="incluir_comparativo" className="text-sm">
                  Incluir datos del Comparativo de 4 Cortes (si está disponible)
                </label>
              </div>

              {/* Evidencias */}
              <div>
                <Label className="text-sm font-medium mb-2 block">Evidencias (Fotos, PDFs, Documentos)</Label>
                
                <div className="border-2 border-dashed border-zinc-300 rounded-lg p-4 text-center hover:border-blue-400 transition-colors">
                  <input
                    type="file"
                    multiple
                    accept="image/*,.pdf,.doc,.docx,.xls,.xlsx"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="evidencias-input"
                  />
                  <label htmlFor="evidencias-input" className="cursor-pointer">
                    <Upload className="h-8 w-8 mx-auto text-zinc-400 mb-2" />
                    <p className="text-sm text-zinc-600">Arrastra archivos o haz clic para seleccionar</p>
                    <p className="text-xs text-zinc-400 mt-1">Imágenes, PDF, Word, Excel (máx. 10MB c/u)</p>
                  </label>
                </div>

                {/* Lista de archivos seleccionados */}
                {evidenciasTemp.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {evidenciasTemp.map((file, idx) => (
                      <div key={`file-${file.name}-${file.size}`} className="flex items-center gap-3 p-2 bg-zinc-50 rounded-lg">
                        {file.type.startsWith('image/') ? (
                          <FileImage className="h-5 w-5 text-blue-500" />
                        ) : (
                          <File className="h-5 w-5 text-zinc-500" />
                        )}
                        <span className="flex-1 text-sm truncate">{file.name}</span>
                        <span className="text-xs text-zinc-400">
                          {(file.size / 1024).toFixed(0)} KB
                        </span>
                        <button 
                          onClick={() => handleRemoveEvidencia(idx)}
                          className="p-1 hover:bg-red-100 rounded text-red-500"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="border-t px-6 py-4 bg-zinc-50 flex justify-between items-center">
              <p className="text-xs text-zinc-500">
                Los informes se guardan en el repositorio de auditorías
              </p>
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setModalInforme(false)}>
                  Cancelar
                </Button>
                <Button 
                  onClick={handleGuardarInforme}
                  disabled={savingInforme}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {savingInforme ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Guardando...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Guardar Informe
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================================================================= */}
      {/* MODAL: VER INFORME COMPLETO */}
      {/* ================================================================= */}
      {viewInformeModal && selectedInforme && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="bg-gradient-to-r from-zinc-800 to-zinc-900 text-white px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold">Informe de Auditoría</h2>
                  <p className="text-zinc-300 text-sm mt-1">
                    {selectedInforme.sucursal_nombre} - {selectedInforme.almacen_nombre}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button 
                    variant="secondary" 
                    size="sm"
                    onClick={() => handleDescargarPDF(selectedInforme.id)}
                  >
                    <Download className="h-4 w-4 mr-1" />
                    PDF
                  </Button>
                  <button 
                    onClick={() => setViewInformeModal(false)}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Info general */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-zinc-500">Fecha del Informe</p>
                  <p className="font-medium">{selectedInforme.fecha_creacion?.split('T')[0]}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Auditor</p>
                  <p className="font-medium">{selectedInforme.auditor || 'No especificado'}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Periodo Analizado</p>
                  <p className="font-medium text-sm">
                    {selectedInforme.inventario_inicial_fecha} al {selectedInforme.inventario_final_fecha}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Estatus</p>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    selectedInforme.estatus === 'finalizado' 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-amber-100 text-amber-700'
                  }`}>
                    {selectedInforme.estatus === 'finalizado' ? 'Finalizado' : 'Borrador'}
                  </span>
                </div>
              </div>

              {/* Resumen */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-zinc-50 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-zinc-800">{selectedInforme.total_productos}</p>
                  <p className="text-sm text-zinc-500">Total Productos</p>
                </div>
                <div className="bg-red-50 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-red-600">{selectedInforme.productos_con_diferencia}</p>
                  <p className="text-sm text-zinc-500">Con Diferencia</p>
                </div>
                <div className="bg-amber-50 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-amber-600">
                    ${(selectedInforme.valor_total_diferencias || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                  </p>
                  <p className="text-sm text-zinc-500">Valor Diferencias</p>
                </div>
                <div className="bg-green-50 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-green-600">
                    {(selectedInforme.porcentaje_precision || 0).toFixed(1)}%
                  </p>
                  <p className="text-sm text-zinc-500">Precisión</p>
                </div>
              </div>

              {/* Comentarios */}
              {selectedInforme.comentarios && (
                <div>
                  <h3 className="font-semibold text-zinc-800 mb-2 flex items-center gap-2">
                    <FileText className="h-4 w-4 text-blue-600" />
                    Comentarios del Auditor
                  </h3>
                  <p className="text-sm text-zinc-600 bg-zinc-50 p-4 rounded-lg whitespace-pre-wrap">
                    {selectedInforme.comentarios}
                  </p>
                </div>
              )}

              {/* Conclusiones */}
              {selectedInforme.conclusiones && (
                <div>
                  <h3 className="font-semibold text-zinc-800 mb-2 flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    Conclusiones
                  </h3>
                  <p className="text-sm text-zinc-600 bg-green-50 p-4 rounded-lg whitespace-pre-wrap">
                    {selectedInforme.conclusiones}
                  </p>
                </div>
              )}

              {/* Recomendaciones */}
              {selectedInforme.recomendaciones && (
                <div>
                  <h3 className="font-semibold text-zinc-800 mb-2 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-amber-600" />
                    Recomendaciones
                  </h3>
                  <p className="text-sm text-zinc-600 bg-amber-50 p-4 rounded-lg whitespace-pre-wrap">
                    {selectedInforme.recomendaciones}
                  </p>
                </div>
              )}

              {/* Evidencias */}
              {selectedInforme.evidencias && selectedInforme.evidencias.length > 0 && (
                <div>
                  <h3 className="font-semibold text-zinc-800 mb-2 flex items-center gap-2">
                    <Upload className="h-4 w-4 text-blue-600" />
                    Evidencias Adjuntas ({selectedInforme.evidencias.length})
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {selectedInforme.evidencias.map((ev, idx) => (
                      <div key={ev.url || `ev-${idx}`} className="border rounded-lg p-3 flex items-center gap-3">
                        {ev.content_type?.startsWith('image/') ? (
                          <FileImage className="h-8 w-8 text-blue-500" />
                        ) : (
                          <File className="h-8 w-8 text-zinc-500" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{ev.filename}</p>
                          <p className="text-xs text-zinc-400">{(ev.size / 1024).toFixed(0)} KB</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Errores de Captura de Inventario */}
              {selectedInforme.errores_captura && selectedInforme.errores_captura.length > 0 && (
                <div>
                  <h3 className="font-semibold text-red-800 mb-2 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    Errores de Captura Detectados ({selectedInforme.errores_captura.length})
                  </h3>
                  <div className="border border-red-200 rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-red-50">
                          <TableHead className="text-red-800">Código</TableHead>
                          <TableHead className="text-red-800">Producto</TableHead>
                          <TableHead className="text-red-800">Tipo Error</TableHead>
                          <TableHead className="text-red-800 text-right">Cantidad</TableHead>
                          <TableHead className="text-red-800">Detalle</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedInforme.errores_captura.slice(0, 15).map((error, idx) => (
                          <TableRow key={error.codigo || `inf-err-${idx}`} className="bg-red-50/50">
                            <TableCell className="font-mono text-xs">{error.codigo}</TableCell>
                            <TableCell className="text-sm">{error.producto}</TableCell>
                            <TableCell>
                              <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                                {error.tipo_error || 'Error'}
                              </span>
                            </TableCell>
                            <TableCell className="text-right font-mono">{error.inv_capturado}</TableCell>
                            <TableCell className="text-xs text-red-600">{error.detalle || '-'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  {selectedInforme.errores_captura.length > 15 && (
                    <p className="text-xs text-red-500 mt-2 text-center">
                      Mostrando 15 de {selectedInforme.errores_captura.length} errores
                    </p>
                  )}
                </div>
              )}

              {/* Productos con diferencias (Top 10) */}
              {selectedInforme.productos_diferencias && selectedInforme.productos_diferencias.length > 0 && (
                <div>
                  <h3 className="font-semibold text-zinc-800 mb-2">
                    Top Productos con Diferencias
                  </h3>
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-zinc-50">
                          <TableHead>Código</TableHead>
                          <TableHead>Producto</TableHead>
                          <TableHead className="text-right">Inv. Ini</TableHead>
                          <TableHead className="text-right">Inv. Fin</TableHead>
                          <TableHead className="text-right">Diferencia</TableHead>
                          <TableHead className="text-right">Valor</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedInforme.productos_diferencias.slice(0, 10).map((prod, idx) => (
                          <TableRow key={prod.codigo || `prod-diff-${idx}`}>
                            <TableCell className="font-mono text-xs">{prod.codigo}</TableCell>
                            <TableCell className="text-sm">{prod.producto}</TableCell>
                            <TableCell className="text-right">{prod.inv_inicial}</TableCell>
                            <TableCell className="text-right">{prod.inv_final}</TableCell>
                            <TableCell className={`text-right font-medium ${prod.diferencia < 0 ? 'text-red-600' : 'text-green-600'}`}>
                              {prod.diferencia}
                            </TableCell>
                            <TableCell className="text-right font-mono">
                              ${(prod.valor_diferencia || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t px-6 py-4 bg-zinc-50 flex justify-end">
              <Button variant="outline" onClick={() => setViewInformeModal(false)}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Pantalla Completa - Resultados de Auditoría */}
      <Dialog open={showFullscreenResultados} onOpenChange={setShowFullscreenResultados}>
        <DialogContent className="max-w-[95vw] w-[95vw] max-h-[95vh] h-[95vh] p-0 overflow-hidden">
          <DialogHeader className="px-4 py-3 border-b bg-zinc-100 flex flex-row items-center justify-between">
            <DialogTitle className="text-lg font-semibold">
              Resultados de Auditoría ({analysisDisplayData.length} registros)
            </DialogTitle>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-zinc-300"
                  checked={mostrarCostos}
                  onChange={(e) => setMostrarCostos(e.target.checked)}
                />
                <span>Mostrar Costos</span>
              </label>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowFullscreenResultados(false)}
                className="h-8 px-2"
              >
                <Minimize2 className="h-4 w-4 mr-1" />
                Minimizar
              </Button>
            </div>
          </DialogHeader>
          <div className="flex-1 overflow-auto" style={{ height: 'calc(95vh - 70px)' }}>
            {reportData.length > 0 && (
              <table className="w-full text-sm">
                <thead className="sticky top-0 z-10 bg-zinc-800 text-white">
                  <tr>
                    {inventoryVisibleColumns.map((key) => (
                      <th
                        key={key}
                        onClick={() => handleInventorySort(key)}
                        title="Ordenar columna"
                        className="text-xs uppercase tracking-wider font-semibold whitespace-nowrap py-3 px-3 text-left"
                        style={{ textAlign: 'left' }}
                      >
                        {formatAnalisisHeader(key)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {inventoryVisibleData.map((row, idx) => (
                    <tr
                      key={row.__rowId || row.id || row.codigo || row.folio || `data-${idx}`}
                      className={`border-b ${row.__rowType === 'group' ? 'bg-zinc-100 font-semibold' : 'hover:bg-zinc-50'}`}
                    >
                      {inventoryVisibleColumns.map((key, cellIdx) => {
                        const value = row[key];
                        const isDiferencia = key.toLowerCase().includes('diferencia');
                        const isCosto = key.toLowerCase().includes('costo');
                        const isPorcentaje = key.toLowerCase().includes('porcentaje');
                        const isGroupRow = row.__rowType === 'group';
                        const isDetailInGroup = agruparProductosAnalisis && row.__rowType === 'detail';
                        const keyLower = key.toLowerCase();
                        const isMovimientos = keyLower === 'movimientos';
                        const isVentas = keyLower === 'ventas';
                        const isNombreProducto = isNombreProductoAnalisisColumn(key);
                        
                        let displayValue = value;
                        let className = `py-2 px-3 text-left ${isGroupRow ? 'text-zinc-900 bg-zinc-100' : 'text-zinc-700'}`;
                        let onDoubleClick = null;
                        
                        if (!isGroupRow && isNombreProducto) {
                          onDoubleClick = () => loadRecipeUsageDetails(row);
                          className = "py-2 px-3 text-left text-blue-600 cursor-pointer hover:underline";
                        } else if (!isGroupRow && isMovimientos && value !== null && value !== undefined && parseFloat(value) !== 0) {
                          onDoubleClick = () => loadMovementDetails(row);
                          className = "py-2 px-3 text-left text-blue-600 cursor-pointer hover:underline";
                          displayValue = formatNumber(value);
                        } else if (!isGroupRow && isVentas && value !== null && value !== undefined && parseFloat(value) !== 0) {
                          onDoubleClick = () => loadSalesDetails(row);
                          className = "py-2 px-3 text-left text-blue-600 cursor-pointer hover:underline";
                          displayValue = formatNumber(value);
                        } else if (isGroupRow && key === 'Agrupacion') {
                          const expanded = isAnalisisGroupExpanded(row.__groupKey);
                          displayValue = (
                            <button
                              type="button"
                              onClick={() => toggleAnalisisGroup(row.__groupKey)}
                              className="inline-flex items-center gap-2 text-left font-semibold text-zinc-900"
                              title={expanded ? 'Contraer grupo' : 'Expandir grupo'}
                            >
                              <ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${expanded ? '' : '-rotate-90'}`} />
                              <span>{value || row.nombre_producto || 'SIN AGRUPACION'}</span>
                            </button>
                          );
                        } else if (isDetailInGroup && (key === 'Agrupacion' || key === 'Items')) {
                          displayValue = '';
                        } else if (typeof value === 'number') {
                          if (isCosto) {
                            displayValue = `$${value.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                            className += " font-mono";
                          } else if (isPorcentaje) {
                            displayValue = `${value.toFixed(2)}%`;
                          } else {
                            displayValue = value.toLocaleString('es-MX', { maximumFractionDigits: 2 });
                          }
                        }
                        
                        if (isDiferencia && typeof value === 'number') {
                          if (value > 0) {
                            className += " text-green-600 font-semibold";
                          } else if (value < 0) {
                            className += " text-red-600 font-semibold";
                          }
                        }
                        
                        return (
                          <td
                            key={cellIdx}
                            className={`${className} align-top whitespace-nowrap`}
                            style={{ textAlign: 'left' }}
                            onDoubleClick={onDoubleClick}
                            title={onDoubleClick ? 'Doble clic para ver detalle' : ''}
                          >
                            {displayValue ?? '-'}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Reportes;
