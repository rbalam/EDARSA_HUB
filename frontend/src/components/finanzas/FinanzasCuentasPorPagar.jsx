import React, { useMemo } from 'react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import {
  Building2, RefreshCw, X, Download, CreditCard,
  ChevronRight, ChevronDown, ChevronUp, PieChart,
  CheckCircle2, XCircle, FileText, File, FileSpreadsheet
} from 'lucide-react';

/**
 * FinanzasCuentasPorPagar
 * 
 * Componente presentacional para renderizar la sección de Cuentas por Pagar (CxP).
 * El estado y la lógica de datos se mantienen en el componente padre (Finanzas.js).
 * 
 * @param {Object} props
 * @param {Object} props.cxpData - Datos de facturas agrupadas por proveedor
 * @param {Object} props.cxpResumen - Resumen de antigüedad
 * @param {Array} props.cxpProveedores - Lista de proveedores para búsqueda
 * @param {Array} props.cxpSucursales - Lista de sucursales
 * @param {Array} props.unidadesNegocio - Unidades de negocio disponibles
 * @param {string} props.selectedUnidad - Unidad de negocio seleccionada
 * @param {boolean} props.loadingUnidades - Estado de carga de unidades
 * @param {Object} props.userPermissions - Permisos del usuario
 * @param {string} props.cxpFiltroSucursal - Filtro de sucursal activo
 * @param {string} props.cxpFiltroProveedor - Filtro de proveedor activo
 * @param {string} props.cxpBusquedaProveedor - Término de búsqueda de proveedor
 * @param {string} props.cxpFechaCorte - Fecha de corte seleccionada
 * @param {boolean} props.cxpSoloVencidas - Filtro solo vencidas
 * @param {boolean} props.cxpSoloDecision - Filtro solo con decisión
 * @param {Object} props.cxpExpandidos - Estado de proveedores expandidos
 * @param {Object} props.cxpCategoriasExpandidas - Estado de categorías expandidas
 * @param {string} props.cxpVistaMode - Modo de vista ('categorias' o 'proveedores')
 * @param {string|null} props.savingDecision - ID de factura siendo guardada
 * @param {boolean} props.loading - Estado de carga general
 * @param {Function} props.onUnidadChange - Callback al cambiar unidad
 * @param {Function} props.onFechaCorteChange - Callback al cambiar fecha corte
 * @param {Function} props.onFiltroSucursalChange - Callback al cambiar sucursal
 * @param {Function} props.onBusquedaProveedorChange - Callback al cambiar búsqueda
 * @param {Function} props.onFiltroProveedorSelect - Callback al seleccionar proveedor
 * @param {Function} props.onLimpiarFiltroProveedor - Callback al limpiar filtro proveedor
 * @param {Function} props.onSoloVencidasChange - Callback al cambiar checkbox vencidas
 * @param {Function} props.onSoloDecisionChange - Callback al cambiar checkbox decisión
 * @param {Function} props.onFiltrar - Callback al hacer clic en Filtrar
 * @param {Function} props.onExportarCSV - Callback al exportar CSV
 * @param {Function} props.onMarcarTodasVencidas - Callback marcar todas vencidas
 * @param {Function} props.onDesmarcarTodas - Callback desmarcar todas
 * @param {Function} props.onExpandirTodos - Callback expandir todos
 * @param {Function} props.onColapsarTodos - Callback colapsar todos
 * @param {Function} props.onVistaModeChange - Callback cambiar modo vista
 * @param {Function} props.onToggleCategoria - Callback toggle categoría
 * @param {Function} props.onToggleProveedor - Callback toggle proveedor
 * @param {Function} props.onDecisionPago - Callback decisión de pago
 * @param {Function} props.formatCurrency - Función para formatear moneda
 * @param {Function} props.reagruparCxPPorProveedores - Función para reagrupar datos
 */
export default function FinanzasCuentasPorPagar({
  cxpData,
  cxpResumen,
  cxpProveedores,
  cxpSucursales,
  unidadesNegocio,
  selectedUnidad,
  loadingUnidades,
  userPermissions,
  cxpFiltroSucursal,
  cxpFiltroProveedor,
  cxpBusquedaProveedor,
  cxpFechaCorte,
  cxpSoloVencidas,
  cxpSoloDecision,
  cxpExpandidos,
  cxpCategoriasExpandidas,
  cxpVistaMode,
  savingDecision,
  loading,
  onUnidadChange,
  onFechaCorteChange,
  onFiltroSucursalChange,
  onBusquedaProveedorChange,
  onFiltroProveedorSelect,
  onLimpiarFiltroProveedor,
  onSoloVencidasChange,
  onSoloDecisionChange,
  onFiltrar,
  onExportarCSV,
  onMarcarTodasVencidas,
  onDesmarcarTodas,
  onExpandirTodos,
  onColapsarTodos,
  onVistaModeChange,
  onToggleCategoria,
  onToggleProveedor,
  onDecisionPago,
  onTogglePagoProveedor,
  formatCurrency,
  reagruparCxPPorProveedores,
  // FASE 1 CxP: Prop para ocultar filtro Sucursal visualmente
  // La lógica interna de sucursal_id se mantiene para compatibilidad legacy
  hideSucursalFilter = false
}) {
  // Memoizar filtrado de sucursales
  const sucursalesFiltradas = useMemo(() => {
    return cxpSucursales.filter(s => {
      if (userPermissions.canSeeAll) return true;
      if (userPermissions.allowedSucursales.length === 0) return true;
      return userPermissions.allowedSucursales.includes(s.SucursalID);
    });
  }, [cxpSucursales, userPermissions.canSeeAll, userPermissions.allowedSucursales]);

  // FASE 1 CxP FIX: Extraer proveedores únicos desde cxpData.proveedores (estructura anidada A/B/X)
  // Esto asegura que la búsqueda funcione correctamente para datos de SoftRestaurant y MPRO
  const proveedoresExtraidos = useMemo(() => {
    if (!cxpData?.proveedores) return [];
    
    const proveedoresMap = {};
    
    // Recorrer las categorías (A, B, X) y extraer proveedores reales de las facturas
    cxpData.proveedores.forEach(categoria => {
      (categoria.facturas || []).forEach(factura => {
        const provNombre = factura.proveedor_nombre || '';
        const provClave = factura.proveedor_clave || factura.proveedor_id || '';
        const provRfc = factura.proveedor_rfc || '';
        const key = provNombre.toLowerCase().trim();
        
        if (key && !proveedoresMap[key]) {
          proveedoresMap[key] = {
            proveedor_id: provClave,
            proveedor_nombre: provNombre,
            proveedor_rfc: provRfc,
            proveedor_clave: provClave,
            categoria: categoria.proveedor_id, // A, B, X
            cantidad_facturas: 0,
            total_saldo: 0
          };
        }
        
        if (key) {
          proveedoresMap[key].cantidad_facturas += 1;
          proveedoresMap[key].total_saldo += parseFloat(factura.saldo) || 0;
        }
      });
    });
    
    // Convertir a array y ordenar por nombre
    return Object.values(proveedoresMap).sort((a, b) => 
      (a.proveedor_nombre || '').localeCompare(b.proveedor_nombre || '')
    );
  }, [cxpData?.proveedores]);

  // Memoizar filtrado de proveedores para búsqueda
  // Usa proveedoresExtraidos (de cxpData) con fallback a cxpProveedores (del endpoint)
  const proveedoresFiltrados = useMemo(() => {
    if (!cxpBusquedaProveedor) return [];
    
    // Normalizar búsqueda: minúsculas, sin acentos, sin espacios extra
    const normalizarTexto = (texto) => {
      if (!texto) return '';
      return texto.toString()
        .toLowerCase()
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // Quitar acentos
        .trim();
    };
    
    const busqueda = normalizarTexto(cxpBusquedaProveedor);
    
    // Primero buscar en proveedoresExtraidos (fuente primaria desde cxpData)
    const fuentePrimaria = proveedoresExtraidos.filter(p => 
      normalizarTexto(p.proveedor_nombre).includes(busqueda) ||
      normalizarTexto(p.proveedor_rfc).includes(busqueda) ||
      normalizarTexto(p.proveedor_clave).includes(busqueda) ||
      normalizarTexto(p.proveedor_id).includes(busqueda)
    );
    
    if (fuentePrimaria.length > 0) {
      return fuentePrimaria;
    }
    
    // Fallback: buscar en cxpProveedores (endpoint)
    return cxpProveedores.filter(p => 
      normalizarTexto(p.proveedor_nombre).includes(busqueda) ||
      normalizarTexto(p.proveedor_rfc).includes(busqueda) ||
      normalizarTexto(p.proveedor_id).includes(busqueda)
    );
  }, [proveedoresExtraidos, cxpProveedores, cxpBusquedaProveedor]);

  // Memoizar cálculo de totales
  const totales = useMemo(() => {
    if (!cxpData?.proveedores) return { total_saldo: 0, total_importe: 0, total_a_pagar: 0, facturas_marcadas: 0, total_vencidas: 0 };
    
    let total_saldo = 0;
    let total_importe = 0;
    let total_a_pagar = 0;
    let facturas_marcadas = 0;
    let total_vencidas = 0;
    
    cxpData.proveedores.forEach(proveedorOCategoria => {
      (proveedorOCategoria.facturas || []).forEach(factura => {
        const saldo = parseFloat(factura.saldo) || 0;
        const importe = parseFloat(factura.importe_original || factura.importe_total) || 0;
        
        total_saldo += saldo;
        total_importe += importe;
        
        if (factura.decision_pago === true) {
          const importeAPagar = parseFloat(factura.importe_a_pagar) || saldo;
          total_a_pagar += importeAPagar;
          facturas_marcadas += 1;
        }
        
        if (parseInt(factura.dias_vencida) > 0) {
          total_vencidas += 1;
        }
      });
    });
    
    return { total_saldo, total_importe, total_a_pagar, facturas_marcadas, total_vencidas };
  }, [cxpData?.proveedores]);
  
  const antiguedad = cxpResumen?.antiguedad || {};

  // Componente interno para renderizar la tabla de facturas de un proveedor
  const FacturasTable = ({ proveedor }) => {
    // Determinar si todas las facturas están marcadas para mostrar indicador visual
    const todasMarcadas = proveedor.facturas.every(f => f.decision_pago === true);
    const algunaMarcada = proveedor.facturas.some(f => f.decision_pago === true);
    
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-zinc-50">
            <tr>
              <th className="text-left p-2 font-medium text-zinc-600">Folio Entrada</th>
              <th className="text-left p-2 font-medium text-zinc-600">Folio Factura</th>
              <th className="text-center p-2 font-medium text-zinc-600">F. Entrada</th>
              <th className="text-center p-2 font-medium text-zinc-600">F. Vencimiento</th>
              <th className="text-center p-2 font-medium text-zinc-600">Días Venc.</th>
              <th className="text-left p-2 font-medium text-zinc-600">Referencia</th>
              <th className="text-right p-2 font-medium text-zinc-600">Importe</th>
              <th className="text-right p-2 font-medium text-zinc-600">Saldo</th>
              <th 
                className={`text-center p-2 font-medium cursor-pointer select-none transition-colors rounded ${
                  todasMarcadas 
                    ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                    : algunaMarcada 
                      ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                      : 'text-zinc-600 hover:bg-zinc-200'
                }`}
                onDoubleClick={(e) => {
                  e.stopPropagation();
                  onTogglePagoProveedor(proveedor);
                }}
                title="Doble clic para marcar/desmarcar todas las facturas de este proveedor"
                data-testid={`pagar-header-${proveedor.proveedor_nombre}`}
              >
                Pagar
                {todasMarcadas && <CheckCircle2 className="h-3 w-3 inline ml-1" />}
              </th>
              <th className="text-right p-2 font-medium text-zinc-600">Importe a Pagar</th>
              <th className="text-center p-2 font-medium text-zinc-600">Docs</th>
            </tr>
          </thead>
          <tbody>
            {proveedor.facturas.map((factura, idx) => (
              <tr key={factura.factura_id || idx} className={`border-b hover:bg-zinc-50 ${factura.dias_vencida > 0 ? 'bg-red-50' : ''}`}>
                <td className="p-2 font-mono text-zinc-700">{factura.folio_entrada || '-'}</td>
                <td className="p-2 font-mono text-zinc-700">{factura.folio_factura || '-'}</td>
                <td className="p-2 text-center text-zinc-600">{factura.fecha_entrada?.split('T')[0] || '-'}</td>
                <td className="p-2 text-center text-zinc-600">{factura.fecha_vencimiento || '-'}</td>
                <td className="p-2 text-center">
                  <span className={`font-bold ${factura.dias_vencida > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {factura.dias_vencida > 0 ? factura.dias_vencida : '-'}
                  </span>
                </td>
                <td className="p-2 max-w-[150px] truncate text-zinc-600" title={factura.referencia || factura.observaciones}>
                  {factura.referencia || factura.observaciones || '-'}
                </td>
                <td className="p-2 text-right font-mono">{formatCurrency(factura.importe_original || factura.importe_total || 0)}</td>
                <td className="p-2 text-right font-mono font-bold">{formatCurrency(factura.saldo)}</td>
                <td className="p-2 text-center">
                  <button
                    onClick={(e) => { e.stopPropagation(); onDecisionPago(factura.factura_id, !factura.decision_pago); }}
                    disabled={savingDecision === factura.factura_id}
                    className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition ${
                      factura.decision_pago 
                        ? 'bg-green-500 border-green-500 text-white' 
                        : 'border-zinc-300 hover:border-green-400'
                    }`}
                  >
                    {savingDecision === factura.factura_id ? (
                      <RefreshCw className="h-3 w-3 animate-spin" />
                    ) : factura.decision_pago ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : null}
                  </button>
                </td>
                <td className="p-2 text-right font-mono text-green-600 font-bold">
                  {factura.decision_pago ? formatCurrency(factura.importe_a_pagar || factura.saldo) : '-'}
                </td>
                <td className="p-2">
                  <div className="flex items-center justify-center gap-1">
                    <button className="p-1 hover:bg-zinc-200 rounded" title="PDF Factura">
                      <FileText className="h-4 w-4 text-red-500" />
                    </button>
                    <button className="p-1 hover:bg-zinc-200 rounded" title="XML">
                      <File className="h-4 w-4 text-green-600" />
                    </button>
                    <button className="p-1 hover:bg-zinc-200 rounded" title="Entrada Sistema">
                      <FileSpreadsheet className="h-4 w-4 text-blue-500" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {/* Subtotal del proveedor */}
            <tr className="bg-zinc-200 font-bold">
              <td colSpan={6} className="p-2 text-right text-xs">SUBTOTAL {proveedor.proveedor_nombre}:</td>
              <td className="p-2 text-right font-mono">{formatCurrency(proveedor.subtotal_importe)}</td>
              <td className="p-2 text-right font-mono">{formatCurrency(proveedor.subtotal_saldo)}</td>
              <td className="p-2"></td>
              <td className="p-2 text-right font-mono text-green-700">{formatCurrency(proveedor.facturas.reduce((sum, f) => sum + (f.decision_pago ? (f.importe_a_pagar || f.saldo || 0) : 0), 0))}</td>
              <td className="p-2"></td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  };

  // Componente interno para el header de proveedor
  const ProveedorHeader = ({ proveedor, provKey, isExpanded }) => (
    <div
      className="bg-zinc-100 px-4 py-2 flex items-center justify-between cursor-pointer hover:bg-zinc-200 transition border-l-4 border-l-zinc-400"
      onClick={() => onToggleProveedor(provKey)}
      data-testid={`proveedor-${provKey}`}
    >
      <div className="flex items-center gap-2">
        <ChevronRight className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
        <div>
          <h3 className="font-medium text-sm text-zinc-800">{proveedor.proveedor_nombre}</h3>
          {proveedor.sucursal && (
            <p className="text-xs text-zinc-500">{proveedor.sucursal}</p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-4 text-xs">
        <div className="text-right">
          <p className="text-zinc-500">Facturas</p>
          <p className="font-medium">{proveedor.cantidad_facturas}</p>
        </div>
        <div className="text-right">
          <p className="text-zinc-500">Saldo</p>
          <p className="font-bold text-zinc-800">{formatCurrency(proveedor.subtotal_saldo)}</p>
        </div>
        {proveedor.cantidad_vencidas > 0 && (
          <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs font-medium">
            {proveedor.cantidad_vencidas} venc.
          </span>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-4" data-testid="cxp-container">
      {/* Filtros - FASE 3.2: Unidad de Negocio */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-7 gap-3 items-end">
            {/* Selector de Unidad de Negocio */}
            <div>
              <Label className="text-xs text-zinc-500">Unidad de Negocio</Label>
              {unidadesNegocio.length === 1 ? (
                <div className="w-full px-3 py-2 border rounded-lg text-sm mt-1 bg-zinc-50 flex items-center gap-2">
                  <Building2 className="h-3 w-3 text-zinc-400" />
                  <span className="truncate">{unidadesNegocio[0].nombre}</span>
                </div>
              ) : (
                <select
                  value={selectedUnidad}
                  onChange={(e) => onUnidadChange(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm mt-1"
                  disabled={loadingUnidades}
                  data-testid="cxp-unidad-select"
                >
                  <option value="">{loadingUnidades ? "Cargando..." : "Todas"}</option>
                  {unidadesNegocio.map(u => (
                    <option key={u.id} value={u.id}>{u.nombre}</option>
                  ))}
                </select>
              )}
            </div>
            <div>
              <Label className="text-xs text-zinc-500">Fecha de Corte</Label>
              <Input
                type="date"
                value={cxpFechaCorte}
                onChange={(e) => onFechaCorteChange(e.target.value)}
                className="mt-1"
                data-testid="cxp-fecha-corte"
              />
            </div>
            {/* FASE 1 CxP: Filtro Sucursal oculto condicionalmente 
                hideSucursalFilter=true → CxP opera exclusivamente por Unidad de Negocio
                La lógica interna (cxpFiltroSucursal) se mantiene para compatibilidad legacy */}
            {!hideSucursalFilter && (
              <div>
                <Label className="text-xs text-zinc-500">Sucursal</Label>
                <select
                  value={cxpFiltroSucursal}
                  onChange={(e) => onFiltroSucursalChange(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm mt-1"
                  disabled={userPermissions.allowedSucursales.length === 1 && !userPermissions.canSeeAll}
                  data-testid="cxp-sucursal-select"
                >
                  {userPermissions.canSeeAll && (
                    <option value="">Todas</option>
                  )}
                  {sucursalesFiltradas.map(s => (
                    <option key={s.SucursalID} value={s.SucursalID}>
                      {s.Nombre_Sucursal} ({s.CantidadFacturas || 0} fact.)
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div className="relative">
              <Label className="text-xs text-zinc-500">Proveedor</Label>
              <Input
                type="text"
                placeholder="Buscar nombre, RFC, clave..."
                value={cxpBusquedaProveedor}
                onChange={(e) => onBusquedaProveedorChange(e.target.value)}
                className="mt-1"
                data-testid="cxp-busqueda-proveedor"
              />
              {cxpBusquedaProveedor && (
                <div className="absolute z-50 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {proveedoresFiltrados.length > 0 ? (
                    proveedoresFiltrados.map((p, idx) => (
                      <div
                        key={p.proveedor_id || `prov-${idx}`}
                        className="px-3 py-2 hover:bg-zinc-100 cursor-pointer text-sm border-b last:border-b-0"
                        onClick={() => onFiltroProveedorSelect(p.proveedor_id || p.proveedor_nombre, p.proveedor_nombre)}
                        data-testid={`cxp-proveedor-option-${p.proveedor_id || idx}`}
                      >
                        <div className="font-medium">{p.proveedor_nombre}</div>
                        <div className="text-xs text-zinc-500 flex justify-between">
                          <span>RFC: {p.proveedor_rfc || 'N/A'}</span>
                          <span className="text-green-600">{p.cantidad_facturas} fact.</span>
                        </div>
                        {p.categoria && (
                          <span className={`text-xs px-1 rounded ${
                            p.categoria === 'A' ? 'bg-emerald-100 text-emerald-700' :
                            p.categoria === 'B' ? 'bg-amber-100 text-amber-700' :
                            'bg-slate-100 text-slate-700'
                          }`}>
                            {p.categoria}
                          </span>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="px-3 py-2 text-sm text-zinc-500 text-center">
                      Sin resultados
                    </div>
                  )}
                </div>
              )}
              {cxpFiltroProveedor && (
                <button
                  onClick={onLimpiarFiltroProveedor}
                  className="absolute right-2 top-8 text-zinc-400 hover:text-zinc-600"
                  title="Limpiar filtro"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={cxpSoloVencidas}
                  onChange={(e) => onSoloVencidasChange(e.target.checked)}
                  className="rounded"
                  data-testid="cxp-solo-vencidas"
                />
                Solo vencidas
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={cxpSoloDecision}
                  onChange={(e) => onSoloDecisionChange(e.target.checked)}
                  className="rounded"
                  data-testid="cxp-solo-decision"
                />
                Con decisión
              </label>
            </div>
            <div className="flex gap-2">
              <Button onClick={onFiltrar} disabled={loading} className="flex-1" data-testid="cxp-filtrar-btn">
                <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                Filtrar
              </Button>
              <Button variant="outline" onClick={onExportarCSV} data-testid="cxp-exportar-btn">
                <Download className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Acciones Masivas */}
      {(cxpData?.proveedores || []).length > 0 && (
        <div className="flex items-center justify-between bg-zinc-100 rounded-lg p-3" data-testid="cxp-acciones-masivas">
          <div className="flex items-center gap-4 text-sm">
            <span className="text-zinc-600">
              <strong className="text-red-600">{totales.total_vencidas || 0}</strong> facturas vencidas
            </span>
            <span className="text-zinc-400">|</span>
            <span className="text-zinc-600">
              <strong className="text-green-600">{totales.facturas_marcadas || 0}</strong> marcadas para pago
            </span>
            <span className="text-zinc-400">|</span>
            <span className="font-bold text-blue-600">
              Total a pagar: {formatCurrency(totales.total_a_pagar || 0)}
            </span>
          </div>
          <div className="flex gap-2">
            <Button 
              onClick={onMarcarTodasVencidas}
              disabled={loading}
              className="bg-green-600 hover:bg-green-700"
              data-testid="cxp-marcar-todas-btn"
            >
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Marcar Todas las Vencidas
            </Button>
            <Button 
              onClick={onDesmarcarTodas}
              disabled={loading}
              variant="outline"
              className="text-red-600 border-red-300 hover:bg-red-50"
              data-testid="cxp-desmarcar-todas-btn"
            >
              <XCircle className="h-4 w-4 mr-2" />
              Desmarcar Todas
            </Button>
          </div>
        </div>
      )}
      
      {/* Resumen por Antigüedad */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3" data-testid="cxp-resumen-antiguedad">
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-3">
            <p className="text-xs text-zinc-500">Corriente</p>
            <p className="text-lg font-bold text-green-600">{formatCurrency(antiguedad.corriente?.monto || 0)}</p>
            <p className="text-xs text-zinc-400">{antiguedad.corriente?.cantidad || 0} facturas</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-yellow-500">
          <CardContent className="p-3">
            <p className="text-xs text-zinc-500">1-30 días</p>
            <p className="text-lg font-bold text-yellow-600">{formatCurrency(antiguedad.vencidas_1_30?.monto || 0)}</p>
            <p className="text-xs text-zinc-400">{antiguedad.vencidas_1_30?.cantidad || 0} facturas</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="p-3">
            <p className="text-xs text-zinc-500">31-60 días</p>
            <p className="text-lg font-bold text-orange-600">{formatCurrency(antiguedad.vencidas_31_60?.monto || 0)}</p>
            <p className="text-xs text-zinc-400">{antiguedad.vencidas_31_60?.cantidad || 0} facturas</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-red-500">
          <CardContent className="p-3">
            <p className="text-xs text-zinc-500">61-90 días</p>
            <p className="text-lg font-bold text-red-600">{formatCurrency(antiguedad.vencidas_61_90?.monto || 0)}</p>
            <p className="text-xs text-zinc-400">{antiguedad.vencidas_61_90?.cantidad || 0} facturas</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-red-700">
          <CardContent className="p-3">
            <p className="text-xs text-zinc-500">+90 días</p>
            <p className="text-lg font-bold text-red-700">{formatCurrency(antiguedad.vencidas_90_plus?.monto || 0)}</p>
            <p className="text-xs text-zinc-400">{antiguedad.vencidas_90_plus?.cantidad || 0} facturas</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-blue-600 bg-blue-50">
          <CardContent className="p-3">
            <p className="text-xs text-blue-600 font-medium">SALDO TOTAL CxP</p>
            <p className="text-lg font-bold text-blue-700">{formatCurrency(totales.total_saldo || 0)}</p>
            <p className="text-xs text-blue-500">{cxpData?.proveedores?.reduce((acc, p) => acc + (p.facturas?.length || 0), 0) || 0} facturas</p>
          </CardContent>
        </Card>
      </div>
      
      {/* Botones Expandir/Colapsar y Toggle de Vista */}
      {(cxpData?.proveedores || []).length > 0 && (
        <div className="flex items-center justify-between" data-testid="cxp-controles-vista">
          {/* Toggle de Vista */}
          <div className="flex items-center gap-2 bg-zinc-100 rounded-lg p-1">
            <button
              onClick={() => onVistaModeChange('categorias')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                cxpVistaMode === 'categorias' 
                  ? 'bg-white text-zinc-800 shadow-sm' 
                  : 'text-zinc-500 hover:text-zinc-700'
              }`}
              data-testid="cxp-vista-categorias-btn"
            >
              <PieChart className="h-3 w-3 inline mr-1" />
              Por Categoría
            </button>
            <button
              onClick={() => onVistaModeChange('proveedores')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                cxpVistaMode === 'proveedores' 
                  ? 'bg-white text-zinc-800 shadow-sm' 
                  : 'text-zinc-500 hover:text-zinc-700'
              }`}
              data-testid="cxp-vista-proveedores-btn"
            >
              <Building2 className="h-3 w-3 inline mr-1" />
              Por Proveedor
            </button>
          </div>
          
          {/* Botones Expandir/Colapsar */}
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={onExpandirTodos}
              className="text-xs"
              data-testid="cxp-expandir-todos-btn"
            >
              <ChevronDown className="h-3 w-3 mr-1" />
              Expandir Todos
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={onColapsarTodos}
              className="text-xs"
              data-testid="cxp-colapsar-todos-btn"
            >
              <ChevronUp className="h-3 w-3 mr-1" />
              Colapsar Todos
            </Button>
          </div>
        </div>
      )}
      
      {/* Vista de datos según modo seleccionado */}
      <div className="space-y-4" data-testid="cxp-lista-datos">
        {(cxpData?.proveedores || []).length === 0 ? (
          <Card className="border-2 border-dashed">
            <CardContent className="py-12 text-center">
              <CreditCard className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
              <p className="text-zinc-500">No hay facturas pendientes con los filtros seleccionados</p>
            </CardContent>
          </Card>
        ) : cxpVistaMode === 'categorias' ? (
          /* VISTA POR CATEGORÍAS (A, B, X, M) -> Proveedor -> Facturas */
          reagruparCxPPorProveedores(cxpData?.proveedores || []).map(categoria => (
            <Card key={categoria.tipo} className="overflow-hidden border-2" data-testid={`categoria-${categoria.tipo}`}>
              {/* Header de Categoría (A, B, X, M) */}
              <div
                className={`px-4 py-3 flex items-center justify-between cursor-pointer transition ${
                  categoria.tipo === 'A' ? 'bg-emerald-600 hover:bg-emerald-700 text-white' :
                  categoria.tipo === 'B' ? 'bg-amber-600 hover:bg-amber-700 text-white' :
                  categoria.tipo === 'M' ? 'bg-indigo-600 hover:bg-indigo-700 text-white' :
                  'bg-slate-600 hover:bg-slate-700 text-white'
                }`}
                onClick={() => onToggleCategoria(categoria.tipo)}
              >
                <div className="flex items-center gap-3">
                  <ChevronRight className={`h-6 w-6 transition-transform ${cxpCategoriasExpandidas[categoria.tipo] ? 'rotate-90' : ''}`} />
                  <div>
                    <h2 className="text-lg font-bold">{categoria.nombre}</h2>
                    <p className="text-xs opacity-80">{categoria.proveedores.length} proveedores</p>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div className="text-right">
                    <p className="text-xs opacity-80">Facturas</p>
                    <p className="font-bold text-lg">{categoria.cantidad_facturas}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs opacity-80">Saldo Total</p>
                    <p className="font-bold text-lg">{formatCurrency(categoria.subtotal_saldo)}</p>
                  </div>
                  {categoria.cantidad_vencidas > 0 && (
                    <span className="px-3 py-1 bg-red-500 rounded-full text-xs font-bold">
                      {categoria.cantidad_vencidas} vencidas
                    </span>
                  )}
                </div>
              </div>
              
              {/* Proveedores dentro de la categoría */}
              {cxpCategoriasExpandidas[categoria.tipo] && (
                <div className="divide-y divide-zinc-200">
                  {categoria.proveedores.map(proveedor => {
                    const provKey = `${categoria.tipo}_${proveedor.proveedor_nombre}`;
                    return (
                      <div key={provKey} className="bg-white">
                        <ProveedorHeader 
                          proveedor={proveedor} 
                          provKey={provKey} 
                          isExpanded={cxpExpandidos[provKey]} 
                        />
                        {cxpExpandidos[provKey] && (
                          <FacturasTable proveedor={proveedor} />
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          ))
        ) : (
          /* VISTA POR PROVEEDOR CON AGRUPACIÓN A/B/C - Mismo estilo que Por Categoría */
          reagruparCxPPorProveedores(cxpData?.proveedores || []).map(categoria => {
            const colorCategoria = {
              A: { bg: 'bg-emerald-600', border: 'border-l-emerald-500', text: 'ALIMENTOS' },
              B: { bg: 'bg-amber-600', border: 'border-l-amber-500', text: 'BEBIDAS' },
              X: { bg: 'bg-slate-600', border: 'border-l-slate-500', text: 'OTROS' },
              M: { bg: 'bg-indigo-600', border: 'border-l-indigo-500', text: 'MPRO' }
            }[categoria.tipo] || { bg: 'bg-slate-600', border: 'border-l-slate-500', text: 'OTROS' };
            
            return (
              <Card key={categoria.tipo} className={`overflow-hidden ${colorCategoria.border} border-l-4`} data-testid={`categoria-prov-${categoria.tipo}`}>
                {/* Header de Categoría */}
                <div
                  className={`${colorCategoria.bg} text-white px-4 py-3 flex items-center justify-between cursor-pointer hover:opacity-90 transition`}
                  onClick={() => onToggleCategoria(categoria.tipo)}
                >
                  <div className="flex items-center gap-3">
                    <ChevronRight className={`h-5 w-5 transition-transform ${cxpCategoriasExpandidas[categoria.tipo] ? 'rotate-90' : ''}`} />
                    <div>
                      <h2 className="font-bold text-lg">{categoria.tipo} - {colorCategoria.text}</h2>
                      <p className="text-xs opacity-80">{categoria.proveedores.length} proveedores | {categoria.cantidad_facturas} facturas</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    <div className="text-right">
                      <p className="text-xs opacity-80">Saldo Total</p>
                      <p className="font-bold text-lg">{formatCurrency(categoria.subtotal_saldo)}</p>
                    </div>
                    {categoria.cantidad_vencidas > 0 && (
                      <span className="px-3 py-1 bg-red-500 rounded-full text-xs font-bold">
                        {categoria.cantidad_vencidas} vencidas
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Proveedores dentro de la categoría */}
                {cxpCategoriasExpandidas[categoria.tipo] && (
                  <div className="divide-y divide-zinc-200">
                    {categoria.proveedores.map(proveedor => {
                      const provKey = `prov_${categoria.tipo}_${proveedor.proveedor_nombre}`;
                      return (
                        <div key={provKey} className="bg-white">
                          <ProveedorHeader 
                            proveedor={proveedor} 
                            provKey={provKey} 
                            isExpanded={cxpExpandidos[provKey]} 
                          />
                          {cxpExpandidos[provKey] && (
                            <FacturasTable proveedor={proveedor} />
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </Card>
            );
          })
        )}
      </div>
      
      {/* Totales Generales */}
      {(cxpData?.proveedores || []).length > 0 && (
        <Card className="bg-zinc-800 text-white" data-testid="cxp-totales-generales">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div>
                  <p className="text-xs text-zinc-400">Proveedores</p>
                  <p className="text-xl font-bold">{totales.total_proveedores}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-400">Facturas</p>
                  <p className="text-xl font-bold">{totales.total_facturas}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-400">Vencidas</p>
                  <p className="text-xl font-bold text-red-400">{totales.total_vencidas}</p>
                </div>
              </div>
              <div className="flex items-center gap-6 text-right">
                <div>
                  <p className="text-xs text-zinc-400">Total Importe</p>
                  <p className="text-xl font-bold">{formatCurrency(totales.total_importe)}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-400">Total Saldo</p>
                  <p className="text-xl font-bold">{formatCurrency(totales.total_saldo)}</p>
                </div>
                <div className="bg-green-600 rounded-lg px-4 py-2">
                  <p className="text-xs text-green-200">TOTAL A PAGAR</p>
                  <p className="text-2xl font-bold">{formatCurrency(totales.total_a_pagar)}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
