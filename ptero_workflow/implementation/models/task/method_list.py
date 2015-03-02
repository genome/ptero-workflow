from ..base import Base
from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection


__all__ = ['MethodList']


class MethodList(Task):
    __tablename__ = 'method_list'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    methods = relationship('Method',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    method_list = relationship('Method', order_by='Method.index')

    __mapper_args__ = {
        'polymorphic_identity': 'MethodList',
    }

    def all_tasks_iterator(self):
        for method in self.method_list:
            for task in method.all_tasks_iterator():
                yield task

    def attach_subclass_transitions(self, transitions, start_place):
        last_failure_place = start_place
        success_places = []
        for method in self.method_list:
            success_place, failure_place = method.attach_transitions(
                    transitions, last_failure_place)
            last_failure_place = failure_place
            success_places.append(success_place)

        for sp in success_places:
            transitions.append({
                'inputs': [sp],
                'outputs': [self._pn('success')],
            })

        return self._pn('success'), last_failure_place

    def create_input_sources(self, session, parallel_depths):
        super(MethodList, self).create_input_sources(session, parallel_depths)
        for method in self.method_list:
            method.create_input_sources(session, parallel_depths)

    def as_dict(self, detailed):
        result = {
            'methods': [m.as_dict(detailed=detailed)
                for m in self.method_list],
        }
        if self.parallel_by is not None:
            result['parallelBy'] = self.parallel_by
        return result
