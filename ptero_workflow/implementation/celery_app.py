from . import celery_tasks
from celery.signals import worker_process_init
import celery
import os
import sqlalchemy


app = celery.Celery('PTero-workflow-celery',
        include='ptero_workflow.implementation.celery_tasks')


_DEFAULT_CELERY_CONFIG = {
    'CELERY_BROKER_URL': 'amqp://localhost',
    'CELERY_RESULT_BACKEND': 'redis://localhost',
    'CELERY_ACCEPT_CONTENT': ['json'],
    'CELERY_ACKS_LATE': True,
    'CELERY_RESULT_SERIALIZER': 'json',
    'CELERY_TASK_SERIALIZER': 'json',
    'CELERYD_PREFETCH_MULTIPLIER': 10,
}
for var, default in _DEFAULT_CELERY_CONFIG.iteritems():
    if var in os.environ:
        app.conf[var] = os.environ[var]
    else:
        app.conf[var] = default


app.Session = sqlalchemy.orm.sessionmaker()


@worker_process_init.connect
def initialize_sqlalchemy_session(**kwargs):
    from . import models

    engine = sqlalchemy.create_engine(os.environ['PTERO_WORKFLOW_DB_STRING'])
    models.Base.metadata.create_all(engine)
    app.Session.configure(bind=engine)
