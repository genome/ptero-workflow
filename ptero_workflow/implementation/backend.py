from . import models
from . import tasks
import simplejson


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

        return workflow.id

    def _save_workflow(self, workflow_data):
        workflow = models.Workflow(
            environment=simplejson.dumps(workflow_data['environment']),
        )

        root_data = {
            'tasks': workflow_data['tasks'],
            'edges': workflow_data['edges'],
            'parallelBy': workflow_data.get('parallelBy'),
        }

        workflow.root_task = tasks.create_task('root',
                root_data, workflow=workflow)

        workflow.input_holder_task = tasks.create_input_holder(
                workflow.root_task, workflow_data['inputs'], color=0,
                workflow=workflow)

        workflow.root_task.create_input_sources(self.session, [])

        self.session.add(workflow)
        self.session.commit()

        return workflow

    def get_workflow(self, workflow_id):
        return self.session.query(models.Workflow).get(workflow_id).as_dict

    def get_workflow_outputs(self, workflow_id):
        workflow = self.session.query(models.Workflow).get(workflow_id)
        return workflow.get_outputs()

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
