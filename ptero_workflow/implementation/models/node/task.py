from ..base import Base
from .node_base import Node
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection


__all__ = ['Task']


class Task(Node):
    __tablename__ = 'task'

    id = Column(Integer, ForeignKey('node.id'), primary_key=True)

    methods = relationship('Method',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    method_list = relationship('Method', order_by='Method.index')

    __mapper_args__ = {
        'polymorphic_identity': 'task',
    }

    def _method_place_name(self, method, kind):
        return '%s-%s-%s' % (self.unique_name, method, kind)

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
