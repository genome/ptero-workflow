from . import exceptions
from . import models
import simplejson


class Backend(object):
    def __init__(self, session):
        self.session = session

    def create_workflow(self, workflow_data):
        self._validate_workflow_data(workflow_data)

        workflow_data['operations']['input connector']  = {'type': 'input'}
        workflow_data['operations']['output connector'] = {'type': 'output'}

        workflow = models.Workflow()

        workflow.environment = simplejson.dumps(workflow_data['environment'])
        workflow.inputs = simplejson.dumps(workflow_data['inputs'])

        workflow.root_operation = models.Operation(name='root', type='root')

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

    def _validate_workflow_data(self, workflow_data):
        if 'input connector' in workflow_data['operations']:
            raise exceptions.InvalidWorkflow(
                    "'input connector' is a reserved operation name")

        if 'output connector' in workflow_data['operations']:
            raise exceptions.InvalidWorkflow(
                    "'output connector' is a reserved operation name")
