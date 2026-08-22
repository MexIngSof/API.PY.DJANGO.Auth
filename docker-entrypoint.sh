#!/bin/sh
set -eu
case "${1:-serve}" in
  serve)
    exec python -m uvicorn config.asgi:application --host 0.0.0.0 --port "${PORT:-8000}" --workers "${UVICORN_WORKERS:-1}"
    ;;
  migrate)
    shift
    exec python manage.py migrate "$@"
    ;;
  check)
    exec python manage.py check --deploy
    ;;
  *)
    exec "$@"
    ;;
esac
