from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from ptero_workflow.implementation.models.execution import Execution

class MethodExecution(Execution):
    __tablename__ = 'method_execution'

    id = Column(Integer, ForeignKey('execution.id'), primary_key=True)

    method_id = Column(Integer, ForeignKey('method.id'), nullable=False)
    method = relationship('Method', backref='executions')

    __mapper_args__ = {
        'polymorphic_identity': 'TaskExecution',
    }
