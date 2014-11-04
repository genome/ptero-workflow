from .. import models
from .. import tasks
from .. import translator
import base64
import celery
import os
import uuid


__all__ = ['SubmitNet']


class SubmitNet(celery.Task):
    ignore_result = True

    def run(self, workflow_id):
        session = celery.current_app.Session()

        workflow = session.query(models.Workflow).get(workflow_id)
        workflow.net_key = generate_net_key()
        session.commit()

        petri_data = translator.build_petri_net(workflow)
        self._submit_net(petri_data, workflow.net_key)

    @property
    def http(self):
        return celery.current_app.tasks[
                'ptero_workflow.implementation.celery_tasks.http.HTTP']

    def _submit_net(self, petri_data, net_key):
        self.http.delay('PUT', self._petri_submit_url(net_key), **petri_data)

    def _petri_submit_url(self, net_key):
        return 'http://%s:%d/v1/nets/%s' % (
            os.environ.get('PTERO_PETRI_HOST', 'localhost'),
            int(os.environ.get('PTERO_PETRI_PORT', 80)),
            net_key,
        )


def generate_net_key():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes)[:-2]
