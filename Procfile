web: gunicorn ptero_workflow.api.wsgi:app --timeout $PTERO_WORKFLOW_GUNICORN_TIMEOUT --access-logfile - --error-logfile -
worker: celery worker -A ptero_workflow.implementation.celery_app --concurrency 1 -Q submit
http_worker: celery worker -A ptero_workflow.implementation.celery_app --concurrency 1 -Q http
