from .operation_base import Operation
from .mixins.petri import OperationPetriMixin
from .mixins.parallel import ParallelPetriMixin
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
import requests


__all__ = ['PassThroughOperation', 'ParallelByPassThroughOperation']


class PassThroughOperation(OperationPetriMixin, Operation):
    __tablename__ = 'operation_pass_through'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'pass-through',
    }

    def execute(self, color, group, response_links):
        self.set_outputs(self.get_inputs(color), color)
        s = object_session(self)
        s.commit()
        response = requests.put(response_links['success'])


class ParallelByPassThroughOperation(ParallelPetriMixin, Operation):
    __tablename__ = 'operation_pass_through_parallel'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'parallel-by-pass-through',
    }

    def execute(self, color, group, response_links):
        self.set_outputs(self.get_inputs(color), color)
        s = object_session(self)
        s.commit()
        response = requests.put(response_links['success'])
