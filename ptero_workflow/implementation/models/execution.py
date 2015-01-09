from .base import Base
from .json_type import JSON
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy import UniqueConstraint, func
from sqlalchemy.orm import backref, relationship


__all__ = ['Execution']


class Execution(Base):
    __tablename__ = 'execution'

    __table_args__ = (
        UniqueConstraint('method_id', 'color'),
    )

    id = Column(Integer, primary_key=True)

    method_id = Column(Integer, ForeignKey('method.id'), nullable=False)
    method = relationship('Method', backref='executions')

    color = Column(Integer, index=True, nullable=False)
    parent_color = Column(Integer, index=True, nullable=True)

    data = Column(JSON)
    colors = Column(JSON)
    begins = Column(JSON)

    def append_status(self, status):
        return ExecutionStatusHistory(execution=self, status=status)

    def get_inputs(self):
        return self.method.task.get_inputs(colors=self.colors,
                begins=self.begins)

    def set_outputs(self, outputs):
        return self.method.task.set_outputs(outputs=outputs,color=self.color,
                parent_color=self.parent_color)


class ExecutionStatusHistory(Base):
    __tablename__ = 'execution_status_history'

    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey('execution.id'), nullable=False)

    timestamp = Column(DateTime(timezone=True), default=func.now(),
            nullable=False)

    status = Column(Text, index=True, nullable=False)

    execution = relationship(Execution,
            backref=backref('status_history', order_by=timestamp))
