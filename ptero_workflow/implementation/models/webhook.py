from .base import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Index
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session
from sqlalchemy import event
from collections import defaultdict
import celery
from ptero_common import nicer_logging
from ptero_common.statuses import succeeded, failed, canceled, errored
from ptero_common.utils import format_dict_of_lists

LOG = nicer_logging.getLogger(__name__)

__all__ = ['Webhook']


class Webhook(Base):
    __tablename__ = 'webhook'
    __table_args__ = (
        Index('method_id', 'name'),
        Index('task_id', 'name'),
    )

    id = Column(Integer, primary_key=True)

    method_id = Column(Integer, ForeignKey('method.id'),
            index=True, nullable=True)
    task_id = Column(Integer, ForeignKey('task.id'),
            index=True, nullable=True)

    task = relationship('Task', backref='webhooks')
    method = relationship('Method', backref='webhooks')

    name = Column(String, index=True, nullable=False)
    url = Column(String, nullable=False)

    @property
    def parent(self):
        if self.parent_type is 'Method':
            return self.method
        else:
            return self.task

    @property
    def parent_type(self):
        if self.method_id is not None:
            return 'Method'
        else:
            return 'Task'

    @property
    def http(self):
        return celery.current_app.tasks[
                'ptero_common.celery.http.HTTP']

    def send(self, **data):
        LOG.info('Sending webhook: %s "%s" of workflow "%s" reached status %s '
                '-- %s',
                self.parent_type, self.parent.name, self.parent.workflow.name,
                self.name, self.url,
                extra={'workflowName':self.parent.workflow.name})
        self.http.delay('POST', self.url, webhookName=self.name, **data)

    def send_after_commit(self, **data):
        session = object_session(self)
        url = self.url
        name = self.name
        workflow_name = self.parent.workflow.name
        parent_type = self.parent_type
        parent_name = self.parent.name

        # Note: closure over self, url, name, data, ect...
        # Closure is to ensure no SQL is emmitted on a 'committed' session
        def callback(session):
            LOG.info('Sending webhook after commit: %s "%s" of workflow "%s" reached '
                    'status %s -- %s',
                    parent_type, parent_name, workflow_name, name, url,
                    extra={'workflowName':workflow_name})
            self.http.delay('POST', url, webhookName=name, **data)
        event.listen(session, "after_commit", callback)


NAME_SYNONYMS = {
        succeeded : [succeeded, "ended"],
        failed : [failed, "ended"],
        canceled : [canceled, "ended"],
        errored : [errored, "ended"],
}


def get_sorted_webhook_dict(entity):
    unsorted_webhook_dict = defaultdict(list)
    for webhook in entity.webhooks:
        unsorted_webhook_dict[webhook.name].append(webhook.url)

    return format_dict_of_lists(unsorted_webhook_dict)


def get_webhooks_for_task(task, name):
    s = object_session(task)
    equivalent_names = NAME_SYNONYMS.get(name, [name])
    return s.query(Webhook).filter_by(task_id=task.id).filter(
        Webhook.name.in_(equivalent_names)).all()


def get_webhooks_for_method(method, name):
    s = object_session(method)
    equivalent_names = NAME_SYNONYMS.get(name, [name])
    return s.query(Webhook).filter_by(method_id=method.id).filter(
        Webhook.name.in_(equivalent_names)).all()
