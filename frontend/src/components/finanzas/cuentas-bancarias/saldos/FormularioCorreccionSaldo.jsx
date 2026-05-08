import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../../../ui/dialog';
import { Button } from '../../../ui/button';
import { Input } from '../../../ui/input';
import { Label } from '../../../ui/label';
import { Textarea } from '../../../ui/textarea';
import { Alert, AlertDescription } from '../../../ui/alert';
import { AlertTriangle, Loader2 } from 'lucide-react';

/**
 * Formulario para corregir un saldo existente
 * El saldo original se marca como CORREGIDO y se crea uno nuevo VIGENTE
 */
export function FormularioCorreccionSaldo({
  open,
  onClose,
  onGuardar,
  saldo,
  moneda = 'MXN',
  saving
}) {
  const [formData, setFormData] = useState({
    saldo_correcto: '',
    motivo: ''
  });
  const [errors, setErrors] = useState({});

  // Reset formulario
  useEffect(() => {
    if (open && saldo) {
      setFormData({
        saldo_correcto: saldo.saldo_final?.toString() || '',
        motivo: ''
      });
      setErrors({});
    }
  }, [open, saldo]);

  // Validar
  const validar = () => {
    const newErrors = {};

    if (!formData.saldo_correcto && formData.saldo_correcto !== '0') {
      newErrors.saldo_correcto = 'Ingrese el saldo correcto';
    } else {
      const saldoNum = parseFloat(formData.saldo_correcto);
      if (isNaN(saldoNum)) {
        newErrors.saldo_correcto = 'Ingrese un monto válido';
      } else if (saldoNum < 0) {
        newErrors.saldo_correcto = 'El saldo no puede ser negativo';
      }
    }

    if (!formData.motivo || formData.motivo.trim().length < 10) {
      newErrors.motivo = 'El motivo debe tener al menos 10 caracteres';
    } else if (formData.motivo.trim().length > 500) {
      newErrors.motivo = 'El motivo no puede exceder 500 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handler de cambios
  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Handler para monto
  const handleMontoChange = (value) => {
    const cleanValue = value.replace(/[^0-9.]/g, '');
    const parts = cleanValue.split('.');
    if (parts.length > 2) return;
    if (parts[1] && parts[1].length > 2) return;
    
    handleChange('saldo_correcto', cleanValue);
  };

  // Submit
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validar()) return;

    onGuardar({
      saldo_correcto: parseFloat(formData.saldo_correcto),
      motivo: formData.motivo.trim()
    });
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

  const diferencia = formData.saldo_correcto 
    ? parseFloat(formData.saldo_correcto) - (saldo.saldo_final || 0)
    : 0;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[450px]" data-testid="modal-correccion-saldo">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-amber-600">
            <AlertTriangle className="h-5 w-5" />
            Corregir saldo
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Info del saldo original */}
          <div className="bg-gray-50 p-4 rounded-lg space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Fecha del saldo:</span>
              <span className="text-sm font-medium">{formatDate(saldo.fecha_saldo)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Saldo original:</span>
              <span className="text-sm font-medium text-red-600">
                {formatCurrency(saldo.saldo_final)}
              </span>
            </div>
          </div>

          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              El saldo original quedará marcado como <strong>CORREGIDO</strong> y 
              se creará un nuevo registro con el saldo correcto.
            </AlertDescription>
          </Alert>

          {/* Saldo correcto */}
          <div className="space-y-2">
            <Label htmlFor="saldo_correcto">Saldo correcto ({moneda}) *</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
              <Input
                id="saldo_correcto"
                value={formData.saldo_correcto}
                onChange={(e) => handleMontoChange(e.target.value)}
                placeholder="0.00"
                className={`pl-7 font-mono text-lg ${errors.saldo_correcto ? 'border-red-500' : ''}`}
                data-testid="input-saldo-correcto"
              />
            </div>
            {errors.saldo_correcto && (
              <p className="text-sm text-red-500">{errors.saldo_correcto}</p>
            )}
            {formData.saldo_correcto && !errors.saldo_correcto && diferencia !== 0 && (
              <p className={`text-sm ${diferencia > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                Diferencia: {diferencia > 0 ? '+' : ''}{formatCurrency(diferencia)}
              </p>
            )}
          </div>

          {/* Motivo */}
          <div className="space-y-2">
            <Label htmlFor="motivo">Motivo de corrección *</Label>
            <Textarea
              id="motivo"
              value={formData.motivo}
              onChange={(e) => handleChange('motivo', e.target.value)}
              placeholder="Explique el motivo de la corrección (mínimo 10 caracteres)"
              rows={3}
              maxLength={500}
              className={errors.motivo ? 'border-red-500' : ''}
              data-testid="textarea-motivo"
            />
            <div className="flex justify-between">
              {errors.motivo ? (
                <p className="text-sm text-red-500">{errors.motivo}</p>
              ) : (
                <span />
              )}
              <span className="text-xs text-gray-400">
                {formData.motivo.length}/500
              </span>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={saving}
            >
              Cancelar
            </Button>
            <Button 
              type="submit" 
              disabled={saving}
              className="bg-amber-600 hover:bg-amber-700"
              data-testid="btn-confirmar-correccion"
            >
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Confirmar corrección
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default FormularioCorreccionSaldo;
