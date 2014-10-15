from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['InputHolder']


class InputHolder(Task):
    __tablename__ = 'input_holder'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': '__input_holder',
    }
