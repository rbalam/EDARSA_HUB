#!/bin/sh
set -eu

SCRIPT_DIR="$(
    CDPATH= cd -- "$(dirname -- "$0")" &&
    pwd
)"

ROOT="$(
    CDPATH= cd -- "$SCRIPT_DIR/../.." &&
    pwd
)"

VERSIONS_FILE="$SCRIPT_DIR/versions.lock"

[ -f "$VERSIONS_FILE" ] || {
    echo "VERSIONS_FILE_CHECK=FAIL"
    exit 1
}

[ -d "$ROOT/third_party/agent-reach" ] || {
    echo "VENDORED_SOURCE_CHECK=FAIL"
    exit 1
}

. "$VERSIONS_FILE"

IMAGE="${IMAGE_REPOSITORY}:${IMAGE_TAG}"

command -v docker >/dev/null 2>&1 || {
    echo "DOCKER_COMMAND_CHECK=FAIL"
    exit 1
}

docker info >/dev/null 2>&1 || {
    echo "DOCKER_DAEMON_CHECK=FAIL"
    exit 1
}

BUILD_CONTEXT="$(mktemp -d)"

cleanup() {
    rm -rf "$BUILD_CONTEXT"
}

trap cleanup EXIT INT TERM

mkdir -p \
    "$BUILD_CONTEXT/infra/agent-reach" \
    "$BUILD_CONTEXT/third_party"

cp -a \
    "$SCRIPT_DIR/." \
    "$BUILD_CONTEXT/infra/agent-reach/"

cp -a \
    "$ROOT/third_party/agent-reach" \
    "$BUILD_CONTEXT/third_party/agent-reach"

test -f \
    "$BUILD_CONTEXT/infra/agent-reach/Dockerfile"

test -f \
    "$BUILD_CONTEXT/infra/agent-reach/requirements.lock"

test -f \
    "$BUILD_CONTEXT/infra/agent-reach/healthcheck.sh"

test -f \
    "$BUILD_CONTEXT/third_party/agent-reach/pyproject.toml"

echo "===== BUILD CANONICO ====="
echo "IMAGE=$IMAGE"
echo "BUILD_CONTEXT=$BUILD_CONTEXT"
echo "BUILD_CONTEXT_SCOPE=infra/agent-reach,third_party/agent-reach"
echo "PYTHON_IMAGE=$PYTHON_IMAGE"
echo "DENO_IMAGE=$DENO_IMAGE"
echo "AGENT_REACH_VERSION=$AGENT_REACH_VERSION"
echo "DENO_VERSION=$DENO_VERSION"
echo "YTDLP_VERSION=$YTDLP_VERSION"
echo "YTDLP_EJS_VERSION=$YTDLP_EJS_VERSION"
echo "PIP_VERSION=$PIP_VERSION"

docker build \
    --pull \
    --build-arg "PYTHON_IMAGE=$PYTHON_IMAGE" \
    --build-arg "DENO_IMAGE=$DENO_IMAGE" \
    --build-arg "AGENT_REACH_VERSION=$AGENT_REACH_VERSION" \
    --build-arg "DENO_VERSION=$DENO_VERSION" \
    --build-arg "YTDLP_VERSION=$YTDLP_VERSION" \
    --build-arg "YTDLP_EJS_VERSION=$YTDLP_EJS_VERSION" \
    --build-arg "PIP_VERSION=$PIP_VERSION" \
    --file \
    "$BUILD_CONTEXT/infra/agent-reach/Dockerfile" \
    --tag "$IMAGE" \
    "$BUILD_CONTEXT"

echo
echo "===== HEALTHCHECK DE IMAGEN ====="

docker run \
    --rm \
    --entrypoint \
    /usr/local/bin/agent-reach-healthcheck \
    "$IMAGE"

echo
echo "===== IDENTIDAD DE IMAGEN ====="

IMAGE_ID="$(
    docker image inspect \
        --format '{{.Id}}' \
        "$IMAGE"
)"

IMAGE_USER="$(
    docker image inspect \
        --format '{{.Config.User}}' \
        "$IMAGE"
)"

IMAGE_ENTRYPOINT="$(
    docker image inspect \
        --format '{{json .Config.Entrypoint}}' \
        "$IMAGE"
)"

if [ "$IMAGE_USER" != "edarsa-agent-reach" ]; then
    echo "IMAGE_NON_ROOT_CHECK=FAIL"
    echo "IMAGE_USER=$IMAGE_USER"
    exit 1
fi

echo "IMAGE_ID=$IMAGE_ID"
echo "IMAGE_USER=$IMAGE_USER"
echo "IMAGE_ENTRYPOINT=$IMAGE_ENTRYPOINT"
echo "IMAGE_BUILD=PASS"
echo "IMAGE_HEALTHCHECK=PASS"
echo "IMAGE_NON_ROOT_CHECK=PASS"
echo "MINIMAL_BUILD_CONTEXT=PASS"
echo "IMAGE_PUSHED=0"
echo "DEPLOY_EXECUTED=0"
