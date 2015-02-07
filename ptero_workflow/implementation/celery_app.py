from celery.signals import worker_process_init, setup_logging
import celery
import os
import sqlalchemy
import time
from ptero_common.logging_configuration import configure_celery_logging


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

# This has to be imported AFTER the app.conf is set up or
# the tasks will default to using pickle serialization which is forbidden by
# this configuration.
from . import celery_tasks


app.Session = sqlalchemy.orm.sessionmaker()


@setup_logging.connect
def setup_celery_logging(**kwargs):
    configure_celery_logging("WORKFLOW")


@worker_process_init.connect
def initialize_sqlalchemy_session(**kwargs):
    from . import models

    engine = sqlalchemy.create_engine(os.environ['PTERO_WORKFLOW_DB_STRING'])
    for i in xrange(3):
        try:
            models.Base.metadata.create_all(engine)
            break
        except sqlalchemy.exc.SQLAlchemyError:
            time.sleep(0.5)

    app.Session.configure(bind=engine)
