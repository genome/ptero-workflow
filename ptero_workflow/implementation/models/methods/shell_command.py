from ..execution import Execution
from .method_base import Method
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
import os
import requests
import simplejson


__all__ = ['ShellCommand']


class ShellCommand(Method):
    __tablename__ = 'shell_command'

    id = Column(Integer, ForeignKey('method.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'ShellCommand',
    }

    VALID_CALLBACK_TYPES = Method.VALID_CALLBACK_TYPES.union(
            ['begun', 'ended', 'execute'])

    @property
    def command_line(self):
        return self.parameters['commandLine']

    def _place_name(self, kind):
        return '%s-%s-%s' % (self.task.unique_name, self.name, kind)

    def _attach(self, transitions, input_place_name):
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
        parallel_index = color - group['begin']

        s = object_session(self)
        execution = Execution(method=self, color=color, data={
            'petri_response_links': response_links,
        })
        s.add(execution)
        s.commit()

        job_id = self._submit_to_shell_command(colors, parallel_index,
                self.command_line, execution.id)

        execution.data['job_id'] = job_id
        s.commit()

    def begun(self, body_data, query_string_data):
        execution_id = query_string_data['execution_id']

        s = object_session(self)
        execution = s.query(Execution).filter_by(id=execution_id,
                method_id=self.id).one()

        execution.append_status('begun')
        s.commit()

    def ended(self, body_data, query_string_data):
        execution_id = query_string_data['execution_id']

        s = object_session(self)
        execution = s.query(Execution).filter_by(id=execution_id,
                method_id=self.id).one()

        if body_data['exitCode'] == 0:
            outputs = simplejson.loads(body_data['stdout'])
            self.task.set_outputs(outputs, execution.color)
            execution.append_status('succeeded')
            s.commit()
            return requests.put(
                    execution.data['petri_response_links']['success'])

        else:
            execution.append_status('failed')
            s.commit()
            return requests.put(
                    execution.data['petri_response_links']['failure'])

    def _submit_to_shell_command(self, colors, parallel_index, command_line,
            execution_id):
        body_data = self._shell_command_submit_data(colors, parallel_index,
                command_line, execution_id)
        response = requests.post(self._shell_command_submit_url,
                data=simplejson.dumps(body_data),
                headers={'Content-Type': 'application/json'})
        return response.json()['jobId']

    @property
    def _shell_command_submit_url(self):
        return 'http://%s:%d/v1/jobs' % (
            os.environ['PTERO_SHELL_COMMAND_HOST'],
            int(os.environ['PTERO_SHELL_COMMAND_PORT']),
        )

    def _shell_command_submit_data(self, colors, parallel_index, command_line,
            execution_id):
        return {
            'commandLine': command_line,
            'user': os.environ.get('USER'),
            'stdin': simplejson.dumps(
                self.task.get_inputs(colors, parallel_index)),
            'callbacks': {
                'begun': self.callback_url('begun', execution_id=execution_id),
                'ended': self.callback_url('ended', execution_id=execution_id),
            },
        }
