from .operation_base import Operation
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['InputHolderOperation']


class InputHolderOperation(Operation):
    __tablename__ = 'operation_input_holder'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': '__input_holder',
    }
