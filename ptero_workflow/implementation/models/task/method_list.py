from ..base import Base
from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection


__all__ = ['MethodList']


class MethodList(Task):
    __tablename__ = 'method-list'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    methods = relationship('Method',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    method_list = relationship('Method', order_by='Method.index')

    __mapper_args__ = {
        'polymorphic_identity': 'method-list',
    }

    def _attach_action(self, transitions, action_ready_place):
        input_place_name = action_ready_place
        success_places = []
        for method in self.method_list:
            success_place, failure_place = method._attach(transitions,
                    input_place_name)
            input_place_name = failure_place
            success_places.append(success_place)

        for sp in success_places:
            transitions.append({
                'inputs': [sp],
                'outputs': [self.success_place_name],
            })

        return self.success_place_name
