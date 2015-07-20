from . import exceptions
from . import models
from networkx.algorithms import is_directed_acyclic_graph
from networkx.exception import NetworkXUnfeasible
from networkx import DiGraph
from ptero_workflow.implementation import exceptions
from ptero_workflow.implementation.validators import validate_unique_links
import logging

LOG = logging.getLogger(__name__)


def build_task(name, data, workflow, parent_method=None):
    task = models.MethodList(name=name,
            parallel_by=data.get('parallelBy'),
            parent=parent_method,
            workflow=workflow)

    for name, webhooks in data.get('webhooks', {}).items():
        if not isinstance(webhooks, list):
            webhooks = [webhooks]
        for url in webhooks:
            webhook = models.Webhook(name=name, url=url, task=task)

    for index, method_data in enumerate(data.get('methods', [])):
        task.method_list.append(build_method(method_data, workflow,
            index=index, parent_task=task))

    return task

def build_method(data, workflow, index=None, parent_task=None):
    if data['service'] == 'workflow':
        method = _build_dag_method(data, workflow, index, parent_task)
    else:
        method = _build_service_method(data, workflow, index, parent_task,
                models.SUBCLASS_LOOKUP[data['service']])

    for name, webhooks in data['parameters'].get('webhooks', {}).items():
        if not isinstance(webhooks, list):
            webhooks = [webhooks]
        for url in webhooks:
            webhook = models.Webhook(name=name, url=url, method=method)

    return method


def _build_dag_method(data, workflow, index, parent_task):
    _validate_dag_data(data)

    method = models.DAG(name=data['name'], index=index,
            task=parent_task, workflow=workflow)

    nodes = data['parameters']['tasks'].keys()
    links = [(l['source'], l['destination'])
            for l in data['parameters']['links']]
    try:
        ordering = get_deterministic_topological_ordering(nodes, links,
                start_node='input connector')
    except NetworkXUnfeasible:
        raise exceptions.DAGCycleError('DAG named "%s" has a cycle', data['name'])

    children = {}
    for idx, name in enumerate(ordering[1:-1]):
        child_task_data = data['parameters']['tasks'][name]
        task = build_task(name, child_task_data, workflow, parent_method=method)
        task.topological_index = idx
        children[name] = task

    children['input connector'] = models.InputConnector(
        name='input connector', parent=method, workflow=workflow, topological_index=-1)
    children['output connector'] = models.OutputConnector(
        name='output connector', parent=method, workflow=workflow, topological_index=-1)

    method.children = children

    validate_unique_links(data['parameters']['links'])
    for link_data in data['parameters']['links']:
        source = children[link_data['source']]
        destination = children[link_data['destination']]
        link = models.Link(
            destination_task=destination,
            source_task=source,
        )
        for source_property, destination_part in link_data['dataFlow'].items():
            if isinstance(destination_part, basestring):
                models.DataFlowEntry(source_property=source_property,
                    destination_property=destination_part,
                    link=link)
            else:
                for destination_property in destination_part:
                    models.DataFlowEntry(source_property=source_property,
                        destination_property=destination_property,
                        link=link)

    return method

def get_deterministic_topological_ordering(nodes, links, start_node):
    """
    Topological sort that is deterministic because it sorts (alphabetically)
    candidates to check
    """
    graph = DiGraph()
    graph.add_nodes_from(nodes)
    for link in links:
        graph.add_edge(*link)

    if not is_directed_acyclic_graph(graph):
        raise NetworkXUnfeasible

    task_names = sorted(graph.successors(start_node))
    task_set = set(task_names)
    graph.remove_node(start_node)

    result = [start_node]
    while task_names:
        for name in task_names:
            if graph.in_degree(name) == 0:
                result.append(name)

                # it is OK to modify task_names because we break out
                # of loop below
                task_names.remove(name)

                new_successors = [t for t in graph.successors(name)
                        if t not in task_set]
                task_names.extend(new_successors)
                task_names.sort()
                task_set.update(set(new_successors))

                graph.remove_node(name)
                break

    return result




def _build_service_method(data, workflow, index, parent_task, cls):
    build_parameters = data['parameters'].copy()
    if 'webhooks' in build_parameters:
        del build_parameters['webhooks']
    return cls(name=data['name'], index=index, task=parent_task,
            parameters=build_parameters, workflow=workflow)


def create_input_holder(root, workflow, inputs, color, parent_color):
    task = models.InputHolder(name='input_holder', workflow=workflow)
    task.set_outputs(inputs, color=color, parent_color=parent_color)
    link = models.Link(source_task=task, destination_task=root)
    for i in inputs.iterkeys():
        models.DataFlowEntry(source_property=i, destination_property=i,
                link=link)
    return task


def _validate_dag_data(data):
    _validate_dag_task_names(data['parameters']['tasks'])


_ILLEGAL_TASK_NAMES = {'input connector', 'output connector'}


def _validate_dag_task_names(tasks):
    for illegal_name in _ILLEGAL_TASK_NAMES:
        if illegal_name in tasks:
            raise exceptions.IllegalTaskNameError('"%s" is an illegal task name'
                    % illegal_name)
