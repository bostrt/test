#!/bin/sh
exec gunicorn wsgi:application --bind=0.0.0.0:8080 --access-logfile=- --config gunicorn.conf
