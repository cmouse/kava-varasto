#!/usr/bin/env bash

set -eu

source $PWD/.venv/bin/activate

pushd frontend
npm ci && npm run build
popd

export DJANGO_SETTINGS_MODULE=kava_varasto.settings.prod

django-admin migrate
django-admin collectstatic --noinput
django-admin compilemessages

exec gunicorn kava_varasto.wsgi:application --bind $APP_HOST:$APP_PORT --log-level info --access-logfile - --access-logformat '%({X-Forwarded-For}i)s host=%({Host}i)s "%(r)s" %(s)s'
