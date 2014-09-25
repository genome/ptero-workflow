from ..base import Base
from .node_base import Node
from .mixins.command import NodePetriMixin
from .mixins.parallel import ParallelPetriMixin
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
import simplejson


__all__ = ['Command', 'Method']


class Method(Base):
    __tablename__ = 'method'

    __table_args__ = (
        UniqueConstraint('node_id', 'name'),
    )

    id = Column(Integer, primary_key=True)

    node_id = Column(Integer, ForeignKey('node.id'))
    name = Column(Text)

    index = Column(Integer, nullable=False, index=True)

    serialized_command_line = Column(Text, nullable=False)

    @property
    def command_line(self):
        return simplejson.loads(self.serialized_command_line)

    @command_line.setter
    def command_line(self, new_value):
        self.serialized_command_line = simplejson.dumps(new_value)


class Command(NodePetriMixin, Node):
    __tablename__ = 'command'

    id = Column(Integer, ForeignKey('node.id'), primary_key=True)

    methods = relationship('Method',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    method_list = relationship('Method', order_by=Method.index)

    __mapper_args__ = {
        'polymorphic_identity': 'command',
    }

    VALID_EVENT_TYPES = Node.VALID_EVENT_TYPES.union(['execute', 'ended'])


class ParallelByCommand(ParallelPetriMixin, NodePetriMixin,
        Node):

    __tablename__ = 'parallel_by_command'

    id = Column(Integer, ForeignKey('node.id'), primary_key=True)

    methods = relationship('Method',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    method_list = relationship('Method', order_by=Method.index)

    __mapper_args__ = {
        'polymorphic_identity': 'parallel-by-command',
    }

    VALID_EVENT_TYPES = Node.VALID_EVENT_TYPES.union(
            ['color_group_created', 'execute', 'ended', 'get_split_size'])
