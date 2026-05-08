/**
 * EDARSA HUB - Tab Automatizaciones Operativas de Compras
 * =======================================================
 * Flujo: Pedido → Gerencia → Tesorería → Aprobado
 * 
 * FASE 4E: Badges extraídos a /components/compras/ComprasBadges.jsx
 * FASE 6: Refactorizado - Subcomponentes en /components/compras/operativas/
 */

import React, { useState, useEffect, useCallback } from 'react';
// FASE AUTH-SECURITY-01 / FASE 4: getToken eliminado, auth viaja en cookie httpOnly
import { getSessionUser } from '../services/authStorage';
import logger from '../services/logger';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
  Zap, RefreshCw, Package, Calendar, Building2, User, FileText, 
  Settings2, Save, XCircle
} from 'lucide-react';
import { toast } from 'sonner';

// Badges reutilizables
import { EstadoBadge, RecomendacionBadge, EstadoProductoBadge } from '@/components/compras/ComprasBadges';

// Subcomponentes refactorizados
import {
  OperativasKPICards,
  AutomatizacionesTable,
  PeriodoEstadisticoCard,
  AccionesGerenciaCard,
  AccionesTesoreriaCard,
  BitacoraList,
  AprobadoCard,
  RechazadoCard
} from '@/components/compras/operativas';
import { getAccionResultLabel, getDiferenciaClass } from '../utils/styleHelpers';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('es-MX', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
};

export default function TabOperativasCompras() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [kpis, setKpis] = useState({});
  const [automatizaciones, setAutomatizaciones] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [editingDias, setEditingDias] = useState(false);
  const [nuevoDiasObjetivo, setNuevoDiasObjetivo] = useState(10);
  const [bitacora, setBitacora] = useState([]);
  const [userRole, setUserRole] = useState('');
  const [comentario, setComentario] = useState('');
  const [procesando, setProcesando] = useState(false);
  
  // Estados para periodo estadístico
  const [editandoConsumo, setEditandoConsumo] = useState(false);
  const [fechaConsumoInicio, setFechaConsumoInicio] = useState('');
  const [fechaConsumoFin, setFechaConsumoFin] = useState('');
  const [porcentajeAjuste, setPorcentajeAjuste] = useState(0);
  const [motivoAjuste, setMotivoAjuste] = useState('');
  
  // FASE AUTH-SECURITY-01: Auth headers reemplazados por credentials: 'include'
  const getFetchOptions = (method = 'GET', body = null) => {
    const options = {
      method,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' }
    };
    if (body) options.body = JSON.stringify(body);
    return options;
  };
  
  const isGerencia = ['Gerente', 'Director', 'Administrador'].includes(userRole);
  const isTesoreria = ['Tesoreria', 'Director', 'Administrador'].includes(userRole);
  
  useEffect(() => {
    const user = getSessionUser() || {};
    setUserRole(user.role || '');
  }, []);
  
  const fetchData = useCallback(async (showLoader = true) => {
    if (showLoader) setLoading(true);
    else setRefreshing(true);
    
    try {
      const [kpisRes, listRes] = await Promise.all([
        fetch(`${API_URL}/api/v2/automatizaciones/operativas/compras/kpis`, { credentials: 'include' }),
        fetch(`${API_URL}/api/v2/automatizaciones/operativas/compras?limite=50`, { credentials: 'include' })
      ]);
      
      if (kpisRes.ok) setKpis(await kpisRes.json());
      if (listRes.ok) setAutomatizaciones(await listRes.json());
    } catch (error) {
      logger.error('Error fetching data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  const handleVerDetalle = async (item) => {
    try {
      const res = await fetch(
        `${API_URL}/api/v2/automatizaciones/operativas/compras/${item.id}`,
        { credentials: 'include' }
      );
      if (res.ok) {
        const data = await res.json();
        setSelectedItem(data);
        setNuevoDiasObjetivo(data.dias_objetivo || 10);
        setFechaConsumoInicio(data.fecha_consumo_inicio?.split('T')[0] || '');
        setFechaConsumoFin(data.fecha_consumo_fin?.split('T')[0] || '');
        setPorcentajeAjuste(data.porcentaje_ajuste_consumo || 0);
        setMotivoAjuste('');
        setEditandoConsumo(false);
        setEditingDias(false);
        setComentario('');
        setShowDetail(true);
        
        const bitRes = await fetch(
          `${API_URL}/api/v2/automatizaciones/operativas/compras/${item.id}/bitacora`,
          { credentials: 'include' }
        );
        if (bitRes.ok) setBitacora(await bitRes.json());
      }
    } catch (error) {
      toast.error('Error al cargar detalle');
    }
  };
  
  const handleModificarDiasObjetivo = async () => {
    if (!selectedItem) return;
    setProcesando(true);
    
    try {
      const res = await fetch(
        `${API_URL}/api/v2/automatizaciones/operativas/compras/${selectedItem.id}/dias-objetivo`,
        {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ dias_objetivo: parseInt(nuevoDiasObjetivo), motivo: comentario || 'Ajuste por Gerencia' })
        }
      );
      
      if (res.ok) {
        const data = await res.json();
        toast.success(`Días objetivo actualizado a ${data.dias_objetivo_nuevo}`);
        handleVerDetalle(selectedItem);
        fetchData(false);
        setEditingDias(false);
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Error al modificar');
      }
    } catch (error) {
      toast.error('Error al modificar días objetivo');
    } finally {
      setProcesando(false);
    }
  };
  
  const handleModificarParametrosConsumo = async () => {
    if (!selectedItem) return;
    setProcesando(true);
    
    try {
      const body = { motivo: motivoAjuste || 'Ajuste de parámetros de consumo' };
      if (fechaConsumoInicio) body.fecha_consumo_inicio = fechaConsumoInicio;
      if (fechaConsumoFin) body.fecha_consumo_fin = fechaConsumoFin;
      if (porcentajeAjuste !== (selectedItem.porcentaje_ajuste_consumo || 0)) {
        body.porcentaje_ajuste = parseFloat(porcentajeAjuste);
      }
      
      const res = await fetch(
        `${API_URL}/api/v2/automatizaciones/operativas/compras/${selectedItem.id}/parametros-consumo`,
        { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
      );
      
      if (res.ok) {
        toast.success('Parámetros de consumo actualizados');
        handleVerDetalle(selectedItem);
        fetchData(false);
        setEditandoConsumo(false);
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Error al modificar parámetros');
      }
    } catch (error) {
      toast.error('Error al modificar parámetros de consumo');
    } finally {
      setProcesando(false);
    }
  };
  
  const handleAccionGerencia = async (accion) => {
    if (!selectedItem) return;
    setProcesando(true);
    
    try {
      const body = { accion, comentario };
      if (accion === 'ajuste') body.dias_objetivo = parseInt(nuevoDiasObjetivo);
      
      const res = await fetch(
        `${API_URL}/api/v2/automatizaciones/operativas/compras/${selectedItem.id}/gerencia`,
        { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
      );
      
      if (res.ok) {
        toast.success(getAccionResultLabel(accion));
        fetchData(false);
        setShowDetail(false);
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Error');
      }
    } catch (error) {
      toast.error('Error en acción');
    } finally {
      setProcesando(false);
    }
  };
  
  const handleAccionTesoreria = async (accion) => {
    if (!selectedItem) return;
    setProcesando(true);
    
    try {
      const res = await fetch(
        `${API_URL}/api/v2/automatizaciones/operativas/compras/${selectedItem.id}/tesoreria`,
        { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ accion, comentario }) }
      );
      
      if (res.ok) {
        toast.success(accion === 'aprobar' ? 'Aprobado Final' : 'Rechazado');
        fetchData(false);
        setShowDetail(false);
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Error');
      }
    } catch (error) {
      toast.error('Error en acción');
    } finally {
      setProcesando(false);
    }
  };
  
  return (
    <div className="space-y-4" data-testid="tab-operativas-compras">
      {/* KPIs */}
      <OperativasKPICards kpis={kpis} />
      
      {/* Lista */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-500" />
                Automatizaciones Operativas de Compras
              </CardTitle>
              <CardDescription>Flujo: Pedido → Auditoría → Gerencia → Tesorería</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => fetchData(false)} disabled={refreshing} data-testid="btn-refresh">
              <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
              Actualizar
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin text-zinc-400" />
            </div>
          ) : automatizaciones.length === 0 ? (
            <div className="text-center py-8 text-zinc-500">
              <Package className="w-12 h-12 mx-auto mb-3 text-zinc-300" />
              <p>No hay automatizaciones registradas</p>
              <p className="text-sm mt-1">Se crean automáticamente al capturar pedidos</p>
            </div>
          ) : (
            <AutomatizacionesTable automatizaciones={automatizaciones} onVerDetalle={handleVerDetalle} />
          )}
        </CardContent>
      </Card>
      
      {/* Dialog Detalle */}
      <Dialog open={showDetail} onOpenChange={setShowDetail}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-500" />
              Detalle de Automatización
            </DialogTitle>
            <DialogDescription>Pedido: {selectedItem?.pedido_id}</DialogDescription>
          </DialogHeader>
          
          {selectedItem && (
            <div className="space-y-4">
              {/* Info General */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div className="flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-zinc-400" />
                  <div>
                    <div className="text-zinc-500 text-xs">Sucursal</div>
                    <div className="font-medium">{selectedItem.sucursal_nombre}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-zinc-400" />
                  <div>
                    <div className="text-zinc-500 text-xs">Almacén</div>
                    <div className="font-medium">{selectedItem.almacen_nombre}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4 text-zinc-400" />
                  <div>
                    <div className="text-zinc-500 text-xs">Usuario</div>
                    <div className="font-medium">{selectedItem.usuario_nombre}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-zinc-400" />
                  <div>
                    <div className="text-zinc-500 text-xs">Fecha Pedido</div>
                    <div className="font-medium">{formatDate(selectedItem.fecha_pedido)}</div>
                  </div>
                </div>
              </div>
              
              {/* Periodo Operativo (Solo lectura) */}
              <Card className="bg-blue-50/50 border-blue-200">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 text-blue-800">
                    <Calendar className="w-4 h-4" />
                    Periodo Operativo de Auditoría
                    <Badge variant="outline" className="text-xs bg-white text-blue-600 border-blue-300">Solo lectura</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-blue-600 text-xs font-medium">Fecha Inventario Inicial</div>
                      <div className="font-medium text-zinc-800">
                        {selectedItem.inventario_inicial_fecha 
                          ? formatDate(selectedItem.inventario_inicial_fecha) 
                          : <span className="text-amber-600">No capturado</span>}
                      </div>
                    </div>
                    <div>
                      <div className="text-blue-600 text-xs font-medium">Fecha Pedido</div>
                      <div className="font-medium text-zinc-800">{formatDate(selectedItem.fecha_pedido)}</div>
                    </div>
                    <div>
                      <div className="text-blue-600 text-xs font-medium">Periodo Auditoría</div>
                      <div className="font-medium text-zinc-800">{selectedItem.dias_periodo_analisis || 15} días</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              {/* Periodo Estadístico (Editable) */}
              <PeriodoEstadisticoCard
                selectedItem={selectedItem}
                isGerencia={isGerencia}
                editandoConsumo={editandoConsumo}
                setEditandoConsumo={setEditandoConsumo}
                fechaConsumoInicio={fechaConsumoInicio}
                setFechaConsumoInicio={setFechaConsumoInicio}
                fechaConsumoFin={fechaConsumoFin}
                setFechaConsumoFin={setFechaConsumoFin}
                porcentajeAjuste={porcentajeAjuste}
                setPorcentajeAjuste={setPorcentajeAjuste}
                motivoAjuste={motivoAjuste}
                setMotivoAjuste={setMotivoAjuste}
                onGuardar={handleModificarParametrosConsumo}
                procesando={procesando}
              />
              
              {/* Estado Actual */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-zinc-500 text-sm">Estado:</span>
                  <EstadoBadge estado={selectedItem.estado} />
                </div>
                {selectedItem.recomendacion_general && (
                  <div className="flex items-center gap-3">
                    <span className="text-zinc-500 text-sm">Recomendación:</span>
                    <RecomendacionBadge recomendacion={selectedItem.recomendacion_general} />
                  </div>
                )}
              </div>
              
              {/* Resumen Auditoría */}
              {selectedItem.resultado && (
                <Card className="bg-zinc-50">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        Resumen de Auditoría
                      </CardTitle>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-zinc-500">Días Objetivo:</span>
                        {editingDias && isGerencia ? (
                          <div className="flex items-center gap-1">
                            <Input
                              type="number" min="1" max="90"
                              value={nuevoDiasObjetivo}
                              onChange={(e) => setNuevoDiasObjetivo(e.target.value)}
                              className="w-16 h-7 text-sm"
                              data-testid="input-dias-objetivo"
                            />
                            <Button size="sm" variant="ghost" className="h-7 px-2" onClick={handleModificarDiasObjetivo} disabled={procesando}>
                              <Save className="w-3 h-3" />
                            </Button>
                            <Button size="sm" variant="ghost" className="h-7 px-2" onClick={() => setEditingDias(false)}>
                              <XCircle className="w-3 h-3" />
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1">
                            <span className="font-medium">{selectedItem.dias_objetivo || 10}</span>
                            {isGerencia && selectedItem.estado === 'EN_REVISION_GERENCIA' && (
                              <Button size="sm" variant="ghost" className="h-7 px-2" onClick={() => setEditingDias(true)} data-testid="btn-edit-dias">
                                <Settings2 className="w-3 h-3" />
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-5 gap-4 text-center">
                      <div>
                        <div className="text-2xl font-bold text-red-600">{selectedItem.resultado.criticos || 0}</div>
                        <div className="text-xs text-zinc-500">Críticos</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-amber-600">{selectedItem.resultado.faltantes || 0}</div>
                        <div className="text-xs text-zinc-500">Faltantes</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-green-600">{selectedItem.resultado.optimos || 0}</div>
                        <div className="text-xs text-zinc-500">Óptimos</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-blue-600">{selectedItem.resultado.sobrantes || 0}</div>
                        <div className="text-xs text-zinc-500">Sobrantes</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-zinc-700">{Math.round(selectedItem.resultado.total_pedido_optimo || 0)}</div>
                        <div className="text-xs text-zinc-500">Pedido Óptimo</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* Detalle Productos */}
              {selectedItem.detalle_productos && selectedItem.detalle_productos.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Detalle por Producto ({selectedItem.detalle_productos.length})</h4>
                  <div className="border rounded-lg overflow-hidden max-h-60 overflow-y-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-zinc-50">
                          <TableHead className="text-xs">Producto</TableHead>
                          <TableHead className="text-xs text-right">Existencia</TableHead>
                          <TableHead className="text-xs text-right">Consumo Base</TableHead>
                          <TableHead className="text-xs text-right">Consumo Ajust.</TableHead>
                          <TableHead className="text-xs text-right">Días Inv.</TableHead>
                          <TableHead className="text-xs">Estado</TableHead>
                          <TableHead className="text-xs text-right">Pedido Óptimo</TableHead>
                          <TableHead className="text-xs text-right">Diferencia</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedItem.detalle_productos.map((prod) => (
                          <TableRow key={prod.codigo || prod.nombre}>
                            <TableCell className="text-xs">
                              <div className="font-medium">{prod.nombre}</div>
                              <div className="text-zinc-400">{prod.codigo}</div>
                            </TableCell>
                            <TableCell className="text-xs text-right">{prod.existencia_fisica}</TableCell>
                            <TableCell className="text-xs text-right text-zinc-500">{prod.consumo_promedio_base || prod.consumo_promedio}</TableCell>
                            <TableCell className="text-xs text-right font-medium">
                              {prod.consumo_promedio_ajustado || prod.consumo_promedio}
                              {prod.porcentaje_ajuste_aplicado !== 0 && prod.porcentaje_ajuste_aplicado !== undefined && (
                                <span className={`ml-1 text-xs ${prod.porcentaje_ajuste_aplicado > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  ({prod.porcentaje_ajuste_aplicado > 0 ? '+' : ''}{prod.porcentaje_ajuste_aplicado}%)
                                </span>
                              )}
                            </TableCell>
                            <TableCell className="text-xs text-right font-medium">{prod.dias_inventario}</TableCell>
                            <TableCell><EstadoProductoBadge estado={prod.estado} /></TableCell>
                            <TableCell className="text-xs text-right font-medium">{prod.pedido_optimo}</TableCell>
                            <TableCell className={`text-xs text-right font-medium ${getDiferenciaClass(prod.diferencia)}`}>
                              {prod.diferencia > 0 ? '+' : ''}{prod.diferencia}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
              
              {/* Acciones Gerencia */}
              {selectedItem.estado === 'EN_REVISION_GERENCIA' && isGerencia && (
                <AccionesGerenciaCard
                  comentario={comentario}
                  setComentario={setComentario}
                  onAccion={handleAccionGerencia}
                  procesando={procesando}
                />
              )}
              
              {/* Acciones Tesorería */}
              {selectedItem.estado === 'PENDIENTE_TESORERIA' && isTesoreria && (
                <AccionesTesoreriaCard
                  selectedItem={selectedItem}
                  comentario={comentario}
                  setComentario={setComentario}
                  onAccion={handleAccionTesoreria}
                  procesando={procesando}
                />
              )}
              
              {/* Estados Finales */}
              {selectedItem.estado === 'APROBADO' && <AprobadoCard selectedItem={selectedItem} />}
              {selectedItem.estado === 'RECHAZADO' && <RechazadoCard selectedItem={selectedItem} />}
              
              {/* Bitácora */}
              <BitacoraList bitacora={bitacora} />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
