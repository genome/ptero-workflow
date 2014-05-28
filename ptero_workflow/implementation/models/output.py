from .base import Base
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.session import object_session
import logging
import simplejson


__all__ = ['Output']


LOG = logging.getLogger(__file__)


class Output(Base):
    __tablename__ = 'output'
    __table_args__ = (
        UniqueConstraint('operation_id', 'name', 'color'),
    )

    id           = Column(Integer, primary_key=True)

    operation_id = Column(Integer, ForeignKey('operation.id'), nullable=True)
    name         = Column(Text, nullable=False, index=True)
    color        = Column(Integer, nullable=False, index=True)

    type         = Column(Text, nullable=False)

    operation = relationship('Operation', backref='outputs')

    __mapper_args__ = {
        'polymorphic_on': 'type',
    }


class Scalar(Output):
    __tablename__ = 'output_scalar'

    id = Column(Integer, ForeignKey('output.id'), primary_key=True)
    data = Column(Text)

    __mapper_args__ = {
        'polymorphic_identity': 'scalar'
    }


class ArrayEntry(Base):
    __tablename__ = 'output_array_entry'

    array_id = Column(Integer, ForeignKey('output_array.id'), primary_key=True)
    index = Column(Integer, primary_key=True)

    serialized_data = Column(Text)

    array = relationship('Array', backref='entries', foreign_keys=[array_id])

    @property
    def data(self):
        return simplejson.loads(self.serialized_data)

    @data.setter
    def data(self, value):
        self.serialized_data = simplejson.dumps(value)


class Array(Output):
    __tablename__ = 'output_array'

    id = Column(Integer, ForeignKey('output.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'array'
    }

    @property
    def data(self):
        return [entry.data for entry in self.entries]

    @property
    def size(self):
        s = object_session(self)
        return s.query(ArrayEntry).filter_by(array_id=self.id).count()

    def get_element(self, index):
        s = object_session(self)
        entry = s.query(ArrayEntry).filter_by(
                array_id=self.id, index=index).one()
        return entry.data

    @classmethod
    def create(cls, operation, name, data, color):
        self = cls(operation=operation, name=name, color=color)
        for index, item in enumerate(data):
            entry = ArrayEntry(index=index)
            entry.data = item
            self.entries.append(entry)
        return self


def create_output(operation, name, data, color):
    if isinstance(data, list):
        return Array.create(operation=operation, name=name, data=data,
                color=color)

    else:
        return Scalar(operation=operation, name=name, data=data, color=color)
