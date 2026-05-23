import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
  Layers, Search, RefreshCw, Eye, CheckCircle, 
  AlertTriangle, Clock, Filter, ChevronLeft, ChevronRight
} from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function PlantillasPage() {
  const [plantillas, setPlantillas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [limit] = useState(20);
  const [searchTerm, setSearchTerm] = useState('');
  const [estatusFilter, setEstatusFilter] = useState('');
  const [selectedPlantilla, setSelectedPlantilla] = useState(null);

  const fetchPlantillas = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: (page * limit).toString()
      });
      if (estatusFilter) params.append('estatus', estatusFilter);
      
      const response = await api.get(`/tablajeria/plantillas?${params}`);
      setPlantillas(response.data.plantillas || []);
      setTotal(response.data.total || 0);
    } catch (err) {
      console.error('Error fetching plantillas:', err);
      toast.error('Error cargando plantillas');
    } finally {
      setLoading(false);
    }
  };

  const fetchPlantillaDetalle = async (plantillaId) => {
    try {
      const response = await api.get(`/tablajeria/plantillas/${plantillaId}`);
      setSelectedPlantilla(response.data);
    } catch (err) {
      toast.error('Error cargando detalle');
    }
  };

  const publicarPlantilla = async (plantillaId) => {
    try {
      await api.put(`/tablajeria/plantillas/${plantillaId}/publicar`);
      toast.success('Plantilla publicada');
      fetchPlantillas();
      if (selectedPlantilla?.PlantillaID === plantillaId) {
        fetchPlantillaDetalle(plantillaId);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error publicando');
    }
  };

  useEffect(() => {
    fetchPlantillas();
  }, [page, estatusFilter]);

  const getEstatusStyle = (estatus) => {
    const styles = {
      'BORRADOR': 'bg-gray-100 text-gray-700',
      'SINCRONIZADA': 'bg-blue-100 text-blue-700',
      'VALIDADA': 'bg-cyan-100 text-cyan-700',
      'PUBLICADA': 'bg-green-100 text-green-700',
      'OBSERVADA': 'bg-yellow-100 text-yellow-700',
      'INACTIVA': 'bg-red-100 text-red-700',
      'REEMPLAZADA': 'bg-purple-100 text-purple-700'
    };
    return styles[estatus] || 'bg-gray-100 text-gray-700';
  };

  const filteredPlantillas = plantillas.filter(p => 
    !searchTerm || 
    p.NombrePlantilla?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.CodigoPlantilla?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6" data-testid="plantillas-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800 flex items-center gap-2">
            <Layers className="h-7 w-7 text-blue-600" />
            Plantillas de Tablajería
          </h1>
          <p className="text-zinc-500">Gestión de plantillas de transformación</p>
        </div>
        <Button onClick={fetchPlantillas} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-zinc-400" />
                <Input
                  placeholder="Buscar por nombre o código..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              value={estatusFilter}
              onChange={(e) => { setEstatusFilter(e.target.value); setPage(0); }}
              className="px-3 py-2 border rounded-md text-sm"
            >
              <option value="">Todos los estatus</option>
              <option value="SINCRONIZADA">Sincronizada</option>
              <option value="PUBLICADA">Publicada</option>
              <option value="VALIDADA">Validada</option>
              <option value="BORRADOR">Borrador</option>
              <option value="OBSERVADA">Observada</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lista de plantillas */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center justify-between">
                <span>Plantillas ({total})</span>
                <span className="text-sm font-normal text-zinc-500">
                  Página {page + 1} de {Math.ceil(total / limit) || 1}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin text-zinc-400" />
                </div>
              ) : (
                <>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Código</TableHead>
                        <TableHead>Nombre</TableHead>
                        <TableHead>Insumo Base</TableHead>
                        <TableHead>Estatus</TableHead>
                        <TableHead className="text-right">Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredPlantillas.map((p) => (
                        <TableRow 
                          key={p.PlantillaID}
                          className={`cursor-pointer hover:bg-zinc-50 ${
                            selectedPlantilla?.PlantillaID === p.PlantillaID ? 'bg-blue-50' : ''
                          }`}
                          onClick={() => fetchPlantillaDetalle(p.PlantillaID)}
                        >
                          <TableCell className="font-mono text-xs">{p.CodigoPlantilla}</TableCell>
                          <TableCell className="font-medium">{p.NombrePlantilla}</TableCell>
                          <TableCell className="text-sm text-zinc-500">{p.InsumoBaseNombre || '-'}</TableCell>
                          <TableCell>
                            <span className={`px-2 py-1 text-xs rounded ${getEstatusStyle(p.Estatus)}`}>
                              {p.Estatus}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={(e) => { e.stopPropagation(); fetchPlantillaDetalle(p.PlantillaID); }}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                      {filteredPlantillas.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center py-8 text-zinc-500">
                            No se encontraron plantillas
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>

                  {/* Paginación */}
                  <div className="flex items-center justify-between mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page === 0}
                      onClick={() => setPage(p => p - 1)}
                    >
                      <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={(page + 1) * limit >= total}
                      onClick={() => setPage(p => p + 1)}
                    >
                      Siguiente <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Detalle de plantilla */}
        <div>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Detalle de Plantilla</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedPlantilla ? (
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-zinc-500">Código</p>
                    <p className="font-mono">{selectedPlantilla.CodigoPlantilla}</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500">Nombre</p>
                    <p className="font-medium">{selectedPlantilla.NombrePlantilla}</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500">Insumo Base</p>
                    <p>{selectedPlantilla.InsumoBaseNombre || '-'}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-zinc-500">Rendimiento Esperado</p>
                      <p className="font-medium">
                        {selectedPlantilla.RendimientoEsperadoPorcentaje?.toFixed(2) || '-'}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-zinc-500">Merma Esperada</p>
                      <p className="font-medium">
                        {selectedPlantilla.MermaEsperadaPorcentaje?.toFixed(2) || '-'}%
                      </p>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500">Estatus</p>
                    <span className={`px-2 py-1 text-xs rounded ${getEstatusStyle(selectedPlantilla.Estatus)}`}>
                      {selectedPlantilla.Estatus}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500">Origen</p>
                    <p className="text-sm">{selectedPlantilla.OrigenPlantilla}</p>
                  </div>

                  {/* Derivados */}
                  {selectedPlantilla.detalles?.length > 0 && (
                    <div>
                      <p className="text-xs text-zinc-500 mb-2">Derivados ({selectedPlantilla.detalles.length})</p>
                      <div className="space-y-2 max-h-[200px] overflow-y-auto">
                        {selectedPlantilla.detalles.map((d, idx) => (
                          <div key={idx} className="p-2 bg-zinc-50 rounded text-sm">
                            <div className="flex justify-between">
                              <span className="font-medium">{d.ProductoDerivadoNombre}</span>
                              <span className={`text-xs px-1.5 py-0.5 rounded ${
                                d.TipoDerivado === 'MERMA' ? 'bg-red-100 text-red-700' :
                                d.TipoDerivado === 'PRINCIPAL' ? 'bg-green-100 text-green-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {d.TipoDerivado}
                              </span>
                            </div>
                            {d.PorcentajeRendimientoEsperado && (
                              <p className="text-xs text-zinc-500">
                                {d.PorcentajeRendimientoEsperado.toFixed(2)}%
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Acciones */}
                  {['SINCRONIZADA', 'VALIDADA', 'BORRADOR'].includes(selectedPlantilla.Estatus) && (
                    <Button 
                      className="w-full"
                      onClick={() => publicarPlantilla(selectedPlantilla.PlantillaID)}
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Publicar Plantilla
                    </Button>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-zinc-400">
                  <Layers className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Selecciona una plantilla para ver su detalle</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
