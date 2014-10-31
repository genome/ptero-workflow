from ..base import Base
from .. import edge
from .. import result
from .. import input_source
from collections import defaultdict
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
import celery
import logging
import os
import simplejson
import urllib


__all__ = ['Task']


LOG = logging.getLogger(__name__)


class Task(Base):
    __tablename__ = 'task'
    __table_args__ = (
        UniqueConstraint('parent_id', 'name'),
    )

    VALID_CALLBACK_TYPES = set([
        'create_array_result',
        'get_split_size',
        'set_status',
    ])

    id        = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('task.id'), nullable=True)
    name      = Column(Text, nullable=False)
    type      = Column(Text, nullable=False)
    workflow_id = Column(Integer, ForeignKey('workflow.id'), nullable=False)
    status = Column(Text)
    parallel_by = Column(Text, nullable=True)

    children = relationship('Task',
            backref=backref('parent', uselist=False, remote_side=[id]),
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    child_list = relationship('Task')

    workflow = relationship('Workflow', foreign_keys=[workflow_id])

    __mapper_args__ = {
        'polymorphic_on': 'type',
    }

    def attach_transitions(self, transitions, start_place):
        if self.parallel_by is None:
            action_success_place, action_failure_place = \
                    self.attach_subclass_transitions(transitions, start_place)

        else:
            split_place = self._attach_split_transitions(
                    transitions, start_place)
            subclass_success_place, subclass_failure_place = \
                    self.attach_subclass_transitions(transitions, split_place)
            action_success_place, action_failure_place = \
                    self._attach_join_transitions(transitions,
                            subclass_success_place, subclass_failure_place)

        success_place, failure_place = self._attach_status_update_actions(
                transitions, action_success_place, action_failure_place)

        return success_place, failure_place

    def attach_subclass_transitions(self, transitions, start_place):
        return start_place, None

    def _attach_split_transitions(self, transitions, start_place):
        transitions.extend([
            {
                'inputs': [start_place],
                'outputs': [self.split_size_wait_place_name,
                    self.join_fail_wait_place_name],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('get_split_size'),
                    'requested_data': ['color_group_size'],
                    'response_places': {
                        'send_data': self.split_size_place_name,
                    },
                },
            },

            {
                'inputs': [self.split_size_wait_place_name,
                    self.split_size_place_name],
                'outputs': [self.color_group_created_place_name],
                'action': {
                    'type': 'create-color-group',
                },
            },

            {
                'inputs': [self.color_group_created_place_name],
                'outputs': [self.split_place_name],
                'action': {
                    'type': 'split',
                },
            },
        ])

        return self.split_place_name


    def _attach_join_transitions(self, transitions, subclass_success_place,
            subclass_failure_place):
        transitions.extend([
            {
                'inputs': [subclass_success_place],
                'outputs': [self.joined_place_name],
                'type': 'barrier',
                'action': {
                    'type': 'join',
                }
            },
            {
                'inputs': [self.joined_place_name],
                'outputs': [self.array_result_wait_place_name],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('create_array_result'),
                    'response_places': {
                        'created': self.array_result_callback_place_name,
                    }
                },
            },
            {
                'inputs': [self.array_result_wait_place_name,
                    self.array_result_callback_place_name],
                'outputs': [self.join_success_place_name],
            },

            {
                'inputs': [subclass_failure_place],
                'outputs': [self.join_fail_convert_place_name],
                'action': {
                    'type': 'convert-to-parent-color',
                },
            },
            {
                'inputs': [self.join_fail_convert_place_name,
                    self.join_fail_wait_place_name],
                'outputs': [self.join_fail_place_name],
            },
        ])

        return self.join_success_place_name, self.join_fail_place_name

    def _attach_status_update_actions(self, transitions, action_success_place,
            action_failure_place):
        transitions.append({
                'inputs': [action_success_place],
                'outputs': [self.update_status_success_place_name],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('set_status', status='success')
                }})
        success_place = self.update_status_success_place_name


        if action_failure_place is None:
            failure_place = action_failure_place

        else:
            transitions.append({
                'inputs': [action_failure_place],
                    'outputs': [self.update_status_failure_place_name],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('set_status', status='failure')
                }})
            failure_place = self.update_status_failure_place_name

        return success_place, failure_place

    @property
    def update_status_success_place_name(self):
        return '%s-update-status-success' % self.unique_name

    @property
    def update_status_failure_place_name(self):
        return '%s-update-status-failure' % self.unique_name

    @property
    def array_result_wait_place_name(self):
        return '%s-array-result-wait' % self.unique_name

    @property
    def array_result_callback_place_name(self):
        return '%s-array-result-callback' % self.unique_name

    @property
    def join_success_place_name(self):
        return '%s-join-success-place' % self.unique_name

    @property
    def split_size_wait_place_name(self):
        return '%s-split-size-wait' % self.unique_name

    @property
    def split_size_place_name(self):
        return '%s-split-size' % self.unique_name

    @property
    def color_group_created_place_name(self):
        return '%s-color-group-created-place' % self.unique_name

    @property
    def split_place_name(self):
        return '%s-split' % self.unique_name

    @property
    def joined_place_name(self):
        return '%s-joined' % self.unique_name

    @property
    def join_fail_wait_place_name(self):
        return '%s-join-fail-wait' % self.unique_name

    @property
    def join_fail_convert_place_name(self):
        return '%s-join-fail-convert' % self.unique_name

    @property
    def join_fail_place_name(self):
        return '%s-join-fail' % self.unique_name

    @property
    def parallel_depth(self):
        increment = 0
        if self.parallel_by:
            increment = 1

        if self.parent:
            return self.parent.parallel_depth + increment

        else:
            return increment

    def get_split_size(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']
        response_links = body_data['response_links']

        colors = group.get('color_lineage', []) + [color]
        begins = group.get('begin_lineage', []) + [group['begin']]

        s = object_session(self)
        source = s.query(input_source.InputSource
                ).filter_by(destination_task=self,
                        destination_property=self.parallel_by
                ).one()
        size = source.get_size(colors, begins)
        LOG.debug('Split size for %s[%s] colors=%s is %s',
                self.name, self.parallel_by, colors, size)
        self.http.delay('PUT', response_links['send_data'],
                color_group_size=size)

    def create_array_result(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']
        parent_color = group.get('parent_color')
        response_links = body_data['response_links']

        s = object_session(self)
        for output_name in self.output_names:
            source, name, parallel_depths = self.resolve_output_source(s,
                    output_name, [])
            results = s.query(result.Result
                    ).filter_by(task=source, name=name, parent_color=color
                    ).order_by('color'
                    ).all()

            array_result = result.ArrayReferenceResult(task=source, name=name,
                    color=color, parent_color=parent_color,
                    size=len(results),
                    reference_ids=[r.id for r in results])
            s.add(array_result)

        s.commit()

        self.http.delay('PUT', response_links['created'])

    @property
    def input_names(self):
        return [e.destination_property for e in self.input_edges]

    @property
    def output_names(self):
        return [e.source_property for e in self.output_edges]

    @classmethod
    def from_dict(cls, type, **kwargs):
        subclass = cls.subclass_for(type)
        return subclass(**kwargs)

    @classmethod
    def subclass_for(cls, type):
        mapper = inspect(cls)
        return mapper.polymorphic_map[type].class_

    @property
    def to_dict(self):
        d = self._as_dict_data
        d['type'] = self.type
        return d
    as_dict = to_dict

    @property
    def _as_dict_data(self):
        return {}

    @property
    def unique_name(self):
        return '-'.join(['task', str(self.id), self.name.replace(' ', '_')])

    @property
    def success_place_name(self):
        return '%s-success' % self.unique_name

    def callback_url(self, callback_type, **params):
        if params:
            query_string = '?%s' % urllib.urlencode(params)
        else:
            query_string = ''

        return 'http://%s:%d/v1/callbacks/tasks/%d/callbacks/%s%s' % (
            os.environ.get('PTERO_WORKFLOW_HOST', 'localhost'),
            int(os.environ.get('PTERO_WORKFLOW_PORT', 80)),
            self.id,
            callback_type,
            query_string,
        )

    @property
    def input_tasks(self):
        source_ids = set([l.source_id for l in self.input_edges])
        if source_ids:
            s = object_session(self)
            return s.query(Task).filter(Task.id.in_(source_ids)).all()
        else:
            return []

    @property
    def output_tasks(self):
        destination_ids = set([l.destination_id for l in self.output_edges])
        if destination_ids:
            s = object_session(self)
            return s.query(Task).filter(
                    Task.id.in_(destination_ids)).all()
        else:
            return []

    def set_outputs(self, outputs, color, parent_color):
        s = object_session(self)
        for name, value in outputs.iteritems():
            o = result.ConcreteResult(task=self, name=name, data=value,
                    color=color, parent_color=parent_color)

    def get_inputs(self, colors, begins):
        inputs = {}
        for source in self.input_sources:
            inputs[source.destination_property] = source.get_data(
                    colors, begins)

        LOG.debug('Got inputs for %s, colors=%s: %s', self.name,
                colors, inputs)

        return inputs

    def handle_callback(self, callback_type, body_data, query_string_data):
        if callback_type in self.VALID_CALLBACK_TYPES:
            return getattr(self, callback_type)(body_data, query_string_data)
        else:
            raise RuntimeError('Invalid callback type (%s).  Allowed types: %s'
                    % (callback_type, self.VALID_CALLBACK_TYPES))

    def set_status(self, body_data, query_string_data):
        LOG.debug('Setting status on task %s (%s) from %s to "%s"',
                self.id, self.name, self.status, query_string_data['status'])
        self.status = query_string_data['status']
        s = object_session(self)
        s.commit()

    @property
    def failure_place_name(self):
        return '%s-failure' % self.unique_name

    def resolve_input_source(self, session, name, parallel_depths):
        if self.parallel_by == name:
            pdepths = [self.parallel_depth] + parallel_depths

        else:
            pdepths = parallel_depths

        for e in self.input_edges:
            if e.destination_property == name:
                return e.source_task.resolve_output_source(session,
                        e.source_property, pdepths)

    def resolve_output_source(self, session, name, parallel_depths):
        return self, name, parallel_depths

    def create_input_sources(self, session, parallel_depths):
        LOG.debug('Creating input sources for %s', self.name)
        for e in self.input_edges:
            source_task, source_property, source_parallel_depths = \
                    self.resolve_input_source(session, e.destination_property,
                            parallel_depths)
            LOG.debug('Found input source %s[%s] = %s[%s]: parallel_depths=%s',
                    self.name, e.destination_property,
                    source_task.name, source_property,
                    source_parallel_depths)

            in_source = input_source.InputSource(
                    source_task=source_task,
                    source_property=source_property,
                    destination_task=self,
                    destination_property=e.destination_property,
                    parallel_depths=source_parallel_depths,
            )
            session.add(in_source)

    @property
    def http(self):
        return celery.current_app.tasks[
                'ptero_workflow.implementation.celery_tasks.http.HTTP']
