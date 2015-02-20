from .method_base import Method
from ptero_workflow.implementation.models.link import Link
from ptero_workflow.implementation.models.task import Task
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session


__all__ = ['DAGMethod']


class DAGMethod(Method):
    __tablename__ = 'method_dag'

    id = Column(Integer, ForeignKey('method.id'), primary_key=True)

    children = relationship('Task',
            backref=backref('parent', uselist=False, remote_side=[id]),
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    child_list = relationship('Task')

    __mapper_args__ = {
        'polymorphic_identity': 'DAG',
    }

    def attach_transitions(self, transitions, start_place):
        for child in self.child_list:
            child_start_place = self._child_start_place(child.name)
            child_success_place, child_failure_place = child.attach_transitions(
                    transitions, child_start_place)

            if child.name == 'output connector':
                transitions.append({
                    'inputs': [child_success_place],
                    'outputs': [self.success_place_name],
                })

            if child_failure_place is not None:
                transitions.append({
                    'inputs': [child_failure_place],
                    'outputs': [self._failure_collection_place_name],
                })

            if child.input_tasks:
                transitions.append({
                    'inputs': [self._link_place_name(t, child)
                        for t in child.input_tasks],
                    'outputs': [child_start_place],
                })

            if child.output_tasks:
                transitions.append({
                    'inputs': [child_success_place],
                    'outputs': [self._link_place_name(child, t)
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

        return (self.success_place_name, self.failure_place_name)

    def _child_start_place(self, child_name):
        return '%s:%s-start' % (self.unique_name, child_name)

    def _link_place_name(self, source, destination):
        return '%s:%s-to-%s-link' % (self.unique_name, source.unique_name,
                destination.unique_name)

    @property
    def _failure_collection_place_name(self):
        return '%s-failure-collection' % self.unique_name

    @property
    def _failure_limit_place_name(self):
        return '%s-failure-limit' % self.unique_name

    def resolve_output_source(self, session, name, parallel_depths):
        oc = self.children['output connector']
        return oc.resolve_input_source(session, name, parallel_depths)

    def create_input_sources(self, session, parallel_depths):
        super(DAGMethod, self).create_input_sources(session, parallel_depths)

        for child_name in self.children:
            self.children[child_name].create_input_sources(session,
                    parallel_depths)

    def get_outputs(self, colors, begins):
        oc = self.children['output connector']
        return oc.get_inputs(colors, begins)

    @property
    def output_names(self):
        oc = self.children['output connector']
        return oc.input_names

    @property
    def unique_name(self):
        name = self.name or ''
        return '-'.join(['task', str(self.id), name.replace(' ', '_')])

    @property
    def failure_place_name(self):
        return '%s-failure' % self.unique_name

    @property
    def success_place_name(self):
        return '%s-success' % self.unique_name

    @property
    def parameters(self):
        return {
            'tasks': [t.as_dict for t in self.children.itervalues()
                if t.type not in ['input connector', 'output connector']],
            'links': [l.as_dict for l in self.links],
        }

    @property
    def links(self):
        s = object_session(self)
        task_query = s.query(Task.id).filter_by(parent_id = self.id)
        return s.query(Link).filter(
                Link.source_id.in_(task_query)).filter(
                    Link.destination_id.in_(task_query)).all()


def _get_parent_color(colors):
    if len(colors) == 1:
        return None

    else:
        return colors[-2]
