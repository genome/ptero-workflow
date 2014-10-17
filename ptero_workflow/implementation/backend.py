from . import models
from . import tasks
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
            'tasks': workflow_data['tasks'],
            'edges': workflow_data['edges'],
        }

        workflow.root_task = tasks.create_task('root',
                root_data, workflow=workflow)

        workflow.input_holder_task = tasks.create_input_holder(
                workflow.root_task, workflow_data['inputs'], color=0,
                parent_color=0, workflow=workflow)

        self.session.add(workflow)
        self.session.commit()

        return workflow

    def _submit_net(self, petri_data):
        with open('/vagrant/new.json', 'w') as ofile:
            ofile.write(simplejson.dumps(petri_data, indent=2))
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

    def handle_task_callback(self, task_id, callback_type, body_data,
            query_string_data):
        task = self.session.query(models.Task
                ).filter_by(id=task_id).one()
        task.handle_callback(callback_type, body_data, query_string_data)

    def handle_method_callback(self, method_id, callback_type, body_data,
            query_string_data):
        method = self.session.query(models.Method
                ).filter_by(id=method_id).one()
        method.handle_callback(callback_type, body_data, query_string_data)

    def cleanup(self):
        self.session.rollback()
