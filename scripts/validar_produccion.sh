#!/usr/bin/env bash
# Validación final en producción — envoltorio de un solo comando.
# Requiere: red hacia el despliegue, Python 3.9+, MOTOR_A_URL y HD_INGEST_TOKEN.
set -euo pipefail

export MOTOR_A_URL="${MOTOR_A_URL:-https://hd-prospector.vercel.app}"

if [[ -z "${HD_INGEST_TOKEN:-}" && "${1:-}" != "--solo-leer" ]]; then
  echo "ERROR: exporta HD_INGEST_TOKEN (X-Ingest-Token del despliegue) o usa --solo-leer." >&2
  exit 2
fi

cd "$(dirname "$0")/.."
echo "Validando producción en: $MOTOR_A_URL"
exec python -m scripts.validar_produccion "$@"
