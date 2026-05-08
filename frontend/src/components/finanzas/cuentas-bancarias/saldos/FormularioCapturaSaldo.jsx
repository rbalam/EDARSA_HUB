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
import { Calendar } from '../../../ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../../../ui/popover';
import { CalendarIcon, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

/**
 * Formulario para capturar nuevo saldo bancario
 */
export function FormularioCapturaSaldo({
  open,
  onClose,
  onGuardar,
  cuenta,
  saving
}) {
  const [formData, setFormData] = useState({
    fecha_saldo: new Date(),
    saldo_final: ''
  });
  const [errors, setErrors] = useState({});

  // Reset formulario
  useEffect(() => {
    if (open) {
      setFormData({
        fecha_saldo: new Date(),
        saldo_final: ''
      });
      setErrors({});
    }
  }, [open]);

  // Validar
  const validar = () => {
    const newErrors = {};

    if (!formData.fecha_saldo) {
      newErrors.fecha_saldo = 'Seleccione una fecha';
    }

    if (!formData.saldo_final && formData.saldo_final !== 0) {
      newErrors.saldo_final = 'Ingrese el saldo';
    } else {
      const saldo = parseFloat(formData.saldo_final);
      if (isNaN(saldo)) {
        newErrors.saldo_final = 'Ingrese un monto válido';
      } else if (saldo < 0) {
        newErrors.saldo_final = 'El saldo no puede ser negativo';
      }
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
    // Permitir números y punto decimal
    const cleanValue = value.replace(/[^0-9.]/g, '');
    // Solo un punto decimal
    const parts = cleanValue.split('.');
    if (parts.length > 2) return;
    if (parts[1] && parts[1].length > 2) return;
    
    handleChange('saldo_final', cleanValue);
  };

  // Submit
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validar()) return;

    const fechaFormateada = format(formData.fecha_saldo, 'yyyy-MM-dd');
    
    onGuardar({
      fecha_saldo: fechaFormateada,
      saldo_final: parseFloat(formData.saldo_final)
    });
  };

  // Formatear moneda para display
  const formatCurrency = (value, moneda = 'MXN') => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: moneda,
    }).format(value || 0);
  };

  if (!cuenta) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[400px]" data-testid="modal-captura-saldo">
        <DialogHeader>
          <DialogTitle>Capturar saldo</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Info de cuenta */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-sm font-medium">{cuenta.alias}</p>
            <p className="text-xs text-gray-500">
              {cuenta.banco_nombre} • {cuenta.numero_cuenta_enmascarado}
            </p>
          </div>

          {/* Fecha */}
          <div className="space-y-2">
            <Label>Fecha del saldo *</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={`w-full justify-start text-left font-normal ${errors.fecha_saldo ? 'border-red-500' : ''}`}
                  data-testid="btn-fecha"
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {formData.fecha_saldo ? (
                    format(formData.fecha_saldo, "d 'de' MMMM, yyyy", { locale: es })
                  ) : (
                    <span>Seleccione fecha</span>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={formData.fecha_saldo}
                  onSelect={(date) => handleChange('fecha_saldo', date)}
                  disabled={(date) => date > new Date()}
                  locale={es}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
            {errors.fecha_saldo && (
              <p className="text-sm text-red-500">{errors.fecha_saldo}</p>
            )}
          </div>

          {/* Saldo */}
          <div className="space-y-2">
            <Label htmlFor="saldo_final">Saldo final ({cuenta.moneda || 'MXN'}) *</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
              <Input
                id="saldo_final"
                value={formData.saldo_final}
                onChange={(e) => handleMontoChange(e.target.value)}
                placeholder="0.00"
                className={`pl-7 font-mono text-lg ${errors.saldo_final ? 'border-red-500' : ''}`}
                data-testid="input-saldo"
              />
            </div>
            {errors.saldo_final && (
              <p className="text-sm text-red-500">{errors.saldo_final}</p>
            )}
            {formData.saldo_final && !errors.saldo_final && (
              <p className="text-sm text-gray-500">
                {formatCurrency(parseFloat(formData.saldo_final) || 0, cuenta.moneda)}
              </p>
            )}
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
            <Button type="submit" disabled={saving} data-testid="btn-guardar-saldo">
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Capturar saldo
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default FormularioCapturaSaldo;
