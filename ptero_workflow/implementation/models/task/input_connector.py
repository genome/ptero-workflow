from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
from ptero_common import nicer_logging
from ptero_common import statuses


LOG = nicer_logging.getLogger(__name__)


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
        execution = self.get_or_create_execution(body_data, query_string_data)

        try:
            self._set_dag_status_running(execution)
            response_url = body_data['response_links']['success']
            LOG.info('Notifying petri: input connector (%s) set dag (%s) '
                    'status to running for workflow "%s"',
                    self.id, self.parent.name, self.workflow.name,
                    extra={'workflowName':self.workflow.name})
        except:
            LOG.exception("Exception while setting dag (%s) status "
                    "to running", self.parent.name)
            response_url = body_data['response_links']['failure']
            LOG.info('Notifying petri: input connector (%s) failed to set '
                    'dag (%s) status to running for workflow "%s"',
                    self.id, self.parent.name, self.workflow.name,
                    extra={'workflowName':self.workflow.name})
        self.http.delay('PUT', response_url)

    def _set_dag_status_running(self, execution):
        s = object_session(self)
        execution.status = statuses.scheduled
        s.flush()
        execution.status = statuses.running
        s.commit()


    def resolve_output_source(self, session, name, parallel_depths):
        return self.parent.task.resolve_input_source(session, name,
                parallel_depths)

    def create_input_sources(self, session, parallel_depths):
        pass

    @property
    def input_names(self):
        return self.parent.task.input_names
