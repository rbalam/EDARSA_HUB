import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  FilePlus, Plus, Trash2, Save, ArrowLeft, 
  CheckCircle, AlertTriangle, Calculator, Package
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { toast } from 'sonner';

const TIPOS_DERIVADO = ['PRINCIPAL', 'SUBPRODUCTO', 'MERMA'];

export default function CapturaDirectaPage() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [empresas, setEmpresas] = useState([]);
  
  // Form principal
  const [form, setForm] = useState({
    empresa_id: '',
    fecha_operacion_mexico: new Date().toISOString().split('T')[0],
    insumo_base_codigo: '',
    insumo_base_nombre: '',
    cantidad_base_planeada: '',
    lote_insumo: '',
    observaciones: ''
  });

  // Detalles de productos derivados
  const [detalles, setDetalles] = useState([
    { 
      producto_derivado_codigo: '',
      producto_derivado_nombre: '', 
      tipo_derivado: 'PRINCIPAL', 
      cantidad_esperada: '', 
      porcentaje_esperado: '' 
    }
  ]);

  useEffect(() => {
    fetchEmpresas();
  }, []);

  const fetchEmpresas = async () => {
    try {
      const response = await api.get('/empresas');
      setEmpresas(response.data.empresas || response.data || []);
    } catch (err) {
      console.error('Error fetching empresas:', err);
    }
  };

  const handleInputChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleDetalleChange = (index, field, value) => {
    const newDetalles = [...detalles];
    newDetalles[index][field] = value;
    
    // Calcular porcentaje automáticamente si hay cantidad base
    if (field === 'cantidad_esperada' && form.cantidad_base_planeada) {
      const cantidadEsperada = parseFloat(value) || 0;
      const cantidadBase = parseFloat(form.cantidad_base_planeada) || 1;
      newDetalles[index].porcentaje_esperado = ((cantidadEsperada / cantidadBase) * 100).toFixed(2);
    }
    
    setDetalles(newDetalles);
  };

  const addDetalle = () => {
    setDetalles([...detalles, {
      producto_derivado_codigo: '',
      producto_derivado_nombre: '',
      tipo_derivado: 'PRINCIPAL',
      cantidad_esperada: '',
      porcentaje_esperado: ''
    }]);
  };

  const removeDetalle = (index) => {
    if (detalles.length > 1) {
      setDetalles(detalles.filter((_, i) => i !== index));
    }
  };

  const calcularTotales = () => {
    const totalCantidad = detalles.reduce((sum, d) => sum + (parseFloat(d.cantidad_esperada) || 0), 0);
    const totalPorcentaje = detalles.reduce((sum, d) => sum + (parseFloat(d.porcentaje_esperado) || 0), 0);
    return { totalCantidad, totalPorcentaje };
  };

  const validarForm = () => {
    if (!form.empresa_id) return 'Seleccione una empresa';
    if (!form.fecha_operacion_mexico) return 'Ingrese fecha de operación';
    if (!form.insumo_base_nombre) return 'Ingrese nombre del insumo base';
    if (!form.cantidad_base_planeada || parseFloat(form.cantidad_base_planeada) <= 0) {
      return 'Ingrese cantidad base válida';
    }
    
    if (detalles.length === 0) return 'Agregue al menos un producto derivado';
    
    for (let i = 0; i < detalles.length; i++) {
      const d = detalles[i];
      if (!d.producto_derivado_nombre) return `Producto ${i + 1}: Ingrese nombre`;
      if (!d.cantidad_esperada || parseFloat(d.cantidad_esperada) <= 0) {
        return `Producto ${i + 1}: Ingrese cantidad esperada válida`;
      }
    }
    
    return null;
  };

  const handleSubmit = async () => {
    const error = validarForm();
    if (error) {
      toast.error(error);
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        empresa_id: form.empresa_id,
        fecha_operacion_mexico: form.fecha_operacion_mexico,
        insumo_base_codigo: form.insumo_base_codigo || `INS-${Date.now()}`,
        insumo_base_nombre: form.insumo_base_nombre,
        cantidad_base_planeada: parseFloat(form.cantidad_base_planeada),
        lote_insumo: form.lote_insumo || null,
        observaciones: form.observaciones || null,
        detalles: detalles.map(d => ({
          producto_derivado_codigo: d.producto_derivado_codigo || null,
          producto_derivado_nombre: d.producto_derivado_nombre,
          tipo_derivado: d.tipo_derivado,
          cantidad_esperada: parseFloat(d.cantidad_esperada),
          porcentaje_esperado: parseFloat(d.porcentaje_esperado) || 
            ((parseFloat(d.cantidad_esperada) / parseFloat(form.cantidad_base_planeada)) * 100)
        }))
      };

      const response = await api.post('/tablajeria/ordenes/captura-directa', payload);
      
      if (response.data.success) {
        toast.success(`Orden ${response.data.folio_orden} creada exitosamente`);
        navigate('/tablajeria/ordenes');
      } else {
        toast.error(response.data.mensaje || 'Error al crear orden');
      }
    } catch (err) {
      console.error('Error creating orden:', err);
      toast.error(err.response?.data?.detail || 'Error al crear orden de captura directa');
    } finally {
      setSubmitting(false);
    }
  };

  const { totalCantidad, totalPorcentaje } = calcularTotales();

  return (
    <div className="p-6 space-y-6" data-testid="captura-directa-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => navigate('/tablajeria/ordenes')}
            data-testid="btn-volver"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <FilePlus className="h-6 w-6" />
              Captura Directa de Tablaje
            </h1>
            <p className="text-sm text-muted-foreground">
              Crear orden de producción sin plantilla predefinida
            </p>
          </div>
        </div>
        
        <Button 
          onClick={handleSubmit}
          disabled={submitting}
          className="gap-2"
          data-testid="btn-crear-orden"
        >
          <Save className="h-4 w-4" />
          {submitting ? 'Creando...' : 'Crear Orden'}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Formulario Principal */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Datos del Insumo Base
            </CardTitle>
            <CardDescription>
              Información del producto a transformar
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="empresa_id">Empresa *</Label>
                <Select 
                  value={form.empresa_id} 
                  onValueChange={(v) => handleInputChange('empresa_id', v)}
                >
                  <SelectTrigger data-testid="select-empresa">
                    <SelectValue placeholder="Seleccionar empresa" />
                  </SelectTrigger>
                  <SelectContent>
                    {empresas.map(emp => (
                      <SelectItem 
                        key={emp.EmpresaID || emp.id} 
                        value={emp.EmpresaID || emp.id}
                      >
                        {emp.NombreComercial || emp.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="fecha_operacion">Fecha Operación *</Label>
                <Input
                  id="fecha_operacion"
                  type="date"
                  value={form.fecha_operacion_mexico}
                  onChange={(e) => handleInputChange('fecha_operacion_mexico', e.target.value)}
                  data-testid="input-fecha"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="insumo_codigo">Código Insumo</Label>
                <Input
                  id="insumo_codigo"
                  placeholder="Ej: INS-RES-001"
                  value={form.insumo_base_codigo}
                  onChange={(e) => handleInputChange('insumo_base_codigo', e.target.value)}
                  data-testid="input-insumo-codigo"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="insumo_nombre">Nombre Insumo *</Label>
                <Input
                  id="insumo_nombre"
                  placeholder="Ej: Res en canal"
                  value={form.insumo_base_nombre}
                  onChange={(e) => handleInputChange('insumo_base_nombre', e.target.value)}
                  data-testid="input-insumo-nombre"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="cantidad_base">Cantidad Base (kg) *</Label>
                <Input
                  id="cantidad_base"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  value={form.cantidad_base_planeada}
                  onChange={(e) => handleInputChange('cantidad_base_planeada', e.target.value)}
                  data-testid="input-cantidad-base"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="lote">Lote Insumo</Label>
                <Input
                  id="lote"
                  placeholder="Ej: LOTE-2026-001"
                  value={form.lote_insumo}
                  onChange={(e) => handleInputChange('lote_insumo', e.target.value)}
                  data-testid="input-lote"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="observaciones">Observaciones</Label>
              <Textarea
                id="observaciones"
                placeholder="Notas adicionales..."
                value={form.observaciones}
                onChange={(e) => handleInputChange('observaciones', e.target.value)}
                data-testid="input-observaciones"
              />
            </div>
          </CardContent>
        </Card>

        {/* Resumen */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5" />
              Resumen
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 rounded-lg bg-muted/50 space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Insumo Base:</span>
                <span className="font-medium">
                  {form.cantidad_base_planeada ? `${form.cantidad_base_planeada} kg` : '-'}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Productos:</span>
                <span className="font-medium">{detalles.length}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Total Esperado:</span>
                <span className="font-medium">{totalCantidad.toFixed(2)} kg</span>
              </div>
              
              <div className="border-t pt-3 flex justify-between">
                <span className="text-sm text-muted-foreground">Rendimiento:</span>
                <span className={`font-bold ${totalPorcentaje > 100 ? 'text-red-500' : 'text-green-600'}`}>
                  {totalPorcentaje.toFixed(1)}%
                </span>
              </div>
            </div>

            {totalPorcentaje > 100 && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 text-red-700 text-sm">
                <AlertTriangle className="h-4 w-4" />
                <span>El rendimiento total excede 100%</span>
              </div>
            )}

            {totalPorcentaje > 0 && totalPorcentaje <= 100 && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 text-green-700 text-sm">
                <CheckCircle className="h-4 w-4" />
                <span>Distribución válida</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabla de Detalles */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Productos Derivados</CardTitle>
            <CardDescription>
              Defina los productos resultantes de la transformación
            </CardDescription>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={addDetalle}
            className="gap-2"
            data-testid="btn-agregar-detalle"
          >
            <Plus className="h-4 w-4" />
            Agregar Producto
          </Button>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Código</TableHead>
                <TableHead>Nombre Producto *</TableHead>
                <TableHead className="w-[140px]">Tipo</TableHead>
                <TableHead className="w-[120px]">Cantidad (kg) *</TableHead>
                <TableHead className="w-[100px]">% Esperado</TableHead>
                <TableHead className="w-[60px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {detalles.map((detalle, index) => (
                <TableRow key={index} data-testid={`detalle-row-${index}`}>
                  <TableCell>
                    <Input
                      placeholder="PROD-001"
                      value={detalle.producto_derivado_codigo}
                      onChange={(e) => handleDetalleChange(index, 'producto_derivado_codigo', e.target.value)}
                      className="h-9"
                      data-testid={`input-codigo-${index}`}
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      placeholder="Nombre del producto"
                      value={detalle.producto_derivado_nombre}
                      onChange={(e) => handleDetalleChange(index, 'producto_derivado_nombre', e.target.value)}
                      className="h-9"
                      data-testid={`input-nombre-${index}`}
                    />
                  </TableCell>
                  <TableCell>
                    <Select
                      value={detalle.tipo_derivado}
                      onValueChange={(v) => handleDetalleChange(index, 'tipo_derivado', v)}
                    >
                      <SelectTrigger className="h-9" data-testid={`select-tipo-${index}`}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {TIPOS_DERIVADO.map(tipo => (
                          <SelectItem key={tipo} value={tipo}>
                            {tipo}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      value={detalle.cantidad_esperada}
                      onChange={(e) => handleDetalleChange(index, 'cantidad_esperada', e.target.value)}
                      className="h-9"
                      data-testid={`input-cantidad-${index}`}
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      step="0.01"
                      value={detalle.porcentaje_esperado}
                      readOnly
                      className="h-9 bg-muted"
                      data-testid={`input-porcentaje-${index}`}
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeDetalle(index)}
                      disabled={detalles.length === 1}
                      className="h-8 w-8 text-red-500 hover:text-red-700"
                      data-testid={`btn-eliminar-${index}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
