web: gunicorn ptero_workflow.api.wsgi:app --access-logfile - --error-logfile -
worker: celery worker --loglevel=INFO -A ptero_workflow.implementation.celery_app
