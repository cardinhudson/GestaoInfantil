#!/usr/bin/env bash
set -euo pipefail
echo "Running DB migration (init_db)"
if [ -n "${GESTAO_DB-}" ]; then
  echo "Using GESTAO_DB=${GESTAO_DB}"
fi
python -c "from db import init_db; init_db()"
echo "Migration complete."
