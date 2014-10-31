from .. import models
import celery


__all__ = ['SubmitNet']


class SubmitNet(celery.Task):
    ignore_result = True

    def run(self, workflow_id):
        pass
