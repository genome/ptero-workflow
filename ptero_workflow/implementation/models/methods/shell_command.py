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
from ptero_common.statuses import (scheduled, running, canceled, errored,
        succeeded, failed)

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
            ['execute', 'running', 'succeeded', 'errored', 'failed'])

    def attach_subclass_transitions(self, transitions, input_place_name):
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
        s = object_session(self)

        color = body_data['color']
        execution = s.query(MethodExecution).filter(
                MethodExecution.method==self,
                MethodExecution.color==color).one()
        execution.data['petri_response_links_for_shell_command'] = \
                body_data['response_links']
        s.commit()

        if (self.task.is_canceled):
            execution.status = canceled
            response_url = body_data['response_links']['failure']
            self.http.delay('PUT', response_url)
        else:
            group = body_data['group']
            colors = group.get('color_lineage', []) + [color]
            begins = group.get('begin_lineage', []) + [group['begin']]

            try:
                job_id = self._submit_to_shell_command(colors, begins, execution.id)
                execution.status = scheduled
                execution.data['job_id'] = job_id
            except Exception as e:
                execution.status = errored;
                execution.data['error_message'] = e.message

                response_url = body_data['response_links']['failure']
                self.http.delay('PUT', response_url)

        s.commit()

    def running(self, body_data, query_string_data):
        execution_id = query_string_data['execution_id']

        s = object_session(self)
        execution = s.query(MethodExecution).filter_by(id=execution_id,
                method_id=self.id).one()

        execution.status = running
        s.commit()

    def _get_execution(self, execution_id):
        s = object_session(self)
        return s.query(MethodExecution).filter_by(id=execution_id,
                method_id=self.id).one()

    def succeeded(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        if execution.outputs_are_set:
            execution.status = succeeded
            execution.data.update(body_data)

            s = object_session(self)
            s.commit()

            response_url = execution.data['petri_response_links_for_shell_command']['success']

            self.http.delay('PUT', response_url)
        else:
            execution.data['error'] = 'Command failed to set required outputs %s' %\
                    sorted(execution.missing_outputs)
            self.errored(body_data, query_string_data)

    def failed(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        execution.status = failed
        execution.data.update(body_data)

        s = object_session(self)
        s.commit()
        response_url = execution.data['petri_response_links_for_shell_command']['failure']

        self.http.delay('PUT', response_url)

    def errored(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        execution.status = errored
        execution.data.update(body_data)

        s = object_session(self)
        s.commit()

        response_url = execution.data['petri_response_links_for_shell_command']['failure']
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
            'webhooks': {status: self.callback_url(status, execution_id=execution_id)
                for status in (running, errored, failed, succeeded)
            },
        })
        return submit_data

    def get_parameters(self, detailed=False):
        parameters = self.parameters.copy()
        webhooks = self.get_webhooks()
        if webhooks:
            parameters['webhooks'] = self.get_webhooks()
        return parameters
