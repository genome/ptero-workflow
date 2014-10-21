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

    @property
    def size(self):
        return json_type.get_data_size(self)

    def get_element(self, index):
        return json_type.get_data_element(self, index)

    @property
    def target_id(self):
        return self.id


class Pointer(Result):
    __tablename__ = 'result_pointer'

    id = Column(Integer, ForeignKey('result.id'), primary_key=True)

    target_id = Column(Integer, ForeignKey('result.id'), nullable=False)
    target = relationship('Result', foreign_keys=[target_id])

    __mapper_args__ = {
            'polymorphic_identity': 'pointer',
            'inherit_condition': id == Result.id,
    }

    @property
    def size(self):
        return self.target.size

    @property
    def data(self):
        return self.target.data

    def get_element(self, index):
        return self.target.get_element(index)


class ElementPointer(Result):
    __tablename__ = 'result_element_pointer'

    id = Column(Integer, ForeignKey('result.id'), primary_key=True)

    target_id = Column(Integer, ForeignKey('result.id'), nullable=False)
    target = relationship('Result', foreign_keys=[target_id])

    index = Column(Integer, nullable=False)

    __mapper_args__ = {
            'polymorphic_identity': 'element_pointer',
            'inherit_condition': id == Result.id,
    }

    @property
    def data(self):
        return self.target.get_element(self.index)

    @property
    def size(self):
        raise NotImplementedError()

    def get_element(self, index):
        raise NotImplementedError()


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

    @property
    def get_element(self, index):
        return json_type.get_referenced_element(self, index)

    @property
    def target_id(self):
        return self.id
