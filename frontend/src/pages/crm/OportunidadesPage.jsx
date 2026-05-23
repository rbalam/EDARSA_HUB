import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow 
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, 
  DropdownMenuTrigger, DropdownMenuSeparator 
} from '@/components/ui/dropdown-menu';
import { 
  Briefcase, Search, Plus, Edit, DollarSign, Building2, 
  ChevronLeft, ChevronRight, Filter, MoreHorizontal, 
  Trophy, XCircle, ArrowRight
} from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';
import OportunidadForm from './OportunidadForm';
import CerrarOportunidadModal from './CerrarOportunidadModal';

const EMPRESA_ID = '00000000-0000-0000-0000-000000000001';

export default function OportunidadesPage() {
  const [oportunidades, setOportunidades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingOportunidad, setEditingOportunidad] = useState(null);
  const [closingOportunidad, setClosingOportunidad] = useState(null);

  useEffect(() => {
    loadOportunidades();
  }, [pagination.page]);

  const loadOportunidades = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        empresa_id: EMPRESA_ID,
        page: pagination.page,
        page_size: 10
      });
      if (search) params.append('busqueda', search);
      
      const response = await api.get(`/crm/native/oportunidades?${params}`);
      setOportunidades(response.data.items || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        totalPages: response.data.total_pages
      }));
    } catch (err) {
      console.error('Error loading oportunidades:', err);
      toast.error('Error al cargar oportunidades');
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (amount) => {
    return new Intl.NumberFormat('es-MX', { 
      style: 'currency', 
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingOportunidad(null);
  };

  const handleFormSaved = () => {
    handleFormClose();
    loadOportunidades();
  };

  const handleCloseModal = () => {
    setClosingOportunidad(null);
  };

  const handleClosed = () => {
    handleCloseModal();
    loadOportunidades();
  };

  const getEtapaBadge = (opp) => {
    const color = opp.etapa_color || '#6B7280';
    return (
      <Badge 
        variant="outline" 
        style={{ borderColor: color, backgroundColor: `${color}15`, color: color }}
      >
        {opp.etapa_nombre || 'Sin etapa'}
      </Badge>
    );
  };

  const getStatusBadge = (opp) => {
    const statusColors = {
      'Abierta': 'bg-blue-100 text-blue-800',
      'Ganada': 'bg-green-100 text-green-800',
      'Perdida': 'bg-red-100 text-red-800',
      'Pausada': 'bg-yellow-100 text-yellow-800',
    };
    const className = statusColors[opp.estatus_nombre] || 'bg-gray-100 text-gray-800';
    return (
      <Badge className={className}>
        {opp.estatus_nombre || 'Sin estatus'}
      </Badge>
    );
  };

  const getProbabilidadBar = (prob) => {
    const color = prob >= 70 ? '#22C55E' : prob >= 40 ? '#F59E0B' : '#6B7280';
    return (
      <div className="flex items-center gap-2">
        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full rounded-full transition-all"
            style={{ width: `${prob}%`, backgroundColor: color }}
          ></div>
        </div>
        <span className="text-xs font-medium" style={{ color }}>{prob}%</span>
      </div>
    );
  };

  const canClose = (opp) => {
    return opp.estatus_nombre === 'Abierta';
  };

  return (
    <div className="space-y-6" data-testid="oportunidades-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Briefcase className="h-6 w-6 text-purple-600" />
            Oportunidades
          </h1>
          <p className="text-gray-500">Gestión del pipeline de ventas</p>
        </div>
        <Button onClick={() => setShowForm(true)} data-testid="new-oportunidad-btn">
          <Plus className="h-4 w-4 mr-2" />
          Nueva Oportunidad
        </Button>
      </div>

      {/* Búsqueda */}
      <Card>
        <CardContent className="pt-4">
          <form onSubmit={(e) => { e.preventDefault(); loadOportunidades(); }} className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Buscar por nombre o folio..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button type="submit" variant="secondary">
              <Filter className="h-4 w-4 mr-2" />
              Filtrar
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Tabla */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Folio</TableHead>
                <TableHead>Oportunidad</TableHead>
                <TableHead>Cuenta</TableHead>
                <TableHead>Monto</TableHead>
                <TableHead>Etapa</TableHead>
                <TableHead>Probabilidad</TableHead>
                <TableHead>Estatus</TableHead>
                <TableHead>Fecha Est.</TableHead>
                <TableHead className="w-20"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
                    </div>
                  </TableCell>
                </TableRow>
              ) : oportunidades.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-gray-500">
                    No se encontraron oportunidades
                  </TableCell>
                </TableRow>
              ) : (
                oportunidades.map((opp) => (
                  <TableRow key={opp.oportunidad_id} data-testid={`opp-row-${opp.oportunidad_id}`}>
                    <TableCell className="font-mono text-xs">
                      {opp.folio_oportunidad}
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{opp.nombre_oportunidad}</p>
                        {opp.descripcion_oportunidad && (
                          <p className="text-xs text-gray-500 truncate max-w-xs">
                            {opp.descripcion_oportunidad}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {opp.cuenta_nombre ? (
                        <div className="flex items-center gap-1">
                          <Building2 className="h-4 w-4 text-gray-400" />
                          <span>{opp.cuenta_nombre}</span>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 font-semibold text-green-700">
                        <DollarSign className="h-4 w-4" />
                        {formatMoney(opp.monto_estimado)}
                      </div>
                    </TableCell>
                    <TableCell>{getEtapaBadge(opp)}</TableCell>
                    <TableCell>{getProbabilidadBar(opp.probabilidad_actual)}</TableCell>
                    <TableCell>{getStatusBadge(opp)}</TableCell>
                    <TableCell className="text-sm">
                      {opp.fecha_estimada_cierre 
                        ? new Date(opp.fecha_estimada_cierre).toLocaleDateString('es-MX')
                        : '-'
                      }
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => setEditingOportunidad(opp)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Editar
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => window.location.href = '/crm/pipeline'}>
                            <ArrowRight className="h-4 w-4 mr-2" />
                            Ver en Pipeline
                          </DropdownMenuItem>
                          {canClose(opp) && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem 
                                onClick={() => setClosingOportunidad(opp)}
                                className="text-green-600"
                              >
                                <Trophy className="h-4 w-4 mr-2" />
                                Cerrar como Ganada
                              </DropdownMenuItem>
                              <DropdownMenuItem 
                                onClick={() => setClosingOportunidad(opp)}
                                className="text-red-600"
                              >
                                <XCircle className="h-4 w-4 mr-2" />
                                Cerrar como Perdida
                              </DropdownMenuItem>
                            </>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          {/* Paginación */}
          {pagination.totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t">
              <p className="text-sm text-gray-500">
                Mostrando {oportunidades.length} de {pagination.total} oportunidades
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.page <= 1}
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm">
                  Página {pagination.page} de {pagination.totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.page >= pagination.totalPages}
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modales */}
      {(showForm || editingOportunidad) && (
        <OportunidadForm 
          oportunidad={editingOportunidad} 
          onClose={handleFormClose} 
          onSaved={handleFormSaved} 
        />
      )}

      {closingOportunidad && (
        <CerrarOportunidadModal
          oportunidad={closingOportunidad}
          onClose={handleCloseModal}
          onClosed={handleClosed}
        />
      )}
    </div>
  );
}
