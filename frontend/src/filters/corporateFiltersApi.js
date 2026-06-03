const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

export function getEdarsaToken() {
  return (
    sessionStorage.getItem("edarsa_memory_token") ||
    localStorage.getItem("token") ||
    sessionStorage.getItem("token") ||
    localStorage.getItem("access_token") ||
    sessionStorage.getItem("access_token") ||
    ""
  );
}

export async function fetchCorporateFiltersBootstrap(scope) {
  const token = getEdarsaToken();

  const response = await fetch(
    `${BACKEND_URL}/api/corporate-filters/bootstrap?scope=${encodeURIComponent(scope)}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Error HTTP ${response.status} cargando filtros corporativos`);
  }

  return response.json();
}

export async function resolveCorporateFilters(scope, selected, requestedFilters) {
  const token = getEdarsaToken();

  const response = await fetch(`${BACKEND_URL}/api/corporate-filters/resolve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      scope,
      selected,
      requested_filters: requestedFilters || []
    })
  });

  if (!response.ok) {
    throw new Error(`Error HTTP ${response.status} resolviendo filtros corporativos`);
  }

  return response.json();
}
