import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { FileDown, Mail, Search, AlertCircle, TrendingUp, TrendingDown } from 'lucide-react';
import { toast } from 'sonner';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

const Reportes = () => {
  const [servers, setServers] = useState([]);
  const [reportData, setReportData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    server_id: '',
    query_type: 'ventas',
    sucursal: '',
    almacen: '',
    fecha_ini: '',
    fecha_fin: ''
  });

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    try {
      const response = await api.get('/servers');
      setServers(response.data);
    } catch (error) {
      toast.error('Error al cargar servidores');
    }
  };

  const handleGenerateReport = async () => {
    if (!filters.server_id) {
      toast.error('Selecciona un servidor');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/reports/inventory', {
        server_id: filters.server_id,
        query_type: filters.query_type,
        params: {
          sucursal: filters.sucursal,
          almacen: filters.almacen,
          fecha_ini: filters.fecha_ini,
          fecha_fin: filters.fecha_fin
        }
      });
      
      setReportData(response.data.data);
      toast.success(`Reporte generado: ${response.data.count} registros`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al generar reporte');
    } finally {
      setLoading(false);
    }
  };

  const handleExportExcel = () => {
    if (reportData.length === 0) {
      toast.error('No hay datos para exportar');
      return;
    }

    const worksheet = XLSX.utils.json_to_sheet(reportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Reporte');
    
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    saveAs(blob, `reporte_inventario_${new Date().toISOString().split('T')[0]}.xlsx`);
    
    toast.success('Reporte exportado a Excel');
  };

  const handleExportPDF = () => {
    if (reportData.length === 0) {
      toast.error('No hay datos para exportar');
      return;
    }

    const doc = new jsPDF('landscape');
    
    doc.setFontSize(18);
    doc.text('Reporte de Inventario', 14, 20);
    
    doc.setFontSize(10);
    doc.text(`Fecha: ${new Date().toLocaleDateString()}`, 14, 28);
    
    const headers = Object.keys(reportData[0]);
    const data = reportData.map(row => headers.map(header => row[header] || ''));
    
    doc.autoTable({
      head: [headers],
      body: data,
      startY: 35,
      styles: { fontSize: 8 },
      headStyles: { fillColor: [24, 24, 27] }
    });
    
    doc.save(`reporte_inventario_${new Date().toISOString().split('T')[0]}.pdf`);
    toast.success('Reporte exportado a PDF');
  };

  const calculateDifference = (row) => {
    // Simplified calculation for display
    if (row.cantidad) {
      return Math.abs(parseFloat(row.cantidad) || 0);
    }
    return 0;
  };

  const getDifferenceColor = (value) => {
    if (value > 0) return 'text-red-600';
    if (value < 0) return 'text-green-600';
    return 'text-zinc-600';
  };

  return (
    <div className="space-y-6" data-testid="reportes-page">
      <div>
        <h1 className="text-3xl font-extrabold text-zinc-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Reportes de Inventario
        </h1>
        <p className="text-zinc-600 mt-1">Genera y analiza reportes de inventario</p>
      </div>

      {/* Filters */}
      <Card className="border border-zinc-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Servidor</Label>
              <Select value={filters.server_id} onValueChange={(value) => setFilters({...filters, server_id: value})}>
                <SelectTrigger data-testid="server-select">
                  <SelectValue placeholder="Selecciona un servidor" />
                </SelectTrigger>
                <SelectContent>
                  {servers.map((server) => (
                    <SelectItem key={server.id} value={server.id}>
                      {server.name} ({server.system_type})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Tipo de Consulta</Label>
              <Select value={filters.query_type} onValueChange={(value) => setFilters({...filters, query_type: value})}>
                <SelectTrigger data-testid="query-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ventas">Ventas</SelectItem>
                  <SelectItem value="movimientos">Movimientos</SelectItem>
                  <SelectItem value="productos">Productos</SelectItem>
                  <SelectItem value="inventarios">Inventarios Físicos</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Sucursal</Label>
              <Input
                value={filters.sucursal}
                onChange={(e) => setFilters({...filters, sucursal: e.target.value})}
                placeholder="Nombre de sucursal"
                data-testid="sucursal-input"
              />
            </div>

            <div className="space-y-2">
              <Label>Almacén</Label>
              <Input
                value={filters.almacen}
                onChange={(e) => setFilters({...filters, almacen: e.target.value})}
                placeholder="Nombre de almacén"
                data-testid="almacen-input"
              />
            </div>

            <div className="space-y-2">
              <Label>Fecha Inicio</Label>
              <Input
                type="date"
                value={filters.fecha_ini}
                onChange={(e) => setFilters({...filters, fecha_ini: e.target.value})}
                data-testid="fecha-inicio-input"
              />
            </div>

            <div className="space-y-2">
              <Label>Fecha Fin</Label>
              <Input
                type="date"
                value={filters.fecha_fin}
                onChange={(e) => setFilters({...filters, fecha_fin: e.target.value})}
                data-testid="fecha-fin-input"
              />
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <Button 
              onClick={handleGenerateReport}
              disabled={loading}
              className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
              data-testid="generate-report-button"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Generando...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Generar Reporte
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      {reportData.length > 0 && (
        <div className="flex gap-2">
          <Button 
            onClick={handleExportExcel}
            variant="outline"
            data-testid="export-excel-button"
          >
            <FileDown className="h-4 w-4 mr-2" />
            Exportar a Excel
          </Button>
          <Button 
            onClick={handleExportPDF}
            variant="outline"
            data-testid="export-pdf-button"
          >
            <FileDown className="h-4 w-4 mr-2" />
            Exportar a PDF
          </Button>
        </div>
      )}

      {/* Results */}
      {reportData.length > 0 && (
        <Card className="border border-zinc-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold">Resultados</CardTitle>
              <span className="text-sm text-zinc-600">
                Total: <span className="font-data font-semibold">{reportData.length}</span> registros
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border border-zinc-200 overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-zinc-50">
                    {Object.keys(reportData[0]).map((key) => (
                      <TableHead key={key} className="text-xs uppercase tracking-wider font-medium text-zinc-500">
                        {key}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reportData.slice(0, 50).map((row, idx) => (
                    <TableRow key={idx} className="hover:bg-zinc-50/50">
                      {Object.values(row).map((value, cellIdx) => (
                        <TableCell key={cellIdx} className="text-sm font-data text-zinc-700">
                          {value !== null && value !== undefined ? String(value) : '-'}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {reportData.length > 50 && (
              <p className="text-sm text-zinc-600 mt-4 text-center">
                Mostrando 50 de {reportData.length} registros. Exporta para ver todos.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {reportData.length === 0 && !loading && (
        <Card className="border border-zinc-200 shadow-sm">
          <CardContent className="py-12">
            <div className="text-center text-zinc-500">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-zinc-400" />
              <p>No hay datos para mostrar</p>
              <p className="text-sm mt-2">Configura los filtros y genera un reporte</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Reportes;