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

    source_id      = Column(Integer, ForeignKey('task.id'), nullable=False)
    destination_id = Column(Integer, ForeignKey('task.id'), nullable=False)

    source_property      = Column(Text, nullable=False)
    destination_property = Column(Text, nullable=False)

    parallel_by = Column(Boolean, nullable=False, default=False)

    source_task = relationship('Task',
            backref=backref('output_edges'),
            foreign_keys=[source_id])

    destination_task = relationship('Task',
            backref=backref('input_edges'),
            foreign_keys=[destination_id])

    @property
    def as_dict(self):
        data = {
            'source': self.source_task.name,
            'destination': self.destination_task.name,
            'sourceProperty': self.source_property,
            'destinationProperty': self.destination_property,
        }
        return data
