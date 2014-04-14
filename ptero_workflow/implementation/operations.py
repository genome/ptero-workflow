from . import exceptions
from . import models


__all__ = ['create_operation']


def _build_model_operation(operation_data, operation):
    _validate_model_operation_data(operation_data)

    for name, child_operation_data in operation_data['operations'].iteritems():
        create_operation(name=name, operation_data=child_operation_data,
                parent=operation)

    create_operation(name='input connector',
            operation_data={'type': 'input'}, parent=operation)
    create_operation(name='output connector',
            operation_data={'type': 'output'}, parent=operation)

    for link_data in operation_data['links']:
        source = operation.children[link_data['source']]
        destination = operation.children[link_data['destination']]
        models.Link(
            destination_operation=destination,
            destination_property=link_data['destination_property'],
            parallel_by=link_data.get('parallel_by', False),
            source_operation=source,
            source_property=link_data['source_property'],
        )


def _validate_model_operation_data(operation_data):
    if 'input connector' in operation_data['operations']:
        raise exceptions.InvalidWorkflow(
                "'input connector' is a reserved operation name")

    if 'output connector' in operation_data['operations']:
        raise exceptions.InvalidWorkflow(
                "'output connector' is a reserved operation name")


def create_operation(name, operation_data, parent=None):
    op_type = operation_data['type'].lower()

    operation = models.Operation.from_dict(name=name, type=op_type)
    if parent is not None:
        parent.children[name] = operation

    if op_type == 'model':
        _build_model_operation(operation_data, operation=operation)

    return operation
