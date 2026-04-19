/**
 * EDARSA HUB - Tab Automatizaciones Operativas de Compras
 * =======================================================
 * Flujo: Pedido → Gerencia → Tesorería → Aprobado
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Zap,
  RefreshCw,
  Eye,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  Package,
  TrendingUp,
  TrendingDown,
  Minus,
  Settings2,
  Save,
  History,
  Send,
  Calendar,
  Building2,
  User,
  FileText,
} from 'lucide-react';
import { toast } from 'sonner';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Badges por estado
const EstadoBadge = ({ estado }) => {
  const config = {
    PEDIDO_DETECTADO: { color: 'bg-zinc-100 text-zinc-800', icon: Clock, label: 'Detectado' },
    PENDIENTE_INVENTARIO_FISICO: { color: 'bg-amber-100 text-amber-800', icon: AlertTriangle, label: 'Pend. Inventario' },
    AUDITORIA_EN_PROCESO: { color: 'bg-blue-100 text-blue-800', icon: Clock, label: 'En Proceso' },
    EN_REVISION_GERENCIA: { color: 'bg-purple-100 text-purple-800', icon: Eye, label: 'Revisión Gerencia' },
    PENDIENTE_TESORERIA: { color: 'bg-cyan-100 text-cyan-800', icon: Send, label: 'Pend. Tesorería' },
    APROBADO: { color: 'bg-green-100 text-green-800', icon: CheckCircle2, label: 'Aprobado' },
    RECHAZADO: { color: 'bg-red-100 text-red-800', icon: XCircle, label: 'Rechazado' },
  };
  
  const { color, icon: Icon, label } = config[estado] || { color: 'bg-zinc-100 text-zinc-800', icon: Clock, label: estado };
  
  return (
    <Badge className={`${color} text-xs flex items-center gap-1`} data-testid={`badge-estado-${estado}`}>
      <Icon className="w-3 h-3" />
      {label}
    </Badge>
  );
};

// Badge de recomendación
const RecomendacionBadge = ({ recomendacion }) => {
  const config = {
    URGENTE: { color: 'bg-red-500 text-white', label: 'URGENTE' },
    COMPRAR: { color: 'bg-amber-500 text-white', label: 'Comprar' },
    NO_COMPRAR: { color: 'bg-green-500 text-white', label: 'No Comprar' },
    REVISAR: { color: 'bg-blue-500 text-white', label: 'Revisar' },
  };
  
  const { color, label } = config[recomendacion] || { color: 'bg-zinc-500 text-white', label: recomendacion };
  
  return <Badge className={`${color} text-xs`}>{label}</Badge>;
};

// Badge estado producto
const EstadoProductoBadge = ({ estado }) => {
  const config = {
    CRITICO: { color: 'text-red-600', icon: TrendingDown, bg: 'bg-red-50' },
    FALTANTE: { color: 'text-amber-600', icon: TrendingDown, bg: 'bg-amber-50' },
    OPTIMO: { color: 'text-green-600', icon: Minus, bg: 'bg-green-50' },
    SOBRANTE: { color: 'text-blue-600', icon: TrendingUp, bg: 'bg-blue-50' },
  };
  
  const { color, icon: Icon, bg } = config[estado] || { color: 'text-zinc-600', icon: Minus, bg: 'bg-zinc-50' };
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${color} ${bg}`}>
      <Icon className="w-3 h-3" />
      {estado}
    </span>
  );
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
  
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  };
  
  // Determinar permisos por rol
  const isGerencia = ['Gerente', 'Director', 'Administrador'].includes(userRole);
  const isTesoreria = ['Tesoreria', 'Director', 'Administrador'].includes(userRole);
  
  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    setUserRole(user.role || '');
  }, []);
  
  const fetchData = useCallback(async (showLoader = true) => {
    if (showLoader) setLoading(true);
    else setRefreshing(true);
    
    try {
      const [kpisRes, listRes] = await Promise.all([
        fetch(`${API_URL}/api/v2/automatizaciones/operativas/compras/kpis`, { headers: getAuthHeaders() }),
        fetch(`${API_URL}/api/v2/automatizaciones/operativas/compras?limite=50`, { headers: getAuthHeaders() })
      ]);
      
      if (kpisRes.ok) setKpis(await kpisRes.json());
      if (listRes.ok) setAutomatizaciones(await listRes.json());
    } catch (error) {
      console.error('Error fetching data:', error);
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
        { headers: getAuthHeaders() }
      );
      if (res.ok) {
        const data = await res.json();
        setSelectedItem(data);
        setNuevoDiasObjetivo(data.dias_objetivo || 10);
        setEditingDias(false);
        setComentario('');
        setShowDetail(true);
        
        // Cargar bitácora
        const bitRes = await fetch(
          `${API_URL}/api/v2/automatizaciones/operativas/compras/${item.id}/bitacora`,
          { headers: getAuthHeaders() }
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
          headers: getAuthHeaders(),
          body: JSON.stringify({
            dias_objetivo: parseInt(nuevoDiasObjetivo),
            motivo: comentario || 'Ajuste por Gerencia'
          })
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
  
  // Acción Gerencia
  const handleAccionGerencia = async (accion) => {
    if (!selectedItem) return;
    setProcesando(true);
    
    try {
      const body = { accion, comentario };
      if (accion === 'ajuste') {
        body.dias_objetivo = parseInt(nuevoDiasObjetivo);
      }
      
      const res = await fetch(
        `${API_URL}/api/v2/automatizaciones/operativas/compras/${selectedItem.id}/gerencia`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(body)
        }
      );
      
      if (res.ok) {
        const data = await res.json();
        toast.success(accion === 'aprobar' ? 'Enviado a Tesorería' : accion === 'rechazar' ? 'Rechazado' : 'Ajustado');
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
  
  // Acción Tesorería
  const handleAccionTesoreria = async (accion) => {
    if (!selectedItem) return;
    setProcesando(true);
    
    try {
      const res = await fetch(
        `${API_URL}/api/v2/automatizaciones/operativas/compras/${selectedItem.id}/tesoreria`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({ accion, comentario })
        }
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
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('es-MX', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };
  
  return (
    <div className="space-y-4" data-testid="tab-operativas-compras">
      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        <Card className="p-3">
          <div className="text-2xl font-bold text-zinc-900">{kpis.total || 0}</div>
          <div className="text-xs text-zinc-500">Total</div>
        </Card>
        <Card className="p-3 border-amber-200 bg-amber-50/50">
          <div className="text-2xl font-bold text-amber-600">{kpis.pendientes_inventario || 0}</div>
          <div className="text-xs text-amber-700">Pend. Inventario</div>
        </Card>
        <Card className="p-3 border-blue-200 bg-blue-50/50">
          <div className="text-2xl font-bold text-blue-600">{kpis.en_proceso || 0}</div>
          <div className="text-xs text-blue-700">En Proceso</div>
        </Card>
        <Card className="p-3 border-purple-200 bg-purple-50/50">
          <div className="text-2xl font-bold text-purple-600">{kpis.pendientes_revision || 0}</div>
          <div className="text-xs text-purple-700">Rev. Gerencia</div>
        </Card>
        <Card className="p-3 border-cyan-200 bg-cyan-50/50">
          <div className="text-2xl font-bold text-cyan-600">{kpis.pendientes_tesoreria || 0}</div>
          <div className="text-xs text-cyan-700">Pend. Tesorería</div>
        </Card>
        <Card className="p-3 border-green-200 bg-green-50/50">
          <div className="text-2xl font-bold text-green-600">{kpis.aprobados || 0}</div>
          <div className="text-xs text-green-700">Aprobados</div>
        </Card>
        <Card className="p-3 border-red-200 bg-red-50/50">
          <div className="text-2xl font-bold text-red-600">{kpis.rechazados || 0}</div>
          <div className="text-xs text-red-700">Rechazados</div>
        </Card>
      </div>
      
      {/* Lista */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-500" />
                Automatizaciones Operativas de Compras
              </CardTitle>
              <CardDescription>
                Flujo: Pedido → Auditoría → Gerencia → Tesorería
              </CardDescription>
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
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Folio</TableHead>
                  <TableHead>Origen</TableHead>
                  <TableHead>Sucursal</TableHead>
                  <TableHead>Usuario</TableHead>
                  <TableHead>Inv. Final</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Resultado</TableHead>
                  <TableHead>Recomendación</TableHead>
                  <TableHead className="text-right">Acción</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {automatizaciones.map((item) => (
                  <TableRow key={item.id} data-testid={`row-${item.id}`}>
                    <TableCell className="text-sm">{formatDate(item.fecha_creacion)}</TableCell>
                    <TableCell className="font-mono text-xs">{item.pedido_id?.substring(0, 10)}...</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">{item.origen_sistema || 'MPRO'}</Badge>
                    </TableCell>
                    <TableCell className="text-sm">{item.sucursal_nombre}</TableCell>
                    <TableCell className="text-sm">{item.usuario_nombre}</TableCell>
                    <TableCell>
                      {item.tiene_inventario_final ? (
                        <Badge variant="outline" className="text-green-600 border-green-300 text-xs">Sí</Badge>
                      ) : (
                        <Badge variant="outline" className="text-amber-600 border-amber-300 text-xs">No</Badge>
                      )}
                    </TableCell>
                    <TableCell><EstadoBadge estado={item.estado} /></TableCell>
                    <TableCell className="text-xs">
                      {item.resultado ? (
                        <span className="flex items-center gap-1">
                          <span className="text-red-600">{item.resultado.criticos}C</span>/
                          <span className="text-amber-600">{item.resultado.faltantes}F</span>/
                          <span className="text-green-600">{item.resultado.optimos}O</span>/
                          <span className="text-blue-600">{item.resultado.sobrantes}S</span>
                        </span>
                      ) : '-'}
                    </TableCell>
                    <TableCell>
                      {item.recomendacion_general ? (
                        <RecomendacionBadge recomendacion={item.recomendacion_general} />
                      ) : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => handleVerDetalle(item)} data-testid={`btn-ver-${item.id}`}>
                        <Eye className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
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
            <DialogDescription>
              Pedido: {selectedItem?.pedido_id}
            </DialogDescription>
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
              
              {/* Periodo de Análisis */}
              <Card className="bg-zinc-50 border-dashed">
                <CardContent className="pt-4">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-zinc-500 text-xs">Periodo Análisis</div>
                      <div className="font-medium">{selectedItem.dias_periodo_analisis} días</div>
                    </div>
                    <div>
                      <div className="text-zinc-500 text-xs">Inventario Inicial</div>
                      <div className="font-medium">
                        {selectedItem.inventario_inicial_fecha ? formatDate(selectedItem.inventario_inicial_fecha) : 'No encontrado'}
                      </div>
                    </div>
                    <div>
                      <div className="text-zinc-500 text-xs">Inventario Final</div>
                      <div className="font-medium">
                        {selectedItem.tiene_inventario_final ? (
                          <span className="text-green-600">{formatDate(selectedItem.inventario_final_fecha)}</span>
                        ) : (
                          <span className="text-amber-600">Pendiente</span>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
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
                              type="number"
                              min="1"
                              max="90"
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
                          <TableHead className="text-xs text-right">Consumo/Día</TableHead>
                          <TableHead className="text-xs text-right">Días Inv.</TableHead>
                          <TableHead className="text-xs">Estado</TableHead>
                          <TableHead className="text-xs text-right">Pedido Óptimo</TableHead>
                          <TableHead className="text-xs text-right">Diferencia</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedItem.detalle_productos.map((prod, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="text-xs">
                              <div className="font-medium">{prod.nombre}</div>
                              <div className="text-zinc-400">{prod.codigo}</div>
                            </TableCell>
                            <TableCell className="text-xs text-right">{prod.existencia_fisica}</TableCell>
                            <TableCell className="text-xs text-right">{prod.consumo_promedio}</TableCell>
                            <TableCell className="text-xs text-right font-medium">{prod.dias_inventario}</TableCell>
                            <TableCell><EstadoProductoBadge estado={prod.estado} /></TableCell>
                            <TableCell className="text-xs text-right font-medium">{prod.pedido_optimo}</TableCell>
                            <TableCell className={`text-xs text-right font-medium ${prod.diferencia > 0 ? 'text-red-600' : prod.diferencia < 0 ? 'text-blue-600' : ''}`}>
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
                <Card className="border-purple-200 bg-purple-50/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-purple-800">Acción Gerencia</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <Label className="text-xs">Comentario (opcional)</Label>
                      <Textarea
                        placeholder="Observaciones..."
                        value={comentario}
                        onChange={(e) => setComentario(e.target.value)}
                        className="h-16"
                        data-testid="textarea-comentario-gerencia"
                      />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleAccionGerencia('rechazar')} disabled={procesando} data-testid="btn-rechazar-gerencia">
                        <XCircle className="w-4 h-4 mr-1" />
                        Rechazar
                      </Button>
                      <Button variant="secondary" size="sm" onClick={() => handleAccionGerencia('ajuste')} disabled={procesando} data-testid="btn-ajuste-gerencia">
                        <Settings2 className="w-4 h-4 mr-1" />
                        Solicitar Ajuste
                      </Button>
                      <Button size="sm" onClick={() => handleAccionGerencia('aprobar')} disabled={procesando} data-testid="btn-aprobar-gerencia">
                        <CheckCircle2 className="w-4 h-4 mr-1" />
                        Aprobar y Enviar a Tesorería
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* Acciones Tesorería */}
              {selectedItem.estado === 'PENDIENTE_TESORERIA' && isTesoreria && (
                <Card className="border-cyan-200 bg-cyan-50/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-cyan-800">Autorización Final - Tesorería</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="text-xs text-zinc-600 bg-white p-2 rounded border">
                      <strong>Autorizado por Gerencia:</strong> {selectedItem.autorizado_por_gerencia || 'N/A'}<br/>
                      <strong>Fecha:</strong> {formatDate(selectedItem.fecha_autorizacion_gerencia)}<br/>
                      {selectedItem.comentario_gerencia && <><strong>Comentario:</strong> {selectedItem.comentario_gerencia}</>}
                    </div>
                    <div>
                      <Label className="text-xs">Comentario (opcional)</Label>
                      <Textarea
                        placeholder="Observaciones..."
                        value={comentario}
                        onChange={(e) => setComentario(e.target.value)}
                        className="h-16"
                        data-testid="textarea-comentario-tesoreria"
                      />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleAccionTesoreria('rechazar')} disabled={procesando} data-testid="btn-rechazar-tesoreria">
                        <XCircle className="w-4 h-4 mr-1" />
                        Rechazar
                      </Button>
                      <Button size="sm" className="bg-green-600 hover:bg-green-700" onClick={() => handleAccionTesoreria('aprobar')} disabled={procesando} data-testid="btn-aprobar-tesoreria">
                        <CheckCircle2 className="w-4 h-4 mr-1" />
                        Aprobar Final
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* Info Aprobado/Rechazado */}
              {selectedItem.estado === 'APROBADO' && (
                <Card className="border-green-200 bg-green-50/30">
                  <CardContent className="pt-4 text-sm">
                    <div className="flex items-center gap-2 text-green-700">
                      <CheckCircle2 className="w-5 h-5" />
                      <span className="font-medium">Aprobado</span>
                    </div>
                    <div className="mt-2 text-xs text-zinc-600">
                      <div><strong>Gerencia:</strong> {selectedItem.autorizado_por_gerencia} - {formatDate(selectedItem.fecha_autorizacion_gerencia)}</div>
                      <div><strong>Tesorería:</strong> {selectedItem.autorizado_por_tesoreria} - {formatDate(selectedItem.fecha_autorizacion_tesoreria)}</div>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {selectedItem.estado === 'RECHAZADO' && (
                <Card className="border-red-200 bg-red-50/30">
                  <CardContent className="pt-4 text-sm">
                    <div className="flex items-center gap-2 text-red-700">
                      <XCircle className="w-5 h-5" />
                      <span className="font-medium">Rechazado</span>
                    </div>
                    <div className="mt-2 text-xs text-zinc-600">
                      <div><strong>Por:</strong> {selectedItem.rechazado_por}</div>
                      <div><strong>Fecha:</strong> {formatDate(selectedItem.fecha_rechazo)}</div>
                      {selectedItem.motivo_rechazo && <div><strong>Motivo:</strong> {selectedItem.motivo_rechazo}</div>}
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* Bitácora */}
              {bitacora.length > 0 && (
                <div className="pt-4 border-t">
                  <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                    <History className="w-4 h-4" />
                    Bitácora ({bitacora.length})
                  </h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {bitacora.map((entry, idx) => (
                      <div key={idx} className="text-xs bg-zinc-50 p-2 rounded flex justify-between items-start">
                        <div>
                          <span className="text-zinc-400">{formatDate(entry.fecha)}</span>
                          <span className="mx-2 font-medium text-zinc-700">{entry.evento}</span>
                          {entry.datos?.motivo && <span className="text-zinc-500">- {entry.datos.motivo}</span>}
                        </div>
                        {entry.datos?.dias_nuevo && (
                          <Badge variant="outline" className="text-xs">
                            {entry.datos.dias_anterior} → {entry.datos.dias_nuevo} días
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
