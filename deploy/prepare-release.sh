#!/usr/bin/env bash
set -euo pipefail

project=/srv/petshelter-nika
repo="$project/repo"
revision=$(git -C "$repo" rev-parse --verify HEAD)
release="$project/releases/$revision"

if [[ ! -f "$release/.ready" ]]; then
    mkdir -p "$release"
    git -C "$repo" archive "$revision" | tar -x -C "$release"

    python3 -m venv "$release/.venv"
    python="$release/.venv/bin/python"
    "$python" -m pip --disable-pip-version-check --no-cache-dir install --requirement "$release/requirements.txt"
    (
        cd "$release/frontend"
        npm ci --no-audit --no-fund
        npm run build
    )
    "$python" "$release/backend/manage.py" check --deploy --fail-level ERROR
    "$python" "$release/backend/manage.py" collectstatic --noinput

    if [[ -f "${DJANGO_SQLITE_PATH:?Set DJANGO_SQLITE_PATH}" ]]; then
        "$python" - "$project/shared/backups" <<'PY'
import os
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys

os.umask(0o077)
folder = Path(sys.argv[1])
folder.mkdir(parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
db = Path(os.environ['DJANGO_SQLITE_PATH'])
with sqlite3.connect(f'{db.as_uri()}?mode=ro', uri=True) as source:
    with sqlite3.connect(folder / f'{stamp}.sqlite3') as backup:
        source.backup(backup)
PY
    fi
    "$python" "$release/backend/manage.py" migrate --noinput

    cp -R "$release/backend/staticfiles/." "$release/frontend/dist/static/"
    git -C "$repo" rev-parse --verify "$revision" > "$release/REVISION"
    install -m 0644 "$release/REVISION" "$release/frontend/dist/revision.txt"
    rm -rf -- "$release/frontend/node_modules"
    touch "$release/.ready"
fi

link="$project/.current-$$"
trap 'rm -f -- "$link"' EXIT
ln -s "$release" "$link"
mv -Tf -- "$link" "$project/current"
