web: python manage.py migrate && (python manage.py run_scheduler & gunicorn myapp.wsgi:application --bind 0.0.0.0:$PORT)

