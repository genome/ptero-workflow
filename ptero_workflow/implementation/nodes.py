from . import exceptions
from . import models


__all__ = ['create_node']


def _build_dag(node_data, node):
    _validate_dag_node_data(node_data)

    for name, child_node_data in node_data['nodes'].iteritems():
        create_node(name=name, node_data=child_node_data,
                parent=node, workflow=node.workflow)

    create_node(name='input connector',
            node_data={'type': 'input connector'}, parent=node,
            workflow=node.workflow)
    create_node(name='output connector',
            node_data={'type': 'output connector'}, parent=node,
            workflow=node.workflow)

    for edge_data in node_data['edges']:
        source = node.children[edge_data['source']]
        destination = node.children[edge_data['destination']]
        models.Edge(
            destination_node=destination,
            destination_property=edge_data['destinationProperty'],
            source_node=source,
            source_property=edge_data['sourceProperty'],
        )


def _build_parallel_by_task(node_data, node):
    node.parallel_by = node_data['parallelBy']
    _build_task(node_data, node)


def _build_task(node_data, node):
    for index, data in enumerate(node_data['methods']):
        method_name = data['name']
        method = models.Method(node_id=node.id,
                name=method_name, index=index)
        method.parameters = {'commandLine':data['commandLine']}
        node.methods[method_name] = method


_NODE_BUILDERS = {
    'dag': _build_dag,
    'parallel-by-task': _build_parallel_by_task,
    'task': _build_task,
}
def _build_node(node_data, node):
    _node_builder = _NODE_BUILDERS.get(node.type)
    if _node_builder:
        _node_builder(node_data, node=node)


def _validate_dag_node_data(node_data):
    if 'input connector' in node_data['nodes']:
        raise exceptions.InvalidWorkflow(
                "'input connector' is a reserved node name")

    if 'output connector' in node_data['nodes']:
        raise exceptions.InvalidWorkflow(
                "'output connector' is a reserved node name")

def _get_node_type(node_data):
    if 'type' in node_data:
        if node_data['type'] in ['input connector', 'output connector']:
            return node_data['type'].lower()
        else:
            raise RuntimeError('Only input/output connector are '
                    'allowed explicit type, not (%s)' % node_data['type'])
    elif 'methods' in node_data:
        if 'parallelBy' in node_data:
            return 'parallel-by-task'
        else:
            return 'task'

    elif 'nodes' in node_data:
        return 'dag'

    else:
        raise RuntimeError('Unable to determine node type')


def create_node(name, node_data, parent=None, workflow=None):
    node_type = _get_node_type(node_data)

    node = models.Node.from_dict(name=name, type=node_type,
            workflow=workflow)
    if parent is not None:
        parent.children[name] = node

    _build_node(node_data, node=node)

    return node

def create_input_holder(root, inputs, color, workflow=None):
    node = models.InputHolder(name='input_holder',
            workflow=workflow)
    node.set_outputs(inputs, color=color)
    for i in inputs.iterkeys():
        models.Edge(source_node=node, destination_node=root,
                source_property=i, destination_property=i)
    return node
