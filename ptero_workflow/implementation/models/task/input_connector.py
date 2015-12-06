from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer
from ptero_common import nicer_logging


LOG = nicer_logging.getLogger(__name__)


__all__ = ['InputConnector']


class InputConnector(Task):
    __tablename__ = 'input_connector'

    id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
            primary_key=True)

    VALID_CALLBACK_TYPES = Task.VALID_CALLBACK_TYPES.union(['set_dag_status_running'])

    __mapper_args__ = {
        'polymorphic_identity': 'InputConnector',
    }

    def attach_subclass_transitions(self, transitions, start_place):
        return self.attach_notify_and_wait_transitions(transitions, start_place,
                'set_dag_status_running')

    def set_dag_status_running(self, body_data, query_string_data):
        execution = self.parent.get_or_create_execution(body_data['color'],
                body_data['group'])

        try:
            self.parent.set_status_running(body_data['color'],
                    body_data['group'])
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

    def resolve_output_source(self, session, name, parallel_depths):
        return self.parent.task.resolve_input_source(session, name,
                parallel_depths)

    def create_input_sources(self, session, parallel_depths):
        pass

    @property
    def input_names(self):
        return self.parent.task.input_names
