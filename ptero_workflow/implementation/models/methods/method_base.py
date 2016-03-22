from ..base import Base
from ..execution.method_execution import MethodExecution
from .. import webhook
from ptero_workflow.urls import url_for
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
import celery
import urllib
from ptero_common import nicer_logging


LOG = nicer_logging.getLogger(__name__)

__all__ = ['Method']


class Method(Base):
    __tablename__ = 'method'
    service = 'NotImplementedError'

    __table_args__ = (
        UniqueConstraint('task_id', 'name'),
    )

    VALID_CALLBACK_TYPES = set()

    id = Column(Integer, primary_key=True)

    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
            index=True)
    task = relationship('Task')

    name = Column(Text)

    index = Column(Integer, nullable=True, index=True)

    executions = relationship('MethodExecution',
            backref=backref('method', uselist=False),
            passive_deletes='all',
            collection_class=attribute_mapped_collection('color'))

    workflow_id = Column(Integer, ForeignKey('workflow.id', ondelete='CASCADE'),
        nullable=False, index=True)
    workflow = relationship('Workflow', foreign_keys=[workflow_id])

    type = Column(Text, nullable=False, index=True)
    __mapper_args__ = {
        'polymorphic_on': 'type',
    }


    def _pn(self, *args):
        name_base = '-'.join(['method', str(self.id), self.name.replace(' ','_')])
        return '-'.join([name_base] + list(args))

    def attach_transitions(self, transitions, start_place):
        return self.attach_subclass_transitions(transitions,
                        start_place)


    def get_or_create_execution(self, color, group):
        colors = group.get('color_lineage', []) + [color]
        begins = group.get('begin_lineage', []) + [group['begin']]
        parent_color = _get_parent_color(colors)

        s = object_session(self)

        try:
            return s.query(MethodExecution).filter(
                    MethodExecution.method==self,
                    MethodExecution.color==color).one()
        except NoResultFound:
            execution = MethodExecution(method=self, color=color,
                    colors=colors, begins=begins,
                    parent_color=parent_color,
                    workflow_id=self.workflow_id,
            )
            s.add(execution)

            try:
                s.commit()
                return execution
            except IntegrityError:
                s.rollback()
                return s.query(MethodExecution).filter(
                        MethodExecution.method==self,
                        MethodExecution.color==color).one()


    def get_webhooks(self, name=None):
        if name is not None:
            return webhook.get_webhooks_for_method(self, name)
        else:
            return webhook.get_sorted_webhook_dict(self)

    @property
    def http(self):
        return celery.current_app.tasks[
                'ptero_common.celery.http.HTTP']

    def handle_callback(self, callback_type, body_data, query_string_data):
        if callback_type in self.VALID_CALLBACK_TYPES:
            return getattr(self, callback_type)(body_data, query_string_data)
        else:
            raise RuntimeError('Invalid callback type (%s).  Allowed types: %s'
                    % (callback_type, self.VALID_CALLBACK_TYPES))

    def callback_url(self, callback_type, **params):
        if params:
            query_string = '?%s' % urllib.urlencode(params)
        else:
            query_string = ''

        base_url = url_for('method-callback',
                method_id=self.id, callback_type=callback_type)
        return base_url + query_string

    def execution_url(self, execution_id):
        return url_for('execution-detail', execution_id=execution_id)

    @property
    def workflow_submit_url(self):
        return url_for('workflow-list')

    def create_input_sources(self, session, parallel_depths):
        pass

    @property
    def parameters(self):
        raise NotImplementedError

    def as_dict(self, detailed):
        result = {
            'name': self.name,
            'service': self.service,
            'parameters': self.get_parameters(detailed=detailed),
        }

        webhooks = self.get_webhooks()
        if webhooks:
            result['webhooks'] = webhooks

        if detailed:
            result['executions'] = {
                    color: execution.as_dict(detailed=detailed)
                    for color, execution in self.executions.iteritems()}

        return result

    def as_dict_for_summary(self):
        execution_summary = self.execution_summary
        result = {
            'executionSummary': execution_summary,
            'name': self.name,
            'service': self.service,
        }
        return result

    @property
    def execution_summary(self):
        s = object_session(self)
        rows = s.execute("""
            SELECT status, count(status)
            FROM execution WHERE method_id = :id
            GROUP BY status;
        """, {"id": self.id})
        return {row[0]: row[1] for row in rows}

    def as_skeleton_dict(self):
        result = {
            'id': self.id,
            'name': self.name,
            'service': self.service,
        }
        return result

    def status(self, color):
        try:
            return self.executions[color].status
        except KeyError:
            # if method hasn't created any Executions of this color yet
            return None

    def cancel(self):
        LOG.info("Canceling method ID:NAME (%s:%s) of task (%s:%s)",
            self.id, self.name, self.task.id, self.task.name,
            extra={'workflowName':self.workflow.name})
        for execution in self.executions.values():
            execution.cancel()

    def issue_job_delete_requests(self):
        LOG.info("Issuing delete requests for "
                "method ID:NAME (%s:%s) of task (%s:%s)",
            self.id, self.name, self.task.id, self.task.name,
            extra={'workflowName':self.workflow.name})
        for execution in self.executions.values():
            execution.issue_job_delete_requests()


def _get_parent_color(colors):
    if len(colors) == 1:
        return None

    else:
        return colors[-2]
