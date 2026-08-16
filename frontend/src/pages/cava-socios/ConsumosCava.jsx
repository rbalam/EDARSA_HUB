/**
 * EDARSA HUB - Consumos y Movimientos de Cava
 * ============================================
 * Bitácora operativa consolidada de descorches, consumos y movimientos de botellas.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Wine, Search, RefreshCw, AlertCircle, 
  ChevronLeft, ChevronRight, Package, DollarSign,
  TrendingDown, FileText
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
  CorporateFiltersProvider,
  CorporateFilterSelect,
  useCorporateFilters,
} from '../../filters';
import { useAccessContext } from '../../hooks/useAccessContext';

const PAGE_SIZE = 20;

import CavaNavHeader from './CavaNavHeader';

function ConsumosCavaContent() {
  const navigate = useNavigate();
  const { selected, loading: filtersLoading } = useCorporateFilters();
  const { context, loading: contextLoading, error: contextError } = useAccessContext();
  const unidadNegocioPk = selected?.unidades_negocio || context?.unidad_activa || '';

  const [movimientos, setMovimientos] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchConsumos = useCallback(async () => {
    if (filtersLoading || contextLoading) return;
    if (!unidadNegocioPk) {
      setMovimientos([]);
      setTotal(0);
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

      const response = await api.get(`/cava-socios/consumos?${params}`);
      setMovimientos(response.data?.movimientos || []);
      setTotal(response.data?.total || 0);
      setError(null);
    } catch (err) {
      console.error('Error cargando bitácora de consumos:', err);
      setMovimientos([]);
      setTotal(0);
      setError(
        err?.response?.status === 403
          ? 'No tienes permiso para consultar consumos de Cavas.'
          : 'Error al consultar consumos y movimientos.'
      );
    } finally {
      setLoading(false);
    }
  }, [page, unidadNegocioPk, filtersLoading, contextLoading]);

  useEffect(() => {
    fetchConsumos();
  }, [fetchConsumos]);

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(val || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const totalDescorches = movimientos.reduce((sum, m) => sum + (parseFloat(m.monto_descorche) || 0), 0);

  const filteredMovimientos = movimientos.filter(m => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      m.producto?.toLowerCase().includes(term) ||
      m.socio?.toLowerCase().includes(term) ||
      m.numero_socio?.toLowerCase().includes(term) ||
      m.motivo?.toLowerCase().includes(term) ||
      m.tipo?.toLowerCase().includes(term)
    );
  });

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="p-6 space-y-6" data-testid="consumos-cava-page">
      {/* Header with Navigation Tabs */}
      <CavaNavHeader
        title="Bitácora de Consumos y Descorches"
        subtitle="Registro operativo de consumos parciales, descorches en mesa y retiros de botellas"
        onRefresh={fetchConsumos}
        loading={loading}
      />

      {(error || contextError) && (
        <div className="p-4 rounded-lg bg-red-50 text-red-700 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          {error || contextError?.message || 'No se pudo resolver el contexto de acceso.'}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total de Movimientos / Consumos</p>
              <p className="text-2xl font-bold text-purple-600">{total}</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full text-purple-700">
              <Package className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Descorches en Esta Vista</p>
              <p className="text-2xl font-bold text-emerald-600">{formatCurrency(totalDescorches)}</p>
            </div>
            <div className="p-3 bg-emerald-100 rounded-full text-emerald-700">
              <DollarSign className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar por socio, botella, tipo de movimiento o motivo..."
              className="pl-9"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Tabla de Movimientos */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Historial de Movimientos ({total} registros)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading || filtersLoading || contextLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
            </div>
          ) : filteredMovimientos.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fecha / Hora</TableHead>
                    <TableHead>Socio Propietario</TableHead>
                    <TableHead>Botella</TableHead>
                    <TableHead>Tipo Movimiento</TableHead>
                    <TableHead className="text-center">% Consumido</TableHead>
                    <TableHead className="text-right">Descorche</TableHead>
                    <TableHead>Motivo / Ocasión</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredMovimientos.map((mov) => (
                    <TableRow key={mov.movimiento_id}>
                      <TableCell className="text-xs font-medium text-zinc-600 whitespace-nowrap">
                        {formatDate(mov.fecha)}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium text-zinc-900">{mov.socio}</div>
                        <div className="text-xs text-muted-foreground">#{mov.numero_socio}</div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium text-sm">{mov.producto}</div>
                        {mov.ubicacion && (
                          <div className="text-xs text-muted-foreground">Casillero: {mov.ubicacion}</div>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          mov.tipo === 'CONSUMO' ? 'bg-amber-100 text-amber-700' :
                          mov.tipo === 'INGRESO' ? 'bg-green-100 text-green-700' :
                          'bg-zinc-100 text-zinc-700'
                        }`}>
                          {mov.tipo}
                        </span>
                      </TableCell>
                      <TableCell className="text-center font-semibold text-sm">
                        {mov.porcentaje ? `${mov.porcentaje}%` : '-'}
                      </TableCell>
                      <TableCell className="text-right font-medium text-emerald-600">
                        {formatCurrency(mov.monto_descorche)}
                      </TableCell>
                      <TableCell className="text-sm text-zinc-600 max-w-xs truncate">
                        {mov.motivo || '-'}
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
              <Package className="h-12 w-12 mx-auto mb-4 opacity-20" />
              <p>No se encontraron movimientos registrados</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function ConsumosCava() {
  return (
    <CorporateFiltersProvider scope="cava_socios">
      <ConsumosCavaContent />
    </CorporateFiltersProvider>
  );
}
