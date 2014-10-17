from .connector_base import Connector
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['DAG']


class DAG(Connector):
    __tablename__ = 'dag'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'dag',
    }

    @property
    def source(self):
        return self.children['output connector']

    def attach_subclass_transitions(self, transitions, start_place):
        for child in self.child_list:
            child_start_place = self._child_start_place(child.name)
            child_success_place, child_failure_place = child.attach_transitions(
                    transitions, child_start_place)

            if child.name == 'output connector':
                success_place = self.attach_make_result_pointer_transitions(
                        transitions, child_success_place)

            if child_failure_place is not None:
                transitions.append({
                    'inputs': [child_failure_place],
                    'outputs': [self._failure_collection_place_name],
                })

            if child.input_tasks:
                transitions.append({
                    'inputs': [self._edge_place_name(t, child)
                        for t in child.input_tasks],
                    'outputs': [child_start_place],
                })

            if child.output_tasks:
                transitions.append({
                    'inputs': [child_success_place],
                    'outputs': [self._edge_place_name(child, t)
                        for t in child.output_tasks],
                })

        transitions.extend([
            {
                'inputs': [start_place],
                'outputs': [self._child_start_place('input connector'),
                    self._failure_limit_place_name],
            },
            {
                'inputs': [self._failure_collection_place_name,
                    self._failure_limit_place_name],
                'outputs': [self.failure_place_name],
            },
        ])

        return (success_place,
                self.failure_place_name)

    def _child_start_place(self, child_name):
        return '%s:%s-start' % (self.unique_name, child_name)

    def _edge_place_name(self, source, destination):
        return '%s:%s-to-%s-edge' % (self.unique_name, source.unique_name,
                destination.unique_name)

    @property
    def _failure_collection_place_name(self):
        return '%s-failure-collection' % self.unique_name

    @property
    def _failure_limit_place_name(self):
        return '%s-failure-limit' % self.unique_name
