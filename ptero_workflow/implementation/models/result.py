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
    parent_color = Column(Integer, nullable=True, index=True)

    type         = Column(Text, nullable=False)

    task = relationship('Task', backref='results')

    __mapper_args__ = {
        'polymorphic_on': 'type',
    }


class ConcreteResult(Result):
    __tablename__ = 'result_concrete'

    id = Column(Integer, ForeignKey('result.id'), primary_key=True)

    data = Column(json_type.JSON)

    __mapper_args__ = {
        'polymorphic_identity': 'concrete'
    }

    def get_data(self, indexes):
        return json_type.get_data_element(self, indexes)

    def get_size(self, indexes):
        return json_type.get_data_size(self, indexes)


class ArrayReferenceResult(Result):
    __tablename__ = 'result_array_reference'

    id = Column(Integer, ForeignKey('result.id'), primary_key=True)

    reference_ids = Column(json_type.JSON)
    size = Column(Integer, nullable=False)

    __mapper_args__ = {
            'polymorphic_identity': 'array_reference',
    }

    @property
    def data(self):
        s = object_session(self)
        results = []
        for rid in self.reference_ids:
            results.append(s.query(Result).filter_by(id=rid).one())
        return [r.data for r in results]

    def get_data(self, indexes):
        if indexes:
            s = object_session(self)
            rid = self.reference_ids[indexes[0]]
            r = s.query(Result).filter_by(id=rid).one()
            return r.get_data(indexes[1:])

        else:
            return self.data

    def get_size(self, indexes):
        if indexes:
            s = object_session(self)
            rid = self.reference_ids[indexes][0]
            r = s.query(Result).filter_by(id=rid).one()
            return r.get_size(indexes[1:])

        else:
            return self.size
