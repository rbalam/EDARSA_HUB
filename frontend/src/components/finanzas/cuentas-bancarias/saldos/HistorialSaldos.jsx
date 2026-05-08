import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../ui/table';
import { Button } from '../../../ui/button';
import { Badge } from '../../../ui/badge';
import { Pencil, XCircle, Clock, CheckCircle, AlertTriangle } from 'lucide-react';
import { Skeleton } from '../../../ui/skeleton';

/**
 * Tabla de historial de saldos de una cuenta
 */
export function HistorialSaldos({ 
  saldos, 
  loading, 
  moneda = 'MXN',
  onCorregir, 
  onCancelar,
  onCapturar
}) {
  // Formatear moneda
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: moneda,
      minimumFractionDigits: 2,
    }).format(value || 0);
  };

  // Formatear fecha
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  // Formatear datetime
  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Obtener badge de estatus
  const getStatusBadge = (estatus, esVigente) => {
    if (estatus === 'VIGENTE' || esVigente) {
      return (
        <Badge className="bg-emerald-100 text-emerald-800">
          <CheckCircle className="h-3 w-3 mr-1" />
          Vigente
        </Badge>
      );
    }
    if (estatus === 'CORREGIDO') {
      return (
        <Badge className="bg-amber-100 text-amber-800">
          <AlertTriangle className="h-3 w-3 mr-1" />
          Corregido
        </Badge>
      );
    }
    if (estatus === 'CANCELADO') {
      return (
        <Badge className="bg-red-100 text-red-800">
          <XCircle className="h-3 w-3 mr-1" />
          Cancelado
        </Badge>
      );
    }
    return (
      <Badge variant="outline">
        <Clock className="h-3 w-3 mr-1" />
        {estatus}
      </Badge>
    );
  };

  // Estado vacío
  if (!loading && (!saldos || saldos.length === 0)) {
    return (
      <div className="text-center py-12" data-testid="empty-saldos">
        <Clock className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">
          Sin historial de saldos
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          Capture el primer saldo de esta cuenta.
        </p>
        <div className="mt-6">
          <Button onClick={onCapturar} data-testid="btn-capturar-empty">
            + Capturar saldo
          </Button>
        </div>
      </div>
    );
  }

  // Loading skeleton
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center space-x-4 p-3 border rounded">
            <Skeleton className="h-6 w-[100px]" />
            <Skeleton className="h-6 w-[150px]" />
            <Skeleton className="h-6 w-[80px]" />
            <Skeleton className="h-6 w-[120px]" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto" data-testid="historial-saldos">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Fecha Saldo</TableHead>
            <TableHead className="text-right">Saldo Final</TableHead>
            <TableHead>Estatus</TableHead>
            <TableHead>Registrado</TableHead>
            <TableHead>Motivo</TableHead>
            <TableHead className="text-right">Acciones</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {saldos.map((saldo) => {
            const esVigente = saldo.es_vigente || saldo.estatus === 'VIGENTE';
            const esCancelado = saldo.estatus === 'CANCELADO';
            const esCorregido = saldo.estatus === 'CORREGIDO';
            
            return (
              <TableRow 
                key={saldo.saldo_bancario_id}
                className={`
                  ${esVigente ? 'bg-emerald-50/50' : ''}
                  ${esCancelado ? 'opacity-50' : ''}
                `}
                data-testid={`row-saldo-${saldo.saldo_bancario_id}`}
              >
                <TableCell className="font-medium">
                  {formatDate(saldo.fecha_saldo)}
                </TableCell>
                <TableCell className="text-right">
                  <span className={`font-mono font-medium ${esVigente ? 'text-emerald-600' : 'text-gray-600'}`}>
                    {formatCurrency(saldo.saldo_final)}
                  </span>
                </TableCell>
                <TableCell>
                  {getStatusBadge(saldo.estatus, saldo.es_vigente)}
                </TableCell>
                <TableCell>
                  <span className="text-sm text-gray-500">
                    {formatDateTime(saldo.fecha_creacion)}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-sm text-gray-500 max-w-[200px] truncate block">
                    {saldo.motivo_correccion || saldo.motivo_cancelacion || '-'}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  {esVigente && !esCancelado && !esCorregido && (
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => onCorregir(saldo)}
                        title="Corregir saldo"
                        data-testid={`btn-corregir-${saldo.saldo_bancario_id}`}
                      >
                        <Pencil className="h-4 w-4 text-blue-500" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => onCancelar(saldo)}
                        title="Cancelar saldo"
                        data-testid={`btn-cancelar-${saldo.saldo_bancario_id}`}
                      >
                        <XCircle className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

export default HistorialSaldos;
