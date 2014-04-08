from . import exceptions
from . import models
import simplejson


class Backend(object):
    def __init__(self, session):
        self.session = session

    def create_workflow(self, workflow_data):
        workflow = models.Workflow(
            inputs=simplejson.dumps(workflow_data['inputs']),
            environment=simplejson.dumps(workflow_data['environment']),
        )

        root_operation_data = {
            'type': 'model',
            'operations': workflow_data['operations'],
            'links': workflow_data['links'],
        }

        workflow.root_operation = _create_operation('root', root_operation_data)

        self.session.add(workflow)
        self.session.commit()

        return workflow.id

    def get_workflow(self, workflow_id):
        return self.session.query(models.Workflow).get(workflow_id).as_dict

    def cleanup(self):
        pass


def _build_dummy_operation(operation_data, operation):
    pass


def _build_model_operation(operation_data, operation):
    _validate_model_operation_data(operation_data)

    for name, child_operation_data in operation_data['operations'].iteritems():
        _create_operation(name=name, operation_data=child_operation_data,
                parent=operation)

    _create_operation(name='input connector', operation_data={'type': 'input'},
            parent=operation)
    _create_operation(name='output connector',
            operation_data={'type': 'output'}, parent=operation)

    for link_data in operation_data['links']:
        source = operation.children[link_data['source']]
        destination = operation.children[link_data['destination']]
        models.Link(
                source_operation=source,
                destination_operation=destination,
                source_property=link_data['source_property'],
                destination_property=link_data['destination_property'])


def _validate_model_operation_data(operation_data):
    if 'input connector' in operation_data['operations']:
        raise exceptions.InvalidWorkflow(
                "'input connector' is a reserved operation name")

    if 'output connector' in operation_data['operations']:
        raise exceptions.InvalidWorkflow(
                "'output connector' is a reserved operation name")


_OPERATION_TYPE_BUILDERS = {
    'dummy-operation': _build_dummy_operation,
    'input': _build_dummy_operation,
    'model': _build_model_operation,
    'output': _build_dummy_operation,
}
def _create_operation(name, operation_data, parent=None):
    op_type = operation_data['type'].lower()

    operation = models.Operation(name=name, type=op_type)
    if parent is not None:
        parent.children[name] = operation

    _OPERATION_TYPE_BUILDERS[op_type](operation_data,
            operation=operation)

    return operation
