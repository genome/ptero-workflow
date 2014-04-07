from . import exceptions
from . import models
import simplejson


class Backend(object):
    def __init__(self, session):
        self.session = session

    def create_workflow(self, workflow_data):
        if 'input connector' in workflow_data['operations']:
            raise exceptions.InvalidWorkflow(
                    "'input connector' is a reserved operation name")

        if 'output connector' in workflow_data['operations']:
            raise exceptions.InvalidWorkflow(
                    "'output connector' is a reserved operation name")

        workflow = models.Workflow()

        workflow.environment = simplejson.dumps(workflow_data['environment'])

        workflow.inputs = simplejson.dumps(workflow_data['inputs'])

        workflow.operations['input connector'] = models.Operation(
                type='input', name='input connector')

        workflow.operations['output connector'] = models.Operation(
                type='output', name='output connector')

        for name, operation_data in workflow_data['operations'].iteritems():
            workflow.operations[name] = models.Operation(
                    name=name, **operation_data)

        for link_data in workflow_data['links']:
            source = workflow.operations[link_data['source']]
            destination = workflow.operations[link_data['destination']]
            models.Link(
                    source_operation=source,
                    destination_operation=destination,
                    source_property=link_data['source_property'],
                    destination_property=link_data['destination_property'])

        self.session.add(workflow)
        self.session.commit()

        return workflow.id

    def get_workflow(self, workflow_id):
        return self.session.query(models.Workflow).get(workflow_id).as_dict

    def cleanup(self):
        pass
