from sqlalchemy.orm import relationship
from ptero_workflow.implementation.models.execution import Execution

class MethodExecution(Execution):
    method = relationship('Method', backref='executions')

    __mapper_args__ = {
        'polymorphic_identity': 'MethodExecution',
    }
