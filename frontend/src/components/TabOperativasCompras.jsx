/**
 * EDARSA HUB - Tab Automatizaciones Operativas de Compras
 * =======================================================
 * Componente para gestionar automatizaciones operativas de compras.
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
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Badges por estado
const EstadoBadge = ({ estado }) => {
  const config = {
    PENDIENTE_INVENTARIO_FISICO: { color: 'bg-amber-100 text-amber-800', icon: AlertTriangle, label: 'Pendiente Inv. Físico' },
    AUDITORIA_EN_PROCESO: { color: 'bg-blue-100 text-blue-800', icon: Clock, label: 'En Proceso' },
    AUDITADO_PENDIENTE_REVISION: { color: 'bg-purple-100 text-purple-800', icon: Eye, label: 'Pendiente Revisión' },
    EN_REVISION_GERENCIA: { color: 'bg-indigo-100 text-indigo-800', icon: Eye, label: 'En Revisión Gerencia' },
    EN_REVISION_TESORERIA: { color: 'bg-cyan-100 text-cyan-800', icon: Eye, label: 'En Revisión Tesorería' },
    APROBADO: { color: 'bg-green-100 text-green-800', icon: CheckCircle2, label: 'Aprobado' },
    RECHAZADO: { color: 'bg-red-100 text-red-800', icon: XCircle, label: 'Rechazado' },
    ERROR: { color: 'bg-red-100 text-red-800', icon: XCircle, label: 'Error' },
  };
  
  const { color, icon: Icon, label } = config[estado] || { color: 'bg-zinc-100 text-zinc-800', icon: Clock, label: estado };
  
  return (
    <Badge className={`${color} text-xs flex items-center gap-1`}>
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
  
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  };
  
  const fetchData = useCallback(async (showLoader = true) => {
    if (showLoader) setLoading(true);
    else setRefreshing(true);
    
    try {
      const [kpisRes, listRes] = await Promise.all([
        fetch(`${API_URL}/api/v2/automatizaciones/operativas/compras/kpis`, { headers: getAuthHeaders() }),
        fetch(`${API_URL}/api/v2/automatizaciones/operativas/compras?limite=50`, { headers: getAuthHeaders() })
      ]);
      
      if (kpisRes.ok) {
        const data = await kpisRes.json();
        setKpis(data);
      }
      
      if (listRes.ok) {
        const data = await listRes.json();
        setAutomatizaciones(data);
      }
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
        setShowDetail(true);
      }
    } catch (error) {
      toast.error('Error al cargar detalle');
    }
  };
  
  const handleAccion = async (accion, id) => {
    try {
      const body = accion === 'rechazar' 
        ? { motivo: 'Rechazado por revisión' }
        : accion === 'enviar-revision'
        ? { tipo_revision: 'gerencia' }
        : { comentario: '' };
      
      const res = await fetch(
        `${API_URL}/api/v2/automatizaciones/operativas/compras/${id}/${accion}`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(body)
        }
      );
      
      if (res.ok) {
        toast.success(`Acción ${accion} completada`);
        fetchData(false);
        setShowDetail(false);
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Error en acción');
      }
    } catch (error) {
      toast.error('Error ejecutando acción');
    }
  };
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('es-MX', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  return (
    <div className="space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
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
          <div className="text-xs text-purple-700">Pend. Revisión</div>
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
                Automatizaciones Operativas
              </CardTitle>
              <CardDescription>
                Auditorías automáticas de compras por evento
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => fetchData(false)} disabled={refreshing}>
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
              <p>No hay automatizaciones operativas registradas</p>
              <p className="text-sm mt-1">Las automatizaciones se crean automáticamente cuando se capturan pedidos</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Pedido</TableHead>
                  <TableHead>Sucursal</TableHead>
                  <TableHead>Usuario</TableHead>
                  <TableHead>Inv. Físico</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Recomendación</TableHead>
                  <TableHead className="text-right">Acción</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {automatizaciones.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="text-sm">{formatDate(item.fecha_creacion)}</TableCell>
                    <TableCell className="font-mono text-xs">{item.pedido_id?.substring(0, 12)}...</TableCell>
                    <TableCell className="text-sm">{item.sucursal_nombre}</TableCell>
                    <TableCell className="text-sm">{item.usuario_nombre}</TableCell>
                    <TableCell>
                      {item.inventario_fisico_id ? (
                        <Badge variant="outline" className="text-green-600 border-green-300 text-xs">Sí</Badge>
                      ) : (
                        <Badge variant="outline" className="text-amber-600 border-amber-300 text-xs">No</Badge>
                      )}
                    </TableCell>
                    <TableCell><EstadoBadge estado={item.estado} /></TableCell>
                    <TableCell>
                      {item.recomendacion_general ? (
                        <RecomendacionBadge recomendacion={item.recomendacion_general} />
                      ) : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => handleVerDetalle(item)}>
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
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
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
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-zinc-500">Sucursal:</span>
                  <span className="ml-2 font-medium">{selectedItem.sucursal_nombre}</span>
                </div>
                <div>
                  <span className="text-zinc-500">Almacén:</span>
                  <span className="ml-2 font-medium">{selectedItem.almacen_nombre}</span>
                </div>
                <div>
                  <span className="text-zinc-500">Usuario:</span>
                  <span className="ml-2 font-medium">{selectedItem.usuario_nombre}</span>
                </div>
                <div>
                  <span className="text-zinc-500">Fecha:</span>
                  <span className="ml-2 font-medium">{formatDate(selectedItem.fecha_creacion)}</span>
                </div>
                <div>
                  <span className="text-zinc-500">Estado:</span>
                  <span className="ml-2"><EstadoBadge estado={selectedItem.estado} /></span>
                </div>
                <div>
                  <span className="text-zinc-500">Recomendación:</span>
                  <span className="ml-2">
                    {selectedItem.recomendacion_general ? (
                      <RecomendacionBadge recomendacion={selectedItem.recomendacion_general} />
                    ) : '-'}
                  </span>
                </div>
              </div>
              
              {/* Resumen */}
              {selectedItem.resultado && (
                <Card className="bg-zinc-50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Resumen de Auditoría</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-4 gap-4 text-center">
                      <div>
                        <div className="text-xl font-bold text-red-600">{selectedItem.resultado.criticos || 0}</div>
                        <div className="text-xs text-zinc-500">Críticos</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold text-amber-600">{selectedItem.resultado.faltantes || 0}</div>
                        <div className="text-xs text-zinc-500">Faltantes</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold text-green-600">{selectedItem.resultado.optimos || 0}</div>
                        <div className="text-xs text-zinc-500">Óptimos</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold text-blue-600">{selectedItem.resultado.sobrantes || 0}</div>
                        <div className="text-xs text-zinc-500">Sobrantes</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* Detalle Productos */}
              {selectedItem.detalle_productos && selectedItem.detalle_productos.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Detalle por Producto</h4>
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-zinc-50">
                          <TableHead className="text-xs">Producto</TableHead>
                          <TableHead className="text-xs text-right">Existencia</TableHead>
                          <TableHead className="text-xs text-right">Consumo/Día</TableHead>
                          <TableHead className="text-xs text-right">Días Inv.</TableHead>
                          <TableHead className="text-xs">Estado</TableHead>
                          <TableHead className="text-xs text-right">Pedido Óptimo</TableHead>
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
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
              
              {/* Acciones */}
              {['AUDITADO_PENDIENTE_REVISION', 'EN_REVISION_GERENCIA', 'EN_REVISION_TESORERIA'].includes(selectedItem.estado) && (
                <div className="flex justify-end gap-2 pt-4 border-t">
                  <Button variant="outline" size="sm" onClick={() => handleAccion('rechazar', selectedItem.id)}>
                    <XCircle className="w-4 h-4 mr-1" />
                    Rechazar
                  </Button>
                  <Button size="sm" onClick={() => handleAccion('aprobar', selectedItem.id)}>
                    <CheckCircle2 className="w-4 h-4 mr-1" />
                    Aprobar
                  </Button>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
