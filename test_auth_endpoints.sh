#!/bin/bash
set -e

if [ -z "$TOKEN" ]; then
  echo "ERROR: falta TOKEN. Ejecuta: export TOKEN='...'"
  exit 1
fi

for url in \
  "http://localhost:8001/api/auth/me" \
  "http://localhost:8001/api/auth/me/menu-permissions" \
  "http://localhost:8001/api/unidades-negocio" \
  "http://localhost:8001/api/corporate-filters/bootstrap"
do
  echo ""
  echo "### $url"
  curl -sS -m 20 \
    -H "Authorization: Bearer $TOKEN" \
    -w "\nHTTP:%{http_code} TIME:%{time_total}\n" \
    "$url" | head -c 3000
  echo ""
done
