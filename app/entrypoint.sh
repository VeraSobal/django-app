#!/bin/sh

echo "Apply migrations"

python manage.py migrate --no-input

echo "Create superuser"

python manage.py createsuperuser --noinput

echo "Load directories"

python manage.py loaddata directories

echo "Starting Django Server..."

exec "$@"