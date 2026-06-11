#!/bin/bash
# Render entrypoint — Render $PORT beradi (default 10000), shu portda eshitamiz.
set -e

python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput

gunicorn config.wsgi:application \
    -b 0.0.0.0:${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-2} \
    --timeout 120
