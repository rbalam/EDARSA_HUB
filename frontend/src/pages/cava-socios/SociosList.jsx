/**
 * EDARSA HUB - Lista de Socios de Cava
 * =====================================
 * Página de gestión de socios con búsqueda, filtros, paginación
 * y promoción directa desde el catálogo canónico de clientes.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Users, Plus, Search, Filter, ChevronLeft, ChevronRight,
  Eye, Edit, RefreshCw, Wine, Mail, Phone, AlertCircle,
  UserCheck, TrendingDown, Layers, CheckCircle2
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  CorporateFiltersProvider,
  CorporateFilterSelect,
  useCorporateFilters,
} from '../../filters';
import { useAccessContext } from '../../hooks/useAccessContext';

const PAGE_SIZE = 15;

const TIPOS_MEMBRESIA = [
  { value: 'ESTANDAR', label: 'Estándar (12 botellas)' },
  { value: 'PREMIUM', label: 'Premium (24 botellas)' },
  { value: 'VIP', label: 'VIP (36 botellas)' },
  { value: 'BLACK', label: 'Black / Ilimitada' }
];

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

  // Modal Promover Cliente Canónico
  const [showPromoverDialog, setShowPromoverDialog] = useState(false);
  const [searchCanonico, setSearchCanonico] = useState('');
  const [clientesCanonicos, setClientesCanonicos] = useState([]);
  const [loadingCanonicos, setLoadingCanonicos] = useState(false);
  const [selectedCliente, setSelectedCliente] = useState(null);
  const [promocionForm, setPromocionForm] = useState({
    tipo_membresia: 'ESTANDAR',
    maximo_botellas: 12,
    observaciones: 'Promovido desde catálogo maestro canónico'
  });
  const [savingPromocion, setSavingPromocion] = useState(false);
  const [promocionSuccess, setPromocionSuccess] = useState(null);

  const unidadNegocioPk = selected?.unidades_negocio || context?.unidad_activa || '';

  const fetchSocios = useCallback(async () => {
    if (filtersLoading || contextLoading) return;
    if (!unidadNegocioPk) {
      setSocios([]);
      setTotal(0);
      setError('Selecciona una unidad de negocio autorizada para consultar Cavas.');
      setLoading(false);
      return;
    }

    setLoading(true);
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

  const handleBuscarCanonicos = async () => {
    if (!unidadNegocioPk) return;
    setLoadingCanonicos(true);
    try {
      const params = new URLSearchParams({
        unidad_negocio_pk: unidadNegocioPk,
        search: searchCanonico.trim(),
        limit: 25
      });
      const response = await api.get(`/cava-socios/clientes-canonicos?${params}`);
      setClientesCanonicos(response.data?.clientes || []);
    } catch (err) {
      console.error('Error buscando clientes canónicos:', err);
    } finally {
      setLoadingCanonicos(false);
    }
  };

  const handleSelectCliente = (cliente) => {
    setSelectedCliente(cliente);
    setPromocionForm({
      tipo_membresia: 'ESTANDAR',
      maximo_botellas: 12,
      observaciones: `Promovido desde catálogo canónico (Código: ${cliente.codigo_cliente || cliente.cliente_id})`
    });
  };

  const handleConfirmarPromocion = async () => {
    if (!selectedCliente) return;
    setSavingPromocion(true);
    setPromocionSuccess(null);
    try {
      const payload = {
        cliente_id: String(selectedCliente.cliente_id),
        nombre_completo: selectedCliente.nombre_completo,
        email: selectedCliente.email,
        telefono: selectedCliente.telefono,
        tipo_membresia: promocionForm.tipo_membresia,
        maximo_botellas: parseInt(promocionForm.maximo_botellas) || 12,
        observaciones: promocionForm.observaciones
      };

      const resp = await api.post(`/cava-socios/socios/promover-cliente?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`, payload);
      setPromocionSuccess(resp.data);
      fetchSocios();
      setTimeout(() => {
        setShowPromoverDialog(false);
        setSelectedCliente(null);
        setPromocionSuccess(null);
      }, 1500);
    } catch (err) {
      console.error('Error promoviendo cliente:', err);
      alert(err?.response?.data?.detail || 'Error promoviendo cliente');
    } finally {
      setSavingPromocion(false);
    }
  };

  const getEstatusBadge = (estatus) => {
    const styles = {
      'ACTIVO': 'bg-green-100 text-green-800',
      'INACTIVO': 'bg-zinc-100 text-zinc-800',
      'VENCIDO': 'bg-red-100 text-red-800',
      'PENDIENTE': 'bg-amber-100 text-amber-800',
      'SUSPENDIDO': 'bg-orange-100 text-orange-800'
    };
    return (
      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${styles[estatus] || 'bg-zinc-100 text-zinc-800'}`}>
        {estatus}
      </span>
    );
  };

  const getTipoMembresiaBadge = (tipo) => {
    const styles = {
      'ESTANDAR': 'bg-blue-50 text-blue-700 border border-blue-200',
      'PREMIUM': 'bg-purple-50 text-purple-700 border border-purple-200',
      'VIP': 'bg-amber-50 text-amber-800 border border-amber-200',
      'BLACK': 'bg-zinc-900 text-white'
    };
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-bold ${styles[tipo] || 'bg-zinc-100 text-zinc-700'}`}>
        {tipo}
      </span>
    );
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
      {/* Shared Header with Tabs */}
      <CavaNavHeader
        title="Directorio de Socios de Cava"
        subtitle="Membresías activas, vinculación canónica de clientes y control de casilleros"
        onRefresh={fetchSocios}
        loading={loading}
      />

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
                placeholder="Buscar por nombre, número de socio o email..."
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
                    <TableHead>Identidad BOS</TableHead>
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
                      <TableCell>
                        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${socio.persona_id ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}`}>
                          {socio.persona_id ? 'Vinculada' : 'Pendiente'}
                        </span>
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
                            title="Ver Cava y Botellas"
                            onClick={() => navigate(`/cava-socios/socios/${socio.socio_id}`)}
                            data-testid={`ver-socio-${socio.socio_id}`}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            title="Editar Socio"
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
              <div className="flex justify-center gap-3 mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowPromoverDialog(true);
                    handleBuscarCanonicos();
                  }}
                >
                  <UserCheck className="h-4 w-4 mr-2 text-indigo-600" />
                  Promover desde Clientes Canónicos
                </Button>
                <Button
                  size="sm"
                  onClick={() => navigate('/cava-socios/socios/nuevo')}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Registrar Nuevo Socio
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Promover Cliente Canónico */}
      <Dialog open={showPromoverDialog} onOpenChange={setShowPromoverDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserCheck className="h-5 w-5 text-indigo-600" />
              Promover Cliente Canónico a Socio de Cava
            </DialogTitle>
            <DialogDescription>
              Selecciona un cliente del catálogo maestro corporativo para afiliarlo a Cava de Socios
            </DialogDescription>
          </DialogHeader>

          {promocionSuccess ? (
            <div className="p-6 text-center space-y-3 bg-green-50 rounded-lg text-green-800">
              <CheckCircle2 className="h-10 w-10 text-green-600 mx-auto" />
              <p className="font-bold text-lg">{promocionSuccess.mensaje}</p>
              <p className="text-sm">Número de Socio Asignado: #{promocionSuccess.numero_socio}</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Buscador de clientes canónicos */}
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Buscar por razón social, nombre comercial o RFC..."
                    className="pl-9"
                    value={searchCanonico}
                    onChange={(e) => setSearchCanonico(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleBuscarCanonicos()}
                  />
                </div>
                <Button onClick={handleBuscarCanonicos} disabled={loadingCanonicos}>
                  {loadingCanonicos ? <RefreshCw className="h-4 w-4 animate-spin" /> : 'Buscar'}
                </Button>
              </div>

              {/* Lista de clientes canónicos */}
              <div className="border rounded-lg max-h-48 overflow-y-auto">
                {loadingCanonicos ? (
                  <div className="py-8 text-center text-muted-foreground">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                    Buscando en catálogo maestro...
                  </div>
                ) : clientesCanonicos.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Cliente / Razón Social</TableHead>
                        <TableHead>RFC</TableHead>
                        <TableHead>Contacto</TableHead>
                        <TableHead className="text-right">Acción</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {clientesCanonicos.map((cli) => {
                        const isSelected = selectedCliente?.cliente_id === cli.cliente_id;
                        return (
                          <TableRow key={cli.cliente_id} className={isSelected ? 'bg-indigo-50' : ''}>
                            <TableCell>
                              <div className="font-medium text-sm">{cli.nombre_completo}</div>
                              <div className="text-xs text-muted-foreground">{cli.codigo_cliente || cli.cliente_id}</div>
                            </TableCell>
                            <TableCell className="text-xs font-mono">{cli.rfc || '-'}</TableCell>
                            <TableCell className="text-xs">
                              <div>{cli.email || '-'}</div>
                              <div>{cli.telefono || ''}</div>
                            </TableCell>
                            <TableCell className="text-right">
                              <Button
                                size="sm"
                                variant={isSelected ? 'default' : 'outline'}
                                onClick={() => handleSelectCliente(cli)}
                              >
                                {isSelected ? 'Seleccionado' : 'Seleccionar'}
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="py-8 text-center text-xs text-muted-foreground">
                    No se encontraron clientes con el criterio ingresado. Realiza una búsqueda.
                  </div>
                )}
              </div>

              {/* Formulario de Membresía cuando hay cliente seleccionado */}
              {selectedCliente && (
                <div className="p-4 bg-zinc-50 rounded-lg space-y-4 border border-indigo-100">
                  <div className="text-sm font-semibold text-indigo-900">
                    Configurar Membresía para: {selectedCliente.nombre_completo}
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Tipo de Membresía</Label>
                      <Select
                        value={promocionForm.tipo_membresia}
                        onValueChange={(v) => {
                          const maxMap = { ESTANDAR: 12, PREMIUM: 24, VIP: 36, BLACK: 50 };
                          setPromocionForm(f => ({
                            ...f,
                            tipo_membresia: v,
                            maximo_botellas: maxMap[v] || 12
                          }));
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {TIPOS_MEMBRESIA.map(m => (
                            <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Capacidad Máxima (Botellas)</Label>
                      <Input
                        type="number"
                        value={promocionForm.maximo_botellas}
                        onChange={(e) => setPromocionForm(f => ({...f, maximo_botellas: parseInt(e.target.value) || 12}))}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Observaciones</Label>
                    <Input
                      value={promocionForm.observaciones}
                      onChange={(e) => setPromocionForm(f => ({...f, observaciones: e.target.value}))}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPromoverDialog(false)}>
              Cerrar
            </Button>
            {selectedCliente && !promocionSuccess && (
              <Button onClick={handleConfirmarPromocion} disabled={savingPromocion}>
                {savingPromocion ? 'Afiliando...' : 'Afiliar como Socio de Cava'}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
