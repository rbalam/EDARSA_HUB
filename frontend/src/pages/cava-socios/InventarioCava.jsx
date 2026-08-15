/**
 * EDARSA HUB - Inventario Global de Cavas
 * ========================================
 * Vista consolidada de botellas en resguardo por casillero, cava y socio.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Wine, Search, Filter, RefreshCw, AlertCircle, 
  ChevronLeft, ChevronRight, QrCode, Eye, Package,
  Layers, DollarSign, Printer
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from '@/components/ui/label';
import {
  CorporateFiltersProvider,
  CorporateFilterSelect,
  useCorporateFilters,
} from '../../filters';
import { useAccessContext } from '../../hooks/useAccessContext';

const PAGE_SIZE = 20;

const TIPOS_BEBIDA = [
  { value: 'todos', label: 'Todos los tipos' },
  { value: 'VINO_TINTO', label: 'Vino Tinto' },
  { value: 'VINO_BLANCO', label: 'Vino Blanco' },
  { value: 'VINO_ROSADO', label: 'Vino Rosado' },
  { value: 'CHAMPAGNE', label: 'Champagne / Espumoso' },
  { value: 'WHISKY', label: 'Whisky' },
  { value: 'TEQUILA', label: 'Tequila' },
  { value: 'MEZCAL', label: 'Mezcal' },
  { value: 'COGNAC', label: 'Cognac / Brandy' },
  { value: 'VODKA', label: 'Vodka' },
  { value: 'RON', label: 'Ron' },
  { value: 'GIN', label: 'Ginebra' },
  { value: 'OTRO', label: 'Otro' }
];

function InventarioCavaContent() {
  const navigate = useNavigate();
  const { selected, loading: filtersLoading } = useCorporateFilters();
  const { context, loading: contextLoading, error: contextError } = useAccessContext();
  const unidadNegocioPk = selected?.unidades_negocio || context?.unidad_activa || '';

  const [botellas, setBotellas] = useState([]);
  const [total, setTotal] = useState(0);
  const [valorTotalCustodia, setValorTotalCustodia] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [tipoBebidaFilter, setTipoBebidaFilter] = useState('todos');
  const [estatusFilter, setEstatusFilter] = useState('todos');
  const [ubicacionFilter, setUbicacionFilter] = useState('');

  // Modal Etiqueta / QR
  const [selectedEtiqueta, setSelectedEtiqueta] = useState(null);
  const [showEtiquetaDialog, setShowEtiquetaDialog] = useState(false);

  // Modal Consumo Rápido
  const [selectedBotellaConsumo, setSelectedBotellaConsumo] = useState(null);
  const [showConsumoDialog, setShowConsumoDialog] = useState(false);
  const [consumoForm, setConsumoForm] = useState({
    porcentaje_consumido: 100,
    motivo: '',
    monto_descorche: 350
  });
  const [savingConsumo, setSavingConsumo] = useState(false);

  const fetchInventario = useCallback(async () => {
    if (filtersLoading || contextLoading) return;
    if (!unidadNegocioPk) {
      setBotellas([]);
      setTotal(0);
      setValorTotalCustodia(0);
      setError('Selecciona una unidad de negocio autorizada para consultar Cavas.');
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        unidad_negocio_pk: unidadNegocioPk,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE
      });

      if (tipoBebidaFilter !== 'todos') {
        params.append('tipo_bebida', tipoBebidaFilter);
      }
      if (estatusFilter !== 'todos') {
        params.append('estatus', estatusFilter);
      }
      if (ubicacionFilter.trim()) {
        params.append('ubicacion', ubicacionFilter.trim());
      }

      const response = await api.get(`/cava-socios/inventario?${params}`);
      setBotellas(response.data?.botellas || []);
      setTotal(response.data?.total || 0);
      setValorTotalCustodia(response.data?.valor_custodia_total || 0);
      setError(null);
    } catch (err) {
      console.error('Error cargando inventario de cavas:', err);
      setBotellas([]);
      setTotal(0);
      setError(
        err?.response?.status === 403
          ? 'No tienes permiso para consultar el inventario de Cavas.'
          : 'Error al consultar inventario de botellas.'
      );
    } finally {
      setLoading(false);
    }
  }, [page, tipoBebidaFilter, estatusFilter, ubicacionFilter, unidadNegocioPk, filtersLoading, contextLoading]);

  useEffect(() => {
    fetchInventario();
  }, [fetchInventario]);

  const handleVerEtiqueta = async (botella) => {
    try {
      const resp = await api.get(`/cava-socios/botellas/${botella.botella_id}/etiqueta?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`);
      setSelectedEtiqueta(resp.data || botella);
      setShowEtiquetaDialog(true);
    } catch (err) {
      setSelectedEtiqueta(botella);
      setShowEtiquetaDialog(true);
    }
  };

  const handleOpenConsumo = (botella) => {
    setSelectedBotellaConsumo(botella);
    setConsumoForm({
      porcentaje_consumido: 100,
      motivo: 'Consumo en restaurante / evento',
      monto_descorche: 350
    });
    setShowConsumoDialog(true);
  };

  const handleConfirmarConsumo = async () => {
    if (!selectedBotellaConsumo) return;
    setSavingConsumo(true);
    try {
      await api.post(`/cava-socios/botellas/${selectedBotellaConsumo.botella_id}/consumo?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`, consumoForm);
      setShowConsumoDialog(false);
      fetchInventario();
    } catch (err) {
      console.error('Error registrando consumo:', err);
      alert('Error al registrar consumo');
    } finally {
      setSavingConsumo(false);
    }
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(val || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  const filteredBotellas = botellas.filter(b => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      b.producto_nombre?.toLowerCase().includes(term) ||
      b.socio_nombre?.toLowerCase().includes(term) ||
      b.numero_socio?.toLowerCase().includes(term) ||
      b.ubicacion?.toLowerCase().includes(term) ||
      b.marca?.toLowerCase().includes(term)
    );
  });

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="p-6 space-y-6" data-testid="inventario-cava-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Wine className="h-7 w-7 text-amber-600" />
            Inventario Global de Cavas
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Control físico de botellas en resguardo por casillero y socio
          </p>
        </div>
        <div className="flex gap-2 items-end">
          <div className="min-w-[260px]">
            <CorporateFilterSelect
              filterKey="unidades_negocio"
              label="Unidad de negocio"
              placeholder="Selecciona una unidad"
            />
          </div>
          <Button variant="outline" size="sm" onClick={fetchInventario}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </Button>
          <Button size="sm" onClick={() => navigate('/cava-socios/socios')}>
            <Layers className="h-4 w-4 mr-2" />
            Ver Socios
          </Button>
        </div>
      </div>

      {(error || contextError) && (
        <div className="p-4 rounded-lg bg-red-50 text-red-700 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          {error || contextError?.message || 'No se pudo resolver el contexto de acceso.'}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Botellas en Resguardo</p>
              <p className="text-2xl font-bold text-amber-600">{total}</p>
            </div>
            <div className="p-3 bg-amber-100 rounded-full text-amber-700">
              <Wine className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Valor Total en Custodia</p>
              <p className="text-2xl font-bold text-emerald-600">{formatCurrency(valorTotalCustodia)}</p>
            </div>
            <div className="p-3 bg-emerald-100 rounded-full text-emerald-700">
              <DollarSign className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Página Actual</p>
              <p className="text-2xl font-bold text-blue-600">{page + 1} de {totalPages || 1}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full text-blue-700">
              <Layers className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por botella, socio o marca..."
                className="pl-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div>
              <Input
                placeholder="Filtrar por casillero / ubicación..."
                value={ubicacionFilter}
                onChange={(e) => setUbicacionFilter(e.target.value)}
              />
            </div>
            <div>
              <Select value={tipoBebidaFilter} onValueChange={setTipoBebidaFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Tipo de Bebida" />
                </SelectTrigger>
                <SelectContent>
                  {TIPOS_BEBIDA.map(t => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Select value={estatusFilter} onValueChange={setEstatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Estatus" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos los estatus</SelectItem>
                  <SelectItem value="GUARDADA">Guardada / Custodia</SelectItem>
                  <SelectItem value="ABIERTA">Abierta / En consumo</SelectItem>
                  <SelectItem value="TERMINADA">Terminada</SelectItem>
                  <SelectItem value="RETIRADA">Retirada por socio</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabla de Botellas */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Inventario Consolidado ({total} botellas)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading || filtersLoading || contextLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
            </div>
          ) : filteredBotellas.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Botella / Producto</TableHead>
                    <TableHead>Socio Propietario</TableHead>
                    <TableHead>Tipo / Añada</TableHead>
                    <TableHead>Casillero / Ubicación</TableHead>
                    <TableHead className="text-center">Nivel</TableHead>
                    <TableHead className="text-right">Valor</TableHead>
                    <TableHead>Estatus</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredBotellas.map((botella) => (
                    <TableRow key={botella.botella_id}>
                      <TableCell>
                        <div className="font-medium">{botella.producto_nombre}</div>
                        {botella.marca && (
                          <div className="text-xs text-muted-foreground">{botella.marca}</div>
                        )}
                      </TableCell>
                      <TableCell>
                        <div 
                          className="text-sm font-medium text-blue-600 hover:underline cursor-pointer"
                          onClick={() => navigate(`/cava-socios/socios/${botella.socio_id}`)}
                        >
                          {botella.socio_nombre}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          #{botella.numero_socio}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">{botella.tipo_bebida || '-'}</div>
                        <div className="text-xs text-muted-foreground">{botella.añada ? `Añada ${botella.añada}` : ''}</div>
                      </TableCell>
                      <TableCell>
                        <span className="px-2 py-1 bg-zinc-100 rounded text-xs font-mono font-medium">
                          {botella.ubicacion || 'Sin asignar'}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700">
                          {botella.porcentaje_restante || 100}%
                        </span>
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(botella.valor_declarado)}
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          botella.estatus === 'GUARDADA' ? 'bg-green-100 text-green-700' :
                          botella.estatus === 'ABIERTA' ? 'bg-amber-100 text-amber-700' :
                          'bg-zinc-100 text-zinc-600'
                        }`}>
                          {botella.estatus}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            title="Ver Etiqueta QR"
                            onClick={() => handleVerEtiqueta(botella)}
                          >
                            <QrCode className="h-4 w-4 text-zinc-700" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            title="Registrar Consumo"
                            onClick={() => handleOpenConsumo(botella)}
                          >
                            <Package className="h-4 w-4 text-amber-600" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            title="Ver Detalle de Socio"
                            onClick={() => navigate(`/cava-socios/socios/${botella.socio_id}`)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Paginación */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <div className="text-sm text-muted-foreground">
                  Mostrando {page * PAGE_SIZE + 1} - {Math.min((page + 1) * PAGE_SIZE, total)} de {total}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 0}
                    onClick={() => setPage(p => p - 1)}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= totalPages - 1}
                    onClick={() => setPage(p => p + 1)}
                  >
                    Siguiente
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Wine className="h-12 w-12 mx-auto mb-4 opacity-20" />
              <p>No se encontraron botellas registradas con los filtros seleccionados</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Etiqueta de Custodia con QR */}
      <Dialog open={showEtiquetaDialog} onOpenChange={setShowEtiquetaDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <QrCode className="h-5 w-5 text-amber-600" />
              Etiqueta de Resguardo / QR Cava
            </DialogTitle>
            <DialogDescription>
              Ficha para identificación física de la botella en el casillero
            </DialogDescription>
          </DialogHeader>
          {selectedEtiqueta && (
            <div className="border-2 border-dashed border-zinc-300 p-6 rounded-lg bg-zinc-50 space-y-4 text-center">
              <div className="text-xs uppercase font-bold tracking-wider text-zinc-500">
                EDARSA HUB • CONTROL DE CAVA
              </div>
              <div className="font-bold text-lg text-zinc-900">
                {selectedEtiqueta.producto_nombre}
              </div>
              <div className="text-sm text-zinc-600">
                {selectedEtiqueta.marca} {selectedEtiqueta.añada ? `• Añada ${selectedEtiqueta.añada}` : ''}
              </div>
              <div className="inline-block p-4 bg-white rounded-lg shadow-sm border border-zinc-200">
                <div className="w-32 h-32 flex flex-col items-center justify-center bg-zinc-900 text-white rounded font-mono text-[10px] p-2 leading-tight">
                  <QrCode className="h-16 w-16 mb-1 text-white" />
                  <span>ID: {selectedEtiqueta.botella_id?.slice(0, 8)}</span>
                  <span>SOCIO: #{selectedEtiqueta.numero_socio}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-left text-xs pt-2 border-t">
                <div>
                  <span className="text-zinc-500">Socio:</span>
                  <p className="font-semibold text-zinc-800">{selectedEtiqueta.socio_nombre}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Casillero / Ubicación:</span>
                  <p className="font-semibold text-zinc-800">{selectedEtiqueta.ubicacion || 'Sin asignar'}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Valor Declarado:</span>
                  <p className="font-semibold text-zinc-800">{formatCurrency(selectedEtiqueta.valor_declarado)}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Fecha Ingreso:</span>
                  <p className="font-semibold text-zinc-800">{formatDate(selectedEtiqueta.fecha_ingreso)}</p>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEtiquetaDialog(false)}>
              Cerrar
            </Button>
            <Button onClick={() => window.print()}>
              <Printer className="h-4 w-4 mr-2" />
              Imprimir Etiqueta
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Consumo Rápido */}
      <Dialog open={showConsumoDialog} onOpenChange={setShowConsumoDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar Consumo de Botella</DialogTitle>
            <DialogDescription>
              {selectedBotellaConsumo?.producto_nombre} • Socio: {selectedBotellaConsumo?.socio_nombre}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Porcentaje a Consumir</Label>
              <Select 
                value={String(consumoForm.porcentaje_consumido)}
                onValueChange={(v) => setConsumoForm(f => ({...f, porcentaje_consumido: parseInt(v)}))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="25">25% (Copa / Degustación)</SelectItem>
                  <SelectItem value="50">50% (Media Botella)</SelectItem>
                  <SelectItem value="75">75% (Tres cuartos)</SelectItem>
                  <SelectItem value="100">100% (Botella Completa)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Motivo / Ocasión</Label>
              <Input
                value={consumoForm.motivo}
                onChange={(e) => setConsumoForm(f => ({...f, motivo: e.target.value}))}
                placeholder="Consumo en mesa, evento privado..."
              />
            </div>
            <div className="space-y-2">
              <Label>Cargo de Descorche ($ MXN)</Label>
              <Input
                type="number"
                value={consumoForm.monto_descorche}
                onChange={(e) => setConsumoForm(f => ({...f, monto_descorche: parseFloat(e.target.value) || 0}))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConsumoDialog(false)}>
              Cancelar
            </Button>
            <Button onClick={handleConfirmarConsumo} disabled={savingConsumo}>
              {savingConsumo ? 'Guardando...' : 'Confirmar Consumo'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function InventarioCava() {
  return (
    <CorporateFiltersProvider scope="cava_socios">
      <InventarioCavaContent />
    </CorporateFiltersProvider>
  );
}
