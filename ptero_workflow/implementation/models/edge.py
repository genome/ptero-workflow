from .base import Base
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
import logging


__all__ = ['Edge']


LOG = logging.getLogger(__file__)


class Edge(Base):
    __tablename__ = 'edge'
    __table_args__ = (
        UniqueConstraint('destination_id', 'destination_property'),
    )

    id = Column(Integer, primary_key=True)

    source_id      = Column(Integer, ForeignKey('node.id'), nullable=False)
    destination_id = Column(Integer, ForeignKey('node.id'), nullable=False)

    source_property      = Column(Text, nullable=False)
    destination_property = Column(Text, nullable=False)

    parallel_by = Column(Boolean, nullable=False, default=False)

    source_node = relationship('Node',
            backref=backref('output_edges'),
            foreign_keys=[source_id])

    destination_node = relationship('Node',
            backref=backref('input_edges'),
            foreign_keys=[destination_id])

    @property
    def as_dict(self):
        data = {
            'source': self.source_node.name,
            'destination': self.destination_node.name,
            'sourceProperty': self.source_property,
            'destinationProperty': self.destination_property,
        }

        if self.parallel_by:
            data['parallel_by'] = True

        return data
