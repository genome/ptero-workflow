from ..execution.method_execution import MethodExecution
from ..json_type import JSON
from .method_base import Method
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
import logging
from ptero_common.statuses import (scheduled, running, canceled, succeeded)

LOG = logging.getLogger(__name__)

__all__ = ['Block']


class Block(Method):
    __tablename__ = 'block'
    service = 'workflow-block'

    id = Column(Integer, ForeignKey('method.id'), primary_key=True)

    parameters = Column(JSON, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'Block',
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

        color = body_data['color']
        execution = s.query(MethodExecution).filter(
                MethodExecution.method==self,
                MethodExecution.color==color).one()

        execution.status = scheduled
        s.flush()
        execution.status = running
        s.flush()

        if (self.task.is_canceled):
            execution.status = canceled
            s.commit()

            response_url = body_data['response_links']['failure']
            self.http.delay('PUT', response_url)
        else:
            outputs = execution.get_inputs()
            outputs.setdefault('result', 1)
            execution.update({'outputs': outputs})
            execution.status = succeeded
            s.commit()

            response_url = body_data['response_links']['success']
            self.http.delay('PUT', response_url)

    def get_parameters(self, **kwargs):
        return {}
