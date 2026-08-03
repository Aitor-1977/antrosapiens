#!/usr/bin/env bash
# Ejecuta los conectores de ingesta Capa 0 (100% gratuitos). Lee .env.
# Operación autónoma: sin argumentos, barre las listas por defecto.
# Uso:
#   ./run.sh                                  # autónomo: noticias por defecto
#   ./run.sh radar                            # idem (barrido por defecto)
#   ./run.sh noticias --query "fintech México ronda"
#   ./run.sh noticias --feed https://un-medio.com/rss
#   ./run.sh youtube                          # autónomo: cola HD_INGESTA_DEFAULT_VIDEOS
#   ./run.sh youtube <VIDEO_URL> ["Organización"] [lang]
set -euo pipefail
PY="${PYTHON:-python3}"

case "${1:-}" in
  ""|radar)
    exec "$PY" -m hd_scraper.ingesta noticias
    ;;
  noticias)
    shift
    exec "$PY" -m hd_scraper.ingesta noticias "$@"
    ;;
  youtube)
    shift
    if [ -n "${1:-}" ]; then
      exec "$PY" -m hd_scraper.ingesta youtube --url "$1" --org "${2:-}" --lang "${3:-es}"
    else
      exec "$PY" -m hd_scraper.ingesta youtube
    fi
    ;;
  help|-h|--help)
    echo "conectores de ingesta Capa 0 (gratuitos) — operación autónoma"
    echo "  ./run.sh                          # autónomo: noticias por defecto"
    echo "  ./run.sh noticias --query \"fintech México ronda\""
    echo "  ./run.sh noticias --feed <URL_RSS>"
    echo "  ./run.sh youtube                  # autónomo: cola HD_INGESTA_DEFAULT_VIDEOS"
    echo "  ./run.sh youtube <VIDEO_URL> [\"Org\"] [lang]"
    exit 0
    ;;
  *)
    echo "subcomando desconocido: ${1}" >&2
    echo "ayuda: ./run.sh help" >&2
    exit 2
    ;;
esac
