from sqlalchemy.orm import relationship
from ptero_workflow.implementation.models.execution import Execution

class TaskExecution(Execution):
    task = relationship('Task', backref='executions')
    __mapper_args__ = {
        'polymorphic_identity': 'TaskExecution',
    }
