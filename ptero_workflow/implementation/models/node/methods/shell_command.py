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

    @property
    def command_line(self):
        return self.parameters['commandLine']

    def _place_name(self, kind):
        return self.task._method_place_name(self.name, kind)

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
                'url': self.task.event_url('execute', method=self.name),
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

    def execute(self, color, group, response_links):
        job_id = self._submit_to_shell_command(color, self.command_line)

        job = Job(node=self.task, method=self, color=color, job_id=job_id)
        s = object_session(self)
        for name, url in response_links.iteritems():
            link = ResponseLink(job=job, url=url, name=name)
            job.response_links[name] = link

        s.add(job)
        s.commit()

    def _submit_to_shell_command(self, color, command_line):
        body_data = self._shell_command_submit_data(color, command_line)
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

    def _shell_command_submit_data(self, color, command_line):
        return {
            'commandLine': command_line,
            'user': os.environ.get('USER'),
            'stdin': simplejson.dumps(self.task.get_inputs(color)),
            'callbacks': {
                'ended': self.task.event_url('ended'),
            },
        }
