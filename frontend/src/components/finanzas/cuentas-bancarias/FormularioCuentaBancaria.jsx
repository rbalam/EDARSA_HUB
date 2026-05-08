import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../../ui/dialog';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Checkbox } from '../../ui/checkbox';
import { Alert, AlertDescription } from '../../ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../ui/select';
import { AlertCircle, Loader2 } from 'lucide-react';

const MONEDAS = [
  { value: 'MXN', label: 'MXN - Peso Mexicano' },
  { value: 'USD', label: 'USD - Dólar Americano' },
  { value: 'EUR', label: 'EUR - Euro' },
  { value: 'CAD', label: 'CAD - Dólar Canadiense' },
];

/**
 * Formulario para crear/editar cuenta bancaria
 * En modo edición solo se puede modificar alias y es_principal
 */
export function FormularioCuentaBancaria({
  open,
  onClose,
  onGuardar,
  cuenta,
  modoEdicion,
  bancos,
  loadingBancos,
  saving
}) {
  const [formData, setFormData] = useState({
    banco_id: '',
    numero_cuenta: '',
    clabe: '',
    alias: '',
    moneda: 'MXN',
    es_principal: false
  });
  const [errors, setErrors] = useState({});

  // Inicializar formulario
  useEffect(() => {
    if (cuenta && modoEdicion) {
      setFormData({
        banco_id: cuenta.banco_id || '',
        numero_cuenta: '', // No se muestra el número real
        clabe: '', // No se muestra la CLABE real
        alias: cuenta.alias || '',
        moneda: cuenta.moneda || 'MXN',
        es_principal: cuenta.es_principal || false
      });
    } else {
      setFormData({
        banco_id: '',
        numero_cuenta: '',
        clabe: '',
        alias: '',
        moneda: 'MXN',
        es_principal: false
      });
    }
    setErrors({});
  }, [cuenta, modoEdicion, open]);

  // Validación
  const validar = () => {
    const newErrors = {};

    if (!modoEdicion) {
      // Validaciones solo para creación
      if (!formData.banco_id) {
        newErrors.banco_id = 'Seleccione un banco';
      }
      
      if (!formData.numero_cuenta) {
        newErrors.numero_cuenta = 'Número de cuenta requerido';
      } else if (!/^\d{10,20}$/.test(formData.numero_cuenta)) {
        newErrors.numero_cuenta = 'Debe tener entre 10 y 20 dígitos';
      }
      
      if (formData.clabe && !/^\d{18}$/.test(formData.clabe)) {
        newErrors.clabe = 'CLABE debe tener exactamente 18 dígitos';
      }
    }

    if (!formData.alias || formData.alias.trim().length < 3) {
      newErrors.alias = 'Mínimo 3 caracteres';
    } else if (formData.alias.trim().length > 50) {
      newErrors.alias = 'Máximo 50 caracteres';
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
    // Limpiar error del campo
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Handler solo números
  const handleNumericChange = (field, value) => {
    const numericValue = value.replace(/\D/g, '');
    handleChange(field, numericValue);
  };

  // Submit
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validar()) return;

    if (modoEdicion) {
      // Solo enviar campos editables
      onGuardar({
        alias: formData.alias.trim(),
        es_principal: formData.es_principal
      });
    } else {
      // Enviar todos los campos
      onGuardar({
        banco_id: parseInt(formData.banco_id),
        numero_cuenta: formData.numero_cuenta,
        clabe: formData.clabe || null,
        alias: formData.alias.trim(),
        moneda: formData.moneda,
        es_principal: formData.es_principal
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]" data-testid="modal-cuenta">
        <DialogHeader>
          <DialogTitle>
            {modoEdicion ? 'Editar cuenta bancaria' : 'Nueva cuenta bancaria'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Banco */}
          <div className="space-y-2">
            <Label htmlFor="banco">Banco *</Label>
            {modoEdicion ? (
              <Input
                value={cuenta?.banco_nombre || ''}
                disabled
                className="bg-gray-50"
              />
            ) : (
              <Select
                value={formData.banco_id}
                onValueChange={(value) => handleChange('banco_id', value)}
                disabled={loadingBancos}
              >
                <SelectTrigger 
                  className={errors.banco_id ? 'border-red-500' : ''}
                  data-testid="select-banco"
                >
                  <SelectValue placeholder={loadingBancos ? 'Cargando...' : 'Seleccione banco'} />
                </SelectTrigger>
                <SelectContent>
                  {bancos.map((banco) => (
                    <SelectItem key={banco.banco_id} value={String(banco.banco_id)}>
                      {banco.nombre_corto || banco.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {errors.banco_id && (
              <p className="text-sm text-red-500">{errors.banco_id}</p>
            )}
          </div>

          {/* Número de cuenta */}
          <div className="space-y-2">
            <Label htmlFor="numero_cuenta">Número de cuenta *</Label>
            {modoEdicion ? (
              <Input
                value={cuenta?.numero_cuenta_enmascarado || '****'}
                disabled
                className="bg-gray-50 font-mono"
              />
            ) : (
              <>
                <Input
                  id="numero_cuenta"
                  value={formData.numero_cuenta}
                  onChange={(e) => handleNumericChange('numero_cuenta', e.target.value)}
                  placeholder="10 a 20 dígitos"
                  maxLength={20}
                  className={`font-mono ${errors.numero_cuenta ? 'border-red-500' : ''}`}
                  data-testid="input-numero-cuenta"
                />
                {errors.numero_cuenta && (
                  <p className="text-sm text-red-500">{errors.numero_cuenta}</p>
                )}
              </>
            )}
          </div>

          {/* CLABE */}
          <div className="space-y-2">
            <Label htmlFor="clabe">CLABE (opcional)</Label>
            {modoEdicion ? (
              <Input
                value={cuenta?.clabe_enmascarada || '-'}
                disabled
                className="bg-gray-50 font-mono"
              />
            ) : (
              <>
                <Input
                  id="clabe"
                  value={formData.clabe}
                  onChange={(e) => handleNumericChange('clabe', e.target.value)}
                  placeholder="18 dígitos"
                  maxLength={18}
                  className={`font-mono ${errors.clabe ? 'border-red-500' : ''}`}
                  data-testid="input-clabe"
                />
                {errors.clabe && (
                  <p className="text-sm text-red-500">{errors.clabe}</p>
                )}
              </>
            )}
          </div>

          {/* Alias */}
          <div className="space-y-2">
            <Label htmlFor="alias">Alias *</Label>
            <Input
              id="alias"
              value={formData.alias}
              onChange={(e) => handleChange('alias', e.target.value)}
              placeholder="Ej: BBVA Principal"
              maxLength={50}
              className={errors.alias ? 'border-red-500' : ''}
              data-testid="input-alias"
            />
            {errors.alias && (
              <p className="text-sm text-red-500">{errors.alias}</p>
            )}
          </div>

          {/* Moneda */}
          <div className="space-y-2">
            <Label htmlFor="moneda">Moneda *</Label>
            {modoEdicion ? (
              <Input
                value={cuenta?.moneda || 'MXN'}
                disabled
                className="bg-gray-50"
              />
            ) : (
              <Select
                value={formData.moneda}
                onValueChange={(value) => handleChange('moneda', value)}
              >
                <SelectTrigger data-testid="select-moneda">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MONEDAS.map((moneda) => (
                    <SelectItem key={moneda.value} value={moneda.value}>
                      {moneda.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Es principal */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="es_principal"
              checked={formData.es_principal}
              onCheckedChange={(checked) => handleChange('es_principal', checked)}
              data-testid="checkbox-principal"
            />
            <Label htmlFor="es_principal" className="cursor-pointer">
              Es cuenta principal
            </Label>
          </div>

          {/* Info modo edición */}
          {modoEdicion && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Solo puede modificar el alias y la marca de cuenta principal.
                Los datos bancarios no son editables por seguridad.
              </AlertDescription>
            </Alert>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={saving}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={saving} data-testid="btn-guardar">
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {modoEdicion ? 'Guardar cambios' : 'Crear cuenta'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default FormularioCuentaBancaria;
