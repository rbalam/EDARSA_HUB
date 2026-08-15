/**
 * EDARSA HUB - Lista de Socios de Cava
 * =====================================
 * Página de gestión de socios con búsqueda, filtros y paginación.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Users, Plus, Search, Filter, ChevronLeft, ChevronRight,
  Eye, Edit, RefreshCw, Wine, Mail, Phone, AlertCircle
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  CorporateFiltersProvider,
  CorporateFilterSelect,
  useCorporateFilters,
} from '../../filters';
import { useAccessContext } from '../../hooks/useAccessContext';


const PAGE_SIZE = 15;

function SociosListContent() {
  const navigate = useNavigate();
  const { selected, loading: filtersLoading } = useCorporateFilters();
  const { context, loading: contextLoading, error: contextError } = useAccessContext();
  const [socios, setSocios] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [estatusFilter, setEstatusFilter] = useState('todos');

  const unidadNegocioPk = selected?.unidades_negocio || context?.unidad_activa || '';
  const fetchSocios = useCallback(async () => {
    setLoading(true);
    if (filtersLoading || contextLoading) return;
    if (!unidadNegocioPk) {
      setSocios([]);
      setTotal(0);
      setError('Selecciona una unidad de negocio autorizada para consultar Cavas.');
      setLoading(false);
      return;
    }

    try {
      const params = new URLSearchParams({
        unidad_negocio_pk: unidadNegocioPk,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE
      });
      
      if (estatusFilter !== 'todos') {
        params.append('estatus', estatusFilter);
      }
      
      const response = await api.get(`/cava-socios/socios?${params}`);
      setSocios(response.data?.socios || []);
      setTotal(response.data?.total || 0);
      setError(null);
    } catch (err) {
      console.error('Error fetching socios:', err);
      setSocios([]);
      setTotal(0);
      setError(
        err?.response?.status === 403
          ? 'No tienes permiso para consultar Cavas en esta unidad.'
          : 'Error cargando lista de socios.'
      );
    } finally {
      setLoading(false);
    }
  }, [page, estatusFilter, unidadNegocioPk, filtersLoading, contextLoading]);

  useEffect(() => {
    fetchSocios();
  }, [fetchSocios]);

  const getEstatusColor = (estatus) => {
    const colors = {
      'ACTIVO': 'text-green-700 bg-green-100',
      'INACTIVO': 'text-gray-600 bg-gray-100',
      'VENCIDO': 'text-red-600 bg-red-100',
      'PENDIENTE': 'text-yellow-600 bg-yellow-100'
    };
    return colors[estatus] || 'text-gray-600 bg-gray-100';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  const filteredSocios = socios.filter(s => 
    s.nombre_completo?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.numero_socio?.includes(searchTerm) ||
    s.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="p-6 space-y-6" data-testid="socios-list-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="h-7 w-7 text-purple-600" />
            Socios de Cava
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Gestión completa de socios y membresías
          </p>
        </div>
        <div className="flex gap-2 items-end">
          <div className="min-w-[260px]">
            <CorporateFilterSelect
              filterKey="unidades_negocio"
              label="Unidad de negocio"
              placeholder="Selecciona una unidad"
            />
          </div>
          <Button variant="outline" size="sm" onClick={fetchSocios}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </Button>
          <Button size="sm" onClick={() => navigate('/cava-socios/socios/nuevo')}>
            <Plus className="h-4 w-4 mr-2" />
            Nuevo Socio
          </Button>
        </div>
      </div>

      {(error || contextError) && (
        <div className="p-4 rounded-lg bg-red-50 text-red-700 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          {error || contextError?.message || 'No se pudo resolver el contexto de acceso.'}
        </div>
      )}

      {/* Filtros */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por nombre, número o email..."
                className="pl-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                data-testid="search-input"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={estatusFilter} onValueChange={setEstatusFilter}>
                <SelectTrigger className="w-[150px]" data-testid="estatus-filter">
                  <SelectValue placeholder="Estatus" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  <SelectItem value="ACTIVO">Activos</SelectItem>
                  <SelectItem value="INACTIVO">Inactivos</SelectItem>
                  <SelectItem value="VENCIDO">Vencidos</SelectItem>
                  <SelectItem value="PENDIENTE">Pendientes</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabla de Socios */}
      <Card>
        <CardHeader>
          <CardTitle>
            {total} socios registrados
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading || filtersLoading || contextLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
            </div>
          ) : filteredSocios.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Socio</TableHead>
                    <TableHead>Contacto</TableHead>
                    <TableHead>Membresía</TableHead>
                    <TableHead className="text-center">Botellas</TableHead>
                    <TableHead>Vencimiento</TableHead>
                    <TableHead>Estatus</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSocios.map((socio) => (
                    <TableRow key={socio.socio_id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{socio.nombre_completo}</div>
                          <div className="text-xs text-muted-foreground">
                            #{socio.numero_socio}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          {socio.email && (
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Mail className="h-3 w-3" />
                              {socio.email}
                            </div>
                          )}
                          {socio.telefono && (
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Phone className="h-3 w-3" />
                              {socio.telefono}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm font-medium">{socio.tipo_membresia}</span>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
                          <Wine className="h-3 w-3" />
                          {socio.botellas_en_cava || 0} / {socio.maximo_botellas || 12}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">{formatDate(socio.fecha_vencimiento)}</span>
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEstatusColor(socio.estatus)}`}>
                          {socio.estatus}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/cava-socios/socios/${socio.socio_id}`)}
                            data-testid={`ver-socio-${socio.socio_id}`}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/cava-socios/socios/${socio.socio_id}/editar`)}
                            data-testid={`editar-socio-${socio.socio_id}`}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Paginación */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <div className="text-sm text-muted-foreground">
                  Mostrando {page * PAGE_SIZE + 1} - {Math.min((page + 1) * PAGE_SIZE, total)} de {total}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 0}
                    onClick={() => setPage(p => p - 1)}
                    data-testid="prev-page"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= totalPages - 1}
                    onClick={() => setPage(p => p + 1)}
                    data-testid="next-page"
                  >
                    Siguiente
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Users className="h-12 w-12 mx-auto mb-4 opacity-20" />
              <p>No se encontraron socios</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-4"
                onClick={() => navigate('/cava-socios/socios/nuevo')}
              >
                <Plus className="h-4 w-4 mr-2" />
                Registrar Nuevo Socio
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function SociosList() {
  return (
    <CorporateFiltersProvider scope="cava_socios">
      <SociosListContent />
    </CorporateFiltersProvider>
  );
}
