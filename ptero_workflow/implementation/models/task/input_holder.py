from .task_base import Task
from .. import result
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['InputHolder']


class InputHolder(Task):
    __tablename__ = 'input_holder'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'InputHolder',
    }

    def __init__(self, *args, **kwargs):
        return super(InputHolder, self).__init__(*args, topological_index=-1, **kwargs)

    def set_outputs(self, outputs, color, parent_color):
        for name, value in outputs.iteritems():
            result.Result(task=self, name=name, data=value,
                    color=color, parent_color=parent_color)
