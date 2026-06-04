export function resetPreviewFilterCache() {
  const hostname = window.location.hostname || "";

  const isPreview =
    hostname.includes("preview") ||
    hostname.includes("emergentagent") ||
    hostname.includes("localhost");

  if (!isPreview) return;

  const protectedKeys = new Set([
    "edarsa_memory_token",
    "access_token",
    "refresh_token",
    "token",
    "user"
  ]);

  const prefixesToClear = [
    "edarsa_filter_",
    "corporate_filter_",
    "dashboard_filter_"
  ];

  for (let i = sessionStorage.length - 1; i >= 0; i--) {
    const key = sessionStorage.key(i);
    if (!key || protectedKeys.has(key)) continue;

    if (prefixesToClear.some(prefix => key.startsWith(prefix))) {
      sessionStorage.removeItem(key);
    }
  }

  for (let i = localStorage.length - 1; i >= 0; i--) {
    const key = localStorage.key(i);
    if (!key || protectedKeys.has(key)) continue;

    if (prefixesToClear.some(prefix => key.startsWith(prefix))) {
      localStorage.removeItem(key);
    }
  }
}
