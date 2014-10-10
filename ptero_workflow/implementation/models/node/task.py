from ..base import Base
from .node_base import Node
from .mixins.task import TaskPetriMixin
from .mixins.parallel import ParallelPetriMixin
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from .method import Method


__all__ = ['Task']



class Task(TaskPetriMixin, Node):
    __tablename__ = 'task'

    id = Column(Integer, ForeignKey('node.id'), primary_key=True)

    methods = relationship('Method',
            collection_class=attribute_mapped_collection('name'),
            backref='task', cascade='all, delete-orphan')

    method_list = relationship('Method', order_by=Method.index)

    __mapper_args__ = {
        'polymorphic_identity': 'task',
    }

    VALID_EVENT_TYPES = Node.VALID_EVENT_TYPES.union(['execute', 'ended'])


class ParallelByTask(ParallelPetriMixin, Node):

    __tablename__ = 'parallel_by_task'

    id = Column(Integer, ForeignKey('node.id'), primary_key=True)

    methods = relationship('Method',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    method_list = relationship('Method', order_by=Method.index)

    __mapper_args__ = {
        'polymorphic_identity': 'parallel-by-task',
    }

    VALID_EVENT_TYPES = Node.VALID_EVENT_TYPES.union(
            ['color_group_created', 'execute', 'ended', 'get_split_size'])
