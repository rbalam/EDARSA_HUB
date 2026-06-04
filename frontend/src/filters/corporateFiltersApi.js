const RAW_BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

/**
 * En preview/deploy, si REACT_APP_BACKEND_URL causa 502, se intenta fallback same-origin.
 * Orden:
 * 1. REACT_APP_BACKEND_URL si existe.
 * 2. Same-origin relativo "".
 */
function getCandidateBaseUrls() {
  const urls = [];

  if (RAW_BACKEND_URL && RAW_BACKEND_URL.trim()) {
    urls.push(RAW_BACKEND_URL.replace(/\/$/, ""));
  }

  urls.push("");

  return Array.from(new Set(urls));
}

export function getEdarsaToken() {
  return (
    sessionStorage.getItem("edarsa_memory_token") ||
    sessionStorage.getItem("access_token") ||
    sessionStorage.getItem("token") ||
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    ""
  );
}

async function fetchWithFallback(path, options = {}) {
  const token = getEdarsaToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };

  let lastError = null;

  for (const baseUrl of getCandidateBaseUrls()) {
    const url = `${baseUrl}${path}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        credentials: "include"  // Incluir cookies httpOnly para autenticación
      });

      if (response.ok) {
        return response.json();
      }

      lastError = new Error(`HTTP ${response.status} al llamar ${url}`);

      // Si REACT_APP_BACKEND_URL dio 502/503/504, probar same-origin.
      if (![502, 503, 504].includes(response.status)) {
        throw lastError;
      }
    } catch (error) {
      lastError = error;
      // intenta siguiente baseUrl
    }
  }

  throw lastError || new Error("No se pudo conectar a Corporate Filters");
}

export async function fetchCorporateFiltersBootstrap(scope) {
  return fetchWithFallback(
    `/api/corporate-filters/bootstrap?scope=${encodeURIComponent(scope)}`,
    { method: "GET" }
  );
}

export async function resolveCorporateFilters(scope, selected, requestedFilters) {
  return fetchWithFallback(
    `/api/corporate-filters/resolve`,
    {
      method: "POST",
      body: JSON.stringify({
        scope,
        selected: selected || {},
        requested_filters: requestedFilters || []
      })
    }
  );
}
