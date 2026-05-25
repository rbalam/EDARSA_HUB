/**
 * EDARSA HUB - Panel de Re-sincronización Manual
 * Fase 0: Consola Administrativa de Scheduler
 * 
 * Features:
 * - Selección de tipo de sync y unidad
 * - Validación previa con dry_run
 * - Ejecución real con confirmación
 * - Historial de re-syncs
 * 
 * MÁXIMAS CUMPLIDAS:
 * - #8: Dry run obligatorio antes de ejecución real
 * - #6: Trazabilidad completa
 * - #7: Motivo obligatorio
 */

import { useState, useEffect, useCallback } from 'react';
import api from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  Database,
  Server,
  Calendar,
  FileText,
  Play,
  Eye,
  History,
} from 'lucide-react';


const formatDateTime = (isoString) => {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleString('es-MX', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};


export default function ResyncPanel() {
  // Estados de opciones
  const [options, setOptions] = useState({ tipos_sync: [], unidades: [] });
  const [loadingOptions, setLoadingOptions] = useState(true);
  
  // Estados del formulario
  const [tipoSync, setTipoSync] = useState('');
  const [unidadId, setUnidadId] = useState('');
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');
  const [motivo, setMotivo] = useState('');
  
  // Estados de validación
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  
  // Estados de ejecución
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState({ open: false, isDryRun: true });
  
  // Historial
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  
  // Cargar opciones
  const fetchOptions = useCallback(async () => {
    try {
      setLoadingOptions(true);
      const response = await api.get('/admin/scheduler/resync/options');
      setOptions(response.data);
    } catch (error) {
      console.error('Error cargando opciones:', error);
    } finally {
      setLoadingOptions(false);
    }
  }, []);
  
  // Cargar historial
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
  
  useEffect(() => {
    fetchOptions();
    fetchHistory();
  }, [fetchOptions, fetchHistory]);
  
  // Validar parámetros
  const handleValidate = async () => {
    if (!tipoSync || !unidadId || !fechaInicio || !fechaFin) {
      alert('Complete todos los campos obligatorios');
      return;
    }
    
    try {
      setValidating(true);
      setValidationResult(null);
      setExecutionResult(null);
      
      const response = await api.post('/admin/scheduler/resync/validate', {
        tipo_sync: tipoSync,
        unidad_negocio_id: unidadId,
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
      });
      
      setValidationResult(response.data);
    } catch (error) {
      setValidationResult({
        success: false,
        error: error.response?.data?.detail || 'Error de validación',
      });
    } finally {
      setValidating(false);
    }
  };
  
  // Ejecutar resync
  const handleExecute = async (isDryRun) => {
    if (!motivo || motivo.length < 10) {
      alert('Debe ingresar un motivo de al menos 10 caracteres');
      return;
    }
    
    setConfirmDialog({ open: false, isDryRun });
    
    try {
      setExecuting(true);
      setExecutionResult(null);
      
      const response = await api.post('/admin/scheduler/resync/execute', {
        tipo_sync: tipoSync,
        unidad_negocio_id: unidadId,
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        motivo: motivo,
        dry_run: isDryRun,
      });
      
      setExecutionResult(response.data);
      
      // Recargar historial
      fetchHistory();
    } catch (error) {
      setExecutionResult({
        success: false,
        error_message: error.response?.data?.detail || 'Error de ejecución',
      });
    } finally {
      setExecuting(false);
    }
  };
  
  const selectedTipoSync = options.tipos_sync.find(t => t.codigo === tipoSync);
  const selectedUnidad = options.unidades.find(u => u.id === unidadId);
  
  if (loadingOptions) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-6 h-6 animate-spin mr-2" />
        Cargando opciones...
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Formulario de Re-sync */}
      <Card data-testid="resync-form-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5" />
            Re-sincronización Manual
          </CardTitle>
          <CardDescription>
            Sincronización controlada de períodos históricos. 
            <strong className="text-amber-600 ml-1">Siempre ejecute DRY RUN primero.</strong>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Tipo de Sync */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Tipo de Sincronización</Label>
              <Select value={tipoSync} onValueChange={setTipoSync} data-testid="select-tipo-sync">
                <SelectTrigger>
                  <SelectValue placeholder="Seleccione tipo..." />
                </SelectTrigger>
                <SelectContent>
                  {options.tipos_sync.map(tipo => (
                    <SelectItem key={tipo.codigo} value={tipo.codigo}>
                      <div className="flex items-center gap-2">
                        <Database className="w-4 h-4" />
                        {tipo.nombre}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedTipoSync && (
                <p className="text-xs text-zinc-500">{selectedTipoSync.descripcion}</p>
              )}
            </div>
            
            <div className="space-y-2">
              <Label>Unidad de Negocio</Label>
              <Select value={unidadId} onValueChange={setUnidadId} data-testid="select-unidad">
                <SelectTrigger>
                  <SelectValue placeholder="Seleccione unidad..." />
                </SelectTrigger>
                <SelectContent>
                  {options.unidades.map(unidad => (
                    <SelectItem key={unidad.id} value={unidad.id}>
                      <div className="flex items-center gap-2">
                        <Server className="w-4 h-4" />
                        {unidad.nombre}
                        <Badge variant="outline" className="ml-2 text-xs">
                          {unidad.sistema}
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {/* Rango de fechas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Fecha Inicio</Label>
              <Input
                type="date"
                value={fechaInicio}
                onChange={(e) => setFechaInicio(e.target.value)}
                data-testid="input-fecha-inicio"
              />
            </div>
            <div className="space-y-2">
              <Label>Fecha Fin</Label>
              <Input
                type="date"
                value={fechaFin}
                onChange={(e) => setFechaFin(e.target.value)}
                data-testid="input-fecha-fin"
              />
            </div>
          </div>
          
          {/* Motivo */}
          <div className="space-y-2">
            <Label>Motivo (obligatorio, mín. 10 caracteres)</Label>
            <Textarea
              placeholder="Describa el motivo de esta re-sincronización..."
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              rows={2}
              data-testid="input-motivo"
            />
            <p className="text-xs text-zinc-500">
              {motivo.length}/10 caracteres mínimos
              {motivo.length >= 10 && <CheckCircle2 className="w-3 h-3 inline ml-1 text-emerald-500" />}
            </p>
          </div>
          
          {/* Botones de acción */}
          <div className="flex gap-3 pt-4">
            <Button
              onClick={handleValidate}
              disabled={validating || !tipoSync || !unidadId || !fechaInicio || !fechaFin}
              variant="outline"
              data-testid="btn-validate"
            >
              {validating ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Eye className="w-4 h-4 mr-2" />
              )}
              Validar Parámetros
            </Button>
            
            <Button
              onClick={() => setConfirmDialog({ open: true, isDryRun: true })}
              disabled={executing || !validationResult?.success || motivo.length < 10}
              className="bg-amber-600 hover:bg-amber-700"
              data-testid="btn-dry-run"
            >
              <Play className="w-4 h-4 mr-2" />
              Ejecutar DRY RUN
            </Button>
            
            <Button
              onClick={() => setConfirmDialog({ open: true, isDryRun: false })}
              disabled={executing || !validationResult?.success || motivo.length < 10 || !validationResult?.conectividad?.conectado}
              className="bg-red-600 hover:bg-red-700"
              data-testid="btn-execute-real"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Ejecutar REAL
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Resultado de validación */}
      {validationResult && (
        <Card data-testid="validation-result-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {validationResult.success ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600" />
              )}
              Resultado de Validación
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Conectividad */}
            <div className="flex items-center gap-3">
              <Badge variant={validationResult.conectividad?.conectado ? "default" : "destructive"}>
                {validationResult.conectividad?.conectado ? 'CONECTADO' : 'SIN CONEXIÓN'}
              </Badge>
              {!validationResult.conectividad?.conectado && (
                <span className="text-sm text-red-600">
                  {validationResult.conectividad?.error?.substring(0, 100)}...
                </span>
              )}
            </div>
            
            {/* Días existentes */}
            {validationResult.dias_existentes && (
              <div>
                <h4 className="font-medium mb-2">
                  Días existentes en destino: {validationResult.dias_existentes.cantidad}
                </h4>
                {validationResult.dias_existentes.cantidad > 0 ? (
                  <div className="bg-zinc-50 p-3 rounded text-sm">
                    {validationResult.dias_existentes.dias_existentes.map((dia, idx) => (
                      <div key={idx} className="flex gap-4 py-1 border-b last:border-0">
                        <span className="font-mono">{dia.fecha}</span>
                        <span>Ventas: ${dia.ventas_total?.toLocaleString()}</span>
                        <span>Tickets: {dia.tickets}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-amber-600 text-sm">
                    <AlertTriangle className="w-4 h-4 inline mr-1" />
                    No hay datos existentes para este rango
                  </p>
                )}
              </div>
            )}
            
            {/* Info adicional */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-zinc-500">Rango:</span>
                <p className="font-medium">{validationResult.rango?.mensaje}</p>
              </div>
              <div>
                <span className="text-zinc-500">Nivel de Riesgo:</span>
                <Badge variant={validationResult.nivel_riesgo === 'ALTO' ? 'destructive' : 'outline'}>
                  {validationResult.nivel_riesgo}
                </Badge>
              </div>
              <div>
                <span className="text-zinc-500">Permite Dry Run:</span>
                <p>{validationResult.permite_dry_run ? '✓ Sí' : '✗ No'}</p>
              </div>
              <div>
                <span className="text-zinc-500">Propinas Separadas:</span>
                <p>{validationResult.propinas_separadas ? '✓ Sí' : '✗ No'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Resultado de ejecución */}
      {executionResult && (
        <Card data-testid="execution-result-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {executionResult.success ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600" />
              )}
              Resultado de Ejecución ({executionResult.modo})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant={executionResult.success ? "default" : "destructive"}>
              <AlertTitle>
                {executionResult.success ? 'Ejecución completada' : 'Ejecución fallida'}
              </AlertTitle>
              <AlertDescription>
                <div className="space-y-2 mt-2">
                  <p><strong>Run ID:</strong> {executionResult.sync_run_id}</p>
                  <p><strong>Modo:</strong> {executionResult.modo}</p>
                  
                  {executionResult.resultado && (
                    <>
                      <p><strong>Registros procesados:</strong> {executionResult.resultado.records_processed || 0}</p>
                      {executionResult.modo === 'REAL' && (
                        <>
                          <p><strong>Insertados:</strong> {executionResult.resultado.records_inserted || 0}</p>
                          <p><strong>Actualizados:</strong> {executionResult.resultado.records_updated || 0}</p>
                        </>
                      )}
                    </>
                  )}
                  
                  {executionResult.resultado?.detalle && executionResult.modo === 'DRY_RUN' && (
                    <div className="mt-3">
                      <p className="font-medium mb-2">Detalle de registros que se sincronizarían:</p>
                      <div className="bg-zinc-100 p-3 rounded max-h-48 overflow-y-auto">
                        {executionResult.resultado.detalle.map((item, idx) => (
                          <div key={idx} className="text-sm py-1 border-b last:border-0">
                            <span className="font-mono">{item.fecha}</span>: 
                            Ventas ${item.ventas_total?.toLocaleString()}, 
                            Sin Propina ${item.ventas_sin_propina?.toLocaleString()}, 
                            Propinas ${item.propinas_total?.toLocaleString()}, 
                            Tickets {item.tickets_total}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {executionResult.error_message && (
                    <p className="text-red-600 mt-2">
                      <strong>Error:</strong> {executionResult.error_message}
                    </p>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )}
      
      {/* Historial de Re-syncs */}
      <Card data-testid="resync-history-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5" />
            Historial de Re-sincronizaciones
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loadingHistory ? (
            <div className="flex items-center justify-center p-4">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
          ) : history.length === 0 ? (
            <p className="text-zinc-500 text-center py-4">No hay re-sincronizaciones registradas</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Acción</TableHead>
                  <TableHead>Unidad</TableHead>
                  <TableHead>Rango</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Usuario</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="text-sm">{formatDateTime(item.fecha)}</TableCell>
                    <TableCell>
                      <Badge variant={item.accion.includes('SUCCESS') ? 'default' : 'destructive'}>
                        {item.accion}
                      </Badge>
                    </TableCell>
                    <TableCell>{item.detalles?.unidad || '-'}</TableCell>
                    <TableCell className="text-sm font-mono">
                      {item.detalles?.fecha_inicio} → {item.detalles?.fecha_fin}
                    </TableCell>
                    <TableCell>
                      {item.exito ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-zinc-500">{item.detalles?.usuario || '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      
      {/* Dialog de confirmación */}
      <Dialog open={confirmDialog.open} onOpenChange={(open) => setConfirmDialog({ ...confirmDialog, open })}>
        <DialogContent data-testid="confirm-resync-dialog">
          <DialogHeader>
            <DialogTitle>
              {confirmDialog.isDryRun ? 'Confirmar DRY RUN' : 'Confirmar Ejecución REAL'}
            </DialogTitle>
            <DialogDescription>
              {confirmDialog.isDryRun ? (
                <>
                  El DRY RUN <strong>NO modificará datos</strong>. 
                  Solo mostrará qué registros se sincronizarían.
                </>
              ) : (
                <>
                  <span className="text-red-600 font-medium">
                    Esta acción MODIFICARÁ datos en EDARSAHUB.
                  </span>
                  <br />
                  Los registros serán insertados o actualizados en la tabla de destino.
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-2 text-sm">
            <p><strong>Tipo:</strong> {selectedTipoSync?.nombre}</p>
            <p><strong>Unidad:</strong> {selectedUnidad?.nombre}</p>
            <p><strong>Rango:</strong> {fechaInicio} a {fechaFin}</p>
            <p><strong>Motivo:</strong> {motivo}</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDialog({ open: false, isDryRun: true })}>
              Cancelar
            </Button>
            <Button
              onClick={() => handleExecute(confirmDialog.isDryRun)}
              className={confirmDialog.isDryRun ? 'bg-amber-600 hover:bg-amber-700' : 'bg-red-600 hover:bg-red-700'}
              data-testid="confirm-execute-btn"
            >
              {executing ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Play className="w-4 h-4 mr-2" />
              )}
              {confirmDialog.isDryRun ? 'Ejecutar DRY RUN' : 'Ejecutar REAL'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
