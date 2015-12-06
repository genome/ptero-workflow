from ..json_type import JSON
from .method_base import Method
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
from ptero_common import nicer_logging
from ptero_common.statuses import (scheduled, running, canceled, succeeded)

LOG = nicer_logging.getLogger(__name__)

__all__ = ['Converge']


class Converge(Method):
    __tablename__ = 'converge'
    service = 'workflow-converge'

    id = Column(Integer, ForeignKey('method.id', ondelete='CASCADE'),
            primary_key=True)

    parameters = Column(JSON, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'Converge',
    }

    VALID_CALLBACK_TYPES = Method.VALID_CALLBACK_TYPES.union(['execute'])

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

        execution = self.get_or_create_execution(body_data['color'],
                body_data['group'])

        execution.status = scheduled
        s.flush()
        execution.status = running
        s.flush()

        if (self.task.is_canceled):
            execution.status = canceled
            s.commit()

            response_url = body_data['response_links']['failure']
            LOG.info('Notifying petri: execution "%s" failed for'
                    ' workflow "%s"', execution.name, self.workflow.name,
                    extra={'workflowName':self.workflow.name})
            self.http.delay('PUT', response_url)
        else:
            execution.update({'outputs': self.get_outputs(execution.get_inputs())})
            execution.status = succeeded
            s.commit()

            response_url = body_data['response_links']['success']
            LOG.info('Notifying petri: execution "%s" succeeded for'
                    ' workflow "%s"', execution.name, self.workflow.name,
                    extra={'workflowName':self.workflow.name})
            self.http.delay('PUT', response_url)

    def get_outputs(self, inputs):
        value = [inputs[x] for x in self.parameters['input_names']]
        return {
            'result': 1,
            self.parameters['output_name']: value,
        }

    def get_parameters(self, **kwargs):
        return self.parameters
