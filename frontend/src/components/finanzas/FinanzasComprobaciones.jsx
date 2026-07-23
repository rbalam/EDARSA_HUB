import React, { useCallback, useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, FileCheck2, Filter, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../lib/api';
import logger from '../../services/logger';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Label } from '../ui/label';

const TIPOS = [
  { value: '', label: 'Todos' },
  { value: 'CAJA_CHICA', label: 'Caja chica' },
  { value: 'FONDO_REVOLVENTE', label: 'Fondo revolvente' },
  { value: 'VIATICO', label: 'Viatico' },
  { value: 'GASTO_POR_COMPROBAR', label: 'Gasto por comprobar' },
  { value: 'REEMBOLSO', label: 'Reembolso' }
];

const ESTADOS = [
  { value: '', label: 'Todos' },
  { value: 'ABIERTA', label: 'Abierta' },
  { value: 'PENDIENTE_AUTORIZACION', label: 'Pendiente autorizacion' },
  { value: 'AUTORIZADA', label: 'Autorizada' },
  { value: 'OBSERVADA', label: 'Observada' },
  { value: 'RECHAZADA', label: 'Rechazada' },
  { value: 'CERRADA', label: 'Cerrada' },
  { value: 'CANCELADA', label: 'Cancelada' }
];

const formatCurrency = (value) => (
  new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN'
  }).format(Number(value || 0))
);

const formatDate = (value) => {
  if (!value) return '-';
  return String(value).split('T')[0] || '-';
};

export default function FinanzasComprobaciones({
  selectedUnidad,
  unidadesNegocio = [],
  loadingUnidades = false,
  onUnidadChange
}) {
  const [status, setStatus] = useState(null);
  const [data, setData] = useState(null);
  const [tipo, setTipo] = useState('');
  const [estado, setEstado] = useState('');
  const [loading, setLoading] = useState(false);

  const loadComprobaciones = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedUnidad) params.append('unidad_negocio_pk', selectedUnidad);
      if (tipo) params.append('tipo_comprobacion', tipo);
      if (estado) params.append('estado_comprobacion', estado);

      const [statusResponse, listResponse] = await Promise.all([
        api.get('/finanzas/comprobaciones/status'),
        api.get(`/finanzas/comprobaciones?${params.toString()}`)
      ]);

      setStatus(statusResponse.data);
      setData(listResponse.data);
    } catch (error) {
      const responseStatus = error?.response?.status;
      const detail = error?.response?.data?.detail;
      if (responseStatus === 409) {
        setStatus({
          ready: false,
          missing_tables: detail?.missing_tables || [],
          fuente: 'CANONICO_EDARSAHUB'
        });
        setData({ comprobaciones: [], total: 0 });
      } else {
        logger.error('[Comprobaciones] Error:', error);
        toast.error(detail?.message || detail || 'Error al cargar comprobaciones');
      }
    } finally {
      setLoading(false);
    }
  }, [selectedUnidad, tipo, estado]);

  useEffect(() => {
    loadComprobaciones();
  }, [loadComprobaciones]);

  const comprobaciones = data?.comprobaciones || [];
  const totalEntregado = comprobaciones.reduce((sum, item) => sum + (Number(item.monto_entregado) || 0), 0);
  const totalComprobado = comprobaciones.reduce((sum, item) => sum + (Number(item.monto_comprobado) || 0), 0);
  const totalPendiente = Math.max(totalEntregado - totalComprobado, 0);

  return (
    <div className="space-y-4" data-testid="finanzas-comprobaciones">
      <Card>
        <CardContent className="p-3">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
            <div>
              <Label className="text-xs text-zinc-500">Unidad de Negocio</Label>
              {unidadesNegocio.length === 1 ? (
                <div className="mt-1 px-3 py-2 border rounded-lg text-sm bg-zinc-50">
                  {unidadesNegocio[0].nombre}
                </div>
              ) : (
                <select
                  value={selectedUnidad}
                  onChange={(event) => onUnidadChange?.(event.target.value)}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  disabled={loadingUnidades}
                >
                  <option value="">{loadingUnidades ? 'Cargando...' : 'Todas'}</option>
                  {unidadesNegocio.map((unidad) => (
                    <option key={unidad.id} value={unidad.id}>{unidad.nombre}</option>
                  ))}
                </select>
              )}
            </div>
            <div>
              <Label className="text-xs text-zinc-500">Tipo</Label>
              <select
                value={tipo}
                onChange={(event) => setTipo(event.target.value)}
                className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
              >
                {TIPOS.map((option) => (
                  <option key={option.value || 'ALL'} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs text-zinc-500">Estado</Label>
              <select
                value={estado}
                onChange={(event) => setEstado(event.target.value)}
                className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
              >
                {ESTADOS.map((option) => (
                  <option key={option.value || 'ALL'} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>
            <div>
              <Button onClick={loadComprobaciones} disabled={loading} className="w-full">
                <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                Filtrar
              </Button>
            </div>
            <div className="text-xs text-zinc-500 flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Fuente EDARSAHUB
            </div>
          </div>
        </CardContent>
      </Card>

      {status && !status.ready && (
        <div className="border border-amber-200 bg-amber-50 rounded-lg p-4 text-sm text-amber-800 flex gap-3">
          <AlertCircle className="h-5 w-5 mt-0.5" />
          <div>
            <p className="font-semibold">Comprobaciones pendientes de configuracion canonica</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-zinc-500">Comprobaciones</p>
            <p className="text-2xl font-bold text-zinc-800">{comprobaciones.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-zinc-500">Entregado</p>
            <p className="text-2xl font-bold text-zinc-800">{formatCurrency(totalEntregado)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-zinc-500">Comprobado</p>
            <p className="text-2xl font-bold text-green-700">{formatCurrency(totalComprobado)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-zinc-500">Pendiente</p>
            <p className="text-2xl font-bold text-amber-700">{formatCurrency(totalPendiente)}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <FileCheck2 className="h-5 w-5" />
            Comprobaciones
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-800 text-white">
                <tr>
                  <th className="text-left p-3 font-medium">ID</th>
                  <th className="text-left p-3 font-medium">Unidad</th>
                  <th className="text-left p-3 font-medium">Tipo</th>
                  <th className="text-left p-3 font-medium">Referencia</th>
                  <th className="text-right p-3 font-medium">Entregado</th>
                  <th className="text-right p-3 font-medium">Comprobado</th>
                  <th className="text-center p-3 font-medium">CFDI</th>
                  <th className="text-center p-3 font-medium">Estado</th>
                  <th className="text-center p-3 font-medium">Alta</th>
                </tr>
              </thead>
              <tbody>
                {comprobaciones.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center py-8 text-zinc-400">
                      {loading ? 'Cargando comprobaciones...' : 'No hay comprobaciones con los filtros seleccionados'}
                    </td>
                  </tr>
                ) : comprobaciones.map((item) => (
                  <tr key={item.comprobacion_id} className="border-b hover:bg-zinc-50">
                    <td className="p-3 font-mono text-zinc-700">{item.comprobacion_id}</td>
                    <td className="p-3">{item.unidad_negocio_nombre || item.unidad_negocio_codigo || '-'}</td>
                    <td className="p-3">{item.tipo_comprobacion || '-'}</td>
                    <td className="p-3">{item.referencia_operacion || '-'}</td>
                    <td className="p-3 text-right font-mono">{formatCurrency(item.monto_entregado)}</td>
                    <td className="p-3 text-right font-mono">{formatCurrency(item.monto_comprobado)}</td>
                    <td className="p-3 text-center">{item.documentos_count || 0}</td>
                    <td className="p-3 text-center">
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded border bg-zinc-50 text-zinc-700 text-xs">
                        <CheckCircle2 className="h-3 w-3" />
                        {item.estado_comprobacion || '-'}
                      </span>
                    </td>
                    <td className="p-3 text-center text-zinc-600">{formatDate(item.fecha_alta)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
