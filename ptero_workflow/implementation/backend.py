from . import models
from . import operations
from . import translator
import os
import simplejson
import requests


class Backend(object):
    def __init__(self, session):
        self.session = session

    def create_workflow(self, workflow_data):
        workflow = self._save_workflow(workflow_data)

        petri_data = translator.build_petri_net(workflow)
        response_data = self._submit_net(petri_data)

        workflow.net_key = response_data['net_key']
        self.session.commit()

        self._start_net(response_data['entry_links'][workflow.start_place_name])

        return workflow.id

    def _save_workflow(self, workflow_data):
        workflow = models.Workflow(
            inputs=simplejson.dumps(workflow_data['inputs']),
            environment=simplejson.dumps(workflow_data['environment']),
        )

        root_data = {
            'type': 'model',
            'operations': workflow_data['operations'],
            'links': workflow_data['links'],
        }

        workflow.root_operation = operations.create_operation('root', root_data)

        self.session.add(workflow)
        self.session.commit()

        return workflow

    def _submit_net(self, petri_data):
        response = requests.post(self._petri_submit_url,
                data=simplejson.dumps(petri_data),
                headers={'Content-Type': 'application/json'})
        return response.json()

    @property
    def _petri_submit_url(self):
        return 'http://%s:%d/v1/nets' % (
            os.environ.get('PTERO_PETRI_HOST', 'localhost'),
            int(os.environ.get('PTERO_PETRI_PORT', 80)),
        )

    def _start_net(self, start_url):
        response = requests.post(start_url,
                headers={'Content-Type': 'application/json'})
        return response.json()

    def get_workflow(self, workflow_id):
        return self.session.query(models.Workflow).get(workflow_id).as_dict

    def event(self, operation_id, event_type, color=None, color_group=None,
            response_links=None):
        if event_type == 'execute':
            if 'success' in response_links:
                response = requests.put(response_links['success'])
        elif event_type == 'done':
            operation = self.session.query(models.Operation).get(operation_id)
            operation.status = 'success'
            self.session.commit()

    def cleanup(self):
        pass
