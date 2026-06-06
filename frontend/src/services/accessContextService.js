const API_URL = process.env.REACT_APP_BACKEND_URL;

function getAuthHeaders() {
  const token = localStorage.getItem("token") || sessionStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function fetchAccessContext(unidadNegocioId = null) {
  const url = new URL(`${API_URL}/api/auth/access-context`);
  if (unidadNegocioId) {
    url.searchParams.set("unidad_negocio_id", unidadNegocioId);
  }

  const res = await fetch(url.toString(), {
    method: "GET",
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Error obteniendo contexto de acceso");
  }

  return res.json();
}

export async function selectAccessUnit(unidadNegocioId) {
  const res = await fetch(`${API_URL}/api/auth/access-context/select-unit`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ unidad_negocio_id: unidadNegocioId }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Error seleccionando unidad");
  }

  return res.json();
}
