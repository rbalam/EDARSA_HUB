import React, { useEffect, useRef, useState } from 'react';
import { Sparkles, Plus, Send, Trash2, Loader2, Bot, User } from 'lucide-react';
import { toast } from 'sonner';
import {
  listarSesiones,
  crearSesion,
  obtenerMensajes,
  eliminarSesion,
  enviarMensaje,
} from '../services/iaAssistantApi';

const SUGERENCIAS = [
  'Resume estos datos de ventas y dame 3 insights',
  'Redacta un correo formal para un proveedor',
  '¿Qué KPIs debería vigilar en un restaurante?',
];

export default function IAAsistente() {
  const [sesiones, setSesiones] = useState([]);
  const [sesionActiva, setSesionActiva] = useState(null);
  const [mensajes, setMensajes] = useState([]);
  const [input, setInput] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [cargandoSesiones, setCargandoSesiones] = useState(true);
  const scrollRef = useRef(null);

  const cargarSesiones = async () => {
    try {
      const data = await listarSesiones();
      setSesiones(data.sesiones || []);
      return data.sesiones || [];
    } catch (e) {
      toast.error('No se pudieron cargar las conversaciones');
      return [];
    } finally {
      setCargandoSesiones(false);
    }
  };

  useEffect(() => {
    cargarSesiones();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [mensajes, enviando]);

  const abrirSesion = async (sesionId) => {
    setSesionActiva(sesionId);
    setMensajes([]);
    try {
      const data = await obtenerMensajes(sesionId);
      setMensajes(data.mensajes || []);
    } catch (e) {
      toast.error('No se pudieron cargar los mensajes');
    }
  };

  const nuevaConversacion = async () => {
    try {
      const data = await crearSesion();
      await cargarSesiones();
      setSesionActiva(data.sesion.sesion_id);
      setMensajes([]);
    } catch (e) {
      toast.error('No se pudo crear la conversación');
    }
  };

  const borrarSesion = async (e, sesionId) => {
    e.stopPropagation();
    try {
      await eliminarSesion(sesionId);
      if (sesionActiva === sesionId) {
        setSesionActiva(null);
        setMensajes([]);
      }
      cargarSesiones();
    } catch (err) {
      toast.error('No se pudo eliminar');
    }
  };

  const enviar = async (textoDirecto) => {
    const texto = (textoDirecto ?? input).trim();
    if (!texto || enviando) return;

    let sid = sesionActiva;
    if (!sid) {
      try {
        const data = await crearSesion();
        sid = data.sesion.sesion_id;
        setSesionActiva(sid);
      } catch (e) {
        toast.error('No se pudo iniciar la conversación');
        return;
      }
    }

    setInput('');
    setMensajes((prev) => [...prev, { rol: 'user', contenido: texto }]);
    setEnviando(true);
    try {
      const res = await enviarMensaje(sid, texto);
      setMensajes((prev) => [...prev, { rol: 'assistant', contenido: res.respuesta }]);
      cargarSesiones();
    } catch (e) {
      toast.error(e.message || 'Error al obtener respuesta');
      setMensajes((prev) => [
        ...prev,
        { rol: 'assistant', contenido: '⚠️ No fue posible generar una respuesta. Intenta de nuevo.' },
      ]);
    } finally {
      setEnviando(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      enviar();
    }
  };

  return (
    <div className="flex h-[calc(100vh-120px)] gap-4" data-testid="ia-asistente-page">
      {/* Sidebar de conversaciones */}
      <aside className="hidden md:flex w-72 flex-col rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="p-4 border-b border-slate-100">
          <button
            data-testid="ia-nueva-conversacion-btn"
            onClick={nuevaConversacion}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-slate-700"
          >
            <Plus className="h-4 w-4" /> Nueva conversación
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1" data-testid="ia-lista-sesiones">
          {cargandoSesiones ? (
            <div className="flex justify-center py-8 text-slate-400">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          ) : sesiones.length === 0 ? (
            <p className="px-3 py-6 text-center text-sm text-slate-400">
              Aún no hay conversaciones
            </p>
          ) : (
            sesiones.map((s) => (
              <div
                key={s.sesion_id}
                data-testid={`ia-sesion-${s.sesion_id}`}
                onClick={() => abrirSesion(s.sesion_id)}
                className={`group flex cursor-pointer items-center justify-between rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  sesionActiva === s.sesion_id ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <span className="truncate pr-2">{s.titulo}</span>
                <button
                  data-testid={`ia-eliminar-sesion-${s.sesion_id}`}
                  onClick={(e) => borrarSesion(e, s.sesion_id)}
                  className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 transition-opacity"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Área de chat */}
      <section className="flex flex-1 flex-col rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <header className="flex items-center gap-3 border-b border-slate-100 px-6 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-slate-900">Asistente IA</h1>
            <p className="text-xs text-slate-400">OpenAI GPT-5.5 · EDARSA HUB</p>
          </div>
        </header>

        <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6 space-y-6" data-testid="ia-mensajes">
          {mensajes.length === 0 && !enviando ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
                <Bot className="h-7 w-7" />
              </div>
              <h2 className="text-lg font-semibold text-slate-800">¿En qué te ayudo hoy?</h2>
              <p className="mt-1 mb-6 text-sm text-slate-400 max-w-md">
                Conversación general, análisis de datos que compartas o generación de textos.
              </p>
              <div className="flex flex-wrap justify-center gap-2 max-w-lg">
                {SUGERENCIAS.map((s, i) => (
                  <button
                    key={i}
                    data-testid={`ia-sugerencia-${i}`}
                    onClick={() => enviar(s)}
                    className="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-600 transition-colors hover:border-indigo-300 hover:text-indigo-600"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            mensajes.map((m, i) => (
              <div key={i} className={`flex gap-3 ${m.rol === 'user' ? 'flex-row-reverse' : ''}`}>
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                    m.rol === 'user' ? 'bg-slate-900 text-white' : 'bg-indigo-600 text-white'
                  }`}
                >
                  {m.rol === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>
                <div
                  className={`max-w-[75%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    m.rol === 'user'
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-50 text-slate-800 border border-slate-100'
                  }`}
                >
                  {m.contenido}
                </div>
              </div>
            ))
          )}
          {enviando && (
            <div className="flex gap-3" data-testid="ia-typing">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white">
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex items-center gap-1 rounded-2xl bg-slate-50 border border-slate-100 px-4 py-3">
                <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                <span className="text-sm text-slate-400">Pensando…</span>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-slate-100 px-6 py-4">
          <div className="flex items-end gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 focus-within:border-indigo-300">
            <textarea
              data-testid="ia-input"
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Escribe tu mensaje…"
              className="flex-1 resize-none bg-transparent py-2 text-sm text-slate-800 outline-none placeholder:text-slate-400 max-h-40"
            />
            <button
              data-testid="ia-enviar-btn"
              onClick={() => enviar()}
              disabled={enviando || !input.trim()}
              className="mb-1 flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white transition-colors hover:bg-indigo-500 disabled:opacity-40"
            >
              {enviando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
