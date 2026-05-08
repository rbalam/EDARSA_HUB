import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../ui/card';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { Alert, AlertDescription } from '../../ui/alert';
import { 
  ArrowLeft, Building2, Plus, RefreshCw, AlertCircle, Wallet
} from 'lucide-react';
import { toast } from 'sonner';

import HistorialSaldos from './saldos/HistorialSaldos';
import FormularioCapturaSaldo from './saldos/FormularioCapturaSaldo';
import FormularioCorreccionSaldo from './saldos/FormularioCorreccionSaldo';
import ModalCancelarSaldo from './saldos/ModalCancelarSaldo';
import { useSaldosBancarios } from './hooks/useSaldosBancarios';

/**
 * Vista detalle de cuenta bancaria con historial de saldos
 */
export function DetalleCuentaBancaria({ cuenta, onVolver }) {
  const {
    saldos,
    saldoActual,
    loading,
    error,
    saving,
    fetchSaldos,
    fetchSaldoActual,
    capturarSaldo,
    corregirSaldo,
    cancelarSaldo,
    clearError
  } = useSaldosBancarios();

  // Estados UI
  const [showCaptura, setShowCaptura] = useState(false);
  const [showCorreccion, setShowCorreccion] = useState(false);
  const [showCancelar, setShowCancelar] = useState(false);
  const [saldoSeleccionado, setSaldoSeleccionado] = useState(null);

  // Cargar datos
  const cargarDatos = useCallback(async () => {
    if (!cuenta?.cuenta_bancaria_id) return;
    
    try {
      await Promise.all([
        fetchSaldos(cuenta.cuenta_bancaria_id, { limite: 50 }),
        fetchSaldoActual(cuenta.cuenta_bancaria_id)
      ]);
    } catch (err) {
      console.error('Error cargando datos:', err);
    }
  }, [cuenta?.cuenta_bancaria_id, fetchSaldos, fetchSaldoActual]);

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);

  // Handlers
  const handleCapturarSaldo = async (data) => {
    try {
      await capturarSaldo({
        cuenta_bancaria_id: cuenta.cuenta_bancaria_id,
        ...data
      });
      toast.success('Saldo capturado correctamente');
      setShowCaptura(false);
      cargarDatos();
    } catch (err) {
      toast.error(err.message || 'Error al capturar saldo');
    }
  };

  const handleCorregirSaldo = async (data) => {
    if (!saldoSeleccionado) return;
    
    try {
      await corregirSaldo(saldoSeleccionado.saldo_bancario_id, data);
      toast.success('Saldo corregido correctamente');
      setShowCorreccion(false);
      setSaldoSeleccionado(null);
      cargarDatos();
    } catch (err) {
      toast.error(err.message || 'Error al corregir saldo');
    }
  };

  const handleCancelarSaldo = async (motivo) => {
    if (!saldoSeleccionado) return;
    
    try {
      await cancelarSaldo(saldoSeleccionado.saldo_bancario_id, motivo);
      toast.success('Saldo cancelado correctamente');
      setShowCancelar(false);
      setSaldoSeleccionado(null);
      cargarDatos();
    } catch (err) {
      toast.error(err.message || 'Error al cancelar saldo');
    }
  };

  const handleOpenCorreccion = (saldo) => {
    setSaldoSeleccionado(saldo);
    setShowCorreccion(true);
    clearError();
  };

  const handleOpenCancelar = (saldo) => {
    setSaldoSeleccionado(saldo);
    setShowCancelar(true);
    clearError();
  };

  // Formatear moneda
  const formatCurrency = (value, moneda = 'MXN') => {
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

  return (
    <div className="space-y-6" data-testid="detalle-cuenta">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onVolver}
            data-testid="btn-volver"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-blue-600" />
              <h2 className="text-xl font-semibold">{cuenta.alias || 'Sin alias'}</h2>
              {cuenta.es_principal && (
                <Badge className="bg-amber-100 text-amber-800">Principal</Badge>
              )}
            </div>
            <p className="text-sm text-gray-500">
              {cuenta.banco_nombre} • {cuenta.numero_cuenta_enmascarado}
            </p>
          </div>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={cargarDatos}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          <Button
            size="sm"
            onClick={() => {
              setShowCaptura(true);
              clearError();
            }}
            disabled={saving}
            data-testid="btn-capturar-saldo"
          >
            <Plus className="h-4 w-4 mr-2" />
            Capturar saldo
          </Button>
        </div>
      </div>

      {/* Info de la cuenta */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-100 rounded-lg">
                <Wallet className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Saldo Actual</p>
                <p className="text-2xl font-bold text-emerald-600">
                  {saldoActual 
                    ? formatCurrency(saldoActual.saldo_final, cuenta.moneda)
                    : '$0.00'
                  }
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-500">Última actualización</p>
            <p className="text-lg font-medium">
              {saldoActual ? formatDate(saldoActual.fecha_saldo) : '-'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-500">CLABE</p>
            <code className="text-lg font-mono bg-gray-100 px-2 py-1 rounded">
              {cuenta.clabe_enmascarada || '-'}
            </code>
          </CardContent>
        </Card>
      </div>

      {/* Error */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Historial de saldos */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">
            Historial de Saldos
          </CardTitle>
        </CardHeader>
        <CardContent>
          <HistorialSaldos
            saldos={saldos}
            loading={loading}
            moneda={cuenta.moneda}
            onCorregir={handleOpenCorreccion}
            onCancelar={handleOpenCancelar}
            onCapturar={() => {
              setShowCaptura(true);
              clearError();
            }}
          />
        </CardContent>
      </Card>

      {/* Modal captura de saldo */}
      <FormularioCapturaSaldo
        open={showCaptura}
        onClose={() => setShowCaptura(false)}
        onGuardar={handleCapturarSaldo}
        cuenta={cuenta}
        saving={saving}
      />

      {/* Modal corrección de saldo */}
      <FormularioCorreccionSaldo
        open={showCorreccion}
        onClose={() => {
          setShowCorreccion(false);
          setSaldoSeleccionado(null);
        }}
        onGuardar={handleCorregirSaldo}
        saldo={saldoSeleccionado}
        moneda={cuenta.moneda}
        saving={saving}
      />

      {/* Modal cancelar saldo */}
      <ModalCancelarSaldo
        open={showCancelar}
        onClose={() => {
          setShowCancelar(false);
          setSaldoSeleccionado(null);
        }}
        onConfirmar={handleCancelarSaldo}
        saldo={saldoSeleccionado}
        moneda={cuenta.moneda}
        saving={saving}
      />
    </div>
  );
}

export default DetalleCuentaBancaria;
