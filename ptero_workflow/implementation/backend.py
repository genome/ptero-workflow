from . import exceptions
from . import models
import simplejson


class Backend(object):
    def __init__(self, session):
        self.session = session

    def create_workflow(self, workflow_data):
        self._validate_workflow_data(workflow_data)

        workflow = models.Workflow(
            inputs=simplejson.dumps(workflow_data['inputs']),
            environment=simplejson.dumps(workflow_data['environment']),
        )

        root_operation_data = {
            'type': 'model',
            'operations': workflow_data['operations'],
            'links': workflow_data['links'],
        }

        workflow.root_operation = _create_operation(root_operation_data)

        self.session.add(workflow)
        self.session.commit()

        return workflow.id

    def get_workflow(self, workflow_id):
        return self.session.query(models.Workflow).get(workflow_id).as_dict

    def cleanup(self):
        pass

    def _validate_workflow_data(self, workflow_data):
        if 'input connector' in workflow_data['operations']:
            raise exceptions.InvalidWorkflow(
                    "'input connector' is a reserved operation name")

        if 'output connector' in workflow_data['operations']:
            raise exceptions.InvalidWorkflow(
                    "'output connector' is a reserved operation name")


def _create_operation(operation_data):
    operation_data['operations']['input connector']  = {'type': 'input'}
    operation_data['operations']['output connector'] = {'type': 'output'}

    root_operation = models.Operation(name='root', type='root')

    for name, child_operation_data in operation_data['operations'].iteritems():
        root_operation.children[name] = models.Operation(name=name,
                **child_operation_data)

    for link_data in operation_data['links']:
        source = root_operation.children[link_data['source']]
        destination = root_operation.children[link_data['destination']]
        models.Link(
                source_operation=source,
                destination_operation=destination,
                source_property=link_data['source_property'],
                destination_property=link_data['destination_property'])

    return root_operation
