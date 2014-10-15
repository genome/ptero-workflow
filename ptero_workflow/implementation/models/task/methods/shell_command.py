from ...job import Job, ResponseLink
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
            ['ended', 'execute'])

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

        job_id = self._submit_to_shell_command(colors, parallel_index,
                self.command_line)

        job = Job(task=self.task, method=self, color=color, job_id=job_id)
        s = object_session(self)
        for name, url in response_links.iteritems():
            link = ResponseLink(job=job, url=url, name=name)
            job.response_links[name] = link

        s.add(job)
        s.commit()

    def ended(self, body_data, query_string_data):
        job_id = body_data.pop('jobId')

        s = object_session(self)
        job = s.query(Job).filter_by(task=self.task, job_id=job_id).one()

        if body_data['exitCode'] == 0:
            outputs = simplejson.loads(body_data['stdout'])
            self.task.set_outputs(outputs, job.color)
            s.commit()
            return requests.put(job.response_links['success'].url)

        else:
            return requests.put(job.response_links['failure'].url)

    def _submit_to_shell_command(self, colors, parallel_index, command_line):
        body_data = self._shell_command_submit_data(colors, parallel_index,
                command_line)
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

    def _shell_command_submit_data(self, colors, parallel_index, command_line):
        return {
            'commandLine': command_line,
            'user': os.environ.get('USER'),
            'stdin': simplejson.dumps(
                self.task.get_inputs(colors, parallel_index)),
            'callbacks': {
                'ended': self.callback_url('ended'),
            },
        }
