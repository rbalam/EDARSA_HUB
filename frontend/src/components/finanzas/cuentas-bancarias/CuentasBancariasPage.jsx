import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../ui/card';
import { Button } from '../../ui/button';
import { Alert, AlertDescription } from '../../ui/alert';
import { Badge } from '../../ui/badge';
import { 
  Landmark, Plus, RefreshCw, AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';

import TablaCuentasBancarias from './TablaCuentasBancarias';
import FormularioCuentaBancaria from './FormularioCuentaBancaria';
import ModalDesactivarCuenta from './ModalDesactivarCuenta';
import DetalleCuentaBancaria from './DetalleCuentaBancaria';
import TarjetaSaldoTotal from './saldos/TarjetaSaldoTotal';

import { useCuentasBancarias } from './hooks/useCuentasBancarias';
import { useBancos } from './hooks/useBancos';
import { useSaldosBancarios } from './hooks/useSaldosBancarios';
import { useFinanzasCorporateFilters } from '../../../filters';

/**
 * Página principal del módulo Cuentas Bancarias
 * P1-FASE5A.1-FUNC-FRONTEND
 */
export function CuentasBancariasPage() {
  // Hooks de datos
  const {
    cuentas,
    loading: loadingCuentas,
    error: errorCuentas,
    saving,
    fetchCuentas,
    crearCuenta,
    editarCuenta,
    desactivarCuenta,
    clearError
  } = useCuentasBancarias();
  
  const { bancos, loading: loadingBancos } = useBancos();
  const { saldoTotal, fetchSaldoTotal } = useSaldosBancarios();
  const {
    unidadesNegocio,
    selectedUnidad,
    setSelectedUnidad,
    loadingUnidades
  } = useFinanzasCorporateFilters();

  // Estados UI
  const [showFormulario, setShowFormulario] = useState(false);
  const [showModalDesactivar, setShowModalDesactivar] = useState(false);
  const [cuentaSeleccionada, setCuentaSeleccionada] = useState(null);
  const [modoEdicion, setModoEdicion] = useState(false);
  const [vistaDetalle, setVistaDetalle] = useState(false);

  const buildFiltroUnidad = useCallback(() => ({
    soloActivas: true,
    unidadNegocioPk: selectedUnidad || undefined
  }), [selectedUnidad]);

  useEffect(() => {
    const filtroUnidad = buildFiltroUnidad();
    fetchCuentas(filtroUnidad);
    fetchSaldoTotal({ unidadNegocioPk: selectedUnidad || undefined });
  }, [fetchCuentas, fetchSaldoTotal, buildFiltroUnidad, selectedUnidad]);

  // Handlers
  const handleNuevaCuenta = () => {
    setCuentaSeleccionada(null);
    setModoEdicion(false);
    setShowFormulario(true);
    clearError();
  };

  const handleEditarCuenta = (cuenta) => {
    setCuentaSeleccionada(cuenta);
    setModoEdicion(true);
    setShowFormulario(true);
    clearError();
  };

  const handleDesactivarCuenta = (cuenta) => {
    setCuentaSeleccionada(cuenta);
    setShowModalDesactivar(true);
    clearError();
  };

  const handleVerDetalle = (cuenta) => {
    setCuentaSeleccionada(cuenta);
    setVistaDetalle(true);
  };

  const handleCerrarDetalle = () => {
    setVistaDetalle(false);
    setCuentaSeleccionada(null);
    // Refrescar para obtener último saldo
    const filtroUnidad = buildFiltroUnidad();
    fetchCuentas(filtroUnidad);
    fetchSaldoTotal({ unidadNegocioPk: selectedUnidad || undefined });
  };

  const handleGuardarCuenta = async (data) => {
    try {
      if (modoEdicion && cuentaSeleccionada) {
        await editarCuenta(cuentaSeleccionada.cuenta_bancaria_id, data);
        toast.success('Cuenta bancaria actualizada correctamente');
      } else {
        if (!selectedUnidad) {
          toast.error('Seleccione una unidad de negocio para crear la cuenta');
          return;
        }
        await crearCuenta({
          ...data,
          unidad_negocio_pk: selectedUnidad
        });
        toast.success('Cuenta bancaria creada correctamente');
      }
      setShowFormulario(false);
      setCuentaSeleccionada(null);
      const filtroUnidad = buildFiltroUnidad();
      fetchCuentas(filtroUnidad);
      fetchSaldoTotal({ unidadNegocioPk: selectedUnidad || undefined });
    } catch (err) {
      toast.error(err.message || 'Error al guardar cuenta');
    }
  };

  const handleConfirmarDesactivar = async (motivo) => {
    if (!cuentaSeleccionada) return;
    
    try {
      await desactivarCuenta(cuentaSeleccionada.cuenta_bancaria_id, motivo);
      toast.success('Cuenta bancaria desactivada correctamente');
      setShowModalDesactivar(false);
      setCuentaSeleccionada(null);
      const filtroUnidad = buildFiltroUnidad();
      fetchCuentas(filtroUnidad);
      fetchSaldoTotal({ unidadNegocioPk: selectedUnidad || undefined });
    } catch (err) {
      toast.error(err.message || 'Error al desactivar cuenta');
    }
  };

  const handleRefrescar = useCallback(() => {
    const filtroUnidad = buildFiltroUnidad();
    fetchCuentas(filtroUnidad);
    fetchSaldoTotal({ unidadNegocioPk: selectedUnidad || undefined });
  }, [fetchCuentas, fetchSaldoTotal, buildFiltroUnidad, selectedUnidad]);

  // Si está en vista detalle, mostrar solo el detalle
  if (vistaDetalle && cuentaSeleccionada) {
    return (
      <DetalleCuentaBancaria
        cuenta={cuentaSeleccionada}
        onVolver={handleCerrarDetalle}
      />
    );
  }

  return (
    <div className="space-y-6" data-testid="cuentas-bancarias-page">
      {/* Header con saldo total */}
      <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-100 rounded-lg">
            <Landmark className="h-6 w-6 text-emerald-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Cuentas Bancarias</h2>
            <p className="text-sm text-gray-500">
              Gestione el catálogo de cuentas y capture saldos
            </p>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-2 items-center">
          <select
            value={selectedUnidad}
            onChange={(e) => setSelectedUnidad(e.target.value)}
            disabled={loadingUnidades}
            className="h-9 rounded-md border border-gray-300 bg-white px-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            data-testid="filtro-unidad-cuentas"
          >
            <option value="">Todas las unidades</option>
            {unidadesNegocio.map(u => (
              <option key={u.id} value={u.id}>{u.nombre}</option>
            ))}
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefrescar}
            disabled={loadingCuentas}
            data-testid="btn-refrescar"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loadingCuentas ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          <Button
            size="sm"
            onClick={handleNuevaCuenta}
            disabled={saving || !selectedUnidad}
            data-testid="btn-nueva-cuenta"
          >
            <Plus className="h-4 w-4 mr-2" />
            Nueva cuenta
          </Button>
        </div>
      </div>

      {/* Tarjeta de saldo total */}
      <TarjetaSaldoTotal saldoTotal={saldoTotal} />

      {/* Errores */}
      {errorCuentas && (
        <Alert variant="destructive" data-testid="error-alert">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{errorCuentas}</AlertDescription>
        </Alert>
      )}

      {/* Tabla de cuentas */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium">
              Catálogo de Cuentas
            </CardTitle>
            <Badge variant="secondary">
              {cuentas.length} cuenta{cuentas.length !== 1 ? 's' : ''}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <TablaCuentasBancarias
            cuentas={cuentas}
            loading={loadingCuentas}
            onEditar={handleEditarCuenta}
            onDesactivar={handleDesactivarCuenta}
            onVerDetalle={handleVerDetalle}
            onNuevaCuenta={handleNuevaCuenta}
          />
        </CardContent>
      </Card>

      {/* Modal crear/editar cuenta */}
      <FormularioCuentaBancaria
        open={showFormulario}
        onClose={() => {
          setShowFormulario(false);
          setCuentaSeleccionada(null);
        }}
        onGuardar={handleGuardarCuenta}
        cuenta={cuentaSeleccionada}
        modoEdicion={modoEdicion}
        bancos={bancos}
        loadingBancos={loadingBancos}
        saving={saving}
      />

      {/* Modal desactivar cuenta */}
      <ModalDesactivarCuenta
        open={showModalDesactivar}
        onClose={() => {
          setShowModalDesactivar(false);
          setCuentaSeleccionada(null);
        }}
        onConfirmar={handleConfirmarDesactivar}
        cuenta={cuentaSeleccionada}
        saving={saving}
      />
    </div>
  );
}

export default CuentasBancariasPage;
