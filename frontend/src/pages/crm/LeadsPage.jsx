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
  UserPlus, Search, Plus, Edit, Phone, Mail, Building2, 
  ChevronLeft, ChevronRight, Filter, MoreHorizontal, ArrowRight, Trash2, XCircle
} from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';
import LeadForm from './LeadForm';
import ConvertirLeadModal from './ConvertirLeadModal';

const EMPRESA_ID = '00000000-0000-0000-0000-000000000001';

export default function LeadsPage() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingLead, setEditingLead] = useState(null);
  const [convertingLead, setConvertingLead] = useState(null);

  useEffect(() => {
    loadLeads();
  }, [pagination.page]);

  const loadLeads = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        empresa_id: EMPRESA_ID,
        page: pagination.page,
        page_size: 10,
        source: 'vtiger'  // Leer desde Vtiger sincronizado
      });
      if (search) params.append('busqueda', search);
      
      const response = await api.get(`/crm/native/leads?${params}`);
      setLeads(response.data.items || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        totalPages: response.data.total_pages
      }));
    } catch (err) {
      console.error('Error loading leads:', err);
      toast.error('Error al cargar leads');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPagination(prev => ({ ...prev, page: 1 }));
    loadLeads();
  };

  const handleDelete = async (lead) => {
    if (!window.confirm(`¿Eliminar lead ${lead.folio_lead}?`)) return;
    
    try {
      await api.delete(`/crm/native/leads/${lead.lead_id}`);
      toast.success('Lead eliminado');
      loadLeads();
    } catch (err) {
      toast.error('Error al eliminar');
    }
  };

  const handleDescalificar = async (lead) => {
    if (!window.confirm(`¿Descalificar lead ${lead.folio_lead}?`)) return;
    
    try {
      await api.post(`/crm/native/leads/${lead.lead_id}/descalificar`, {
        motivo_descalificacion_id: 1,
        notas: 'Descalificado manualmente'
      });
      toast.success('Lead descalificado');
      loadLeads();
    } catch (err) {
      toast.error('Error al descalificar');
    }
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingLead(null);
  };

  const handleFormSaved = () => {
    handleFormClose();
    loadLeads();
  };

  const handleConvertClose = () => {
    setConvertingLead(null);
  };

  const handleConverted = () => {
    handleConvertClose();
    loadLeads();
    toast.success('Lead convertido exitosamente');
  };

  const getStatusBadge = (lead) => {
    const color = lead.estatus_color || '#6B7280';
    return (
      <Badge 
        variant="outline" 
        style={{ borderColor: color, color: color }}
      >
        {lead.estatus_nombre || 'Sin estatus'}
      </Badge>
    );
  };

  const getPrioridadBadge = (lead) => {
    const colors = {
      'Alta': 'bg-red-100 text-red-800',
      'Media': 'bg-yellow-100 text-yellow-800',
      'Baja': 'bg-green-100 text-green-800',
      'Crítica': 'bg-purple-100 text-purple-800'
    };
    const className = colors[lead.prioridad_nombre] || 'bg-gray-100 text-gray-800';
    return lead.prioridad_nombre ? (
      <Badge className={className}>{lead.prioridad_nombre}</Badge>
    ) : null;
  };

  const canConvert = (lead) => {
    return !lead.convertido_a_cuenta && !lead.descalificado && 
           lead.estatus_nombre !== 'Convertido' && lead.estatus_nombre !== 'Descalificado';
  };

  return (
    <div className="space-y-6" data-testid="leads-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <UserPlus className="h-6 w-6 text-blue-600" />
            Leads
          </h1>
          <p className="text-gray-500">Gestión de prospectos y oportunidades iniciales</p>
        </div>
        <Button onClick={() => setShowForm(true)} data-testid="new-lead-btn">
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Lead
        </Button>
      </div>

      {/* Búsqueda y Filtros */}
      <Card>
        <CardContent className="pt-4">
          <form onSubmit={handleSearch} className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Buscar por nombre, empresa o email..."
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

      {/* Tabla de Leads */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Folio</TableHead>
                <TableHead>Contacto</TableHead>
                <TableHead>Empresa</TableHead>
                <TableHead>Contacto</TableHead>
                <TableHead>Origen</TableHead>
                <TableHead>Estatus</TableHead>
                <TableHead>Prioridad</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead className="w-20"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    </div>
                  </TableCell>
                </TableRow>
              ) : leads.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-gray-500">
                    No se encontraron leads
                  </TableCell>
                </TableRow>
              ) : (
                leads.map((lead) => (
                  <TableRow key={lead.lead_id} data-testid={`lead-row-${lead.lead_id}`}>
                    <TableCell className="font-mono text-xs">
                      {lead.folio_lead}
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">
                          {lead.nombre_contacto} {lead.apellido_paterno}
                        </p>
                        {lead.puesto && (
                          <p className="text-xs text-gray-500">{lead.puesto}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Building2 className="h-4 w-4 text-gray-400" />
                        <span>{lead.nombre_empresa || '-'}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        {lead.email && (
                          <div className="flex items-center gap-1 text-xs">
                            <Mail className="h-3 w-3 text-gray-400" />
                            <span>{lead.email}</span>
                          </div>
                        )}
                        {lead.telefono && (
                          <div className="flex items-center gap-1 text-xs">
                            <Phone className="h-3 w-3 text-gray-400" />
                            <span>{lead.telefono}</span>
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{lead.origen_nombre || '-'}</span>
                    </TableCell>
                    <TableCell>{getStatusBadge(lead)}</TableCell>
                    <TableCell>{getPrioridadBadge(lead)}</TableCell>
                    <TableCell className="text-xs text-gray-500">
                      {new Date(lead.created_at).toLocaleDateString('es-MX')}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => setEditingLead(lead)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Editar
                          </DropdownMenuItem>
                          {canConvert(lead) && (
                            <DropdownMenuItem onClick={() => setConvertingLead(lead)}>
                              <ArrowRight className="h-4 w-4 mr-2" />
                              Convertir
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          {canConvert(lead) && (
                            <DropdownMenuItem 
                              onClick={() => handleDescalificar(lead)}
                              className="text-amber-600"
                            >
                              <XCircle className="h-4 w-4 mr-2" />
                              Descalificar
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem 
                            onClick={() => handleDelete(lead)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Eliminar
                          </DropdownMenuItem>
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
                Mostrando {leads.length} de {pagination.total} leads
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
      {(showForm || editingLead) && (
        <LeadForm 
          lead={editingLead} 
          onClose={handleFormClose} 
          onSaved={handleFormSaved} 
        />
      )}

      {convertingLead && (
        <ConvertirLeadModal
          lead={convertingLead}
          onClose={handleConvertClose}
          onConverted={handleConverted}
        />
      )}
    </div>
  );
}
