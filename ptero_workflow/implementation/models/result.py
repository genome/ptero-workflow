from .base import Base
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.session import object_session
import json_type
import logging
import os
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


class Array(Result):
    __tablename__ = 'result_array'

    id = Column(Integer, ForeignKey('result.id'), primary_key=True)

    data = Column(json_type.JSON)

    __mapper_args__ = {
        'polymorphic_identity': 'array'
    }

    @property
    def size(self):
        if self._using_postgres:
            s = object_session(self)
            tup = s.query(json_type.json_array_length(Array.data)
                ).filter_by(id=self.id).one()
            return tup[0]

        else:
            return len(self.data)

    @property
    def _using_postgres(self):
        return os.environ.get('PTERO_WORKFLOW_DB_STRING', 'sqlite://'
                ).startswith('postgres')

    def get_element(self, index):
        if self._using_postgres:
            s = object_session(self)
            tup = s.query(Array.data[index]).filter_by(id=self.id).one()
            return tup[0]

        else:
            return self.data[index]


def create_result(task, name, data, color):
    if isinstance(data, list):
        return Array(task=task, name=name, data=data, color=color)

    else:
        return Scalar(task=task, name=name, data=data, color=color)
