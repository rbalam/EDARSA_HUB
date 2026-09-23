/**
 * EDARSA HUB - Panel de Re-sincronización Manual
 * Consola Administrativa de Scheduler
 *
 * Catálogo CANÓNICO (dbo.Sistema_Sync_Catalogo): tipos de sync agrupados por
 * `grupo`, ejecutables individualmente o por grupo. Si una sync seleccionada
 * requiere otra (dependencia), se AGREGA automáticamente y se pide confirmar,
 * permitiendo des-seleccionar las opcionales (las obligatorias quedan fijas).
 *
 * MÁXIMAS: NO hardcode (catálogo SQL) · DRY RUN primero · motivo obligatorio.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import api from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  RefreshCw, CheckCircle2, XCircle, AlertTriangle, Loader2, Database, Server,
  Play, History, Layers, Link2, Lock, Clock,
} from 'lucide-react';

const formatDateTime = (isoString) => {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleString('es-MX', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
};

const RIESGO_COLOR = { ALTO: 'destructive', MEDIO: 'outline', BAJO: 'secondary' };

const formatMoney = (value) => {
  const number = Number(value);
  if (!Number.isFinite(number)) return '-';
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(number);
};

const formatInteger = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? Math.trunc(number).toLocaleString('es-MX') : '-';
};

const splitDailyDateRange = (start, end) => {
  const first = new Date(`${start}T00:00:00Z`);
  const last = new Date(`${end}T00:00:00Z`);
  if (Number.isNaN(first.getTime()) || Number.isNaN(last.getTime()) || first > last) {
    return [[start, end]];
  }
  const days = [];
  const current = new Date(first);
  while (current <= last) {
    const day = current.toISOString().slice(0, 10);
    days.push([day, day]);
    current.setUTCDate(current.getUTCDate() + 1);
  }
  return days;
};

export default function ResyncPanel() {
  const [options, setOptions] = useState({ tipos_sync: [], unidades: [], grupos: [] });
  const [loadingOptions, setLoadingOptions] = useState(true);

  // Selección
  const [selectedCodigos, setSelectedCodigos] = useState([]);
  const [unidadId, setUnidadId] = useState('');
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');
  const [motivo, setMotivo] = useState('');
  const [netpayReports, setNetpayReports] = useState({
    transacciones: true,
    depositos: true,
  });

  // Diálogo de resolución de dependencias / confirmación
  const [resolveDialog, setResolveDialog] = useState({ open: false, isDryRun: true, loading: false });
  const [resolvedItems, setResolvedItems] = useState([]); // [{codigo, nombre, grupo, obligatoria, seleccionado_directo, handler_implementado,...}]
  const [itemChecked, setItemChecked] = useState({});      // {codigo: bool}

  // Ejecución
  const [executing, setExecuting] = useState(false);
  const [batchResults, setBatchResults] = useState([]);
  const [progress, setProgress] = useState({ current: 0, total: 0 });

  // Historial
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const fetchOptions = useCallback(async () => {
    try {
      setLoadingOptions(true);
      const response = await api.get('/admin/scheduler/resync/options');
      setOptions({
        tipos_sync: response.data.tipos_sync || [],
        unidades: response.data.unidades || [],
        grupos: response.data.grupos || [],
      });
    } catch (error) {
      console.error('Error cargando opciones:', error);
    } finally {
      setLoadingOptions(false);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      setLoadingHistory(true);
      const response = await api.get('/admin/scheduler/resync/history?limit=20');
      setHistory(response.data.ejecuciones || []);
    } catch (error) {
      console.error('Error cargando historial:', error);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => { fetchOptions(); fetchHistory(); }, [fetchOptions, fetchHistory]);

  const tipoMap = useMemo(() => {
    const m = {};
    (options.tipos_sync || []).forEach(t => { m[t.codigo] = t; });
    return m;
  }, [options.tipos_sync]);

  const requiereFechas = useMemo(
    () => selectedCodigos.some(c => tipoMap[c]?.requiere_rango_fechas),
    [selectedCodigos, tipoMap]
  );

  const toggleTipo = (codigo) => {
    setSelectedCodigos(prev =>
      prev.includes(codigo) ? prev.filter(c => c !== codigo) : [...prev, codigo]
    );
  };

  const toggleGrupo = (grupo) => {
    const codigos = grupo.tipos.map(t => t.codigo);
    const allSelected = codigos.every(c => selectedCodigos.includes(c));
    setSelectedCodigos(prev =>
      allSelected ? prev.filter(c => !codigos.includes(c)) : [...new Set([...prev, ...codigos])]
    );
  };

  const netpaySeleccionado = selectedCodigos.includes('finanzas_netpay');
  const netpayReportesValidos = !netpaySeleccionado || netpayReports.transacciones || netpayReports.depositos;

  const getNetpayExecutionCode = () => {
    if (netpayReports.transacciones && netpayReports.depositos) return 'finanzas_netpay';
    if (netpayReports.transacciones) return 'finanzas_netpay_transacciones';
    if (netpayReports.depositos) return 'finanzas_netpay_depositos';
    return 'finanzas_netpay';
  };

  const formValid = motivo.length >= 10 && unidadId && selectedCodigos.length > 0
    && netpayReportesValidos
    && (!requiereFechas || (fechaInicio && fechaFin));

  // Paso 1: resolver dependencias y abrir confirmación
  const handleResolve = async (isDryRun) => {
    if (!formValid) {
      alert('Complete unidad, motivo (mín. 10), seleccione al menos un tipo y el rango de fechas si aplica.');
      return;
    }
    setResolveDialog({ open: true, isDryRun, loading: true });
    setResolvedItems([]);
    try {
      const resp = await api.post('/admin/scheduler/resync/resolve', { codigos: selectedCodigos });
      const items = resp.data.items || [];
      setResolvedItems(items);
      const checks = {};
      items.forEach(it => { checks[it.codigo] = true; });
      setItemChecked(checks);
    } catch (error) {
      alert('Error resolviendo dependencias: ' + (error.response?.data?.detail || error.message));
      setResolveDialog({ open: false, isDryRun, loading: false });
      return;
    }
    setResolveDialog({ open: true, isDryRun, loading: false });
  };

  const toggleItemCheck = (item) => {
    if (item.obligatoria && !item.seleccionado_directo) return; // dependencia obligatoria: bloqueada
    setItemChecked(prev => ({ ...prev, [item.codigo]: !prev[item.codigo] }));
  };

  // Paso 2: ejecutar en orden el conjunto confirmado
  const handleExecuteBatch = async () => {
    const finalItems = resolvedItems.filter(it => itemChecked[it.codigo]);
    if (finalItems.length === 0) { alert('Seleccione al menos un tipo para ejecutar.'); return; }

    const isDryRun = resolveDialog.isDryRun;
    setResolveDialog({ open: false, isDryRun, loading: false });
    setExecuting(true);
    setBatchResults([]);

    const results = [];
    const fi = fechaInicio || new Date().toISOString().slice(0, 10);
    const ff = fechaFin || new Date().toISOString().slice(0, 10);

    const executionPlan = finalItems.flatMap((it) => {
      const executionCodigo = it.codigo === 'finanzas_netpay' ? getNetpayExecutionCode() : it.codigo;
      if (executionCodigo !== 'comercial_ventas_cerradas') {
        return [{ it, executionCodigo, fechaInicioItem: fi, fechaFinItem: ff }];
      }
      return splitDailyDateRange(fi, ff).map(([dayStart, dayEnd]) => ({
        it,
        executionCodigo,
        fechaInicioItem: dayStart,
        fechaFinItem: dayEnd,
      }));
    });

    setProgress({ current: 0, total: executionPlan.length });

    for (let i = 0; i < executionPlan.length; i++) {
      const { it, executionCodigo, fechaInicioItem, fechaFinItem } = executionPlan[i];
      setProgress({ current: i + 1, total: executionPlan.length });
      try {
        const resp = await api.post('/admin/scheduler/resync/execute', {
          tipo_sync: executionCodigo,
          unidad_negocio_id: unidadId,
          fecha_inicio: fechaInicioItem,
          fecha_fin: fechaFinItem,
          motivo,
          dry_run: isDryRun,
        }, { timeout: 120000 });
        results.push({
          tipo: {
            ...it,
            codigo: executionCodigo,
            nombre: executionCodigo === 'comercial_ventas_cerradas'
              ? `${it.nombre} · ${fechaInicioItem}`
              : it.nombre,
          },
          data: {
            ...resp.data,
            fecha_inicio: resp.data?.fecha_inicio || fechaInicioItem,
            fecha_fin: resp.data?.fecha_fin || fechaFinItem,
          },
        });
      } catch (error) {
        const errorData = error.response?.data || {};
        const resultadoError = errorData?.resultado || {};
        const isTimeout = error.code === 'ECONNABORTED' || String(error.message || '').toLowerCase().includes('timeout');
        const errorMessage = isTimeout
          ? `TIMEOUT_CLIENTE: la re-sincronización del día ${fechaInicioItem} superó 120 segundos.`
          : errorData?.error_message
            || resultadoError?.error_message
            || errorData?.detail
            || error.message
            || `Error de ejecución para ${fechaInicioItem}`;
        results.push({
          tipo: {
            ...it,
            codigo: executionCodigo,
            nombre: executionCodigo === 'comercial_ventas_cerradas'
              ? `${it.nombre} · ${fechaInicioItem}`
              : it.nombre,
          },
          data: {
            success: false,
            modo: isDryRun ? 'DRY_RUN' : 'REAL',
            stage: isTimeout ? 'TIMEOUT_CLIENTE' : (errorData?.stage || resultadoError?.stage || 'EJECUCION'),
            error_message: errorMessage,
            fecha_inicio: fechaInicioItem,
            fecha_fin: fechaFinItem,
          },
        });
      }
      setBatchResults([...results]);
    }
    setExecuting(false);
    fetchHistory();
  };

  const selectedUnidad = options.unidades.find(u => u.id === unidadId);

  if (loadingOptions) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> Cargando catálogo de sincronizaciones...
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="resync-panel">
      <Card data-testid="resync-form-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5" /> Re-sincronización Manual
          </CardTitle>
          <CardDescription>
            Selecciona una o varias sincronizaciones (individual o por grupo).
            <strong className="text-amber-600 ml-1">Ejecuta DRY RUN primero.</strong>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Catálogo agrupado */}
          <div className="space-y-3">
            <Label className="flex items-center gap-2"><Layers className="w-4 h-4" /> Tipos de Sincronización (por grupo)</Label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {(options.grupos || []).map(grupo => {
                const codigos = grupo.tipos.map(t => t.codigo);
                const allSel = codigos.every(c => selectedCodigos.includes(c));
                const someSel = codigos.some(c => selectedCodigos.includes(c));
                return (
                  <div key={grupo.grupo} className="border rounded-lg p-3 bg-zinc-50/50" data-testid={`grupo-${grupo.grupo}`}>
                    <div className="flex items-center justify-between mb-2 pb-2 border-b">
                      <span className="font-semibold text-sm flex items-center gap-2">
                        <Database className="w-4 h-4 text-zinc-500" /> {grupo.grupo}
                      </span>
                      <button
                        type="button"
                        onClick={() => toggleGrupo(grupo)}
                        className="text-xs text-blue-600 hover:underline"
                        data-testid={`btn-toggle-grupo-${grupo.grupo}`}
                      >
                        {allSel ? 'Quitar grupo' : (someSel ? 'Completar grupo' : 'Seleccionar grupo')}
                      </button>
                    </div>
                    <div className="space-y-2">
                      {grupo.tipos.map(tipo => (
                        <label
                          key={tipo.codigo}
                          className="flex items-start gap-2 cursor-pointer text-sm hover:bg-white rounded p-1"
                          data-testid={`tipo-row-${tipo.codigo}`}
                        >
                          <Checkbox
                            checked={selectedCodigos.includes(tipo.codigo)}
                            onCheckedChange={() => toggleTipo(tipo.codigo)}
                            data-testid={`check-tipo-${tipo.codigo}`}
                          />
                          <span className="flex-1">
                            <span className="font-medium">{tipo.nombre}</span>
                            <span className="block text-xs text-zinc-500">{tipo.descripcion}</span>
                              {tipo.codigo === 'finanzas_netpay' && selectedCodigos.includes('finanzas_netpay') && (
                                <span className="mt-2 grid grid-cols-1 gap-1 rounded-md border bg-white p-2" onClick={(e) => e.stopPropagation()}>
                                  <span className="text-[11px] font-medium text-zinc-500">Reportes a sincronizar</span>
                                  <span className="flex items-center gap-2 text-xs text-zinc-700">
                                    <Checkbox
                                      checked={netpayReports.transacciones}
                                      onCheckedChange={(checked) => setNetpayReports(prev => ({ ...prev, transacciones: Boolean(checked) }))}
                                      data-testid="check-netpay-transacciones"
                                    />
                                    Transacciones
                                  </span>
                                  <span className="flex items-center gap-2 text-xs text-zinc-700">
                                    <Checkbox
                                      checked={netpayReports.depositos}
                                      onCheckedChange={(checked) => setNetpayReports(prev => ({ ...prev, depositos: Boolean(checked) }))}
                                      data-testid="check-netpay-depositos"
                                    />
                                    Depósitos
                                  </span>
                                  {!netpayReportesValidos && (
                                    <span className="text-xs text-red-600">Selecciona al menos un reporte NetPay.</span>
                                  )}
                                </span>
                              )}
                            <span className="flex items-center gap-1 mt-1 flex-wrap">
                              {!tipo.handler_implementado && (
                                <Badge variant="outline" className="text-[10px] gap-1 text-amber-600 border-amber-300">
                                  <Clock className="w-3 h-3" /> Handler pendiente
                                </Badge>
                              )}
                              {(tipo.dependencias || []).length > 0 && (
                                <Badge variant="outline" className="text-[10px] gap-1">
                                  <Link2 className="w-3 h-3" /> {tipo.dependencias.length} dep.
                                </Badge>
                              )}
                            </span>
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
            {selectedCodigos.length > 0 && (
              <p className="text-xs text-zinc-600" data-testid="seleccionados-count">
                {selectedCodigos.length} sincronización(es) seleccionada(s).
              </p>
            )}
          </div>

          {/* Unidad + fechas */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Unidad de Negocio</Label>
              <Select value={unidadId} onValueChange={setUnidadId} data-testid="select-unidad">
                <SelectTrigger><SelectValue placeholder="Seleccione unidad..." /></SelectTrigger>
                <SelectContent>
                  {options.unidades.map(unidad => (
                    <SelectItem key={unidad.id} value={unidad.id}>
                      <div className="flex items-center gap-2">
                        <Server className="w-4 h-4" /> {unidad.nombre}
                        <Badge variant="outline" className="ml-2 text-xs">{unidad.sistema}</Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Fecha Inicio {requiereFechas && <span className="text-red-500">*</span>}</Label>
              <Input type="date" value={fechaInicio} onChange={(e) => setFechaInicio(e.target.value)} data-testid="input-fecha-inicio" />
            </div>
            <div className="space-y-2">
              <Label>Fecha Fin {requiereFechas && <span className="text-red-500">*</span>}</Label>
              <Input type="date" value={fechaFin} onChange={(e) => setFechaFin(e.target.value)} data-testid="input-fecha-fin" />
            </div>
          </div>

          {/* Motivo */}
          <div className="space-y-2">
            <Label>Motivo (obligatorio, mín. 10 caracteres)</Label>
            <Textarea
              placeholder="Describa el motivo de esta re-sincronización..."
              value={motivo} onChange={(e) => setMotivo(e.target.value)} rows={2} data-testid="input-motivo"
            />
            <p className="text-xs text-zinc-500">
              {motivo.length}/10 caracteres mínimos
              {motivo.length >= 10 && <CheckCircle2 className="w-3 h-3 inline ml-1 text-emerald-500" />}
            </p>
          </div>

          {/* Botones */}
          <div className="flex gap-3 pt-2">
            <Button
              onClick={() => handleResolve(true)}
              disabled={executing || !formValid}
              className="bg-amber-600 hover:bg-amber-700"
              data-testid="btn-dry-run"
            >
              <Play className="w-4 h-4 mr-2" /> Ejecutar DRY RUN
            </Button>
            <Button
              onClick={() => handleResolve(false)}
              disabled={executing || !formValid}
              className="bg-red-600 hover:bg-red-700"
              data-testid="btn-execute-real"
            >
              <RefreshCw className="w-4 h-4 mr-2" /> Ejecutar REAL
            </Button>
            {executing && (
              <span className="flex items-center text-sm text-zinc-600" data-testid="batch-progress">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Ejecutando {progress.current}/{progress.total}...
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Resultados del lote */}
      {batchResults.length > 0 && (
        <Card data-testid="batch-results-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Layers className="w-5 h-5" /> Resultados de Ejecución</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {batchResults.map((r, idx) => {
              const resultado = r.data.resultado || {};
              const detalle = Array.isArray(resultado.detalle)
                ? resultado.detalle
                : (Array.isArray(r.data.detalle) ? r.data.detalle : []);
              const querySource = resultado.query_source || r.data.query_source || '-';

              return (
                <Alert key={idx} variant={r.data.success ? 'default' : 'destructive'} data-testid={`result-${r.tipo.codigo}`}>
                  <AlertTitle className="flex items-center gap-2">
                    {r.data.success ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <XCircle className="w-4 h-4 text-red-600" />}
                    {r.tipo.nombre} <Badge variant="outline" className="ml-1">{r.data.modo}</Badge>
                  </AlertTitle>
                  <AlertDescription>
                    {r.data.success ? (
                      <div className="text-sm mt-1 space-y-3">
                        <div>
                          <span>Run ID: <span className="font-mono">{r.data.sync_run_id}</span></span>
                          {r.data.resultado && (
                            <span className="ml-3">Procesados: {resultado.records_processed || 0}
                              {r.data.modo === 'REAL' && ` · Insertados: ${resultado.records_inserted || 0} · Actualizados: ${resultado.records_updated || 0}`}
                            </span>
                          )}
                        </div>
                        {(r.data.warning_message || resultado.warning_message) && (
                          <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                            Advertencia {resultado.stage || r.data.stage || 'DETALLE_ISCAM'}: {r.data.warning_message || resultado.warning_message}
                          </p>
                        )}

                        {r.data.modo === 'DRY_RUN' && (
                          <div className="space-y-2" data-testid={`dry-run-detail-${r.tipo.codigo}`}>
                            <div className="flex flex-wrap gap-x-6 gap-y-1 rounded-md border bg-white px-3 py-2 text-xs text-zinc-600">
                              <span><strong>Fuente de consulta:</strong> <span className="font-mono">{querySource}</span></span>
                              <span><strong>Registros detallados:</strong> {detalle.length}</span>
                            </div>

                            {detalle.length > 0 ? (
                              <div className="overflow-x-auto rounded-md border bg-white">
                                <Table>
                                  <TableHeader>
                                    <TableRow>
                                      <TableHead className="whitespace-nowrap">Fecha</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">Venta</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">Propina</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">Total c/ propina</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">PAX</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">Cheques</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">Alimentos</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">Bebidas</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">Otros</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">Cortesías</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">Descuentos</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">Subtotal</TableHead>
                                      <TableHead className="text-right whitespace-nowrap">IVA</TableHead>
                                    </TableRow>
                                  </TableHeader>
                                  <TableBody>
                                    {detalle.map((fila, detalleIdx) => (
                                      <TableRow key={`${fila.fecha || 'sin-fecha'}-${detalleIdx}`}>
                                        <TableCell className="font-mono whitespace-nowrap">{fila.fecha || '-'}</TableCell>
                                        <TableCell className="text-right whitespace-nowrap font-medium">{formatMoney(fila.ventas_total)}</TableCell>
                                        <TableCell className="text-right whitespace-nowrap">{formatMoney(fila.propinas_total)}</TableCell>
                                        <TableCell className="text-right whitespace-nowrap">{formatMoney(fila.total_con_propina)}</TableCell>
                                        <TableCell className="text-right">{formatInteger(fila.pax_total)}</TableCell>
                                        <TableCell className="text-right">{formatInteger(fila.tickets_total)}</TableCell>
                                        <TableCell className="text-right whitespace-nowrap">{formatMoney(fila.alimentos)}</TableCell>
                                        <TableCell className="text-right whitespace-nowrap">{formatMoney(fila.bebidas)}</TableCell>
                                        <TableCell className="text-right whitespace-nowrap">{formatMoney(fila.otros)}</TableCell>
                                        <TableCell className="text-right whitespace-nowrap">{formatMoney(fila.cortesias)}</TableCell>
                                        <TableCell className="text-right whitespace-nowrap">{formatMoney(fila.descuentos)}</TableCell>
                                        <TableCell className="text-right whitespace-nowrap">{formatMoney(fila.subtotal)}</TableCell>
                                        <TableCell className="text-right whitespace-nowrap">{formatMoney(fila.iva)}</TableCell>
                                      </TableRow>
                                    ))}
                                  </TableBody>
                                </Table>
                              </div>
                            ) : (
                              <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                                El backend no devolvió filas de detalle para este DRY RUN. No ejecute REAL hasta validar la respuesta.
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm mt-1">{r.data.error_message}</p>
                    )}
                  </AlertDescription>
                </Alert>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* Historial */}
      <Card data-testid="resync-history-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><History className="w-5 h-5" /> Historial de Re-sincronizaciones</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingHistory ? (
            <div className="flex items-center justify-center p-4"><Loader2 className="w-5 h-5 animate-spin" /></div>
          ) : history.length === 0 ? (
            <p className="text-zinc-500 text-center py-4">No hay re-sincronizaciones registradas</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead><TableHead>Acción</TableHead><TableHead>Unidad</TableHead>
                  <TableHead>Rango</TableHead><TableHead>Estado</TableHead><TableHead>Usuario</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="text-sm">{formatDateTime(item.fecha)}</TableCell>
                    <TableCell><Badge variant={item.exito ? 'default' : 'destructive'}>{item.accion}</Badge></TableCell>
                    <TableCell>{item.detalles?.unidad || '-'}</TableCell>
                    <TableCell className="text-sm font-mono">{item.detalles?.fecha_inicio} → {item.detalles?.fecha_fin}</TableCell>
                    <TableCell>{item.exito ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> : <XCircle className="w-4 h-4 text-red-500" />}</TableCell>
                    <TableCell className="text-sm text-zinc-500">{item.detalles?.usuario || '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Diálogo de resolución de dependencias / confirmación */}
      <Dialog open={resolveDialog.open} onOpenChange={(open) => setResolveDialog(prev => ({ ...prev, open }))}>
        <DialogContent data-testid="confirm-resync-dialog" className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {resolveDialog.isDryRun ? 'Confirmar DRY RUN' : 'Confirmar Ejecución REAL'}
            </DialogTitle>
            <DialogDescription>
              {resolveDialog.isDryRun
                ? 'El DRY RUN no modifica datos. Revisa el conjunto a ejecutar.'
                : <span className="text-red-600 font-medium">Esta acción MODIFICARÁ datos en EDARSAHUB.</span>}
            </DialogDescription>
          </DialogHeader>

          {resolveDialog.loading ? (
            <div className="flex items-center justify-center py-8"><Loader2 className="w-6 h-6 animate-spin mr-2" /> Resolviendo dependencias...</div>
          ) : (
            <div className="py-2 space-y-3">
              {resolvedItems.some(it => !it.seleccionado_directo) && (
                <Alert>
                  <AlertTriangle className="w-4 h-4" />
                  <AlertTitle>Dependencias agregadas automáticamente</AlertTitle>
                  <AlertDescription className="text-sm">
                    Para un resultado consistente se incluyeron sincronizaciones relacionadas.
                    Puedes des-seleccionar las opcionales; las <strong>obligatorias</strong> quedan fijas.
                  </AlertDescription>
                </Alert>
              )}
              <div className="border rounded-lg divide-y" data-testid="resolved-items">
                {resolvedItems.map((it, idx) => {
                  const locked = it.obligatoria && !it.seleccionado_directo;
                  return (
                    <div key={it.codigo} className="flex items-center gap-3 p-2 text-sm" data-testid={`resolved-${it.codigo}`}>
                      <span className="text-xs text-zinc-400 w-5">{idx + 1}.</span>
                      <Checkbox
                        checked={!!itemChecked[it.codigo]}
                        disabled={locked}
                        onCheckedChange={() => toggleItemCheck(it)}
                        data-testid={`resolved-check-${it.codigo}`}
                      />
                      <div className="flex-1">
                        <span className="font-medium">{it.nombre}</span>
                        <span className="ml-2 text-xs text-zinc-500">({it.grupo})</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {it.seleccionado_directo
                          ? <Badge variant="secondary" className="text-[10px]">Seleccionada</Badge>
                          : <Badge variant="outline" className="text-[10px] gap-1"><Link2 className="w-3 h-3" /> Dependencia</Badge>}
                        {locked && <Lock className="w-3 h-3 text-zinc-400" />}
                        {!it.handler_implementado && (
                          <Badge variant="outline" className="text-[10px] gap-1 text-amber-600 border-amber-300">
                            <Clock className="w-3 h-3" /> Pendiente
                          </Badge>
                        )}
                        <Badge variant={RIESGO_COLOR[it.nivel_riesgo] || 'outline'} className="text-[10px]">{it.nivel_riesgo}</Badge>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="text-sm text-zinc-600 space-y-1">
                <p><strong>Unidad:</strong> {selectedUnidad?.nombre || unidadId}</p>
                {requiereFechas && <p><strong>Rango:</strong> {fechaInicio} a {fechaFin}</p>}
                <p><strong>Motivo:</strong> {motivo}</p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setResolveDialog(prev => ({ ...prev, open: false }))}>Cancelar</Button>
            <Button
              onClick={handleExecuteBatch}
              disabled={resolveDialog.loading || resolvedItems.filter(it => itemChecked[it.codigo]).length === 0}
              className={resolveDialog.isDryRun ? 'bg-amber-600 hover:bg-amber-700' : 'bg-red-600 hover:bg-red-700'}
              data-testid="confirm-execute-btn"
            >
              <Play className="w-4 h-4 mr-2" />
              {resolveDialog.isDryRun ? 'Ejecutar DRY RUN del conjunto' : 'Ejecutar REAL del conjunto'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
