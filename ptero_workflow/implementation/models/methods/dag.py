from .method_base import Method
from ptero_workflow.implementation.models.link import Link
from ptero_workflow.implementation.models.task import Task
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import backref, aliased, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
from ptero_common import statuses


__all__ = ['DAG']


class DAG(Method):
    __tablename__ = 'dag'
    service = 'workflow'

    id = Column(Integer, ForeignKey('method.id', ondelete='CASCADE'),
            primary_key=True)

    children = relationship('Task',
            backref=backref('parent', uselist=False, remote_side=[id]),
            passive_deletes='all',
            collection_class=attribute_mapped_collection('name'))

    child_list = relationship('Task', passive_deletes='all')

    __mapper_args__ = {
        'polymorphic_identity': 'DAG',
    }

    VALID_CALLBACK_TYPES = Method.VALID_CALLBACK_TYPES.union(['set_status'])

    def attach_subclass_transitions(self, transitions, start_place):
        for child in self.child_list:
            child_start_place = self._pn(child.name, 'start')
            child_success_place, child_failure_place = child.attach_transitions(
                    transitions, child_start_place)

            if child.name == 'output connector':
                transitions.append({
                    'inputs': [child_success_place],
                    'outputs': [self._pn('dag_success')],
                })

            if child_failure_place is not None:
                transitions.append({
                    'inputs': [child_failure_place],
                    'outputs': [self._pn('failure_collection')],
                })

            if child.input_tasks:
                transitions.append({
                    'inputs': [self._link_pn(t, child)
                        for t in child.input_tasks],
                    'outputs': [child_start_place],
                })

            if child.output_tasks:
                transitions.append({
                    'inputs': [child_success_place],
                    'outputs': [self._link_pn(child, t)
                        for t in child.output_tasks],
                })

        transitions.extend([
            {
                'inputs': [start_place],
                'outputs': [self._pn('input connector', 'start'),
                    self._pn('failure_limit')],
            },
            {
                'inputs': [self._pn('failure_collection'),
                    self._pn('failure_limit')],
                'outputs': [self._pn('dag_failure')],
            },
        ])

        success, failure = self._attach_status_update_actions(
                transitions, self._pn('dag_success'), self._pn('dag_failure'))

        return success, failure


    def _link_pn(self, source, destination):
        return '%s:%s-to-%s-link' % (self._pn(), source._pn(),
                destination._pn())

    def _attach_status_update_actions(self, transitions, action_success_place,
            action_failure_place):
        transitions.append({
                'inputs': [action_success_place],
                'outputs': [self._pn('update_status_success')],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('set_status',
                        status=statuses.succeeded)
                }})
        success_place = self._pn('update_status_success')

        transitions.append({
            'inputs': [action_failure_place],
                'outputs': [self._pn('update_status_failure')],
            'action': {
                'type': 'notify',
                'url': self.callback_url('set_status', status=statuses.failed)
            }})
        failure_place = self._pn('update_status_failure')

        return success_place, failure_place

    def set_status(self, body_data, query_string_data):
        s = object_session(self)

        execution = self.get_or_create_execution(body_data['color'],
                body_data['group'])
        execution.status = query_string_data['status']

        s.commit()

    def resolve_output_source(self, session, name, parallel_depths):
        oc = self.children['output connector']
        return oc.resolve_input_source(session, name, parallel_depths)

    def create_input_sources(self, session, parallel_depths):
        super(DAG, self).create_input_sources(session, parallel_depths)

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

    def get_parameters(self,detailed=False):
        result = {
            'tasks': {t.name: t.as_dict(detailed=detailed)
                for t in self.children.itervalues()
                    if t.type not in ['InputConnector', 'OutputConnector']},
            'links': [l.as_dict(detailed=detailed) for l in self.links],
        }
        return result

    @property
    def links(self):
        s = object_session(self)
        source_task = aliased(Task)
        destination_task = aliased(Task)
        return s.query(Link).\
            join(source_task,source_task.id==Link.source_id).\
            join(destination_task,destination_task.id==Link.destination_id).\
            filter(destination_task.parent_id==self.id, source_task.parent_id==self.id).\
            order_by(source_task.name,destination_task.name).all()

    def as_dict_for_summary(self):
        result = super(DAG, self).as_dict_for_summary()

        sorted_tasks = sorted(self.children.values(),
                key=lambda x: x.topological_index)
        tasks_list = [t.as_dict_for_summary() for t in sorted_tasks
                if t.name not in ['input connector', 'output connector']]
        result['parameters'] = {'tasks': tasks_list}
        return result

    def as_skeleton_dict(self):
        result = super(DAG, self).as_skeleton_dict()
        result['parameters'] = {
            'tasks': {t.name: t.as_skeleton_dict()
                for t in self.children.itervalues()
                    if t.type not in ['InputConnector', 'OutputConnector']},
        }
        return result

    def set_status_running(self, color, group):
        if self.index == 0:
            self.task.set_status_running(color, group)

        execution = self.get_or_create_execution(color, group)

        s = object_session(execution)
        execution.status = statuses.scheduled
        s.flush()
        execution.status = statuses.running
        s.commit()


def _get_parent_color(colors):
    if len(colors) == 1:
        return None

    else:
        return colors[-2]
