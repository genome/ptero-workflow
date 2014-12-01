from . import exceptions
from . import models


__all__ = ['create_task']


def _build_dag(task_data, method):
    _validate_dag_task_data(task_data)

    for name, child_task_data in task_data['tasks'].iteritems():
        create_task(name=name, task_data=child_task_data,
                parent=method)

    create_task(name='input connector',
            task_data={'type': 'input connector'}, parent=method)
    create_task(name='output connector',
            task_data={'type': 'output connector'}, parent=method)

    for edge_data in task_data['edges']:
        source = method.children[edge_data['source']]
        destination = method.children[edge_data['destination']]
        models.Edge(
            destination_task=destination,
            destination_property=edge_data['destinationProperty'],
            source_task=source,
            source_property=edge_data['sourceProperty'],
        )


def _build_method_list(task_data, task):
    for index, data in enumerate(task_data['methods']):
        method_name = data['name']
        method = models.new_method(
                name=method_name,
                service=data['service'],
                parameters=data['parameters'],
                task_id=task.id,
                index=index
        )
        task.method_list.append(method)
        if 'tasks' in data:
            _build_dag(data, method)


_NODE_BUILDERS = {
    'method-list': _build_method_list,
}
def _build_task(task_data, task):
    if 'parallelBy' in task_data:
        task.parallel_by = task_data['parallelBy']

    _task_builder = _NODE_BUILDERS.get(task.type)
    if _task_builder:
        _task_builder(task_data, task=task)


def _validate_dag_task_data(task_data):
    if 'input connector' in task_data['tasks']:
        raise exceptions.InvalidWorkflow(
                "'input connector' is a reserved task name")

    if 'output connector' in task_data['tasks']:
        raise exceptions.InvalidWorkflow(
                "'output connector' is a reserved task name")

def _get_task_type(task_data):
    if 'type' in task_data:
        if task_data['type'] in ['input connector', 'output connector']:
            return task_data['type'].lower()
        else:
            raise RuntimeError('Only input/output connector are '
                    'allowed explicit type, not (%s)' % task_data['type'])
    elif 'methods' in task_data:
        return 'method-list'

    else:
        raise RuntimeError('Cannot determine task type from task_data (%s)' %
                task_data)


def create_task(name, task_data, parent=None, workflow=None):
    task_type = _get_task_type(task_data)

    task = models.Task.from_dict(name=name, type=task_type,
            workflow=workflow)
    if parent is not None:
        parent.children[name] = task

    _build_task(task_data, task=task)

    return task

def create_input_holder(root, inputs, color, workflow=None):
    task = models.InputHolder(name='input_holder',
            workflow=workflow)
    task.set_outputs(inputs, color=color, parent_color=None)
    for i in inputs.iterkeys():
        models.Edge(source_task=task, destination_task=root,
                source_property=i, destination_property=i)
    return task
