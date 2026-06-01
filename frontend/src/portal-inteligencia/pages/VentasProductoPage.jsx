/**
 * Ventas por Producto - Análisis detallado
 */
import React, { useState, useEffect } from 'react';
import { Package, Search, Filter, ArrowUpDown, Download } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const FALLBACK_PRODUCTOS = [
  { id: 1, codigo: 'DIAG-004', nombre: 'Don Julio Blanco', familia: 'LICORES', subfamilia: 'TEQUILA', casa: 'DIAGEO', alcohol: 38, cantidad: 245, ventas: 159250, propina: 12500 },
  { id: 2, codigo: 'DIAG-005', nombre: 'Don Julio Reposado', familia: 'LICORES', subfamilia: 'TEQUILA', casa: 'DIAGEO', alcohol: 38, cantidad: 198, ventas: 148500, propina: 11200 },
  { id: 3, codigo: 'ALIM-001', nombre: 'Filete Mignon', familia: 'ALIMENTOS', subfamilia: 'CARNES', casa: 'COCINA', alcohol: 0, cantidad: 312, ventas: 140400, propina: 15800 },
  { id: 4, codigo: 'DIAG-003', nombre: 'Buchanan\'s 12 Años', familia: 'LICORES', subfamilia: 'WHISKY', casa: 'DIAGEO', alcohol: 40, cantidad: 156, ventas: 117000, propina: 9200 },
  { id: 5, codigo: 'CUER-005', nombre: 'Maestro Dobel Diamante', familia: 'LICORES', subfamilia: 'TEQUILA', casa: 'CASA CUERVO', alcohol: 35, cantidad: 128, ventas: 113920, propina: 8500 },
  { id: 6, codigo: 'ALIM-002', nombre: 'Camarón al Mojo de Ajo', familia: 'ALIMENTOS', subfamilia: 'MARISCOS', casa: 'COCINA', alcohol: 0, cantidad: 287, ventas: 109060, propina: 12300 },
  { id: 7, codigo: 'PERN-003', nombre: 'Chivas Regal 18', familia: 'LICORES', subfamilia: 'WHISKY', casa: 'PERNOD RICARD', alcohol: 40, cantidad: 89, ventas: 106800, propina: 7800 },
  { id: 8, codigo: 'BACA-005', nombre: 'Patron Silver', familia: 'LICORES', subfamilia: 'TEQUILA', casa: 'BACARDI', alcohol: 40, cantidad: 105, ventas: 99750, propina: 7200 },
  { id: 9, codigo: 'VINO-004', nombre: 'Moët & Chandon', familia: 'VINOS', subfamilia: 'CHAMPAGNE', casa: 'LVMH', alcohol: 12, cantidad: 52, ventas: 93600, propina: 8900 },
  { id: 10, codigo: 'CERV-001', nombre: 'Corona Extra', familia: 'CERVEZAS', subfamilia: 'CLARA', casa: 'GRUPO MODELO', alcohol: 4.5, cantidad: 1856, ventas: 83520, propina: 4200 },
];

export default function VentasProductoPage({ unidadSeleccionada }) {
  const [productos, setProductos] = useState(FALLBACK_PRODUCTOS);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('ventas');
  const [sortDir, setSortDir] = useState('desc');
  const [filtroFamilia, setFiltroFamilia] = useState('todas');

  useEffect(() => {
    fetchProductos();
  }, [unidadSeleccionada]);

  const fetchProductos = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/inteligencia/productos?unidad=${unidadSeleccionada}`,
        { credentials: 'include' }
      );
      if (response.ok) {
        const data = await response.json();
        if (data.length > 0) setProductos(data);
      }
    } catch (error) {
      console.log('[Productos] Usando fallback');
    } finally {
      setLoading(false);
    }
  };

  const familias = [...new Set(productos.map(p => p.familia))];

  const filteredProducts = productos
    .filter(p => 
      (filtroFamilia === 'todas' || p.familia === filtroFamilia) &&
      (p.nombre.toLowerCase().includes(search.toLowerCase()) || 
       p.codigo.toLowerCase().includes(search.toLowerCase()))
    )
    .sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      return sortDir === 'desc' ? bVal - aVal : aVal - bVal;
    });

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortDir(sortDir === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setSortDir('desc');
    }
  };

  const formatMoney = (val) => `$${val.toLocaleString()}`;

  return (
    <div className="space-y-6" data-testid="ventas-producto-page">
      {/* Header con filtros */}
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar producto..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:outline-none w-64"
            />
          </div>
          
          <select
            value={filtroFamilia}
            onChange={(e) => setFiltroFamilia(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:outline-none"
          >
            <option value="todas">Todas las Familias</option>
            {familias.map(f => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>

        <button className="flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg text-sm transition-colors">
          <Download className="h-4 w-4" />
          Exportar
        </button>
      </div>

      {/* Tabla */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left text-xs font-medium text-slate-400 px-4 py-3">CÓDIGO</th>
                <th className="text-left text-xs font-medium text-slate-400 px-4 py-3">PRODUCTO</th>
                <th className="text-left text-xs font-medium text-slate-400 px-4 py-3">FAMILIA</th>
                <th className="text-left text-xs font-medium text-slate-400 px-4 py-3">CASA</th>
                <th className="text-center text-xs font-medium text-slate-400 px-4 py-3">ALCOHOL</th>
                <th 
                  className="text-right text-xs font-medium text-slate-400 px-4 py-3 cursor-pointer hover:text-white"
                  onClick={() => handleSort('cantidad')}
                >
                  <div className="flex items-center justify-end gap-1">
                    CANTIDAD
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th 
                  className="text-right text-xs font-medium text-slate-400 px-4 py-3 cursor-pointer hover:text-white"
                  onClick={() => handleSort('ventas')}
                >
                  <div className="flex items-center justify-end gap-1">
                    VENTAS
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">PROPINA</th>
              </tr>
            </thead>
            <tbody>
              {filteredProducts.map((prod, idx) => (
                <tr 
                  key={prod.id}
                  className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="text-xs font-mono text-slate-500">{prod.codigo}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-white">{prod.nombre}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <span className="text-xs text-slate-300">{prod.familia}</span>
                      <p className="text-xs text-slate-500">{prod.subfamilia}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-purple-500/20 text-purple-300 text-xs rounded">
                      {prod.casa}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {prod.alcohol > 0 ? (
                      <span className="text-xs text-amber-400">{prod.alcohol}%</span>
                    ) : (
                      <span className="text-xs text-slate-500">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm text-slate-300">{prod.cantidad.toLocaleString()}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm font-semibold text-emerald-400">{formatMoney(prod.ventas)}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm text-blue-400">{formatMoney(prod.propina)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Footer */}
        <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between">
          <span className="text-sm text-slate-400">
            Mostrando {filteredProducts.length} de {productos.length} productos
          </span>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-slate-400">
              Total Ventas: <span className="text-emerald-400 font-semibold">
                {formatMoney(filteredProducts.reduce((a, b) => a + b.ventas, 0))}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
