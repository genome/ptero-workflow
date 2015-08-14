from celery.signals import worker_process_init, setup_logging
import celery
import os
import time
from factory import Factory
from ptero_common.logging_configuration import configure_celery_logging
from ptero_common.celery.utils import get_config_from_env


app = celery.Celery('PTero-workflow-celery',
        include='ptero_workflow.implementation.celery_tasks')

app.conf['CELERY_ROUTES'] = (
    {
        'ptero_workflow.implementation.celery_tasks.submit_net.SubmitNet': {'queue': 'submit'},
        'ptero_common.celery.http.HTTP': {'queue': 'http'},
        'ptero_common.celery.http.HTTPWithResult': {'queue': 'http'},
    },
)

config = get_config_from_env('WORKFLOW')
app.conf.update(config)


# This has to be imported AFTER the app.conf is set up or
# the tasks will default to using pickle serialization which is forbidden by
# this configuration.
from . import celery_tasks


@setup_logging.connect
def setup_celery_logging(**kwargs):
    configure_celery_logging("WORKFLOW")


@worker_process_init.connect
def initialize_factory(**kwargs):
    app.factory = Factory(
        connection_string=os.environ.get('PTERO_WORKFLOW_DB_STRING',
            'sqlite://'), celery_app=app)
