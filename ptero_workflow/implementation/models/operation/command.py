from .operation_base import Operation
from .mixins.petri import OperationPetriMixin
from .mixins.parallel import ParallelPetriMixin
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['CommandOperation', 'ParallelByCommandOperation']


class CommandOperation(OperationPetriMixin, Operation):
    __tablename__ = 'operation_command'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'command',
    }


class ParallelByCommandOperation(ParallelPetriMixin, Operation):
    __tablename__ = 'operation_command_parallel'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'parallel-by-command',
    }
