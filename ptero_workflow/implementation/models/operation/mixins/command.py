from ...job import Job, ResponseLink
from .base import BasePetriMixin
from sqlalchemy.orm.session import object_session
import os
import requests
import simplejson


class OperationPetriMixin(BasePetriMixin):
    def _method_place_name(self, method, kind):
        return '%s-%s-%s' % (self.unique_name, method, kind)

    def _attach_action(self, transitions, action_ready_place):
        input_place_name = action_ready_place
        success_places = []
        for method in self.method_list:
            success_place, failure_place = self._attach_method(transitions,
                    method, input_place_name)
            input_place_name = failure_place
            success_places.append(success_place)

        for sp in success_places:
            transitions.append({
                'inputs': [sp],
                'outputs': [self.success_place_name],
            })

        return self.success_place_name

    def _attach_method(self, transitions, method, input_place_name):
        success_place_name = self._method_place_name(
                method.name, 'success')
        failure_place_name = self._method_place_name(
                method.name, 'failure')

        wait_place_name = self._method_place_name(
                method.name, 'wait')

        success_callback_place_name = self._method_place_name(
                method.name, 'success-callback')
        failure_callback_place_name = self._method_place_name(
                method.name, 'failure-callback')

        transitions.append({
            'inputs': [input_place_name],
            'outputs': [wait_place_name],
            'action': {
                'type': 'notify',
                'url': self.event_url('execute', method=method.name),
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

        method_name = query_string_data['method']
        method = self.methods[method_name]

        job_id = self._submit_to_fork(color, method.command_line)

        job = Job(operation=self, method=method, color=color, job_id=job_id)
        s = object_session(self)
        for name, url in response_links.iteritems():
            link = ResponseLink(job=job, url=url, name=name)
            job.response_links[name] = link

        s.add(job)
        s.commit()

    def ended(self, body_data, query_string_data):
        job_id = body_data.pop('job_id')

        s = object_session(self)
        job = s.query(Job).filter_by(operation=self, job_id=job_id).one()

        if body_data['exit_code'] == 0:
            outputs = simplejson.loads(body_data['stdout'])
            self.set_outputs(outputs, job.color)
            s.commit()
            return requests.put(job.response_links['success'].url)

        else:
            return requests.put(job.response_links['failure'].url)

    def _submit_to_fork(self, color, command_line):
        body_data = self._fork_submit_data(color, command_line)
        response = requests.post(self._fork_submit_url,
                data=simplejson.dumps(body_data),
                headers={'Content-Type': 'application/json'})
        return response.json()['job_id']

    @property
    def _fork_submit_url(self):
        return 'http://%s:%d/v1/jobs' % (
            os.environ.get('PTERO_FORK_HOST', 'localhost'),
            int(os.environ.get('PTERO_FORK_PORT', 80)),
        )

    def _fork_submit_data(self, color, command_line):
        return {
            'command_line': command_line,
            'user': os.environ.get('USER'),
            'stdin': simplejson.dumps(self.get_inputs(color)),
            'callbacks': {
                'ended': self.event_url('ended'),
            },
        }
