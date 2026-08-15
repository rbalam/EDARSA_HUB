/**
 * EDARSA HUB - Cava de Socios Dashboard
 * =====================================
 * Panel principal del módulo Cava de Socios.
 * Muestra KPIs, socios activos, botellas en resguardo y actividad reciente.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Wine, Users, Package, TrendingUp, AlertCircle,
  RefreshCw, Plus, Eye, Search, Clock, TrendingDown, Layers
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  CorporateFiltersProvider,
  CorporateFilterSelect,
  useCorporateFilters,
} from '../../filters';
import { useAccessContext } from '../../hooks/useAccessContext';


function CavaSociosDashboardContent() {
  const navigate = useNavigate();
  const { selected, loading: filtersLoading } = useCorporateFilters();
  const { context, loading: contextLoading, error: contextError } = useAccessContext();
  const [dashboard, setDashboard] = useState(null);
  const [socios, setSocios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const unidadNegocioPk = selected?.unidades_negocio || context?.unidad_activa || '';

  const fetchData = async () => {
    if (!unidadNegocioPk) {
      setDashboard(null);
      setSocios([]);
      setError('Selecciona una unidad de negocio autorizada para consultar Cavas.');
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const scope = `unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`;
      const [dashboardRes, sociosRes] = await Promise.all([
        api.get(`/cava-socios/dashboard?${scope}`),
        api.get(`/cava-socios/socios?${scope}&limit=10`)
      ]);

      setDashboard(dashboardRes.data);
      setSocios(sociosRes.data?.socios || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching cava data:', err);
      const status = err?.response?.status;
      setDashboard(null);
      setSocios([]);
      setError(
        status === 403
          ? 'No tienes permiso para consultar Cavas en esta unidad.'
          : 'Error cargando datos de Cavas.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (filtersLoading || contextLoading) return;
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadNegocioPk, filtersLoading, contextLoading]);

  const getEstatusColor = (estatus) => {
    const colors = {
      'ACTIVO': 'text-green-700 bg-green-100',
      'INACTIVO': 'text-gray-600 bg-gray-100',
      'VENCIDO': 'text-red-600 bg-red-100',
      'PENDIENTE': 'text-yellow-600 bg-yellow-100',
      'SUSPENDIDO': 'text-orange-600 bg-orange-100'
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

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(amount || 0);
  };

  if (loading || filtersLoading || contextLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="cava-socios-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Wine className="h-7 w-7 text-purple-600" />
            Cava de Socios
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Gestión de botellas en resguardo para clientes VIP
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
          <Button variant="outline" size="sm" onClick={() => navigate('/cava-socios/inventario')}>
            <Wine className="h-4 w-4 mr-2" />
            Inventario
          </Button>
          <Button variant="outline" size="sm" onClick={() => navigate('/cava-socios/consumos')}>
            <TrendingDown className="h-4 w-4 mr-2" />
            Consumos
          </Button>
          <Button variant="outline" size="sm" onClick={fetchData}>
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

      {/* KPIs Principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Users className="h-4 w-4" />
              Socios Activos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">
              {dashboard?.socios?.activos || 0}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              de {dashboard?.socios?.total || 0} totales
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Wine className="h-4 w-4" />
              Botellas en Resguardo
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {dashboard?.botellas?.en_cava || 0}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {dashboard?.botellas?.consumidas || 0} consumidas
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Valor Total en Cava
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-600">
              {formatCurrency(dashboard?.botellas?.valor_custodia)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Valor declarado de botellas
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Pendiente de Cobro
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">
              {formatCurrency(dashboard?.financiero?.pendiente_cobro)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {dashboard?.financiero?.cargos_pendientes || 0} cargos pendientes
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Membresías por vencer (solo si hay socios vencidos) */}
      {dashboard?.socios?.vencidos > 0 && (
        <Card className="border-orange-200 bg-orange-50/50">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-orange-700">
              <AlertCircle className="h-5 w-5" />
              Membresías Vencidas ({dashboard.socios.vencidos})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-orange-600">
              Hay {dashboard.socios.vencidos} socio(s) con membresía vencida. 
              Por favor revise la lista de socios para más detalles.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Lista de Socios */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Socios Recientes
              </CardTitle>
              <CardDescription>Últimos socios registrados en la cava</CardDescription>
            </div>
            <div className="flex gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar socio..."
                  className="pl-9 w-[200px]"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  data-testid="search-socio-input"
                />
              </div>
              <Button variant="outline" size="sm" asChild>
                <Link to="/cava-socios/socios">
                  Ver Todos
                </Link>
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {socios.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Socio</TableHead>
                  <TableHead>Membresía</TableHead>
                  <TableHead className="text-center">Botellas</TableHead>
                  <TableHead>Estatus</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {socios
                  .filter(s => 
                    s.nombre_completo?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    s.numero_socio?.includes(searchTerm)
                  )
                  .map((socio) => (
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
                      <span className="text-sm">{socio.tipo_membresia}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
                        <Wine className="h-3 w-3" />
                        {socio.botellas_en_cava ?? 0} / {socio.maximo_botellas ?? '—'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEstatusColor(socio.estatus)}`}>
                        {socio.estatus}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/cava-socios/socios/${socio.socio_id}`)}
                        data-testid={`ver-socio-${socio.socio_id}`}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Wine className="h-12 w-12 mx-auto mb-4 opacity-20" />
              <p>{error ? 'Datos no disponibles' : 'No hay socios registrados aún'}</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-4"
                onClick={() => navigate('/cava-socios/socios/nuevo')}
              >
                <Plus className="h-4 w-4 mr-2" />
                Registrar Primer Socio
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link to="/cava-socios/socios">
          <Card className="hover:bg-zinc-50 transition-colors cursor-pointer">
            <CardContent className="p-4 flex items-center gap-3">
              <Users className="h-8 w-8 text-purple-500" />
              <div>
                <div className="font-medium">Socios</div>
                <div className="text-xs text-muted-foreground">Gestionar</div>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}

export default function CavaSociosDashboard() {
  return (
    <CorporateFiltersProvider scope="cava_socios">
      <CavaSociosDashboardContent />
    </CorporateFiltersProvider>
  );
}
