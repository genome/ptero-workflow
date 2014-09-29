from .node_base import Node
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['InputHolder']


class InputHolder(Node):
    __tablename__ = 'input_holder'

    id = Column(Integer, ForeignKey('node.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': '__input_holder',
    }
