#!/usr/bin/env bash

set -eu

# Only activate our own venv if the caller hasn't already got one active
# (e.g. under `uv run` or a manually activated env).
if [ -z "${VIRTUAL_ENV:-}" ]; then
	source $PWD/.venv/bin/activate
fi

pushd frontend
npm ci && npm run build
popd

export DJANGO_SETTINGS_MODULE=kava_varasto.settings.prod

django-admin migrate
django-admin collectstatic --noinput
django-admin compilemessages

exec gunicorn kava_varasto.wsgi:application --bind $APP_HOST:$APP_PORT --log-level info --access-logfile - --access-logformat '%({X-Forwarded-For}i)s host=%({Host}i)s "%(r)s" %(s)s'
