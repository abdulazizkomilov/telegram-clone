#!/bin/bash

# Check for Postgres readiness
if [ "$DATABASE" = "postgres" ]; then
  echo "Waiting for postgres..."
  while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
  done
  echo "PostgreSQL started"
fi

# Check for Redis readiness
if [ "$REDIS_HOST" ] && [ "$REDIS_PORT" ]; then
  echo "Waiting for Redis..."
  while ! nc -z $REDIS_HOST $REDIS_PORT; do
    sleep 0.1
  done
  echo "Redis started"
fi

# Run migrations
echo "Running migrations"
python manage.py migrate

# Collect static files
echo "Collecting static files"
python manage.py collectstatic --no-input

# Compile translation messages
#echo "Compiling translation messages"
#django-admin compilemessages

# Start Celery worker and beat as background processes
echo "Starting Celery worker and beat"
celery -A core worker --loglevel=info &
celery -A core beat --loglevel=info &

# Start Django server
echo "Starting Django server"
exec python manage.py runserver 0.0.0.0:8000
