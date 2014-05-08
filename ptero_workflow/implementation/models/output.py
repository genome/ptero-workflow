from .base import Base
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
import logging
import simplejson


__all__ = ['Output']


LOG = logging.getLogger(__file__)


class Output(Base):
    __tablename__ = 'output'
    __table_args__ = (
        UniqueConstraint('operation_id', 'name'),
    )

    id = Column(Integer, primary_key=True)

    operation_id = Column(Integer, ForeignKey('operation.id'), nullable=False)
    name = Column(Text, nullable=False)
    serialized_value = Column(Text, nullable=False)

    operation = relationship('Operation', backref='outputs')

    @property
    def value(self):
        return simplejson.loads(self.serialized_value)
