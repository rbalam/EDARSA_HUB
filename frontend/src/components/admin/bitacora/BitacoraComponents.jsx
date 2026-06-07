/**
 * Subcomponentes para BitacoraRBAC
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  FileText, 
  Filter,
  RefreshCw,
  Calendar,
  User,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';

// ============================================================================
// Utilidades
// ============================================================================

export const formatearFecha = (timestamp) => {
  if (!timestamp) return '-';
  try {
    const fecha = new Date(timestamp);
    return fecha.toLocaleString('es-MX', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch {
    return timestamp;
  }
};

export const getResultadoBadge = (resultado) => {
  switch (resultado?.toLowerCase()) {
    case 'exitoso':
    case 'success':
      return <Badge className="bg-green-100 text-green-800 hover:bg-green-100"><CheckCircle className="w-3 h-3 mr-1" />Exitoso</Badge>;
    case 'fallido':
    case 'failed':
      return <Badge className="bg-red-100 text-red-800 hover:bg-red-100"><XCircle className="w-3 h-3 mr-1" />Fallido</Badge>;
    case 'parcial':
      return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100"><AlertCircle className="w-3 h-3 mr-1" />Parcial</Badge>;
    default:
      return <Badge variant="secondary">{resultado || '-'}</Badge>;
  }
};

export const getTipoBadge = (tipo) => {
  const tipos = {
    'LOGIN': { color: 'bg-blue-100 text-blue-800', label: 'Login' },
    'LOGOUT': { color: 'bg-zinc-100 text-zinc-800', label: 'Logout' },
    'CREAR': { color: 'bg-green-100 text-green-800', label: 'Crear' },
    'EDITAR': { color: 'bg-yellow-100 text-yellow-800', label: 'Editar' },
    'ELIMINAR': { color: 'bg-red-100 text-red-800', label: 'Eliminar' },
    'ASIGNAR': { color: 'bg-purple-100 text-purple-800', label: 'Asignar' },
    'REVOCAR': { color: 'bg-orange-100 text-orange-800', label: 'Revocar' }
  };
  const config = tipos[tipo?.toUpperCase()] || { color: 'bg-zinc-100 text-zinc-800', label: tipo || '-' };
  return <Badge className={`${config.color} hover:${config.color}`}>{config.label}</Badge>;
};

// ============================================================================
// BitacoraFilters - Panel de filtros
// ============================================================================

export function BitacoraFilters({ 
  filtros, 
  updateFiltro, 
  onAplicar, 
  onLimpiar, 
  loading 
}) {
  return (
    <Card className="mb-4">
      <CardHeader className="py-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Filter className="h-4 w-4" />
          Filtros
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <label className="text-xs text-zinc-500 mb-1 block">Fecha Inicio</label>
            <Input
              type="date"
              value={filtros.fecha_inicio}
              onChange={(e) => updateFiltro('fecha_inicio', e.target.value)}
              className="h-9"
            />
          </div>
          <div>
            <label className="text-xs text-zinc-500 mb-1 block">Fecha Fin</label>
            <Input
              type="date"
              value={filtros.fecha_fin}
              onChange={(e) => updateFiltro('fecha_fin', e.target.value)}
              className="h-9"
            />
          </div>
          <div>
            <label className="text-xs text-zinc-500 mb-1 block">Email</label>
            <Input
              type="text"
              placeholder="usuario@ejemplo.com"
              value={filtros.email}
              onChange={(e) => updateFiltro('email', e.target.value)}
              className="h-9"
            />
          </div>
          <div>
            <label className="text-xs text-zinc-500 mb-1 block">Resultado</label>
            <Select value={filtros.resultado || 'todos'} onValueChange={(v) => updateFiltro('resultado', v === 'todos' ? '' : v)}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Todos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos</SelectItem>
                <SelectItem value="exitoso">Exitoso</SelectItem>
                <SelectItem value="fallido">Fallido</SelectItem>
                <SelectItem value="parcial">Parcial</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs text-zinc-500 mb-1 block">Tipo</label>
            <Select value={filtros.tipo || 'todos'} onValueChange={(v) => updateFiltro('tipo', v === 'todos' ? '' : v)}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Todos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos</SelectItem>
                <SelectItem value="LOGIN">Login</SelectItem>
                <SelectItem value="LOGOUT">Logout</SelectItem>
                <SelectItem value="CREAR">Crear</SelectItem>
                <SelectItem value="EDITAR">Editar</SelectItem>
                <SelectItem value="ELIMINAR">Eliminar</SelectItem>
                <SelectItem value="ASIGNAR">Asignar</SelectItem>
                <SelectItem value="REVOCAR">Revocar</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" size="sm" onClick={onLimpiar} disabled={loading}>
            Limpiar
          </Button>
          <Button size="sm" onClick={onAplicar} disabled={loading}>
            <Search className="h-4 w-4 mr-1" />
            Aplicar Filtros
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// BitacoraTable - Tabla de eventos
// ============================================================================

export function BitacoraTable({ eventos, loading, onVerDetalle }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="h-6 w-6 animate-spin text-zinc-400" />
        <span className="ml-2 text-zinc-500">Cargando eventos...</span>
      </div>
    );
  }

  if (eventos.length === 0) {
    return (
      <div className="text-center py-12 text-zinc-500">
        <FileText className="h-12 w-12 mx-auto mb-3 text-zinc-300" />
        <p>No se encontraron eventos</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-zinc-50 border-b">
          <tr>
            <th className="text-left p-3 font-medium">Fecha</th>
            <th className="text-left p-3 font-medium">Usuario</th>
            <th className="text-left p-3 font-medium">Tipo</th>
            <th className="text-left p-3 font-medium">Descripción</th>
            <th className="text-left p-3 font-medium">Resultado</th>
            <th className="text-center p-3 font-medium">Acción</th>
          </tr>
        </thead>
        <tbody>
          {eventos.map((evento, idx) => (
            <tr key={evento.id || idx} className="border-b hover:bg-zinc-50">
              <td className="p-3 whitespace-nowrap">
                <div className="flex items-center gap-1 text-xs text-zinc-600">
                  <Calendar className="h-3 w-3" />
                  {formatearFecha(evento.timestamp)}
                </div>
              </td>
              <td className="p-3">
                <div className="flex items-center gap-1">
                  <User className="h-3 w-3 text-zinc-400" />
                  <span className="text-xs">{evento.email || '-'}</span>
                </div>
              </td>
              <td className="p-3">{getTipoBadge(evento.tipo)}</td>
              <td className="p-3 max-w-xs truncate" title={evento.descripcion}>
                {evento.descripcion || '-'}
              </td>
              <td className="p-3">{getResultadoBadge(evento.resultado)}</td>
              <td className="p-3 text-center">
                <Button variant="ghost" size="sm" onClick={() => onVerDetalle(evento)}>
                  <FileText className="h-4 w-4" />
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ============================================================================
// BitacoraPagination - Controles de paginación
// ============================================================================

export function BitacoraPagination({ 
  pagina, 
  paginasTotal, 
  total, 
  limit,
  onAnterior, 
  onSiguiente,
  loading 
}) {
  const inicio = (pagina - 1) * limit + 1;
  const fin = Math.min(pagina * limit, total);

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t">
      <div className="text-sm text-zinc-500">
        Mostrando {inicio}-{fin} de {total} eventos
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onAnterior}
          disabled={pagina <= 1 || loading}
        >
          <ChevronLeft className="h-4 w-4" />
          Anterior
        </Button>
        <span className="text-sm text-zinc-600">
          Página {pagina} de {paginasTotal}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={onSiguiente}
          disabled={pagina >= paginasTotal || loading}
        >
          Siguiente
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// BitacoraDetailModal - Modal de detalle de evento
// ============================================================================

export function BitacoraDetailModal({ open, onClose, evento }) {
  if (!evento) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Detalle del Evento
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-zinc-500">Fecha/Hora</label>
              <p className="font-medium">{formatearFecha(evento.timestamp)}</p>
            </div>
            <div>
              <label className="text-xs text-zinc-500">Usuario</label>
              <p className="font-medium">{evento.email || '-'}</p>
            </div>
            <div>
              <label className="text-xs text-zinc-500">Tipo</label>
              <div className="mt-1">{getTipoBadge(evento.tipo)}</div>
            </div>
            <div>
              <label className="text-xs text-zinc-500">Resultado</label>
              <div className="mt-1">{getResultadoBadge(evento.resultado)}</div>
            </div>
          </div>
          
          <div>
            <label className="text-xs text-zinc-500">Descripción</label>
            <p className="font-medium mt-1">{evento.descripcion || '-'}</p>
          </div>
          
          {evento.detalles && (
            <div>
              <label className="text-xs text-zinc-500">Detalles Adicionales</label>
              <pre className="mt-1 p-3 bg-zinc-50 rounded text-xs overflow-auto max-h-48">
                {typeof evento.detalles === 'string' 
                  ? evento.detalles 
                  : JSON.stringify(evento.detalles, null, 2)}
              </pre>
            </div>
          )}
          
          {evento.ip && (
            <div>
              <label className="text-xs text-zinc-500">IP Origen</label>
              <p className="font-mono text-sm mt-1">{evento.ip}</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
