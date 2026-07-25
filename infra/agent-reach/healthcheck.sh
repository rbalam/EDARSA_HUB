#!/bin/sh
set -eu

fail() {
    echo "AGENT_REACH_HEALTHCHECK=FAIL"
    echo "DETAIL=$1"
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 ||
        fail "Comando no encontrado: $1"
}

require_command agent-reach
require_command python
require_command yt-dlp
require_command deno
require_command ffmpeg
require_command ffprobe
require_command curl

[ "$(id -u)" -ne 0 ] ||
    fail "El runtime no debe ejecutarse como root"

[ -n "${EDARSA_AGENT_REACH_VERSION:-}" ] ||
    fail "EDARSA_AGENT_REACH_VERSION no definido"

[ -n "${EDARSA_DENO_VERSION:-}" ] ||
    fail "EDARSA_DENO_VERSION no definido"

[ -n "${EDARSA_YTDLP_VERSION:-}" ] ||
    fail "EDARSA_YTDLP_VERSION no definido"

[ -n "${EDARSA_YTDLP_EJS_VERSION:-}" ] ||
    fail "EDARSA_YTDLP_EJS_VERSION no definido"

AGENT_VERSION="$(agent-reach version)"
DENO_VERSION="$(deno --version | sed -n '1s/^deno //p')"
YTDLP_VERSION="$(yt-dlp --version)"

[ "$AGENT_VERSION" = \
  "Agent Reach v${EDARSA_AGENT_REACH_VERSION}" ] ||
    fail "Agent-Reach inesperado: $AGENT_VERSION"

[ "$DENO_VERSION" = "$EDARSA_DENO_VERSION" ] ||
    fail "Deno inesperado: $DENO_VERSION"

[ "$YTDLP_VERSION" = "$EDARSA_YTDLP_VERSION" ] ||
    fail "yt-dlp inesperado: $YTDLP_VERSION"

python - <<'PY_CHECK'
from importlib.metadata import version

expected = {
    "agent-reach": "1.5.0",
    "yt-dlp": "2026.7.4",
    "yt-dlp-ejs": "0.8.0",
}

for package, required in expected.items():
    actual = version(package)

    if actual != required:
        raise SystemExit(
            f"{package}: esperado={required}, actual={actual}"
        )
PY_CHECK

ffmpeg -version >/dev/null 2>&1 ||
    fail "ffmpeg no responde"

ffprobe -version >/dev/null 2>&1 ||
    fail "ffprobe no responde"

CONFIG_FILE="${XDG_CONFIG_HOME}/yt-dlp/config"

[ -f "$CONFIG_FILE" ] ||
    fail "Configuracion de yt-dlp no encontrada"

grep -qxF \
    -- \
    '--js-runtimes deno:/usr/local/bin/deno' \
    "$CONFIG_FILE" ||
    fail "Runtime Deno no configurado"

grep -qxF \
    -- '--no-remote-components' \
    "$CONFIG_FILE" ||
    fail "Componentes remotos no bloqueados"

grep -qxF \
    -- '--no-update' \
    "$CONFIG_FILE" ||
    fail "Actualizaciones dinamicas no bloqueadas"

[ -d "$HOME" ] ||
    fail "HOME no existe"

[ -w "$HOME" ] ||
    fail "HOME no es escribible"

[ -d /work ] ||
    fail "/work no existe"

[ -w /work ] ||
    fail "/work no es escribible"

echo "AGENT_REACH_HEALTHCHECK=PASS"
echo "AGENT_REACH_VERSION=$AGENT_VERSION"
echo "DENO_VERSION=$DENO_VERSION"
echo "YTDLP_VERSION=$YTDLP_VERSION"
echo "FFMPEG_CHECK=PASS"
echo "FFPROBE_CHECK=PASS"
echo "NON_ROOT_CHECK=PASS"
echo "RUNTIME_CONFIG_CHECK=PASS"
