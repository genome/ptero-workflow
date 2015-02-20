from . import models
from . import tasks
from sqlalchemy.exc import IntegrityError
from ptero_workflow.implementation.exceptions import OutputsAlreadySet
import logging

LOG = logging.getLogger(__name__)


_TASK_BASE = 'ptero_workflow.implementation.celery_tasks.'


class Backend(object):
    def __init__(self, session, celery_app):
        self.session = session
        self.celery_app = celery_app

    @property
    def submit_net_task(self):
        return self.celery_app.tasks[_TASK_BASE + 'submit_net.SubmitNet']

    def create_workflow(self, workflow_data):
        workflow = self._save_workflow(workflow_data)

        self.submit_net_task.delay(workflow.id)

        return workflow.id, workflow.as_dict

    def _save_workflow(self, workflow_data):
        workflow = models.Workflow()

        root_data = {
            'methods': [
                {
                    'name': 'root',
                    'parameters': {
                        'tasks': workflow_data['tasks'],
                        'links': workflow_data['links'],
                    },
                    'service': 'workflow',
                },
            ],
        }

        workflow.root_task = tasks.build_task('root', root_data)

        workflow.input_holder_task = tasks.create_input_holder(
                workflow.root_task, workflow_data['inputs'], color=0)

        dummy_output_task = models.InputHolder(name='dummy output task')
        self.session.add(dummy_output_task)

        for link_data in workflow_data['links']:
            if 'output connector' == link_data['destination']:
                self.session.add(models.Link(source_task=workflow.root_task,
                        source_property=link_data['destinationProperty'],
                        destination_task=dummy_output_task,
                        destination_property=link_data['destinationProperty']))

        self.session.add(workflow)
        self.session.commit()

        workflow.root_task.create_input_sources(self.session, [])

        self.session.commit()

        return workflow

    def get_workflow(self, workflow_id):
        return self.session.query(models.Workflow).get(workflow_id).as_dict

    def get_workflow_status(self, workflow_id):
        return self.session.query(models.Workflow).get(workflow_id).status

    def get_workflow_details(self, workflow_id):
        workflow = self.session.query(models.Workflow).get(workflow_id)

    def get_workflow_outputs(self, workflow_id):
        workflow = self.session.query(models.Workflow).get(workflow_id)
        return workflow.get_outputs()

    def get_execution(self, execution_id):
        execution = self.session.query(models.Execution).get(execution_id)
        return execution.as_dict

    def update_execution(self, execution_id, update_data):
        execution = self.session.query(models.Execution).get(execution_id)
        execution.update(update_data)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise OutputsAlreadySet
        return execution.as_dict

    def handle_task_callback(self, task_id, callback_type, body_data,
            query_string_data):
        task = self.session.query(models.Task
                ).filter_by(id=task_id).one()
        task.handle_callback(callback_type, body_data, query_string_data)

    def handle_method_callback(self, method_id, callback_type, body_data,
            query_string_data):
        method = self.session.query(models.Method
                ).filter_by(id=method_id).one()
        method.handle_callback(callback_type, body_data, query_string_data)

    def cleanup(self):
        self.session.rollback()
