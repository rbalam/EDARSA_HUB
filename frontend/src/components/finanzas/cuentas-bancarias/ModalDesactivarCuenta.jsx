import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '../../ui/dialog';
import { Button } from '../../ui/button';
import { Textarea } from '../../ui/textarea';
import { Label } from '../../ui/label';
import { Alert, AlertDescription } from '../../ui/alert';
import { AlertTriangle, Loader2 } from 'lucide-react';

/**
 * Modal de confirmación para desactivar cuenta bancaria
 */
export function ModalDesactivarCuenta({
  open,
  onClose,
  onConfirmar,
  cuenta,
  saving
}) {
  const [motivo, setMotivo] = useState('');
  const [error, setError] = useState('');

  const handleConfirmar = () => {
    if (motivo.trim().length < 10) {
      setError('El motivo debe tener al menos 10 caracteres');
      return;
    }
    if (motivo.trim().length > 500) {
      setError('El motivo no puede exceder 500 caracteres');
      return;
    }
    onConfirmar(motivo.trim());
  };

  const handleClose = () => {
    setMotivo('');
    setError('');
    onClose();
  };

  // Formatear moneda
  const formatCurrency = (value, moneda = 'MXN') => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: moneda,
      minimumFractionDigits: 2,
    }).format(value || 0);
  };

  if (!cuenta) return null;

  const tieneSaldos = cuenta.ultimo_saldo !== null && cuenta.ultimo_saldo !== undefined && cuenta.ultimo_saldo > 0;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[450px]" data-testid="modal-desactivar">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            Desactivar cuenta bancaria
          </DialogTitle>
          <DialogDescription>
            Esta acción desactivará la cuenta bancaria de forma permanente.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Info de la cuenta */}
          <div className="bg-gray-50 p-4 rounded-lg space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Alias:</span>
              <span className="text-sm font-medium">{cuenta.alias || 'Sin alias'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Banco:</span>
              <span className="text-sm font-medium">{cuenta.banco_nombre}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Cuenta:</span>
              <code className="text-sm bg-gray-200 px-2 py-0.5 rounded">
                {cuenta.numero_cuenta_enmascarado}
              </code>
            </div>
            {tieneSaldos && (
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Último saldo:</span>
                <span className="text-sm font-medium text-emerald-600">
                  {formatCurrency(cuenta.ultimo_saldo, cuenta.moneda)}
                </span>
              </div>
            )}
          </div>

          {/* Advertencia si tiene saldos */}
          {tieneSaldos && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Esta cuenta tiene un saldo registrado de{' '}
                <strong>{formatCurrency(cuenta.ultimo_saldo, cuenta.moneda)}</strong>.
                Asegúrese de que desea desactivarla.
              </AlertDescription>
            </Alert>
          )}

          {/* Motivo */}
          <div className="space-y-2">
            <Label htmlFor="motivo">Motivo de desactivación *</Label>
            <Textarea
              id="motivo"
              value={motivo}
              onChange={(e) => {
                setMotivo(e.target.value);
                setError('');
              }}
              placeholder="Ingrese el motivo de la desactivación (mínimo 10 caracteres)"
              rows={3}
              maxLength={500}
              className={error ? 'border-red-500' : ''}
              data-testid="textarea-motivo"
            />
            <div className="flex justify-between">
              {error ? (
                <p className="text-sm text-red-500">{error}</p>
              ) : (
                <span />
              )}
              <span className="text-xs text-gray-400">
                {motivo.length}/500
              </span>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={saving}
          >
            Cancelar
          </Button>
          <Button
            variant="destructive"
            onClick={handleConfirmar}
            disabled={saving || motivo.trim().length < 10}
            data-testid="btn-confirmar-desactivar"
          >
            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Confirmar desactivación
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default ModalDesactivarCuenta;
