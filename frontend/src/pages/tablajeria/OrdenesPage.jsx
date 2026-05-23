import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { 
  FileText, Plus, Play, CheckCircle, XCircle, 
  RefreshCw, Eye, Clock, AlertTriangle, ChevronLeft, ChevronRight
} from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function OrdenesPage() {
  const [ordenes, setOrdenes] = useState([]);
  const [plantillas, setPlantillas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [limit] = useState(20);
  const [estatusFilter, setEstatusFilter] = useState('');
  
  // Modales
  const [showCrearModal, setShowCrearModal] = useState(false);
  const [showDetalleModal, setShowDetalleModal] = useState(false);
  const [showResultadosModal, setShowResultadosModal] = useState(false);
  const [selectedOrden, setSelectedOrden] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Form crear orden
  const [formCrear, setFormCrear] = useState({
    plantilla_id: '',
    cantidad_base_planeada: '',
    lote_insumo: '',
    observaciones: ''
  });

  // Form resultados
  const [formResultados, setFormResultados] = useState({
    cantidad_base_real: '',
    peso_inicial_kg: '',
    peso_final_kg: '',
    detalles: []
  });

  const fetchOrdenes = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: (page * limit).toString()
      });
      if (estatusFilter) params.append('estatus', estatusFilter);
      
      const response = await api.get(`/tablajeria/ordenes?${params}`);
      setOrdenes(response.data.ordenes || []);
      setTotal(response.data.total || 0);
    } catch (err) {
      console.error('Error fetching ordenes:', err);
      toast.error('Error cargando órdenes');
    } finally {
      setLoading(false);
    }
  };

  const fetchPlantillas = async () => {
    try {
      const response = await api.get('/tablajeria/plantillas?estatus=PUBLICADA&limit=100');
      // También incluir SINCRONIZADA y VALIDADA para pruebas
      const response2 = await api.get('/tablajeria/plantillas?estatus=SINCRONIZADA&limit=100');
      const response3 = await api.get('/tablajeria/plantillas?estatus=VALIDADA&limit=100');
      const all = [
        ...(response.data.plantillas || []),
        ...(response2.data.plantillas || []),
        ...(response3.data.plantillas || [])
      ];
      setPlantillas(all);
    } catch (err) {
      console.error('Error fetching plantillas:', err);
    }
  };

  const fetchOrdenDetalle = async (ordenId) => {
    try {
      const response = await api.get(`/tablajeria/ordenes/${ordenId}`);
      setSelectedOrden(response.data);
      setShowDetalleModal(true);
    } catch (err) {
      toast.error('Error cargando detalle');
    }
  };

  useEffect(() => {
    fetchOrdenes();
    fetchPlantillas();
  }, [page, estatusFilter]);

  const handleCrearOrden = async () => {
    if (!formCrear.plantilla_id || !formCrear.cantidad_base_planeada) {
      toast.error('Completa los campos requeridos');
      return;
    }
    setSubmitting(true);
    try {
      const plantilla = plantillas.find(p => p.PlantillaID === formCrear.plantilla_id);
      const response = await api.post('/tablajeria/ordenes', {
        empresa_id: plantilla?.EmpresaID || '00000000-0000-0000-0000-000000000001',
        plantilla_id: formCrear.plantilla_id,
        fecha_operacion_mexico: new Date().toISOString().split('T')[0],
        cantidad_base_planeada: parseFloat(formCrear.cantidad_base_planeada),
        lote_insumo: formCrear.lote_insumo || null,
        observaciones: formCrear.observaciones || null
      });
      toast.success(response.data.mensaje);
      setShowCrearModal(false);
      setFormCrear({ plantilla_id: '', cantidad_base_planeada: '', lote_insumo: '', observaciones: '' });
      fetchOrdenes();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error creando orden');
    } finally {
      setSubmitting(false);
    }
  };

  const handleIniciarOrden = async (ordenId) => {
    try {
      const response = await api.put(`/tablajeria/ordenes/${ordenId}/iniciar`);
      toast.success(response.data.mensaje);
      fetchOrdenes();
      if (selectedOrden?.OrdenID === ordenId) {
        fetchOrdenDetalle(ordenId);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error iniciando orden');
    }
  };

  const abrirResultadosModal = (orden) => {
    setSelectedOrden(orden);
    setFormResultados({
      cantidad_base_real: orden.CantidadBasePlaneada?.toString() || '',
      peso_inicial_kg: '',
      peso_final_kg: '',
      detalles: orden.detalles?.map(d => ({
        orden_detalle_id: d.OrdenDetalleID,
        nombre: d.ProductoDerivadoNombre,
        tipo: d.TipoDerivado,
        cantidad_esperada: d.CantidadEsperada,
        cantidad_real: '',
        peso_real_kg: ''
      })) || []
    });
    setShowResultadosModal(true);
    setShowDetalleModal(false);
  };

  const handleRegistrarResultados = async () => {
    if (!formResultados.cantidad_base_real) {
      toast.error('Ingresa la cantidad base real');
      return;
    }
    setSubmitting(true);
    try {
      const detalles = formResultados.detalles
        .filter(d => d.cantidad_real)
        .map(d => ({
          orden_detalle_id: d.orden_detalle_id,
          cantidad_real: parseFloat(d.cantidad_real),
          peso_real_kg: d.peso_real_kg ? parseFloat(d.peso_real_kg) : null
        }));

      const response = await api.put(`/tablajeria/ordenes/${selectedOrden.OrdenID}/resultados`, {
        cantidad_base_real: parseFloat(formResultados.cantidad_base_real),
        peso_inicial_kg: formResultados.peso_inicial_kg ? parseFloat(formResultados.peso_inicial_kg) : null,
        peso_final_kg: formResultados.peso_final_kg ? parseFloat(formResultados.peso_final_kg) : null,
        detalles
      });
      toast.success(response.data.mensaje);
      setShowResultadosModal(false);
      fetchOrdenes();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error registrando resultados');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCerrarOrden = async (ordenId) => {
    try {
      const response = await api.put(`/tablajeria/ordenes/${ordenId}/cerrar`, {
        observaciones: 'Cierre desde UI'
      });
      toast.success(response.data.mensaje);
      fetchOrdenes();
      setShowDetalleModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error cerrando orden');
    }
  };

  const handleCancelarOrden = async (ordenId) => {
    const motivo = prompt('Motivo de cancelación:');
    if (!motivo) return;
    try {
      const response = await api.put(`/tablajeria/ordenes/${ordenId}/cancelar`, { motivo });
      toast.success(response.data.mensaje);
      fetchOrdenes();
      setShowDetalleModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error cancelando orden');
    }
  };

  const getEstatusStyle = (estatus) => {
    const styles = {
      'BORRADOR': 'bg-gray-100 text-gray-700',
      'PLANEADA': 'bg-blue-100 text-blue-700',
      'EN_EJECUCION': 'bg-yellow-100 text-yellow-800',
      'PENDIENTE_AUTORIZACION': 'bg-orange-100 text-orange-700',
      'CERRADA': 'bg-green-100 text-green-700',
      'CANCELADA': 'bg-red-100 text-red-700',
      'REVERTIDA': 'bg-purple-100 text-purple-700'
    };
    return styles[estatus] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="p-6 space-y-6" data-testid="ordenes-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800 flex items-center gap-2">
            <FileText className="h-7 w-7 text-green-600" />
            Órdenes de Tablaje
          </h1>
          <p className="text-zinc-500">Gestión de órdenes de producción</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchOrdenes} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </Button>
          <Button onClick={() => setShowCrearModal(true)} size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Nueva Orden
          </Button>
        </div>
      </div>

      {/* Filtros */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex gap-4">
            <select
              value={estatusFilter}
              onChange={(e) => { setEstatusFilter(e.target.value); setPage(0); }}
              className="px-3 py-2 border rounded-md text-sm"
            >
              <option value="">Todos los estatus</option>
              <option value="BORRADOR">Borrador</option>
              <option value="EN_EJECUCION">En Ejecución</option>
              <option value="PENDIENTE_AUTORIZACION">Pendiente Autorización</option>
              <option value="CERRADA">Cerrada</option>
              <option value="CANCELADA">Cancelada</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Tabla */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center justify-between">
            <span>Órdenes ({total})</span>
            <span className="text-sm font-normal text-zinc-500">
              Página {page + 1} de {Math.ceil(total / limit) || 1}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-zinc-400" />
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Folio</TableHead>
                    <TableHead>Plantilla</TableHead>
                    <TableHead>Fecha Op.</TableHead>
                    <TableHead>Cantidad</TableHead>
                    <TableHead>Rendimiento</TableHead>
                    <TableHead>Estatus</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ordenes.map((o) => (
                    <TableRow key={o.OrdenID} className="hover:bg-zinc-50">
                      <TableCell className="font-mono text-sm">{o.FolioOrden}</TableCell>
                      <TableCell className="font-medium">{o.NombrePlantilla || '-'}</TableCell>
                      <TableCell>{o.FechaOperacionMexico}</TableCell>
                      <TableCell>
                        {o.CantidadBaseReal || o.CantidadBasePlaneada}
                        {o.CantidadBaseReal && o.CantidadBasePlaneada && 
                          <span className="text-xs text-zinc-400 ml-1">
                            (plan: {o.CantidadBasePlaneada})
                          </span>
                        }
                      </TableCell>
                      <TableCell>
                        {o.RendimientoRealPorcentaje ? (
                          <span className="font-medium text-emerald-600">
                            {o.RendimientoRealPorcentaje.toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-zinc-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 text-xs rounded ${getEstatusStyle(o.EstatusOrden)}`}>
                          {o.EstatusOrden}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => fetchOrdenDetalle(o.OrdenID)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {o.EstatusOrden === 'BORRADOR' && (
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleIniciarOrden(o.OrdenID)}
                              title="Iniciar"
                            >
                              <Play className="h-4 w-4 text-green-600" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                  {ordenes.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-zinc-500">
                        No se encontraron órdenes
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>

              {/* Paginación */}
              <div className="flex items-center justify-between mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage(p => p - 1)}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={(page + 1) * limit >= total}
                  onClick={() => setPage(p => p + 1)}
                >
                  Siguiente <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Modal Crear Orden */}
      <Dialog open={showCrearModal} onOpenChange={setShowCrearModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Nueva Orden de Tablaje</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Plantilla *</Label>
              <select
                value={formCrear.plantilla_id}
                onChange={(e) => setFormCrear({...formCrear, plantilla_id: e.target.value})}
                className="w-full px-3 py-2 border rounded-md text-sm mt-1"
              >
                <option value="">Seleccionar plantilla...</option>
                {plantillas.map(p => (
                  <option key={p.PlantillaID} value={p.PlantillaID}>
                    {p.NombrePlantilla} ({p.Estatus})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Cantidad Base Planeada *</Label>
              <Input
                type="number"
                step="0.01"
                value={formCrear.cantidad_base_planeada}
                onChange={(e) => setFormCrear({...formCrear, cantidad_base_planeada: e.target.value})}
                placeholder="Ej: 10.5"
              />
            </div>
            <div>
              <Label>Lote de Insumo</Label>
              <Input
                value={formCrear.lote_insumo}
                onChange={(e) => setFormCrear({...formCrear, lote_insumo: e.target.value})}
                placeholder="Ej: LOTE-001"
              />
            </div>
            <div>
              <Label>Observaciones</Label>
              <Input
                value={formCrear.observaciones}
                onChange={(e) => setFormCrear({...formCrear, observaciones: e.target.value})}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCrearModal(false)}>Cancelar</Button>
            <Button onClick={handleCrearOrden} disabled={submitting}>
              {submitting ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
              Crear Orden
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Detalle Orden */}
      <Dialog open={showDetalleModal} onOpenChange={setShowDetalleModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Orden {selectedOrden?.FolioOrden}</DialogTitle>
          </DialogHeader>
          {selectedOrden && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-zinc-500">Estatus</p>
                  <span className={`px-2 py-1 text-xs rounded ${getEstatusStyle(selectedOrden.EstatusOrden)}`}>
                    {selectedOrden.EstatusOrden}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Fecha Operación</p>
                  <p>{selectedOrden.FechaOperacionMexico}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Insumo Base</p>
                  <p>{selectedOrden.InsumoBaseNombre || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Lote</p>
                  <p>{selectedOrden.LoteInsumo || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Cantidad Planeada</p>
                  <p className="font-medium">{selectedOrden.CantidadBasePlaneada}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Cantidad Real</p>
                  <p className="font-medium">{selectedOrden.CantidadBaseReal || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Rendimiento Real</p>
                  <p className="font-medium text-emerald-600">
                    {selectedOrden.RendimientoRealPorcentaje?.toFixed(2) || '-'}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Merma Real</p>
                  <p className="font-medium text-orange-600">
                    {selectedOrden.MermaRealPorcentaje?.toFixed(2) || '-'}%
                  </p>
                </div>
              </div>

              {selectedOrden.detalles?.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Derivados</p>
                  <div className="max-h-[200px] overflow-y-auto border rounded">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Producto</TableHead>
                          <TableHead>Tipo</TableHead>
                          <TableHead className="text-right">Esperado</TableHead>
                          <TableHead className="text-right">Real</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedOrden.detalles.map((d, idx) => (
                          <TableRow key={idx}>
                            <TableCell>{d.ProductoDerivadoNombre}</TableCell>
                            <TableCell>
                              <span className={`text-xs px-1.5 py-0.5 rounded ${
                                d.TipoDerivado === 'MERMA' ? 'bg-red-100 text-red-700' :
                                d.TipoDerivado === 'PRINCIPAL' ? 'bg-green-100 text-green-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {d.TipoDerivado}
                              </span>
                            </TableCell>
                            <TableCell className="text-right">{d.CantidadEsperada?.toFixed(2) || '-'}</TableCell>
                            <TableCell className="text-right font-medium">{d.CantidadReal?.toFixed(2) || '-'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            {selectedOrden?.EstatusOrden === 'EN_EJECUCION' && (
              <>
                <Button variant="outline" onClick={() => abrirResultadosModal(selectedOrden)}>
                  Registrar Resultados
                </Button>
                <Button onClick={() => handleCerrarOrden(selectedOrden.OrdenID)}>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Cerrar Orden
                </Button>
              </>
            )}
            {selectedOrden?.EstatusOrden === 'BORRADOR' && (
              <>
                <Button variant="outline" onClick={() => handleCancelarOrden(selectedOrden.OrdenID)}>
                  <XCircle className="h-4 w-4 mr-2" />
                  Cancelar
                </Button>
                <Button onClick={() => handleIniciarOrden(selectedOrden.OrdenID)}>
                  <Play className="h-4 w-4 mr-2" />
                  Iniciar
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Registrar Resultados */}
      <Dialog open={showResultadosModal} onOpenChange={setShowResultadosModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Registrar Resultados</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Cantidad Base Real *</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={formResultados.cantidad_base_real}
                  onChange={(e) => setFormResultados({...formResultados, cantidad_base_real: e.target.value})}
                />
              </div>
              <div>
                <Label>Peso Inicial (kg)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={formResultados.peso_inicial_kg}
                  onChange={(e) => setFormResultados({...formResultados, peso_inicial_kg: e.target.value})}
                />
              </div>
              <div>
                <Label>Peso Final (kg)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={formResultados.peso_final_kg}
                  onChange={(e) => setFormResultados({...formResultados, peso_final_kg: e.target.value})}
                />
              </div>
            </div>

            {formResultados.detalles.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">Derivados</p>
                <div className="max-h-[250px] overflow-y-auto space-y-2">
                  {formResultados.detalles.map((d, idx) => (
                    <div key={idx} className="p-3 bg-zinc-50 rounded flex items-center gap-4">
                      <div className="flex-1">
                        <p className="font-medium text-sm">{d.nombre}</p>
                        <p className="text-xs text-zinc-500">
                          Esperado: {d.cantidad_esperada?.toFixed(2) || '-'}
                        </p>
                      </div>
                      <div className="w-24">
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="Real"
                          value={d.cantidad_real}
                          onChange={(e) => {
                            const updated = [...formResultados.detalles];
                            updated[idx].cantidad_real = e.target.value;
                            setFormResultados({...formResultados, detalles: updated});
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowResultadosModal(false)}>Cancelar</Button>
            <Button onClick={handleRegistrarResultados} disabled={submitting}>
              {submitting ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : null}
              Guardar Resultados
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
