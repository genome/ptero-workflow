from . import models
from . import operations
import simplejson


class Backend(object):
    def __init__(self, session):
        self.session = session

    def create_workflow(self, workflow_data):
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

        return workflow.id

    def get_workflow(self, workflow_id):
        return self.session.query(models.Workflow).get(workflow_id).as_dict

    def cleanup(self):
        pass
