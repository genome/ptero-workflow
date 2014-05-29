from .operation_base import Operation
from .mixins.petri import OperationPetriMixin
from .mixins.parallel import ParallelPetriMixin
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['PassThroughOperation', 'ParallelByPassThroughOperation']


class PassThroughOperation(OperationPetriMixin, Operation):
    __tablename__ = 'operation_pass_through'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'pass-through',
    }

    def execute(self, color, group):
        self.set_outputs(self.get_inputs(color), color)


class ParallelByPassThroughOperation(ParallelPetriMixin, Operation):
    __tablename__ = 'operation_pass_through_parallel'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'parallel-by-pass-through',
    }

    def execute(self, color, group):
        self.set_outputs(self.get_inputs(color), color)
