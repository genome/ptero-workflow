from .. import result
from .task_base import Task
from ..execution.method_execution import MethodExecution
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
import logging
from ptero_common import statuses


LOG = logging.getLogger(__name__)


__all__ = ['InputConnector']


class InputConnector(Task):
    __tablename__ = 'input_connector'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    VALID_CALLBACK_TYPES = Task.VALID_CALLBACK_TYPES.union(['set_dag_status_running'])

    __mapper_args__ = {
        'polymorphic_identity': 'InputConnector',
    }

    def attach_subclass_transitions(self, transitions, start_place):
        return self.attach_notify_and_wait_transitions(transitions, start_place,
                'set_dag_status_running')

    def set_dag_status_running(self, body_data, query_string_data):
        color = body_data['color']

        try:
            self._set_dag_status_running(color)
            response_url = body_data['response_links']['success']
        except:
            LOG.exception("Unexpected exception setting dag status to running")
            response_url = body_data['response_links']['failure']
        self.http.delay('PUT', response_url)

    def _set_dag_status_running(self, color):
        s = object_session(self)
        execution = s.query(MethodExecution).filter(
                MethodExecution.method==self.parent,
                MethodExecution.color==color).one()
        execution.status = statuses.scheduled
        execution.status = 'running'
        s.commit()


    def resolve_output_source(self, session, name, parallel_depths):
        return self.parent.task.resolve_input_source(session, name,
                parallel_depths)

    def create_input_sources(self, session, parallel_depths):
        pass

    @property
    def input_names(self):
        return self.parent.task.input_names
