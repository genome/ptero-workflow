from ..base import Base
from .operation_base import Operation
from .mixins.command import OperationPetriMixin
from .mixins.parallel import ParallelPetriMixin
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
import simplejson


__all__ = ['CommandOperation', 'Method']


class Method(Base):
    __tablename__ = 'operation_command_method'

    __table_args__ = (
        UniqueConstraint('operation_id', 'name'),
    )

    id = Column(Integer, primary_key=True)

    operation_id = Column(Integer, ForeignKey('operation.id'))
    name = Column(Text)

    index = Column(Integer, nullable=False, index=True)

    serialized_command_line = Column(Text, nullable=False)

    @property
    def command_line(self):
        return simplejson.loads(self.serialized_command_line)

    @command_line.setter
    def command_line(self, new_value):
        self.serialized_command_line = simplejson.dumps(new_value)


class CommandOperation(OperationPetriMixin, Operation):
    __tablename__ = 'operation_command'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    methods = relationship('Method', backref='operation',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    method_list = relationship('Method', order_by=Method.index)

    __mapper_args__ = {
        'polymorphic_identity': 'command',
    }

    VALID_EVENT_TYPES = Operation.VALID_EVENT_TYPES.union(['execute', 'ended'])
