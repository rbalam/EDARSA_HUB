import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { 
  Pencil, Trash2, Eye, Landmark, Wallet, Building2
} from 'lucide-react';
import { Skeleton } from '../../ui/skeleton';

/**
 * Tabla de listado de cuentas bancarias
 * Muestra datos enmascarados (cuenta/CLABE)
 */
export function TablaCuentasBancarias({ 
  cuentas, 
  loading, 
  onEditar, 
  onDesactivar, 
  onVerDetalle,
  onNuevaCuenta 
}) {
  // Formatear moneda
  const formatCurrency = (value, moneda = 'MXN') => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: moneda,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value || 0);
  };

  // Formatear fecha
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-MX', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  // Estado vacío
  if (!loading && (!cuentas || cuentas.length === 0)) {
    return (
      <div className="text-center py-12" data-testid="empty-state">
        <Landmark className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">
          No hay cuentas bancarias
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          Configure al menos una cuenta bancaria para comenzar.
        </p>
        <div className="mt-6">
          <Button onClick={onNuevaCuenta} data-testid="btn-nueva-empty">
            + Nueva cuenta
          </Button>
        </div>
      </div>
    );
  }

  // Loading skeleton
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center space-x-4 p-4 border rounded-lg">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="space-y-2 flex-1">
              <Skeleton className="h-4 w-[250px]" />
              <Skeleton className="h-4 w-[200px]" />
            </div>
            <Skeleton className="h-8 w-[100px]" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto" data-testid="tabla-cuentas">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[200px]">Alias / Banco</TableHead>
            <TableHead>Cuenta</TableHead>
            <TableHead>CLABE</TableHead>
            <TableHead>Moneda</TableHead>
            <TableHead className="text-right">Último Saldo</TableHead>
            <TableHead>Fecha Saldo</TableHead>
            <TableHead className="text-center">Principal</TableHead>
            <TableHead className="text-right">Acciones</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {cuentas.map((cuenta) => (
            <TableRow 
              key={cuenta.cuenta_bancaria_id}
              className="cursor-pointer hover:bg-gray-50"
              onClick={() => onVerDetalle(cuenta)}
              data-testid={`row-cuenta-${cuenta.cuenta_bancaria_id}`}
            >
              <TableCell>
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-blue-50 rounded">
                    <Building2 className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-medium text-sm">{cuenta.alias || 'Sin alias'}</div>
                    <div className="text-xs text-gray-500">{cuenta.banco_nombre}</div>
                  </div>
                </div>
              </TableCell>
              <TableCell>
                <code className="text-sm bg-gray-100 px-2 py-0.5 rounded">
                  {cuenta.numero_cuenta_enmascarado || '****'}
                </code>
              </TableCell>
              <TableCell>
                <code className="text-sm bg-gray-100 px-2 py-0.5 rounded">
                  {cuenta.clabe_enmascarada || '-'}
                </code>
              </TableCell>
              <TableCell>
                <Badge variant="outline" className="font-mono">
                  {cuenta.moneda || 'MXN'}
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                {cuenta.ultimo_saldo !== null && cuenta.ultimo_saldo !== undefined ? (
                  <span className="font-medium text-emerald-600">
                    {formatCurrency(cuenta.ultimo_saldo, cuenta.moneda)}
                  </span>
                ) : (
                  <span className="text-gray-400 text-sm">Sin saldo</span>
                )}
              </TableCell>
              <TableCell>
                <span className="text-sm text-gray-500">
                  {formatDate(cuenta.fecha_ultimo_saldo)}
                </span>
              </TableCell>
              <TableCell className="text-center">
                {cuenta.es_principal && (
                  <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">
                    Principal
                  </Badge>
                )}
              </TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={(e) => {
                      e.stopPropagation();
                      onVerDetalle(cuenta);
                    }}
                    title="Ver detalle y saldos"
                    data-testid={`btn-ver-${cuenta.cuenta_bancaria_id}`}
                  >
                    <Eye className="h-4 w-4 text-gray-500" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEditar(cuenta);
                    }}
                    title="Editar cuenta"
                    data-testid={`btn-editar-${cuenta.cuenta_bancaria_id}`}
                  >
                    <Pencil className="h-4 w-4 text-blue-500" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDesactivar(cuenta);
                    }}
                    title="Desactivar cuenta"
                    data-testid={`btn-desactivar-${cuenta.cuenta_bancaria_id}`}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export default TablaCuentasBancarias;
