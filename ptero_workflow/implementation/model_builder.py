from networkx.exception import NetworkXUnfeasible
from ptero_workflow.implementation import exceptions, models
from ptero_workflow.implementation import validators
from ptero_workflow.utils import deterministic_topological_ordering


class ModelBuilder(object):
    def __init__(self, data):
        validators.required_inputs(data)
        self.data = data
        self.workflow = models.Workflow(name=data.get('name'))

    def build_workflow(self):
        root_task = self.build_root_task()
        self.workflow.root_task = root_task

        root_method = root_task.method_list[0]
        self.build_initial_dag_execution(root_method)

        input_holder = self.build_input_holder()
        self.set_workflow_inputs(input_holder)

        self.build_root_task_output_link()

        return self.workflow

    def build_root_task(self):
        task = self.build_task('root', self.root_task_data)
        task.topological_index = -1
        return task

    @property
    def root_task_data(self):
        return {
            'methods': [
                {
                    'name': 'root',
                    'parameters': {
                        'tasks': self.data['tasks'],
                        'links': self.data['links'],
                    },
                    'webhooks': self.data.get('webhooks', {}),
                    'service': 'workflow',
                },
            ],
        }

    def build_task(self, task_name, task_data, parent_method=None):
        task = models.MethodList(name=task_name,
                parallel_by=task_data.get('parallelBy'),
                parent=parent_method,
                workflow=self.workflow)

        webhook_data = task_data.get('webhooks', {})
        self.build_webhooks_for_task(webhook_data, task)

        for index, method_data in enumerate(task_data.get('methods', [])):
            task.method_list.append(
                self.build_method(method_data, index=index, parent_task=task))

        return task

    def build_webhooks_for_task(self, webhook_data, task):
        return self.build_webhooks_for_entity(webhook_data, entity=task,
                arg_name='task')

    def build_webhooks_for_method(self, webhook_data, method):
        return self.build_webhooks_for_entity(webhook_data, entity=method,
                arg_name='method')

    def build_webhooks_for_entity(self, webhook_data, entity, arg_name):
        result = []
        for name, webhooks in webhook_data.items():
            if not isinstance(webhooks, list):
                webhooks = [webhooks]
            for url in webhooks:
                args = {'name': name,
                        'url': url,
                        arg_name: entity}
                result.append(models.Webhook(**args))
        return result

    def build_method(self, method_data, index=None, parent_task=None):
        service_name = method_data['service']
        if service_name == 'workflow':
            method = self.build_dag_method(method_data, index, parent_task)
        else:
            method_class = models.SUBCLASS_LOOKUP[service_name]
            method = self.build_service_method(method_data, index, parent_task,
                    method_class)

        webhook_data = method_data.get('webhooks', {})
        self.build_webhooks_for_method(webhook_data, method)

        return method

    def build_dag_method(self, method_data, index, parent_task):
        validators.dag_task_names(method_data['parameters']['tasks'])

        method = models.DAG(name=method_data['name'], index=index,
                task=parent_task, workflow=self.workflow)

        children = self.build_dag_children(method_data, method)
        method.children = children

        links_data = method_data['parameters']['links']
        validators.unique_links(links_data)
        self.build_links(links_data, method)

        return method

    def get_deterministic_topological_ordering(self, dag_data):
        nodes = dag_data['parameters']['tasks'].keys()
        links = [(l['source'], l['destination'])
                for l in dag_data['parameters']['links']]
        try:
            ordering = deterministic_topological_ordering(nodes, links,
                    start_node='input connector')
        except NetworkXUnfeasible:
            raise exceptions.DAGCycleError('DAG named "%s" has a cycle' % 
                    dag_data['name'])

        # disregard input_connector and output_connector
        return ordering[1:-1]

    def build_dag_children(self, dag_data, parent_method):
        children = {}
        ordering = self.get_deterministic_topological_ordering(dag_data)
        for idx, name in enumerate(ordering):
            task_data = dag_data['parameters']['tasks'][name]
            task = self.build_task(name, task_data,
                    parent_method=parent_method)
            task.topological_index = idx
            children[name] = task

        children['input connector'] = models.InputConnector(
            name='input connector', parent=parent_method,
            workflow=self.workflow, topological_index=-1)
        children['output connector'] = models.OutputConnector(
            name='output connector', parent=parent_method,
            workflow=self.workflow, topological_index=-1)

        return children

    def build_links(self, links_data, method):
        for link_data in links_data:
            source = method.children[link_data['source']]
            destination = method.children[link_data['destination']]
            link = models.Link(
                destination_task=destination,
                source_task=source,
            )
            for source_property, destination_part in \
                    link_data.get('dataFlow', {}).items():
                if isinstance(destination_part, basestring):
                    models.DataFlowEntry(source_property=source_property,
                        destination_property=destination_part,
                        link=link)
                else:
                    for destination_property in destination_part:
                        models.DataFlowEntry(source_property=source_property,
                            destination_property=destination_property,
                            link=link)

    def build_service_method(self, method_data, index, parent_task, cls):
        parameters = method_data['parameters'].copy()

        constructor_args = {
                'name': method_data['name'],
                'index': index,
                'task': parent_task,
                'parameters': parameters,
                'workflow': self.workflow
        }

        if 'serviceUrl' in method_data:
            constructor_args['service_url'] = method_data['serviceUrl']

        return cls(**constructor_args)

    def build_initial_dag_execution(self, root_method):
        return models.MethodExecution(method=root_method,
                color=0, parent_color=None, colors=[0],
                begins=[], workflow=self.workflow, data={})

    def build_input_holder(self):
        task = models.InputHolder(name='input_holder', workflow=self.workflow)
        link = models.Link(source_task=task,
                destination_task=self.workflow.root_task)
        for i in self.inputs.iterkeys():
            models.DataFlowEntry(source_property=i, destination_property=i,
                    link=link)
        return task

    @property
    def inputs(self):
        return self.data['inputs']

    def build_root_task_output_link(self):
        dummy_output_task = models.InputHolder(name='dummy output task',
                workflow=self.workflow)

        link = models.Link(source_task=self.workflow.root_task,
            destination_task=dummy_output_task)
        for link_data in self.data['links']:
            if 'output connector' == link_data['destination']:
                for source_property, destination_part in link_data.get('dataFlow', {}).items():
                    if isinstance(destination_part, basestring):
                        models.DataFlowEntry(source_property=destination_part,
                            destination_property=destination_part,
                            link=link)
                    else:
                        for destination_property in destination_part:
                            models.DataFlowEntry(source_property=destination_property,
                                destination_property=destination_property,
                                link=link)
        return link

    def set_workflow_inputs(self, input_holder):
        input_holder.set_outputs(self.inputs,
                color=self.workflow.color,
                parent_color=self.workflow.parent_color)
