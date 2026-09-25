#!/usr/bin/env bash
set -euo pipefail

MIRROR_SYNC_GUARD="/app/tools/mirror_sync/mirror_sync_guard.sh"

test -r "$MIRROR_SYNC_GUARD" || {
    echo "ABORT=MIRROR_SYNC_GUARD_MISSING"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 90
}

. "$MIRROR_SYNC_GUARD"

mirror_sync_require_enabled || exit $?
mirror_sync_acquire_global_lock || exit $?

ROOT="/app"
DEV_BRANCH="Edarsahub_Desarrollo"
MIRROR_BRANCH="mirror/emergent-live"
REMOTE="origin"

MAX_BYTES=5000000

MODE="${1:---dry-run}"

case "$MODE" in
    --dry-run|--publish)
        ;;
    *)
        echo "USAGE=$0 [--dry-run|--publish]"
        exit 2
        ;;
esac

cd "$ROOT"

echo "===== EDARSAHUB SAFE WEB -> MIRROR PUBLISHER ====="
echo "MODE=$MODE"

BRANCH="$(git branch --show-current)"
LOCAL_HEAD="$(git rev-parse HEAD)"

echo "LOCAL_BRANCH=$BRANCH"
echo "LOCAL_HEAD=$LOCAL_HEAD"

test "$BRANCH" = "$DEV_BRANCH" || {
    echo "ABORT=WRONG_BRANCH"
    exit 10
}

echo
echo "===== 1. FETCH CANONICAL REFS ====="

git fetch "$REMOTE" "$DEV_BRANCH" "$MIRROR_BRANCH"

REMOTE_DEV="$(git rev-parse "$REMOTE/$DEV_BRANCH")"
REMOTE_MIRROR="$(git rev-parse "$REMOTE/$MIRROR_BRANCH")"

echo "REMOTE_DEV=$REMOTE_DEV"
echo "REMOTE_MIRROR=$REMOTE_MIRROR"

test "$REMOTE_DEV" = "$LOCAL_HEAD" || {
    echo "ABORT=LOCAL_NOT_EQUAL_REMOTE_DEV"
    exit 11
}

test "$REMOTE_MIRROR" = "$LOCAL_HEAD" || {
    echo "ABORT=MIRROR_NOT_EQUAL_LOCAL_BASE"
    exit 12
}

echo
echo "===== 2. STAGING GUARD ====="

STAGED_COUNT="$(git diff --cached --name-only | wc -l)"

echo "STAGED_COUNT=$STAGED_COUNT"

test "$STAGED_COUNT" -eq 0 || {
    echo "ABORT=REAL_INDEX_HAS_STAGED_WORK"
    git diff --cached --name-status
    exit 20
}

echo
echo "===== 3. BUILD ISOLATED SNAPSHOT ====="

TMP_INDEX="$(mktemp)"

cleanup() {
    rm -f "$TMP_INDEX"
}

trap cleanup EXIT

export GIT_INDEX_FILE="$TMP_INDEX"

git read-tree "$LOCAL_HEAD"

# Cambios de archivos ya versionados.
git add -u

# Nuevos archivos permitidos dentro de áreas reales del proyecto.
for PATHNAME in \
    backend \
    frontend \
    docs \
    memory \
    tools \
    .github
do
    if [ -e "$PATHNAME" ]; then
        git add -- "$PATHNAME"
    fi
done

# Archivos raíz de gobierno/agentes permitidos.
for PATHNAME in \
    AGENTS.md \
    ANTIGRAVITY.md \
    CLAUDE.md \
    CODEX.md \
    GEMINI.md \
    GROK.md \
    KIMI.md
do
    if [ -f "$PATHNAME" ]; then
        git add -- "$PATHNAME"
    fi
done

PAYLOAD_COUNT="$(git diff --cached --name-only "$LOCAL_HEAD" | wc -l)"

echo "PAYLOAD_COUNT=$PAYLOAD_COUNT"

if [ "$PAYLOAD_COUNT" -eq 0 ]; then
    unset GIT_INDEX_FILE

    echo "DECISION=NO_CHANGES_TO_PUBLISH"
    echo "WRITE_OPERATION_EXECUTED=NO"
    echo "PRODUCTION_TOUCHED=NO"
    exit 0
fi

echo
echo "===== 4. EXACT PAYLOAD ====="

git diff --cached --name-status "$LOCAL_HEAD"

echo
echo "===== 5. SECRET GUARD ====="

SENSITIVE="$(
    git diff --cached --name-only "$LOCAL_HEAD" |
    grep -Ei '(^|/)(\.env($|\.)|.*\.pem$|.*\.key$|id_rsa$|id_ed25519$|credentials?\.json$|secrets?\.json$)' \
    || true
)"

if [ -n "$SENSITIVE" ]; then
    echo "ABORT=SENSITIVE_FILENAME_DETECTED"
    printf '%s\n' "$SENSITIVE"
    exit 30
fi

LEAK_FOUND=0

# Los patrones se construyen en fragmentos para que el scanner no
# se detecte a si mismo al inspeccionar este archivo.
PRIVATE_KEY_RX='BEGIN (RSA |EC |OPENSSH )?PRIVATE[[:space:]]+KEY'
API_KEY_RX='s''k-[A-Za-z0-9]{20,}'
PASSWORD_RX='pass''word[[:space:]]*=[[:space:]]*[^[:space:]]+'
SECRET_VALUE_RX='sec''ret[[:space:]]*=[[:space:]]*[^[:space:]]+'

while IFS= read -r FILE; do
    [ -n "$FILE" ] || continue

    CONTENT="$(
        git show ":$FILE" 2>/dev/null || true
    )"

    if printf '%s' "$CONTENT" |
        grep -Eqi \
            -e "$PRIVATE_KEY_RX" \
            -e "$API_KEY_RX" \
            -e "$PASSWORD_RX" \
            -e "$SECRET_VALUE_RX"
    then
        echo "CREDENTIAL_RISK_FILE=$FILE"
        LEAK_FOUND=1
    fi
done < <(git diff --cached --name-only "$LOCAL_HEAD")

test "$LEAK_FOUND" -eq 0 || {
    echo "ABORT=POTENTIAL_CREDENTIAL_CONTENT"
    exit 31
}

echo "SECRET_GUARD=PASS"

echo
echo "===== 6. LARGE FILE GUARD ====="

LARGE_FOUND=0

while IFS= read -r FILE; do
    [ -n "$FILE" ] || continue

    BLOB="$(
        git rev-parse ":$FILE" 2>/dev/null || true
    )"

    [ -n "$BLOB" ] || continue

    SIZE="$(git cat-file -s "$BLOB")"

    if [ "$SIZE" -gt "$MAX_BYTES" ]; then
        echo "LARGE_FILE=$FILE"
        echo "BYTES=$SIZE"
        LARGE_FOUND=1
    fi

done < <(git diff --cached --name-only "$LOCAL_HEAD")

test "$LARGE_FOUND" -eq 0 || {
    echo "ABORT=LARGE_FILE_IN_PAYLOAD"
    exit 32
}

echo "LARGE_FILE_GUARD=PASS"

echo
echo "===== 7. CREATE SNAPSHOT COMMIT ====="

TREE="$(git write-tree)"

SNAPSHOT="$(
    printf 'chore(mirror): Emergent live snapshot\n\nSource-Branch: %s\nSource-HEAD: %s\n' \
        "$BRANCH" \
        "$LOCAL_HEAD" |
    git commit-tree "$TREE" -p "$LOCAL_HEAD"
)"

echo "SNAPSHOT_TREE=$TREE"
echo "SNAPSHOT_COMMIT=$SNAPSHOT"

git merge-base --is-ancestor "$LOCAL_HEAD" "$SNAPSHOT" || {
    echo "ABORT=SNAPSHOT_NOT_FAST_FORWARD"
    exit 40
}

echo
echo "===== 8. SNAPSHOT VERIFICATION ====="

git diff-tree \
    --no-commit-id \
    --name-status \
    -r "$SNAPSHOT"

unset GIT_INDEX_FILE

echo
echo "===== 9. VERIFY REAL REPOSITORY UNTOUCHED ====="

test "$(git branch --show-current)" = "$DEV_BRANCH" || {
    echo "ABORT=REAL_BRANCH_CHANGED"
    exit 41
}

test "$(git rev-parse HEAD)" = "$LOCAL_HEAD" || {
    echo "ABORT=REAL_HEAD_CHANGED"
    exit 42
}

test "$(git diff --cached --name-only | wc -l)" -eq 0 || {
    echo "ABORT=REAL_INDEX_CHANGED"
    exit 43
}

if [ "$MODE" = "--dry-run" ]; then
    echo
    echo "DECISION=SAFE_SNAPSHOT_READY"
    echo "SNAPSHOT_COMMIT=$SNAPSHOT"
    echo "PUBLISH_EXECUTED=NO"
    echo "DEVELOPMENT_MODIFIED=NO"
    echo "PRODUCTION_TOUCHED=NO"
    exit 0
fi

echo
echo "===== 10. CONCURRENCY RECHECK ====="

git fetch "$REMOTE" "$DEV_BRANCH" "$MIRROR_BRANCH"

REMOTE_DEV_2="$(git rev-parse "$REMOTE/$DEV_BRANCH")"
REMOTE_MIRROR_2="$(git rev-parse "$REMOTE/$MIRROR_BRANCH")"
LOCAL_2="$(git rev-parse HEAD)"

echo "LOCAL_RECHECK=$LOCAL_2"
echo "REMOTE_DEV_RECHECK=$REMOTE_DEV_2"
echo "REMOTE_MIRROR_RECHECK=$REMOTE_MIRROR_2"

test "$LOCAL_2" = "$LOCAL_HEAD" || {
    echo "ABORT=LOCAL_MOVED_DURING_SNAPSHOT"
    exit 50
}

test "$REMOTE_DEV_2" = "$LOCAL_HEAD" || {
    echo "ABORT=DEVELOPMENT_MOVED_DURING_SNAPSHOT"
    exit 51
}

test "$REMOTE_MIRROR_2" = "$LOCAL_HEAD" || {
    echo "ABORT=MIRROR_MOVED_DURING_SNAPSHOT"
    exit 52
}

echo
echo "===== 11. PUBLISH MIRROR ONLY ====="

EDARSA_ALLOW_PUSH=1 EDARSA_PUSH_JOB_ID="mirror-snapshot-$$" EDARSA_PUSH_OWNER="mirror-snapshot" git push "$REMOTE" "$SNAPSHOT:refs/heads/$MIRROR_BRANCH"

echo
echo "===== 12. FINAL VALIDATION ====="

git fetch "$REMOTE" "$DEV_BRANCH" "$MIRROR_BRANCH"

FINAL_LOCAL="$(git rev-parse HEAD)"
FINAL_DEV="$(git rev-parse "$REMOTE/$DEV_BRANCH")"
FINAL_MIRROR="$(git rev-parse "$REMOTE/$MIRROR_BRANCH")"

echo "FINAL_LOCAL=$FINAL_LOCAL"
echo "FINAL_DEV=$FINAL_DEV"
echo "FINAL_MIRROR=$FINAL_MIRROR"

test "$FINAL_LOCAL" = "$LOCAL_HEAD" || exit 60
test "$FINAL_DEV" = "$LOCAL_HEAD" || exit 61
test "$FINAL_MIRROR" = "$SNAPSHOT" || exit 62

echo
echo "MIRROR_SNAPSHOT_PUBLISHED=YES"
echo "MIRROR_HEAD=$FINAL_MIRROR"
echo "DEVELOPMENT_HEAD=$FINAL_DEV"
echo "DEVELOPMENT_MODIFIED=NO"
echo "LOCAL_HEAD_MODIFIED=NO"
echo "PRODUCTION_TOUCHED=NO"
echo "NEXT_ACTION=AUDIT_AND_PROMOTE_MIRROR"
