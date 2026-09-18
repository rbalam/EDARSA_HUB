import React, { useEffect, useState } from 'react';
import api from '@/lib/api';

export default function LotesProveedorPage() {
  const [rows, setRows] = useState([]);
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function loadData() {
    setLoading(true);
    setError('');

    try {
      const lotesRes = await api.get('/tablajeria/lotes-proveedor/rendimientos?limit=100&offset=0');
      const reclamosRes = await api.get('/tablajeria/reclamos-proveedor?limit=100');
      const nextRows = lotesRes.data && lotesRes.data.rendimientos ? lotesRes.data.rendimientos : [];
      const nextClaims = reclamosRes.data && reclamosRes.data.reclamos ? reclamosRes.data.reclamos : [];
      setRows(nextRows);
      setClaims(nextClaims);
    } catch (err) {
      setError('No fue posible cargar lotes proveedor.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(function init() {
    loadData();
  }, []);

  return (
    <div data-testid="tablajeria-lotes-proveedor" style={{ padding: 24 }}>
      <header>
        <h1>Lotes proveedor</h1>
        <p>Rendimiento, desviaciones, impacto economico y reclamos por lote de compra.</p>
        <button type="button" onClick={loadData} disabled={loading}>Actualizar</button>
      </header>

      {error ? <p role="alert">{error}</p> : null}

      <section>
        <h2>Rendimientos por lote</h2>
        <p>Total de lotes: {rows.length}</p>
        <ul>
          {rows.map(function renderRow(row, index) {
            const key = row.LoteRendimientoID || row.LoteProveedor || index;
            return (
              <li key={key}>
                <strong>{row.LoteProveedor || row.LoteInterno || 'Sin lote'}</strong>
                <span> - {row.ProveedorNombre || 'Sin proveedor'} - {row.Semaforo || 'SIN_DATOS'}</span>
              </li>
            );
          })}
        </ul>
        {!rows.length && !loading ? <p>Sin registros.</p> : null}
      </section>

      <section>
        <h2>Reclamos proveedor</h2>
        <p>Total de reclamos: {claims.length}</p>
        <ul>
          {claims.map(function renderClaim(claim, index) {
            const key = claim.ReclamoProveedorID || claim.FolioReclamo || index;
            return (
              <li key={key}>
                <strong>{claim.FolioReclamo || 'Sin folio'}</strong>
                <span> - {claim.ProveedorNombre || 'Sin proveedor'} - {claim.Estatus || 'SIN_ESTATUS'}</span>
              </li>
            );
          })}
        </ul>
        {!claims.length && !loading ? <p>Sin reclamos.</p> : null}
      </section>
    </div>
  );
}
