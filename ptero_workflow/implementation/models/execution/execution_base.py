from ..base import Base
from ..json_type import JSON, MutableJSONDict
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, String
from sqlalchemy import UniqueConstraint, func
from sqlalchemy.orm import backref, relationship
from ptero_workflow.implementation.exceptions import (OutputsAlreadySet,
        ImmutableUpdateError)
import logging

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

    method_id = Column(Integer, ForeignKey('method.id'), nullable=True)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=True)

    data = Column(MutableJSONDict)
    colors = Column(JSON)
    begins = Column(JSON)

    type = Column(String, nullable=False)
    __mapper_args__ = {
            'polymorphic_on': 'type',
    }

    UPDATE_METHODS = {
        'status': 'update_status',
        'data': 'update_data',
        'outputs': 'update_outputs',
    }

    def __init__(self, *args, **kwargs):
        Base.__init__(self, *args, **kwargs)
        self.append_status('new')

    def append_status(self, status):
        return ExecutionStatusHistory(execution=self, status=status)

    @property
    def status(self):
        return self.status_history[-1].status

    def as_dict(self, detailed):
        result = {name: getattr(self, name) for name in ['color',
            'parent_color', 'data', 'colors', 'begins', 'status']}

        if not detailed:
            result['method'] = self.method.as_dict(detailed=detailed)
        result['inputs'] = self.get_inputs()
        result['outputs'] = self.get_outputs()
        result['status_history'] = [h.as_dict(detailed=detailed) for h in self.status_history]
        result['status'] = self.status

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
        self.append_status(new_status)

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


class ExecutionStatusHistory(Base):
    __tablename__ = 'execution_status_history'

    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey('execution.id'), nullable=False)

    timestamp = Column(DateTime(timezone=True), default=func.now(),
            nullable=False)

    status = Column(Text, index=True, nullable=False)

    execution = relationship(Execution,
            backref=backref('status_history', order_by=timestamp))

    def as_dict(self, detailed):
        return {'timestamp': str(self.timestamp), 'status': self.status}
