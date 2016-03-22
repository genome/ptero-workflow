from ..execution.method_execution import MethodExecution
from ..json_type import JSON
from .method_base import Method
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm.session import object_session
import celery
from ptero_common import nicer_logging
from ptero_common.statuses import (submitted, running,
        canceled, errored, succeeded, failed)

LOG = nicer_logging.getLogger(__name__)

__all__ = ['Job']


class Job(Method):
    __tablename__ = 'job'
    service = 'job'

    id = Column(Integer, ForeignKey('method.id', ondelete='CASCADE'),
            primary_key=True)

    parameters = Column(JSON, nullable=False)

    service_url = Column(Text, nullable=False)

    service_data_to_save = Column(JSON, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'Job',
    }

    VALID_CALLBACK_TYPES = Method.VALID_CALLBACK_TYPES.union(
            ['execute', 'submitted', 'running', 'succeeded',
             'errored', 'failed'])

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
            s.commit()
        else:
            self.submit_job.delay(execution.id)

    def submitted(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        execution.status = submitted
        self._update_execution_data(execution, body_data)

        s = object_session(self)
        s.commit()

    def running(self, body_data, query_string_data):
        execution = self._get_execution(query_string_data['execution_id'])

        execution.status = running
        self._update_execution_data(execution, body_data)

        s = object_session(self)
        s.commit()

    def _update_execution_data(self, execution, body_data):
        if self.service_data_to_save is not None:
            for field_name in self.service_data_to_save:
                if field_name in body_data:
                    execution.data[field_name] = body_data[field_name]
        else:
            return

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
            self._update_execution_data(execution, body_data)

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
        self._update_execution_data(execution, body_data)

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
        self._update_execution_data(execution, body_data)

        s = object_session(self)
        s.commit()

        response_url = execution.data['petri_response_links_for_job']['failure']
        LOG.info('Notifing petri: execution "%s" errored for'
                ' workflow "%s"', execution.name, self.workflow.name,
                extra={'workflowName':self.workflow.name})
        self.http.delay('PUT', response_url)

    @property
    def submit_job(self):
        return celery.current_app.tasks[
                'ptero_workflow.implementation.celery_tasks.submit_job.SubmitJob']

    def get_job_submit_url(self, job_id):
        return '%s/jobs/%s' % (self.service_url, job_id)

    def get_job_submit_data(self, execution_id):
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

        for status in (submitted, running, errored, failed, succeeded):
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
