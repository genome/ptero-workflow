from ..execution.method_execution import MethodExecution
from ..json_type import JSON
from .method_base import Method
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm.session import object_session
import celery
from ptero_common import nicer_logging
from pprint import pformat
from ptero_common.statuses import (scheduled, running, canceled, errored,
        succeeded, failed)
import uuid

LOG = nicer_logging.getLogger(__name__)

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
        if self.index == 0:
            self.task.set_status_running(body_data['color'],
                body_data['group'])

        s = object_session(self)

        execution = self.get_or_create_execution(body_data['color'],
                body_data['group'])
        execution.data['petri_response_links_for_job'] = \
                body_data['response_links']
        s.commit()

        if (self.task.is_canceled):
            execution.status = canceled
            response_url = body_data['response_links']['failure']
            LOG.info('Notifing petri: execution "%s" canceled for'
                    ' workflow "%s"', execution.name, self.workflow.name,
                    extra={'workflowName': self.workflow.name})
            self.http.delay('PUT', response_url)
        else:
            group = body_data['group']
            color = body_data['color']
            colors = group.get('color_lineage', []) + [color]
            begins = group.get('begin_lineage', []) + [group['begin']]

            job_id = str(uuid.uuid4())
            execution.data['jobId'] = job_id
            s.commit()

            try:
                job_url = self._submit_to_job_service(job_id, colors,
                        begins, execution)
                execution.status = scheduled
                execution.data['jobUrl'] = job_url
            except Exception as e:
                LOG.exception(
                        'Failed to submit job to service. Execution id: %s'
                        % execution.id)
                execution.status = errored;
                execution.data['error_message'] = e.message

                response_url = body_data['response_links']['failure']
                LOG.info('Notifying petri: execution "%s" failed for'
                        ' workflow "%s"', execution.name, self.workflow.name,
                        extra={'workflowName':self.workflow.name})
                self.http.delay('PUT', response_url)

        s.commit()

    def running(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        execution.status = running

        s = object_session(self)
        s.commit()

    def _get_execution(self, execution_id):
        s = object_session(self)
        return s.query(MethodExecution).filter_by(id=execution_id,
                method_id=self.id).one()

    def succeeded(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        missing_outputs = execution.missing_outputs
        if execution.missing_outputs:
            execution.data['error'] = 'Command failed to set required outputs %s' %\
                    sorted(execution.missing_outputs)
            self.errored(body_data, query_string_data)
        else:
            execution.status = succeeded

            s = object_session(self)
            s.commit()

            response_url = execution.data['petri_response_links_for_job']['success']

            LOG.info('Notifying petri: execution "%s" succeeded for'
                    ' workflow "%s"', execution.name, self.workflow.name,
                    extra={'workflowName':self.workflow.name})
            self.http.delay('PUT', response_url)

    def failed(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        execution.status = failed

        s = object_session(self)
        s.commit()
        response_url = execution.data['petri_response_links_for_job']['failure']

        LOG.info('Notifying petri: execution "%s" failed for'
                ' workflow "%s"', execution.name, self.workflow.name,
                extra={'workflowName':self.workflow.name})
        self.http.delay('PUT', response_url)

    def errored(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        execution.status = errored

        s = object_session(self)
        s.commit()

        response_url = execution.data['petri_response_links_for_job']['failure']
        LOG.info('Notifing petri: execution "%s" errored for'
                ' workflow "%s"', execution.name, self.workflow.name,
                extra={'workflowName':self.workflow.name})
        self.http.delay('PUT', response_url)

    def _submit_to_job_service(self, job_id, colors, begins, execution):
        body_data = self._job_submit_data(colors, begins,
                execution.id)
        job_url = "%s/%s" % (self._job_submit_url, job_id)
        LOG.info('Submitting Job for execution "%s" of workflow '
                '"%s" -- %s', execution.name, self.workflow.name,
                self._job_submit_url, extra={'workflowName':self.workflow.name})
        result = self.http_with_result.delay('PUT', job_url, **body_data)
        response_info = result.wait()
        if 'json' in response_info:
            return (response_info['json']['jobId'],
                    response_info['headers']['location'])
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

        self.add_webhooks_to_submit_data(submit_data, execution_id)
        return submit_data

    def add_webhooks_to_submit_data(self, submit_data, execution_id):
        webhooks = submit_data.get('webhooks', {})

        for status in (running, errored, failed, succeeded):
            webhooks_entry = webhooks.get(status, [])
            new_webhook = self.callback_url(status, execution_id=execution_id)
            if isinstance(webhooks_entry, list):
                webhooks[status] = webhooks_entry + [new_webhook]
            else:
                webhooks[status] = [webhooks_entry, new_webhook]
        submit_data['webhooks'] = webhooks

    def get_parameters(self, detailed=False):
        return self.parameters

    def as_dict(self, detailed):
        result = Method.as_dict(self, detailed)
        result['serviceUrl'] = self.service_url
        return result;

    def as_skeleton_dict(self):
        result = Method.as_skeleton_dict(self)
        result['serviceUrl'] = self.service_url
        return result;
