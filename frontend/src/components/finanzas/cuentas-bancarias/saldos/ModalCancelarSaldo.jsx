import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '../../../ui/dialog';
import { Button } from '../../../ui/button';
import { Textarea } from '../../../ui/textarea';
import { Label } from '../../../ui/label';
import { Alert, AlertDescription } from '../../../ui/alert';
import { AlertTriangle, Loader2, XCircle } from 'lucide-react';

/**
 * Modal de confirmación para cancelar saldo
 */
export function ModalCancelarSaldo({
  open,
  onClose,
  onConfirmar,
  saldo,
  moneda = 'MXN',
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

  if (!saldo) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[450px]" data-testid="modal-cancelar-saldo">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <XCircle className="h-5 w-5" />
            Cancelar saldo
          </DialogTitle>
          <DialogDescription>
            Esta acción marcará el registro de saldo como cancelado.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Info del saldo */}
          <div className="bg-gray-50 p-4 rounded-lg space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Fecha del saldo:</span>
              <span className="text-sm font-medium">{formatDate(saldo.fecha_saldo)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Saldo a cancelar:</span>
              <span className="text-sm font-medium text-emerald-600">
                {formatCurrency(saldo.saldo_final)}
              </span>
            </div>
          </div>

          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Al cancelar este saldo, quedará marcado como <strong>CANCELADO</strong> y 
              no se considerará en los cálculos. Esta acción no se puede deshacer.
            </AlertDescription>
          </Alert>

          {/* Motivo */}
          <div className="space-y-2">
            <Label htmlFor="motivo">Motivo de cancelación *</Label>
            <Textarea
              id="motivo"
              value={motivo}
              onChange={(e) => {
                setMotivo(e.target.value);
                setError('');
              }}
              placeholder="Ingrese el motivo de la cancelación (mínimo 10 caracteres)"
              rows={3}
              maxLength={500}
              className={error ? 'border-red-500' : ''}
              data-testid="textarea-motivo-cancelar"
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
            data-testid="btn-confirmar-cancelar"
          >
            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Confirmar cancelación
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default ModalCancelarSaldo;
