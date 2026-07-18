/**
 * Cliente del Asistente IA.
 * Usa exclusivamente el cliente Axios canónico.
 */
import api from '../lib/api';

const unwrap = async (promise) => {
  const response = await promise;
  return response.data;
};

export const iaHealth = () =>
  unwrap(
    api.get('/ia/health')
  );

export const listarSesiones = () =>
  unwrap(
    api.get('/ia/sesiones')
  );

export const crearSesion = (
  titulo = null
) =>
  unwrap(
    api.post(
      '/ia/sesiones',
      { titulo }
    )
  );

export const obtenerMensajes = (
  sesionId
) =>
  unwrap(
    api.get(
      `/ia/sesiones/${
        encodeURIComponent(sesionId)
      }/mensajes`
    )
  );

export const eliminarSesion = (
  sesionId
) =>
  unwrap(
    api.delete(
      `/ia/sesiones/${
        encodeURIComponent(sesionId)
      }`
    )
  );

export const enviarMensaje = (
  sesionId,
  mensaje
) =>
  unwrap(
    api.post(
      '/ia/chat',
      {
        sesion_id: sesionId,
        mensaje,
      },
      {
        timeout: 70000,
      }
    )
  );

export default {
  iaHealth,
  listarSesiones,
  crearSesion,
  obtenerMensajes,
  eliminarSesion,
  enviarMensaje,
};
