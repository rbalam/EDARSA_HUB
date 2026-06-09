/**
 * Ventas por Producto - Análisis detallado (datos reales, sin mock).
 * Fuente: /api/inteligencia/productos (Comercial_Inteligencia_VentasDetalleProducto).
 */
import React, { useState, useEffect } from 'react';
import { Search, ArrowUpDown } from 'lucide-react';
import { apiGet, ESTADO } from '../api/client';
import { EstadoVacio } from '../components/EstadoVacio';

export default function VentasProductoPage({ unidadSeleccionada }) {
  const [productos, setProductos] = useState([]);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('ventas');
  const [sortDir, setSortDir] = useState('desc');
  const [filtroFamilia, setFiltroFamilia] = useState('todas');

  useEffect(() => {
    fetchProductos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadSeleccionada]);

  const fetchProductos = async () => {
    setEstado(ESTADO.CARGANDO);
    const { estado: est, data } = await apiGet('/inteligencia/productos', {
      unidad: unidadSeleccionada, limit: 200,
    });
    if (est !== ESTADO.OK || !data || data.success === false) {
      setProductos([]);
      setEstado(est === ESTADO.OK ? ESTADO.ERROR : est);
      return;
    }
    const lista = data.productos || [];
    setProductos(lista);
    setEstado(lista.length ? ESTADO.OK : ESTADO.SIN_DATOS);
  };

  const familias = [...new Set(productos.map(p => p.familia).filter(Boolean))];

  const filteredProducts = productos
    .filter(p =>
      (filtroFamilia === 'todas' || p.familia === filtroFamilia) &&
      ((p.nombre || '').toLowerCase().includes(search.toLowerCase()) ||
       (p.codigo || '').toLowerCase().includes(search.toLowerCase()))
    )
    .sort((a, b) => {
      const aVal = a[sortBy], bVal = b[sortBy];
      return sortDir === 'desc' ? bVal - aVal : aVal - bVal;
    });

  const handleSort = (field) => {
    if (sortBy === field) setSortDir(sortDir === 'desc' ? 'asc' : 'desc');
    else { setSortBy(field); setSortDir('desc'); }
  };

  const formatMoney = (val) => `$${Number(val || 0).toLocaleString('es-MX')}`;

  return (
    <div className="space-y-6" data-testid="ventas-producto-page">
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input type="text" placeholder="Buscar producto..." value={search} onChange={(e) => setSearch(e.target.value)}
              data-testid="producto-search"
              className="pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:outline-none w-64" />
          </div>
          <select value={filtroFamilia} onChange={(e) => setFiltroFamilia(e.target.value)} data-testid="producto-familia-filter"
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:outline-none">
            <option value="todas">Todas las Familias</option>
            {familias.map(f => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>
      </div>

      {estado !== ESTADO.OK ? (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl">
          <EstadoVacio estado={estado} testid="ventas-producto-estado" />
        </div>
      ) : (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left text-xs font-medium text-slate-400 px-4 py-3">CÓDIGO</th>
                  <th className="text-left text-xs font-medium text-slate-400 px-4 py-3">PRODUCTO</th>
                  <th className="text-left text-xs font-medium text-slate-400 px-4 py-3">FAMILIA</th>
                  <th className="text-center text-xs font-medium text-slate-400 px-4 py-3">ALCOHOL</th>
                  <th className="text-right text-xs font-medium text-slate-400 px-4 py-3 cursor-pointer hover:text-white" onClick={() => handleSort('cantidad')}>
                    <div className="flex items-center justify-end gap-1">CANTIDAD <ArrowUpDown className="h-3 w-3" /></div>
                  </th>
                  <th className="text-right text-xs font-medium text-slate-400 px-4 py-3 cursor-pointer hover:text-white" onClick={() => handleSort('ventas')}>
                    <div className="flex items-center justify-end gap-1">VENTAS <ArrowUpDown className="h-3 w-3" /></div>
                  </th>
                  <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">PROPINA</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map((prod) => (
                  <tr key={prod.id} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3"><span className="text-xs font-mono text-slate-500">{prod.codigo || '—'}</span></td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-white">{prod.nombre}</span>
                      {prod.subfamilia && <p className="text-xs text-slate-500">{prod.subfamilia}</p>}
                    </td>
                    <td className="px-4 py-3"><span className="text-xs text-slate-300">{prod.familia || '—'}</span></td>
                    <td className="px-4 py-3 text-center">
                      {prod.alcohol > 0 ? <span className="text-xs text-amber-400">{prod.alcohol}%</span> : <span className="text-xs text-slate-500">—</span>}
                    </td>
                    <td className="px-4 py-3 text-right"><span className="text-sm text-slate-300">{Number(prod.cantidad || 0).toLocaleString()}</span></td>
                    <td className="px-4 py-3 text-right"><span className="text-sm font-semibold text-emerald-400">{formatMoney(prod.ventas)}</span></td>
                    <td className="px-4 py-3 text-right"><span className="text-sm text-blue-400">{formatMoney(prod.propina)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between">
            <span className="text-sm text-slate-400">Mostrando {filteredProducts.length} de {productos.length} productos</span>
            <span className="text-sm text-slate-400">Total Ventas:{' '}
              <span className="text-emerald-400 font-semibold">{formatMoney(filteredProducts.reduce((a, b) => a + Number(b.ventas || 0), 0))}</span>
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
