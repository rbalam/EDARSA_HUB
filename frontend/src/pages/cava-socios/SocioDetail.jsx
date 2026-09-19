/**
 * EDARSA HUB - Detalle de Socio
 * ==============================
 * Página con información completa del socio y sus botellas en cava.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Users, Wine, ArrowLeft, Edit, Plus, RefreshCw,
  AlertCircle, Mail, Phone, Calendar, Package, Trash2,
  FileDown, FileText, Receipt, Send, MessageSquare, Loader2,
  QrCode, Printer
} from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '@/lib/api';
import { toast } from 'sonner';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  CorporateFiltersProvider,
  CorporateFilterSelect,
  useCorporateFilters,
} from '../../filters';
import { useAccessContext } from '../../hooks/useAccessContext';
import PersonaLinkCard from './PersonaLinkCard';



const TIPOS_BEBIDA = [
  { value: 'VINO_TINTO', label: 'Vino Tinto' },
  { value: 'VINO_BLANCO', label: 'Vino Blanco' },
  { value: 'VINO_ROSADO', label: 'Vino Rosado' },
  { value: 'CHAMPAGNE', label: 'Champagne/Espumoso' },
  { value: 'WHISKY', label: 'Whisky' },
  { value: 'TEQUILA', label: 'Tequila' },
  { value: 'MEZCAL', label: 'Mezcal' },
  { value: 'COGNAC', label: 'Cognac/Brandy' },
  { value: 'VODKA', label: 'Vodka' },
  { value: 'RON', label: 'Ron' },
  { value: 'GIN', label: 'Ginebra' },
  { value: 'OTRO', label: 'Otro' }
];

function SocioDetailContent() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { selected, loading: filtersLoading } = useCorporateFilters();
  const { context, loading: contextLoading, error: contextError } = useAccessContext();
  const unidadNegocioPk = selected?.unidades_negocio || context?.unidad_activa || '';

  const [socio, setSocio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showBotellaDialog, setShowBotellaDialog] = useState(false);
  const [showConsumoDialog, setShowConsumoDialog] = useState(false);
  const [showEtiquetaDialog, setShowEtiquetaDialog] = useState(false);
  const [selectedEtiqueta, setSelectedEtiqueta] = useState(null);
  const [selectedBotella, setSelectedBotella] = useState(null);
  const [savingBotella, setSavingBotella] = useState(false);
  const [savingConsumo, setSavingConsumo] = useState(false);

  const [botellaForm, setBotellaForm] = useState({
    producto_nombre: '',
    marca: '',
    tipo_bebida: 'VINO_TINTO',
    añada: '',
    capacidad: 750,
    ubicacion: '',
    valor_declarado: 0,
    observaciones: ''
  });

  const [consumoForm, setConsumoForm] = useState({
    porcentaje_consumido: 100,
    motivo: '',
    generar_cargo_descorche: true,
    monto_descorche: 350,
    observaciones: ''
  });

  const [enviandoReporte, setEnviandoReporte] = useState(false);

  const fetchSocio = useCallback(async () => {
    if (filtersLoading || contextLoading) return;
    if (!unidadNegocioPk) {
      setSocio(null);
      setError('Selecciona una unidad de negocio autorizada para consultar Cavas.');
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const response = await api.get(`/cava-socios/socios/${id}?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`);
      setSocio(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching socio:', err);
      setError(
        err?.response?.status === 403
          ? 'No tienes permiso para consultar Cavas en esta unidad.'
          : 'Error cargando datos del socio'
      );
    } finally {
      setLoading(false);
    }
  }, [id, unidadNegocioPk, filtersLoading, contextLoading]);

  useEffect(() => {
    fetchSocio();
  }, [fetchSocio]);

  const getEstatusColor = (estatus) => {
    const colors = {
      'ACTIVO': 'text-green-700 bg-green-100',
      'EN_CAVA': 'text-blue-700 bg-blue-100',
      'CONSUMIDA': 'text-gray-600 bg-gray-100',
      'PARCIAL': 'text-orange-600 bg-orange-100'
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

  const handleAddBotella = async () => {
    if (!botellaForm.producto_nombre.trim()) {
      toast.error('El nombre del producto es requerido');
      return;
    }
    if (!unidadNegocioPk) {
      toast.error('Selecciona una unidad de negocio autorizada.');
      return;
    }

    setSavingBotella(true);
    try {
      await api.post(`/cava-socios/socios/${id}/botellas?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`, botellaForm);
      toast.success('Botella registrada correctamente');
      setShowBotellaDialog(false);
      setBotellaForm({
        producto_nombre: '',
        marca: '',
        tipo_bebida: 'VINO_TINTO',
        añada: '',
        capacidad: 750,
        ubicacion: '',
        valor_declarado: 0,
        observaciones: ''
      });
      fetchSocio();
    } catch (err) {
      console.error('Error adding botella:', err);
      toast.error(err.response?.data?.detail || 'Error registrando botella');
    } finally {
      setSavingBotella(false);
    }
  };

  const handleConsumo = async () => {
    if (!selectedBotella) return;
    if (!unidadNegocioPk) {
      toast.error('Selecciona una unidad de negocio autorizada.');
      return;
    }

    setSavingConsumo(true);
    try {
      await api.post(`/cava-socios/botellas/${selectedBotella.botella_id}/consumo?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`, consumoForm);
      toast.success('Consumo registrado correctamente');
      setShowConsumoDialog(false);
      setSelectedBotella(null);
      setConsumoForm({
        porcentaje_consumido: 100,
        motivo: '',
        generar_cargo_descorche: true,
        monto_descorche: 350,
        observaciones: ''
      });
      fetchSocio();
    } catch (err) {
      console.error('Error registering consumo:', err);
      toast.error(err.response?.data?.detail || 'Error registrando consumo');
    } finally {
      setSavingConsumo(false);
    }
  };

  const openConsumoDialog = (botella) => {
    setSelectedBotella(botella);
    setShowConsumoDialog(true);
  };

  const handleVerEtiqueta = async (botella) => {
    try {
      const resp = await api.get(`/cava-socios/botellas/${botella.botella_id}/etiqueta?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`);
      setSelectedEtiqueta(resp.data || botella);
      setShowEtiquetaDialog(true);
    } catch (err) {
      setSelectedEtiqueta({
        ...botella,
        socio_nombre: socio?.nombre_completo,
        numero_socio: socio?.numero_socio
      });
      setShowEtiquetaDialog(true);
    }
  };

  // Funciones de descarga de reportes PDF
  const descargarReporte = async (tipo) => {
    if (!unidadNegocioPk) {
      toast.error('Selecciona una unidad de negocio autorizada.');
      return;
    }
    try {
      toast.loading(`Generando ${tipo}...`, { id: 'pdf-loading' });

      const response = await api.get(`/cava-socios/reportes/socio/${id}/${tipo}?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`, {
        responseType: 'blob'
      });

      // Crear URL del blob y descargar
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${tipo}_${socio?.numero_socio || id}.pdf`;
      document.body.appendChild(link);
      link.click();
      if (link && link.parentNode) { link.parentNode.removeChild(link); }
      window.URL.revokeObjectURL(url);

      toast.success('Reporte descargado', { id: 'pdf-loading' });
    } catch (err) {
      console.error('Error descargando reporte:', err);
      toast.error('Error descargando reporte', { id: 'pdf-loading' });
    }
  };

  // Función para enviar reportes por Email o WhatsApp
  const enviarReporte = async (tipoReporte, canales) => {
    if (!socio) return;
    if (!unidadNegocioPk) {
      toast.error('Selecciona una unidad de negocio autorizada.');
      return;
    }

    // Validaciones previas
    if (canales.includes('email') && !socio.email) {
      toast.error('El socio no tiene email registrado');
      return;
    }
    if (canales.includes('whatsapp') && !socio.telefono) {
      toast.error('El socio no tiene teléfono registrado');
      return;
    }

    setEnviandoReporte(true);
    const canalTexto = canales.join(' y ');

    try {
      toast.loading(`Enviando ${tipoReporte} por ${canalTexto}...`, { id: 'envio-reporte' });

      const response = await api.post(`/cava-socios/socios/${id}/enviar-reporte?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`, {
        tipo_reporte: tipoReporte,
        canales: canales
      });

      if (response.data.success) {
        const resultados = response.data.canales;
        let mensaje = `Reporte enviado`;

        if (resultados.email?.success) {
          mensaje += ` por Email`;
        }
        if (resultados.whatsapp?.success) {
          mensaje += resultados.email?.success ? ` y WhatsApp` : ` por WhatsApp`;
        }

        toast.success(mensaje, { id: 'envio-reporte' });
      } else {
        toast.error('Error parcial en el envío', { id: 'envio-reporte' });
      }
    } catch (err) {
      console.error('Error enviando reporte:', err);
      toast.error(err.response?.data?.detail || 'Error enviando reporte', { id: 'envio-reporte' });
    } finally {
      setEnviandoReporte(false);
    }
  };

  // Enviar todos los reportes
  const enviarTodosReportes = async (canales) => {
    if (!socio) return;
    if (!unidadNegocioPk) {
      toast.error('Selecciona una unidad de negocio autorizada.');
      return;
    }

    if (canales.includes('email') && !socio.email) {
      toast.error('El socio no tiene email registrado');
      return;
    }
    if (canales.includes('whatsapp') && !socio.telefono) {
      toast.error('El socio no tiene teléfono registrado');
      return;
    }

    setEnviandoReporte(true);

    try {
      toast.loading('Enviando todos los reportes...', { id: 'envio-todos' });

      const response = await api.post(
        `/cava-socios/socios/${id}/enviar-todos-reportes?canales=${canales.join('&canales=')}&unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`,
        {}
      );

      const { exitos, total_reportes } = response.data;

      if (exitos === total_reportes) {
        toast.success(`${exitos} reportes enviados exitosamente`, { id: 'envio-todos' });
      } else {
        toast.warning(`${exitos}/${total_reportes} reportes enviados`, { id: 'envio-todos' });
      }
    } catch (err) {
      console.error('Error enviando reportes:', err);
      toast.error(err.response?.data?.detail || 'Error enviando reportes', { id: 'envio-todos' });
    } finally {
      setEnviandoReporte(false);
    }
  };


  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  if (error || !socio) {
    return (
      <div className="p-6">
        <div className="p-4 rounded-lg bg-red-50 text-red-700 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          {error || 'Socio no encontrado'}
        </div>
        <Button variant="outline" className="mt-4" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
      </div>
    );
  }

  const botellasActivas = socio.botellas?.filter(b => b.estatus === 'EN_CAVA') || [];
  const botellasConsumidas = socio.botellas?.filter(b => b.estatus !== 'EN_CAVA') || [];

  return (
    <div className="p-6 space-y-6" data-testid="socio-detail-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Users className="h-7 w-7 text-purple-600" />
              {socio.nombre_completo}
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Socio #{socio.numero_socio} • {socio.tipo_membresia}
            </p>
          </div>
        </div>
        <div className="flex gap-2 flex-wrap items-end">
          <div className="min-w-[240px]">
            <CorporateFilterSelect
              filterKey="unidades_negocio"
              label="Unidad de negocio"
              placeholder="Selecciona una unidad"
            />
          </div>
          {/* Dropdown de Reportes y Envío */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" disabled={enviandoReporte} data-testid="btn-reportes-menu">

                {enviandoReporte ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <FileDown className="h-4 w-4 mr-2" />
                )}
                Reportes
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              {/* Descargar PDFs */}
              <DropdownMenuItem onClick={() => descargarReporte('ficha')} data-testid="menu-descargar-ficha">
                <FileText className="h-4 w-4 mr-2" />
                Descargar Ficha PDF
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => descargarReporte('consumos')} data-testid="menu-descargar-consumos">
                <FileText className="h-4 w-4 mr-2" />
                Descargar Consumos PDF
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => descargarReporte('estado-cuenta')} data-testid="menu-descargar-cuenta">
                <Receipt className="h-4 w-4 mr-2" />
                Descargar Estado Cuenta
              </DropdownMenuItem>

              <DropdownMenuSeparator />

              {/* Enviar por Email */}
              <DropdownMenuItem
                onClick={() => enviarReporte('ficha', ['email'])}
                disabled={!socio?.email}
                data-testid="menu-email-ficha"
              >
                <Mail className="h-4 w-4 mr-2" />
                Enviar Ficha por Email
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => enviarReporte('consumos', ['email'])}
                disabled={!socio?.email}
                data-testid="menu-email-consumos"
              >
                <Mail className="h-4 w-4 mr-2" />
                Enviar Consumos por Email
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => enviarReporte('estado_cuenta', ['email'])}
                disabled={!socio?.email}
                data-testid="menu-email-cuenta"
              >
                <Mail className="h-4 w-4 mr-2" />
                Enviar Edo. Cuenta por Email
              </DropdownMenuItem>

              <DropdownMenuSeparator />

              {/* Enviar por WhatsApp */}
              <DropdownMenuItem
                onClick={() => enviarReporte('ficha', ['whatsapp'])}
                disabled={!socio?.telefono}
                data-testid="menu-wa-ficha"
              >
                <MessageSquare className="h-4 w-4 mr-2" />
                Enviar Ficha por WhatsApp
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => enviarReporte('estado_cuenta', ['whatsapp'])}
                disabled={!socio?.telefono}
                data-testid="menu-wa-cuenta"
              >
                <MessageSquare className="h-4 w-4 mr-2" />
                Enviar Edo. Cuenta por WhatsApp
              </DropdownMenuItem>

              <DropdownMenuSeparator />

              {/* Enviar Todos */}
              <DropdownMenuItem
                onClick={() => enviarTodosReportes(['email'])}
                disabled={!socio?.email}
                className="font-medium"
                data-testid="menu-email-todos"
              >
                <Send className="h-4 w-4 mr-2 text-purple-600" />
                Enviar TODO por Email
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => enviarTodosReportes(['email', 'whatsapp'])}
                disabled={!socio?.email || !socio?.telefono}
                className="font-medium"
                data-testid="menu-multicanal-todos"
              >
                <Send className="h-4 w-4 mr-2 text-blue-600" />
                Enviar TODO (Email + WA)
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Button variant="outline" size="sm" onClick={fetchSocio}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </Button>
          <Button variant="outline" size="sm" onClick={() => navigate(`/cava-socios/socios/${id}/editar`)}>
            <Edit className="h-4 w-4 mr-2" />
            Editar
          </Button>
        </div>
      </div>

      <PersonaLinkCard
        socioId={id}
        unidadNegocioPk={unidadNegocioPk}
        onChanged={fetchSocio}
      />

      {/* Info del Socio */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Información de Contacto</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {socio.email && (
              <div className="flex items-center gap-2 text-sm">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <span>{socio.email}</span>
              </div>
            )}
            {socio.telefono && (
              <div className="flex items-center gap-2 text-sm">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <span>{socio.telefono}</span>
              </div>
            )}
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span>Alta: {formatDate(socio.fecha_alta)}</span>
            </div>
            {socio.fecha_vencimiento && (
              <div className="flex items-center gap-2 text-sm">
                <Calendar className="h-4 w-4 text-orange-500" />
                <span>Vence: {formatDate(socio.fecha_vencimiento)}</span>
              </div>
            )}
            {socio.observaciones && (
              <div className="pt-3 border-t">
                <p className="text-xs text-muted-foreground">Observaciones:</p>
                <p className="text-sm mt-1">{socio.observaciones}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Resumen de Cava</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-3xl font-bold text-blue-700">
                  {botellasActivas.length}
                </div>
                <div className="text-xs text-blue-600 mt-1">Botellas en Resguardo</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-3xl font-bold text-purple-700">
                  {socio.maximo_botellas}
                </div>
                <div className="text-xs text-purple-600 mt-1">Capacidad Máxima</div>
              </div>
              <div className="text-center p-4 bg-emerald-50 rounded-lg">
                <div className="text-3xl font-bold text-emerald-700">
                  {formatCurrency(socio.valor_total_declarado || botellasActivas.reduce((sum, b) => sum + (b.valor_declarado || 0), 0))}
                </div>
                <div className="text-xs text-emerald-600 mt-1">Valor Total Declarado</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Botellas en Resguardo */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Wine className="h-5 w-5 text-blue-500" />
                Botellas en Resguardo ({botellasActivas.length})
              </CardTitle>
              <CardDescription>
                Botellas actualmente almacenadas en la cava del socio
              </CardDescription>
            </div>
            <Dialog open={showBotellaDialog} onOpenChange={setShowBotellaDialog}>
              <DialogTrigger asChild>
                <Button size="sm" disabled={botellasActivas.length >= socio.maximo_botellas}>
                  <Plus className="h-4 w-4 mr-2" />
                  Agregar Botella
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Registrar Nueva Botella</DialogTitle>
                  <DialogDescription>
                    Agrega una botella al resguardo del socio
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Nombre del Producto *</Label>
                    <Input
                      value={botellaForm.producto_nombre}
                      onChange={(e) => setBotellaForm(f => ({...f, producto_nombre: e.target.value}))}
                      placeholder="Ej: Chateau Margaux 2015"
                      data-testid="input-botella-nombre"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Marca</Label>
                      <Input
                        value={botellaForm.marca}
                        onChange={(e) => setBotellaForm(f => ({...f, marca: e.target.value}))}
                        placeholder="Marca"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Tipo de Bebida</Label>
                      <Select
                        value={botellaForm.tipo_bebida}
                        onValueChange={(v) => setBotellaForm(f => ({...f, tipo_bebida: v}))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {TIPOS_BEBIDA.map(t => (
                            <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Añada</Label>
                      <Input
                        value={botellaForm.añada}
                        onChange={(e) => setBotellaForm(f => ({...f, añada: e.target.value}))}
                        placeholder="2018"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Capacidad (ml)</Label>
                      <Input
                        type="number"
                        value={botellaForm.capacidad}
                        onChange={(e) => setBotellaForm(f => ({...f, capacidad: parseInt(e.target.value) || 750}))}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Ubicación en Cava</Label>
                      <Input
                        value={botellaForm.ubicacion}
                        onChange={(e) => setBotellaForm(f => ({...f, ubicacion: e.target.value}))}
                        placeholder="Estante A-3"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Valor Declarado</Label>
                      <Input
                        type="number"
                        value={botellaForm.valor_declarado}
                        onChange={(e) => setBotellaForm(f => ({...f, valor_declarado: parseFloat(e.target.value) || 0}))}
                        placeholder="$0.00"
                      />
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowBotellaDialog(false)}>
                    Cancelar
                  </Button>
                  <Button onClick={handleAddBotella} disabled={savingBotella}>
                    {savingBotella ? 'Guardando...' : 'Registrar Botella'}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {botellasActivas.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Producto</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Añada</TableHead>
                  <TableHead>Ubicación</TableHead>
                  <TableHead className="text-right">Valor</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {botellasActivas.map((botella) => (
                  <TableRow key={botella.botella_id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{botella.producto_nombre}</div>
                        {botella.marca && (
                          <div className="text-xs text-muted-foreground">{botella.marca}</div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">
                        {TIPOS_BEBIDA.find(t => t.value === botella.tipo_bebida)?.label || botella.tipo_bebida}
                      </span>
                    </TableCell>
                    <TableCell>{botella.añada || '-'}</TableCell>
                    <TableCell>{botella.ubicacion || '-'}</TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(botella.valor_declarado)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          title="Ver Etiqueta QR"
                          onClick={() => handleVerEtiqueta(botella)}
                        >
                          <QrCode className="h-4 w-4 text-zinc-700" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openConsumoDialog(botella)}
                          data-testid={`consumir-${botella.botella_id}`}
                        >
                          <Package className="h-4 w-4 mr-1" />
                          Consumir
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Wine className="h-12 w-12 mx-auto mb-4 opacity-20" />
              <p>No hay botellas en resguardo</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Etiqueta de Custodia con QR */}
      <Dialog open={showEtiquetaDialog} onOpenChange={setShowEtiquetaDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <QrCode className="h-5 w-5 text-amber-600" />
              Etiqueta de Resguardo / QR Cava
            </DialogTitle>
            <DialogDescription>
              Ficha para identificación física de la botella en el casillero
            </DialogDescription>
          </DialogHeader>
          {selectedEtiqueta && (
            <div className="border-2 border-dashed border-zinc-300 p-6 rounded-lg bg-zinc-50 space-y-4 text-center">
              <div className="text-xs uppercase font-bold tracking-wider text-zinc-500">
                EDARSA HUB • CONTROL DE CAVA
              </div>
              <div className="font-bold text-lg text-zinc-900">
                {selectedEtiqueta.producto_nombre}
              </div>
              <div className="text-sm text-zinc-600">
                {selectedEtiqueta.marca} {selectedEtiqueta.añada ? `• Añada ${selectedEtiqueta.añada}` : ''}
              </div>
              <div className="inline-block p-4 bg-white rounded-lg shadow-sm border border-zinc-200">
                <div className="w-32 h-32 flex flex-col items-center justify-center bg-zinc-900 text-white rounded font-mono text-[10px] p-2 leading-tight">
                  <QrCode className="h-16 w-16 mb-1 text-white" />
                  <span>ID: {selectedEtiqueta.botella_id?.slice(0, 8)}</span>
                  <span>SOCIO: #{selectedEtiqueta.numero_socio || socio?.numero_socio}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-left text-xs pt-2 border-t">
                <div>
                  <span className="text-zinc-500">Socio:</span>
                  <p className="font-semibold text-zinc-800">{selectedEtiqueta.socio_nombre || socio?.nombre_completo}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Casillero / Ubicación:</span>
                  <p className="font-semibold text-zinc-800">{selectedEtiqueta.ubicacion || 'Sin asignar'}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Valor Declarado:</span>
                  <p className="font-semibold text-zinc-800">{formatCurrency(selectedEtiqueta.valor_declarado)}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Fecha Ingreso:</span>
                  <p className="font-semibold text-zinc-800">{formatDate(selectedEtiqueta.fecha_ingreso)}</p>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEtiquetaDialog(false)}>
              Cerrar
            </Button>
            <Button onClick={() => window.print()}>
              <Printer className="h-4 w-4 mr-2" />
              Imprimir Etiqueta
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog de Consumo */}
      <Dialog open={showConsumoDialog} onOpenChange={setShowConsumoDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar Consumo</DialogTitle>
            <DialogDescription>
              {selectedBotella?.producto_nombre}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Porcentaje Consumido</Label>
              <Select
                value={String(consumoForm.porcentaje_consumido)}
                onValueChange={(v) => setConsumoForm(f => ({...f, porcentaje_consumido: parseInt(v)}))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="25">25% (Parcial)</SelectItem>
                  <SelectItem value="50">50% (Medio)</SelectItem>
                  <SelectItem value="75">75% (Casi completo)</SelectItem>
                  <SelectItem value="100">100% (Completo)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Motivo</Label>
              <Input
                value={consumoForm.motivo}
                onChange={(e) => setConsumoForm(f => ({...f, motivo: e.target.value}))}
                placeholder="Cena especial, celebración..."
              />
            </div>
            <div className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg">
              <div>
                <Label>Cargo por Descorche</Label>
                <p className="text-xs text-muted-foreground">Se agregará a la cuenta</p>
              </div>
              <Input
                type="number"
                className="w-24"
                value={consumoForm.monto_descorche}
                onChange={(e) => setConsumoForm(f => ({...f, monto_descorche: parseFloat(e.target.value) || 0}))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConsumoDialog(false)}>
              Cancelar
            </Button>
            <Button onClick={handleConsumo} disabled={savingConsumo}>
              {savingConsumo ? 'Procesando...' : 'Confirmar Consumo'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Historial de Botellas Consumidas */}
      {botellasConsumidas.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Package className="h-5 w-5 text-gray-500" />
              Historial de Consumos ({botellasConsumidas.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Producto</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Estatus</TableHead>
                  <TableHead>Fecha Registro</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {botellasConsumidas.map((botella) => (
                  <TableRow key={botella.botella_id} className="opacity-60">
                    <TableCell>{botella.producto_nombre}</TableCell>
                    <TableCell>{TIPOS_BEBIDA.find(t => t.value === botella.tipo_bebida)?.label || '-'}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEstatusColor(botella.estatus)}`}>
                        {botella.estatus}
                      </span>
                    </TableCell>
                    <TableCell>{formatDate(botella.fecha_ingreso)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function SocioDetail() {
  return (
    <CorporateFiltersProvider scope="cava_socios">
      <SocioDetailContent />
    </CorporateFiltersProvider>
  );
}
