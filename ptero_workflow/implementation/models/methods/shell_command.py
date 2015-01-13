from ..execution import Execution
from ..json_type import JSON
from .method_base import Method
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
import celery
import os
import requests
import json


__all__ = ['ShellCommand']


class ShellCommand(Method):
    __tablename__ = 'shell_command'

    id = Column(Integer, ForeignKey('method.id'), primary_key=True)

    parameters = Column(JSON, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'ShellCommand',
    }

    VALID_CALLBACK_TYPES = Method.VALID_CALLBACK_TYPES.union(
            ['begun', 'error', 'execute', 'failure', 'success'])

    def _place_name(self, kind):
        return '%s-%s-%s' % (self.task.unique_name, self.name, kind)

    def attach_transitions(self, transitions, input_place_name):
        success_place_name = self._place_name('success')
        failure_place_name = self._place_name('failure')

        wait_place_name = self._place_name('wait')

        success_callback_place_name = self._place_name('success-callback')
        failure_callback_place_name = self._place_name('failure-callback')

        transitions.append({
            'inputs': [input_place_name],
            'outputs': [wait_place_name],
            'action': {
                'type': 'notify',
                'url': self.callback_url('execute'),
                'response_places': {
                    'success': success_callback_place_name,
                    'failure': failure_callback_place_name,
                },
            }
        })

        transitions.extend([
            {
                'inputs': [wait_place_name, success_callback_place_name],
                'outputs': [success_place_name],
            },
            {
                'inputs': [wait_place_name, failure_callback_place_name],
                'outputs': [failure_place_name],
            }
        ])

        return success_place_name, failure_place_name

    def execute(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']
        response_links = body_data['response_links']

        colors = group.get('color_lineage', []) + [color]
        begins = group.get('begin_lineage', []) + [group['begin']]
        parent_color = _get_parent_color(colors)

        s = object_session(self)
        execution = Execution(method=self, color=color,
                colors=colors, begins=begins,
                parent_color=parent_color, data={
                    'petri_response_links': response_links,
        })
        s.add(execution)
        s.commit()

        job_id = self._submit_to_shell_command(colors, begins, execution.id)

        execution.data['job_id'] = job_id
        s.commit()

    def begun(self, body_data, query_string_data):
        execution_id = query_string_data['execution_id']

        s = object_session(self)
        execution = s.query(Execution).filter_by(id=execution_id,
                method_id=self.id).one()

        execution.append_status('begun')
        s.commit()

    def success(self, body_data, query_string_data):
        execution_id = query_string_data['execution_id']

        s = object_session(self)
        execution = s.query(Execution).filter_by(id=execution_id,
                method_id=self.id).one()

        execution.append_status('succeeded')
        s.commit()
        response_url = execution.data['petri_response_links']['success']

        self.http.delay('PUT', response_url)

    def failure(self, body_data, query_string_data):
        execution_id = query_string_data['execution_id']

        s = object_session(self)
        execution = s.query(Execution).filter_by(id=execution_id,
                method_id=self.id).one()

        execution.append_status('failed')
        s.commit()
        response_url = execution.data['petri_response_links']['failure']

        self.http.delay('PUT', response_url)

    def error(self, body_data, query_string_data):
        execution_id = query_string_data['execution_id']

        s = object_session(self)
        execution = s.query(Execution).filter_by(id=execution_id,
                method_id=self.id).one()

        execution.append_status('errored')
        s.commit()
        response_url = execution.data['petri_response_links']['failure']
        self.http.delay('PUT', response_url)

    def _submit_to_shell_command(self, colors, begins, execution_id):
        body_data = self._shell_command_submit_data(colors, begins,
                execution_id)
        response = requests.post(self._shell_command_submit_url,
                data=json.dumps(body_data),
                headers={'Content-Type': 'application/json'})
        return response.json()['jobId']

    @property
    def http(self):
        return celery.current_app.tasks[
                'ptero_workflow.implementation.celery_tasks.http.HTTP']

    @property
    def _shell_command_submit_url(self):
        return 'http://%s:%d/v1/jobs' % (
            os.environ['PTERO_SHELL_COMMAND_HOST'],
            int(os.environ['PTERO_SHELL_COMMAND_PORT']),
        )

    def _shell_command_submit_data(self, colors, begins, execution_id):
        submit_data = self.parameters

        submit_data['environment'].update({
            'PTERO_WORKFLOW_EXECUTION_URL': self.execution_url(execution_id),
        })

        submit_data.update({
            'webhooks': {
                'begun': self.callback_url('begun', execution_id=execution_id),
                'error': self.callback_url('error', execution_id=execution_id),
                'failure': self.callback_url('failure', execution_id=execution_id),
                'success': self.callback_url('success', execution_id=execution_id),
            },
        })
        return submit_data

def _get_parent_color(colors):
    if len(colors) == 1:
        return None

    else:
        return colors[-2]
