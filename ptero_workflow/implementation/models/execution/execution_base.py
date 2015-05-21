from ..base import Base
from ..json_type import JSON, MutableJSONDict
from flask import url_for
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, String
from sqlalchemy import UniqueConstraint, func
from sqlalchemy.orm import backref, relationship
from ptero_workflow.implementation.exceptions import (OutputsAlreadySet,
        ImmutableUpdateError, InvalidStatusError)
from sqlalchemy.orm.session import object_session
from operator import attrgetter
import logging
from ptero_common import statuses

LOG = logging.getLogger(__name__)

__all__ = ['Execution']

class Execution(Base):
    __tablename__ = 'execution'

    __table_args__ = (
        UniqueConstraint('method_id', 'color'),
        UniqueConstraint('task_id', 'color'),
    )

    id = Column(Integer, primary_key=True)

    color = Column(Integer, index=True, nullable=False)
    parent_color = Column(Integer, index=True, nullable=True)

    method_id = Column(Integer, ForeignKey('method.id'),
            index=True, nullable=True)
    task_id = Column(Integer, ForeignKey('task.id'),
            index=True, nullable=True)
    _status = Column('status', Text, nullable=False)

    data = Column(MutableJSONDict, nullable=False)
    colors = Column(JSON)
    begins = Column(JSON)

    workflow_id = Column(Integer, ForeignKey('workflow.id'),
        nullable=False, index=True)
    workflow = relationship('Workflow', foreign_keys=[workflow_id])

    type = Column(String, nullable=False)
    __mapper_args__ = {
            'polymorphic_on': 'type',
    }

    UPDATE_METHODS = {
        'status': 'update_status',
        'data': 'update_data',
        'outputs': 'update_outputs',
    }

    @property
    def name(self):
        if self.method_id is not None:
            return "%s.%s.%s" % (
                    self.method.task.name,
                    self.method.name,
                    self.id,
            )
        else:
            return "%s.%s" % (
                    self.task.name,
                    self.id,
            )

    def __init__(self, *args, **kwargs):
        Base.__init__(self, *args, **kwargs)
        self._status = 'new'
        ExecutionStatusHistory(execution=self, status='new')


    @property
    def ordered_status_history(self):
        return sorted(self.status_history, key=attrgetter('timestamp'))


    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        if not statuses.is_valid(status):
            raise InvalidStatusError(
                    "Status (%s) isn't one of the valid status values: %s" %
                    (status, str(statuses.VALID_STATUSES)))
        else:
            if not statuses.is_valid_transition(self.status, status):
                LOG.debug("Refusing to change status from (%s) to (%s), valid status transitions are: %s",
                    self.status, status, str(statuses.VALID_STATUS_TRANSITIONS[status]))
            else:
                self.send_webhooks(status)
                self._status = status
                return ExecutionStatusHistory(execution=self, status=status)

    def send_webhooks(self, status):
        webhooks = self.parent.get_webhooks(status)
        if webhooks:
            # this involves at least a little overhead, so only do it once
            # we know that there are webhooks to send.
            webhook_data = {
                # not sure how to get to the workflow, but would be nice...
                #'workflowUrl': self.workflow.url
                'executionUrl': self.url,
                'targetName': self.parent.name,
                'targetType': self.parent.type,
                'color': self.color,
                'parentColor': self.parent_color,
                'oldStatus': self.status,
                'status': status,
            }
            for webhook in webhooks:
                webhook.send_after_commit(**webhook_data)

    def as_dict(self, detailed):
        result = {name: getattr(self, name) for name in ['name', 'color',
            'parent_color', 'data', 'colors', 'begins', 'status']}

        result['status_history'] = [h.as_dict(detailed=detailed)
                for h in self.ordered_status_history]

        if not detailed:
            result['inputs'] = self.get_inputs()
            result['outputs'] = self.get_outputs()

        return result

    def update(self, update_data):
        old_data = self.as_dict(detailed=False)
        needs_updating = [name for name, new_value in update_data.iteritems()
                if old_data[name] != new_value]

        invalid_fields = set(needs_updating) - set(self.UPDATE_METHODS.keys())
        if (invalid_fields):
            raise ImmutableUpdateError("Cannot update the following fields: %s"
                    % invalid_fields)
        else:
            for name in needs_updating:
                getattr(self, self.UPDATE_METHODS[name])(old_data[name], update_data[name])

    def update_status(self, old_status, new_status):
        self.status = new_status

    def update_data(self, old_data, new_data):
        updated_data = old_data.copy()
        updated_data.update(new_data)
        self.data = updated_data

    def update_outputs(self, old_outputs, new_outputs):
        if (old_outputs):
            raise OutputsAlreadySet(
                    "Cannot update outputs after they have been set once")
        else:
            return self.method.task.set_outputs(outputs=new_outputs,
                    color=self.color, parent_color=self.parent_color)

    @property
    def url(self):
        return url_for('execution-detail', execution_id=self.id,
                _external=True)


class ExecutionStatusHistory(Base):
    __tablename__ = 'execution_status_history'

    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey('execution.id'), nullable=False)

    timestamp = Column(DateTime(timezone=True), default=func.now(),
            nullable=False)

    status = Column(Text, index=True, nullable=False)

    execution = relationship(Execution,
            backref=backref('status_history', order_by=timestamp, lazy='joined'))

    def as_dict(self, detailed):
        return {'timestamp': str(self.timestamp), 'status': self.status}
