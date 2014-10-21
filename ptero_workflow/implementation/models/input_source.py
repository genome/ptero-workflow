from .base import Base
from .json_type import JSON
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
import logging


__all__ = ['InputSource']


LOG = logging.getLogger(__file__)


class InputSource(Base):
    __tablename__ = 'input_source'
    __table_args__ = (
        UniqueConstraint('destination_id', 'destination_property'),
    )

    id = Column(Integer, primary_key=True)

    source_id      = Column(Integer, ForeignKey('task.id'), nullable=False)
    destination_id = Column(Integer, ForeignKey('task.id'), nullable=False)

    source_property      = Column(Text, nullable=False)
    destination_property = Column(Text, nullable=False)

    parallel_depths = Column(JSON, nullable=None)

    source_task = relationship('Task', foreign_keys=[source_id])
    destination_task = relationship('Task', backref='input_sources',
            foreign_keys=[destination_id])
