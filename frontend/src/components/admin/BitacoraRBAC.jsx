/**
 * FASE 12: Panel de Bitácora RBAC de Solo Lectura
 * 
 * Componente aislado para consultar sec_bitacora_admin.
 * Acceso restringido a SuperAdministrador (verificado en backend).
 * 
 * REFACTORIZADO: Lógica extraída a useBitacoraRBACData hook
 * Subcomponentes en /components/admin/bitacora/
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RefreshCw, FileText, AlertCircle } from 'lucide-react';
import {
  useBitacoraRBACData,
  BitacoraFilters,
  BitacoraTable,
  BitacoraPagination,
  BitacoraDetailModal
} from './bitacora';

const BitacoraRBAC = () => {
  const {
    // Estado
    eventos,
    total,
    pagina,
    paginasTotal,
    loading,
    error,
    filtros,
    detalleOpen,
    eventoDetalle,
    LIMIT,
    // Acciones
    cargarEventos,
    handleAplicarFiltros,
    handleLimpiarFiltros,
    handlePaginaAnterior,
    handlePaginaSiguiente,
    handleVerDetalle,
    handleCerrarDetalle,
    updateFiltro
  } = useBitacoraRBACData();

  // Error de acceso
  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="py-8 text-center">
          <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-3" />
          <p className="text-red-700 font-medium">{error}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4" data-testid="bitacora-rbac">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-600" />
            Bitácora de Auditoría RBAC
          </h2>
          <p className="text-sm text-zinc-500">
            Registro de acciones administrativas del sistema
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => cargarEventos(pagina, filtros)}
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

      {/* Filtros */}
      <BitacoraFilters
        filtros={filtros}
        updateFiltro={updateFiltro}
        onAplicar={handleAplicarFiltros}
        onLimpiar={handleLimpiarFiltros}
        loading={loading}
      />

      {/* Tabla */}
      <Card>
        <CardHeader className="py-3 border-b">
          <CardTitle className="text-sm">
            Eventos ({total} registros)
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <BitacoraTable
            eventos={eventos}
            loading={loading}
            onVerDetalle={handleVerDetalle}
          />
          
          {eventos.length > 0 && (
            <BitacoraPagination
              pagina={pagina}
              paginasTotal={paginasTotal}
              total={total}
              limit={LIMIT}
              onAnterior={handlePaginaAnterior}
              onSiguiente={handlePaginaSiguiente}
              loading={loading}
            />
          )}
        </CardContent>
      </Card>

      {/* Modal de Detalle */}
      <BitacoraDetailModal
        open={detalleOpen}
        onClose={handleCerrarDetalle}
        evento={eventoDetalle}
      />
    </div>
  );
};

export default BitacoraRBAC;
