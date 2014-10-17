from .base import Base
from .json_type import JSON
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.session import object_session
import logging
import simplejson


__all__ = ['Result', 'Json', 'Pointer', 'GenericArray']


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
    parent_color = Column(Integer, nullable=False, index=True)

    type         = Column(Text, nullable=False)

    task = relationship('Task', backref='results')

    __mapper_args__ = {
        'polymorphic_on': 'type',
    }

class Json(Result):
    __tablename__ = 'result_json'

    id = Column(Integer, ForeignKey('result.id'), primary_key=True)
    data = Column(JSON)

    __mapper_args__ = {
        'polymorphic_identity': 'json'
    }

    @property
    def size(self):
        # TODO make fast
        return len(self.data)

    def get_element(self, index):
        # TODO make fast
        return self.data[index]

class Pointer(Result):
    __tablename__ = 'result_pointer'

    id = Column(Integer, ForeignKey('result.id'), primary_key=True)
    target_id = Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'pointer'
    }

    @property
    def target(self):
        s = object_session(self)
        return s.query(Result).filter_by(id=self.target_id).one()

    @target.setter
    def target(self, target):
        self.target_id = target.id

    @property
    def data(self):
        return target.data

class GenericArrayElement(Base):
    __tablename__ = 'result_generic_array_element'

    array_id = Column(Integer, ForeignKey('result_generic_array.id'),
            primary_key=True)

    result_id = Column(Integer, ForeignKey('result.id'))
    result = relationship(Result, foreign_keys=[result_id])

    index = Column(Integer, primary_key=True)

    @property
    def data(self):
        return result.data

class GenericArray(Result):
    __tablename__ = 'result_generic_array'

    id = Column(Integer, ForeignKey('result.id'), primary_key=True)
    _elements = relationship(GenericArrayElement,
            order_by=GenericArrayElement.index,
            collection_class=ordering_list('index'),
            single_parent=True,
            cascade='all, delete-orphan')
    elements = association_proxy('_elements', 'elements',
                            creator=lambda r: GenericArrayElement(result=r))

    __mapper_args__ = {
        'polymorphic_identity': 'generic_array'
    }

    @property
    def data(self):
        return [e.data for e in self.elements]

    @property
    def size(self):
        s = object_session(self)
        return s.query(GenericArrayElement).filter_by(array_id=self.id).count()

    def get_element(self, index):
        s = object_session(self)
        element = s.query(GenericArrayElement).filter_by(
                array_id=self.id, index=index).one()
        return element.data
