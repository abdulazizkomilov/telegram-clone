#!/bin/bash

# Check for Postgres
if [ "$DATABASE" = "postgres" ]; then
  echo "Waiting for postgres..."
  while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
  done
  echo "PostgreSQL started"
fi

# Check for Redis
if [ "$REDIS_HOST" ] && [ "$REDIS_PORT" ]; then
  echo "Waiting for Redis..."
  while ! nc -z $REDIS_HOST $REDIS_PORT; do
    sleep 0.1
  done
  echo "Redis started"
fi

echo "Starting celery"
celery -A core worker --loglevel=info &

echo "Starting celery beat"
celery -A core beat --loglevel=info &

# Running migrations
echo "Running migrations"
python manage.py migrate
echo "Successfully migrated database"

# Collecting static files
echo "Collecting static files"
python manage.py collectstatic --no-input
echo "Successfully collected static files"

# Compile translation messages
#echo "Compiling translation messages"
#django-admin compilemessages
#echo "Successfully compiled messages"

# Starting server
echo "Starting server"
python manage.py runserver 0.0.0.0:8000
