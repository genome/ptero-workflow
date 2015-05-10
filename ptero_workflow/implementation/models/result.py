from .base import Base
from sqlalchemy import Column, UniqueConstraint, Index
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
import json_type


__all__ = ['Result']


class Result(Base):
    __tablename__ = 'result'
    __table_args__ = (
        UniqueConstraint('color', 'name', 'task_id'),
        Index('color', 'name', 'task_id'),
    )

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('task.id'),
            index=True, nullable=False)
    name = Column(Text, nullable=False, index=True)
    color = Column(Integer, nullable=False, index=True)
    parent_color = Column(Integer, nullable=True, index=True)

    task = relationship('Task', backref='results')

    data = Column(json_type.JSON)

    def get_data(self, indexes):
        return json_type.get_data_element(self, indexes)

    def get_size(self, indexes):
        return json_type.get_data_size(self, indexes)
