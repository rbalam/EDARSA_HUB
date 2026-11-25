import React, { useRef, useState } from "react";

/**
 * Formulario movil Cajas V1 sin backend simulado.
 * El padre debe proveer catalogos ya filtrados por el servidor y onRegistrar
 * conectado al servicio SQL autorizado; no obtiene permisos del navegador.
 * No modifica el POS ni registra incidencias mientras no haya onRegistrar.
 */
export default function IncidenciaCajaForm({
  tipos = [],
  motivos = [],
  contexto = null,
  onRegistrar,
  guardando = false,
}) {
  const [tipo, setTipo] = useState("");
  const [motivo, setMotivo] = useState("");
  const [cuentaFolio, setCuentaFolio] = useState("");
  const [importe, setImporte] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [error, setError] = useState("");
  const solicitudId = useRef(null);

  const catalogoMotivos = motivos.filter((m) =>
    m.activo === true && (!m.tipo || m.tipo === tipo)
  );
  const habilitado = Boolean(
    typeof onRegistrar === "function" && contexto?.autorizado === true &&
    tipo && motivo && descripcion.trim() &&
    tipos.some((t) => t.codigo === tipo && t.activo === true) &&
    catalogoMotivos.some((m) => m.codigo === motivo) &&
    (!importe || (Number.isFinite(Number(importe)) && Number(importe) >= 0))
  );

  async function registrar(event) {
    event.preventDefault();
    if (!habilitado || guardando) return;
    setError("");
    try {
      if (!solicitudId.current) {
        solicitudId.current = window.crypto?.randomUUID?.();
      }
      if (!solicitudId.current) {
        setError("Este dispositivo no puede generar una clave segura. Intenta con otro navegador.");
        return;
      }
      const result = await onRegistrar({
        tipo,
        motivo_codigo: motivo,
        cuenta_folio: cuentaFolio.trim() || null,
        importe_involucrado: importe ? Number(importe) : null,
        descripcion: descripcion.trim(),
        solicitud_idempotencia: solicitudId.current,
      });
      if (!result?.folio) {
        setError("No se confirmó el registro. Verifica su estado antes de reenviar.");
        return;
      }
      solicitudId.current = null;
      setTipo(""); setMotivo(""); setCuentaFolio(""); setImporte(""); setDescripcion("");
    } catch {
      setError("No se confirmó el registro. Verifica el expediente antes de reintentar.");
    }
  }

  const bloqueado = !contexto?.autorizado || typeof onRegistrar !== "function";
  return (
    <form onSubmit={registrar} aria-label="Registrar incidencia de caja" style={{
      width: "100%", maxWidth: 460, margin: "0 auto", display: "grid",
      gap: 14, padding: 16,
    }}>
      <h2 style={{ margin: 0 }}>Nueva incidencia de caja</h2>
      <p style={{ margin: 0 }}>
        {contexto?.nombreUnidad || "Selecciona una unidad autorizada desde EDARSAHUB"}
      </p>
      {bloqueado && <p role="status">
        Registro no disponible hasta confirmar permisos y conexión segura con EDARSAHUB.
      </p>}
      <label>¿Qué ocurrió?
        <select value={tipo} onChange={(e) => {setTipo(e.target.value); setMotivo("");}}
          required disabled={bloqueado || guardando}>
          <option value="">Selecciona un tipo</option>
          {tipos.filter((t) => t.activo).map((t) =>
            <option key={t.codigo} value={t.codigo}>{t.nombre}</option>)}
        </select>
      </label>
      <label>Motivo
        <select value={motivo} onChange={(e) => setMotivo(e.target.value)}
          required disabled={bloqueado || guardando || !tipo}>
          <option value="">Selecciona un motivo</option>
          {catalogoMotivos.map((m) =>
            <option key={m.codigo} value={m.codigo}>{m.nombre}</option>)}
        </select>
      </label>
      <label>Folio de cuenta (opcional)
        <input value={cuentaFolio} onChange={(e) => setCuentaFolio(e.target.value)}
          maxLength={100} disabled={bloqueado || guardando} />
      </label>
      <label>Importe involucrado (opcional)
        <input type="number" min="0" step="0.01" inputMode="decimal"
          value={importe} onChange={(e) => setImporte(e.target.value)}
          disabled={bloqueado || guardando} />
      </label>
      <label>Describe lo sucedido
        <textarea value={descripcion} onChange={(e) => setDescripcion(e.target.value)}
          required maxLength={2000} rows={4} disabled={bloqueado || guardando} />
      </label>
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={!habilitado || guardando}>
        {guardando ? "Registrando..." : "Registrar incidencia"}
      </button>
      <small>El registro no cancela cuentas ni modifica operaciones del POS.</small>
    </form>
  );
}
