from . import exceptions
from . import models
import logging

LOG = logging.getLogger(__name__)


def build_task(name, data, parent_method=None):
    task = models.MethodList(name=name,
            parallel_by=data.get('parallelBy'),
            parent=parent_method)

    for name, webhooks in data.get('webhooks', {}).items():
        if not isinstance(webhooks, list):
            webhooks = [webhooks]
        for url in webhooks:
            webhook = models.Webhook(name=name, url=url, task=task)

    for index, method_data in enumerate(data.get('methods', [])):
        task.method_list.append(build_method(method_data, index=index,
            parent_task=task))

    return task

def build_method(data, index=None, parent_task=None):
    if data['service'] == 'workflow':
        method = _build_dag_method(data, index, parent_task)
    else:
        method = _build_service_method(data, index, parent_task,
                models.SUBCLASS_LOOKUP[data['service']])

    for name, webhooks in data['parameters'].get('webhooks', {}).items():
        if not isinstance(webhooks, list):
            webhooks = [webhooks]
        for url in webhooks:
            webhook = models.Webhook(name=name, url=url, method=method)

    return method


def _build_dag_method(data, index, parent_task):
    _validate_dag_data(data)

    method = models.DAG(name=data['name'], index=index,
            task=parent_task)

    children = {}
    for name, child_task_data in data['parameters']['tasks'].iteritems():
        children[name] = build_task(name, child_task_data,
                parent_method=method)
    children['input connector'] = models.InputConnector(
        name='input connector', parent=method)
    children['output connector'] = models.OutputConnector(
        name='output connector', parent=method)

    method.children = children

    for link_data in data['parameters']['links']:
        source = children[link_data['source']]
        destination = children[link_data['destination']]
        models.Link(
            destination_task=destination,
            destination_property=link_data['destinationProperty'],
            source_task=source,
            source_property=link_data['sourceProperty'],
        )

    return method


def _build_service_method(data, index, parent_task, cls):
    build_parameters = data['parameters'].copy()
    if 'webhooks' in build_parameters:
        del build_parameters['webhooks']
    return cls(name=data['name'], index=index, task=parent_task,
            parameters=build_parameters)


def create_input_holder(root, inputs, color, parent_color):
    task = models.InputHolder(name='input_holder')
    task.set_outputs(inputs, color=color, parent_color=parent_color)
    for i in inputs.iterkeys():
        models.Link(source_task=task, destination_task=root,
                source_property=i, destination_property=i)
    return task


def _validate_dag_data(data):
    _validate_dag_task_names(data['parameters']['tasks'])


_ILLEGAL_TASK_NAMES = {'input connector', 'output connector'}


def _validate_dag_task_names(tasks):
    for illegal_name in _ILLEGAL_TASK_NAMES:
        if illegal_name in tasks:
            raise exceptions.InvalidWorkflow('"%s" is an illegal task name'
                    % illegal_name)
