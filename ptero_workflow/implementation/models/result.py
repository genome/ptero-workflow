from .base import Base
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.session import object_session
import logging
import simplejson


__all__ = ['Result']


LOG = logging.getLogger(__file__)


class Result(Base):
    __tablename__ = 'result'
    __table_args__ = (
        UniqueConstraint('task_id', 'name', 'color'),
    )

    id           = Column(Integer, primary_key=True)

    task_id = Column(Integer, ForeignKey('task.id'), nullable=True)
    name    = Column(Text, nullable=False, index=True)
    color   = Column(Integer, nullable=False, index=True)

    type         = Column(Text, nullable=False)

    task = relationship('Task', backref='results')

    __mapper_args__ = {
        'polymorphic_on': 'type',
    }


class Scalar(Result):
    __tablename__ = 'result_scalar'

    id = Column(Integer, ForeignKey('result.id'), primary_key=True)
    data = Column(Text)

    __mapper_args__ = {
        'polymorphic_identity': 'scalar'
    }


class ArrayEntry(Base):
    __tablename__ = 'result_array_entry'

    array_id = Column(Integer, ForeignKey('result_array.id'), primary_key=True)
    index = Column(Integer, primary_key=True)

    serialized_data = Column(Text)

    array = relationship('Array', backref='entries', foreign_keys=[array_id])

    @property
    def data(self):
        return simplejson.loads(self.serialized_data)

    @data.setter
    def data(self, value):
        self.serialized_data = simplejson.dumps(value)


class Array(Result):
    __tablename__ = 'result_array'

    id = Column(Integer, ForeignKey('result.id'), primary_key=True)

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
    def create(cls, task, name, data, color):
        self = cls(task=task, name=name, color=color)
        for index, item in enumerate(data):
            entry = ArrayEntry(index=index)
            entry.data = item
            self.entries.append(entry)
        return self


def create_result(task, name, data, color):
    if isinstance(data, list):
        return Array.create(task=task, name=name, data=data,
                color=color)

    else:
        return Scalar(task=task, name=name, data=data, color=color)
