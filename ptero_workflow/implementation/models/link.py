from .base import Base
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
import logging


__all__ = ['Link']


LOG = logging.getLogger(__name__)


class Link(Base):
    __tablename__ = 'link'
    __table_args__ = (
        UniqueConstraint('destination_id', 'destination_property'),
    )

    id = Column(Integer, primary_key=True)

    source_id      = Column(Integer, ForeignKey('task.id'), nullable=False)
    destination_id = Column(Integer, ForeignKey('task.id'), nullable=False)

    source_property      = Column(Text, nullable=False)
    destination_property = Column(Text, nullable=False)

    source_task = relationship('Task',
            backref=backref('output_links'),
            foreign_keys=[source_id])

    destination_task = relationship('Task',
            backref=backref('input_links'),
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
