from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from ptero_workflow.implementation.models.execution import Execution

class TaskExecution(Execution):
    __tablename__ = 'task_execution'

    id = Column(Integer, ForeignKey('execution.id'), primary_key=True)
    task_id = Column(Integer, ForeignKey('task.id'))
    task = relationship('Task', backref='executions')

    __mapper_args__ = {
        'polymorphic_identity': 'TaskExecution',
    }
