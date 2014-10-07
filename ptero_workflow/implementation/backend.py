from . import models
from . import nodes
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
            'nodes': workflow_data['nodes'],
            'edges': workflow_data['edges'],
        }

        workflow.root_node = nodes.create_node('root',
                root_data, workflow=workflow)

        root_color_group = models.ColorGroup(workflow=workflow, index=0,
                begin=0, end=1)

        workflow.input_holder_node = nodes.create_input_holder(
                workflow.root_node, workflow_data['inputs'], color=0,
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

    def event(self, node_id, event_type, body_data, query_string_data):
        node = self.session.query(models.Node
                ).filter_by(id=node_id).one()
        node.handle_event(event_type, body_data, query_string_data)

    def cleanup(self):
        self.session.rollback()
