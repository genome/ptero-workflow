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
            environment=simplejson.dumps(workflow_data['environment']),
        )

        root_data = {
            'type': 'model',
            'operations': workflow_data['operations'],
            'links': workflow_data['links'],
        }

        workflow.root_operation = operations.create_operation('root',
                root_data, workflow=workflow)

        root_color_group = models.ColorGroup(workflow=workflow, index=0,
                begin=0, end=1)

        workflow.input_holder_operation = operations.create_input_holder(
                workflow.root_operation, workflow_data['inputs'], color=0,
                workflow=workflow)

        self.session.add(workflow)
        self.session.add(root_color_group)
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

    def event(self, operation_id, event_type, color=None, group=None,
            response_links=None, **kwargs):
        operation = self.session.query(models.Operation).get(operation_id)
        if event_type == 'execute':
            operation.execute(color, group, response_links)
            self.session.commit()

        elif event_type == 'ended':
            operation.ended(**kwargs)
            self.session.commit()

        elif event_type == 'get_split_size':
            size = operation.get_split_size(color)
            response = requests.put(response_links['send_data'],
                    data=simplejson.dumps({'color_group_size': size}),
                    headers={'Content-Type': 'application/json'})

        elif event_type == 'color_group_created':
            workflow = operation.workflow
            cg = models.ColorGroup.create(workflow, group)
            self.session.add(cg)
            self.session.commit()

        elif event_type == 'done':
            operation = self.session.query(models.Operation).get(operation_id)
            operation.status = 'success'
            self.session.commit()

    def cleanup(self):
        pass
