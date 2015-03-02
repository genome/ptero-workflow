from ..execution.method_execution import MethodExecution
from ..json_type import JSON
from .method_base import Method
from ptero_common.logging_configuration import logged_request
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
import celery
import logging
import os
import json
from pprint import pformat

LOG = logging.getLogger(__name__)

__all__ = ['ShellCommand']


class ShellCommand(Method):
    __tablename__ = 'shell_command'
    service = 'shell-command'

    id = Column(Integer, ForeignKey('method.id'), primary_key=True)

    parameters = Column(JSON, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'ShellCommand',
    }

    VALID_CALLBACK_TYPES = Method.VALID_CALLBACK_TYPES.union(
            ['begun', 'error', 'execute', 'failure', 'success'])

    def attach_transitions(self, transitions, input_place_name):
        transitions.append({
            'inputs': [input_place_name],
            'outputs': [self._pn('wait')],
            'action': {
                'type': 'notify',
                'url': self.callback_url('execute'),
                'response_places': {
                    'success': self._pn('execute_success'),
                    'failure': self._pn('execute_failure'),
                },
            }
        })

        transitions.extend([
            {
                'inputs': [self._pn('wait'), self._pn('execute_success')],
                'outputs': [self._pn('success')],
            },
            {
                'inputs': [self._pn('wait'), self._pn('execute_failure')],
                'outputs': [self._pn('failure')],
            }
        ])

        return self._pn('success'), self._pn('failure')

    def execute(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']
        response_links = body_data['response_links']

        colors = group.get('color_lineage', []) + [color]
        begins = group.get('begin_lineage', []) + [group['begin']]
        parent_color = _get_parent_color(colors)

        s = object_session(self)
        execution = MethodExecution(method=self, color=color,
                colors=colors, begins=begins,
                parent_color=parent_color, data={
                    'petri_response_links': response_links,
        })
        s.add(execution)
        s.commit()

        if (self.task.is_canceled):
            execution.append_status('canceled')
        else:
            job_id = self._submit_to_shell_command(colors, begins, execution.id)
            execution.data['job_id'] = job_id

        s.commit()

    def begun(self, body_data, query_string_data):
        execution_id = query_string_data['execution_id']

        s = object_session(self)
        execution = s.query(MethodExecution).filter_by(id=execution_id,
                method_id=self.id).one()

        execution.append_status('begun')
        s.commit()

    def success(self, body_data, query_string_data):
        execution_id = query_string_data['execution_id']

        s = object_session(self)
        execution = s.query(MethodExecution).filter_by(id=execution_id,
                method_id=self.id).one()

        execution.append_status('succeeded')
        s.commit()
        response_url = execution.data['petri_response_links']['success']

        self.http.delay('PUT', response_url)

    def failure(self, body_data, query_string_data):
        execution_id = query_string_data['execution_id']

        s = object_session(self)
        execution = s.query(MethodExecution).filter_by(id=execution_id,
                method_id=self.id).one()

        execution.append_status('failed')
        s.commit()
        response_url = execution.data['petri_response_links']['failure']

        self.http.delay('PUT', response_url)

    def error(self, body_data, query_string_data):
        execution_id = query_string_data['execution_id']

        s = object_session(self)
        execution = s.query(MethodExecution).filter_by(id=execution_id,
                method_id=self.id).one()

        execution.append_status('errored')
        s.commit()
        response_url = execution.data['petri_response_links']['failure']
        self.http.delay('PUT', response_url)

    def _submit_to_shell_command(self, colors, begins, execution_id):
        body_data = self._shell_command_submit_data(colors, begins,
                execution_id)
        result = self.http_with_result.delay('POST', self._shell_command_submit_url,
                **body_data)
        response_info = result.wait()
        if 'json' in response_info:
            return response_info['json']['jobId']
        else:
            raise RuntimeError("Cannot submit to shell-command:\n%s" %
                    pformat(response_info))

    @property
    def http(self):
        return celery.current_app.tasks[
                'ptero_common.celery.http.HTTP']

    @property
    def http_with_result(self):
        return celery.current_app.tasks[
                'ptero_common.celery.http.HTTPWithResult']

    @property
    def _shell_command_submit_url(self):
        return 'http://%s:%d/v1/jobs' % (
            os.environ['PTERO_SHELL_COMMAND_HOST'],
            int(os.environ['PTERO_SHELL_COMMAND_PORT']),
        )

    def _shell_command_submit_data(self, colors, begins, execution_id):
        submit_data = self.parameters

        if 'environment' not in submit_data:
            submit_data['environment'] = {}

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
