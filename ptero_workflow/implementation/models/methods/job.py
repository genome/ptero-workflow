from ..execution.method_execution import MethodExecution
from ..json_type import JSON
from .method_base import Method
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm.session import object_session
import celery
import logging
from pprint import pformat
from ptero_common.statuses import (scheduled, running, canceled, errored,
        succeeded, failed)
from ptero_workflow.implementation import exceptions

LOG = logging.getLogger(__name__)

__all__ = ['Job']


class Job(Method):
    __tablename__ = 'job'
    service = 'job'

    id = Column(Integer, ForeignKey('method.id'), primary_key=True)

    parameters = Column(JSON, nullable=False)

    service_url = Column(Text, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'Job',
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

        execution = self.get_or_create_execution(body_data, query_string_data)
        execution.data['petri_response_links_for_job'] = \
                body_data['response_links']
        s.commit()

        if (self.task.is_canceled):
            execution.status = canceled
            response_url = body_data['response_links']['failure']
            self.http.delay('PUT', response_url)
        else:
            group = body_data['group']
            color = body_data['color']
            colors = group.get('color_lineage', []) + [color]
            begins = group.get('begin_lineage', []) + [group['begin']]

            try:
                job_id = self._submit_to_job_service(colors, begins, execution.id)
                execution.status = scheduled
                execution.data['job_id'] = job_id
            except Exception as e:
                LOG.exception(
                    'Failed to submit job to service. Execution id: %s' % execution.id)
                execution.status = errored;
                execution.data['error_message'] = e.message

                response_url = body_data['response_links']['failure']
                self.http.delay('PUT', response_url)

        s.commit()

    def running(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        self.validate_source(body_data, execution)

        execution.status = running

        s = object_session(self)
        s.commit()

    def _get_execution(self, execution_id):
        s = object_session(self)
        return s.query(MethodExecution).filter_by(id=execution_id,
                method_id=self.id).one()

    def succeeded(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        self.validate_source(body_data, execution)

        missing_outputs = execution.missing_outputs
        if execution.missing_outputs:
            execution.data['error'] = 'Command failed to set required outputs %s' %\
                    sorted(execution.missing_outputs)
            self.errored(body_data, query_string_data)
        else:
            execution.status = succeeded
            execution.data.update(body_data)

            s = object_session(self)
            s.commit()

            response_url = execution.data['petri_response_links_for_job']['success']

            self.http.delay('PUT', response_url)

    def failed(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        self.validate_source(body_data, execution)

        execution.status = failed
        execution.data.update(body_data)

        s = object_session(self)
        s.commit()
        response_url = execution.data['petri_response_links_for_job']['failure']

        self.http.delay('PUT', response_url)

    def errored(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        self.validate_source(body_data, execution)

        execution.status = errored
        execution.data.update(body_data)

        s = object_session(self)
        s.commit()

        response_url = execution.data['petri_response_links_for_job']['failure']
        self.http.delay('PUT', response_url)

    def _submit_to_job_service(self, colors, begins, execution_id):
        body_data = self._job_submit_data(colors, begins,
                execution_id)
        result = self.http_with_result.delay('POST', self._job_submit_url,
                **body_data)
        response_info = result.wait()
        if 'json' in response_info:
            return response_info['json']['jobId']
        else:
            raise RuntimeError("Cannot submit to job service.\n"
                "URL: %s\nResponse info: %s" % (self._job_submit_url,
                    pformat(response_info)))

    @property
    def http_with_result(self):
        return celery.current_app.tasks[
                'ptero_common.celery.http.HTTPWithResult']

    @property
    def _job_submit_url(self):
        return '%s/jobs' % self.service_url

    def _job_submit_data(self, colors, begins, execution_id):
        submit_data = self.parameters

        if 'environment' not in submit_data:
            submit_data['environment'] = {}

        submit_data['environment'].update({
            'PTERO_WORKFLOW_EXECUTION_URL': self.execution_url(execution_id),
            'PTERO_WORKFLOW_SUBMIT_URL': self.workflow_submit_url,
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

    def as_dict(self, detailed):
        result = Method.as_dict(self, detailed)
        result['serviceUrl'] = self.service_url
        return result;

    def as_skeleton_dict(self):
        result = Method.as_skeleton_dict(self)
        result['serviceUrl'] = self.service_url
        return result;

    def validate_source(self, request_body_data, execution):
        if execution.data['job_id'] != request_body_data['jobId']:
            raise exceptions.DuplicateJobError('Job from service (%s) '
                    'with id (%s) does not match submitted job id (%s)',
                    execution.data['job_id'], request_body_data['jobId'])
