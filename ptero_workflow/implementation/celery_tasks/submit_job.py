import celery
from ptero_common import nicer_logging


LOG = nicer_logging.getLogger(__name__)

__all__ = ['SubmitJob']


class SubmitJob(celery.Task):
    ignore_result = True

    def run(self, execution_id):
        backend = celery.current_app.factory.create_backend()
        backend.submit_job(execution_id)
        backend.cleanup()
