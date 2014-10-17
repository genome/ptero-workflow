from ..base import Base
from .. import result
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
import logging
import os
import requests
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
        transitions.append({
            'inputs': [subclass_success_place],
            'outputs': [self.joined_place_name],
            'type': 'barrier',
            'action': {
                'type': 'join',
            }
        })

        transitions.extend([
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

        return self.joined_place_name, self.join_fail_place_name

    def _attach_status_update_actions(self, transitions, action_success_place,
            action_failure_place):
        if action_success_place is None:
            success_place = action_success_place

        else:
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


    def get_split_size(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']
        response_links = body_data['response_links']

        colors = group.get('color_lineage', []) + [color]

        source_data = self.get_input_task_and_name(self.parallel_by)
        output = self._fetch_input(colors, source_data)
        response = requests.put(response_links['send_data'],
                data=simplejson.dumps({'color_group_size': output.size}),
                headers={'Content-Type': 'application/json'})
        return response

    def get_outputs(self, color):
        if self.parallel_by is None:
            # XXX Broken -- does not even use color.
            return {o.name: o.data for o in self.results}
        else:
            grouped = {}
            for o in self.results:
                if o.name not in grouped:
                    grouped[o.name] = []
                grouped[o.name].append(o)

            results = {}
            for name, outputs in grouped.iteritems():
                results[name] = [o.data
                        for o in sorted(outputs, key=lambda x: x.color)]
            return results

    def _convert_output(self, property_name, output_holder, parallel_index):
        LOG.debug('Converting output for: property_name="%s", parallel_by="%s"',
                property_name, self.parallel_by)
        if property_name == self.parallel_by:
            return output_holder.get_element(parallel_index)
        else:
            return output_holder.data

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

    def success_place_pair_name(self, task):
        return '%s-success-for-%s' % (self.unique_name, task.unique_name)

    @property
    def ready_place_name(self):
        return '%s-ready' % self.unique_name

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

    def get_output(self, name, color):
        return self.get_outputs(color).get(name)

    def set_outputs(self, outputs, color, parent_color):
        s = object_session(self)
        for name, value in outputs.iteritems():
            o = result.ConcreteResult(task=self, name=name, data=value,
                    color=color, parent_color=parent_color)

    def get_inputs(self, colors, parallel_index):
        source_tasks = self._source_task_data()

        inputs = {}
        for property_name, source_data in source_tasks.iteritems():
            output_holder = self._fetch_input(colors, source_data)
            inputs[property_name] = self._convert_output(property_name,
                    output_holder, parallel_index)
        LOG.debug('Got inputs for color lineage %s (parallel_index %s): %s',
                colors, parallel_index, inputs)

        return inputs

    def _source_task_data(self):
        source_tasks = {}
        for edge in self.input_edges:
            source_tasks[edge.destination_property] =\
                    edge.source_task.get_source_task_and_name(
                            edge.source_property)

        return source_tasks

    def get_source_task_and_name(self, output_param_name):
        return self, output_param_name

    def get_input_task_and_name(self, input_param_name):
        for edge in self.input_edges:
            if edge.destination_property == input_param_name:
                return edge.source_task.get_source_task_and_name(
                        edge.source_property)
        raise ValueError('Could not determine input task and name from (%s)'
                % input_param_name)

    def get_input_sources(self):
        input_sources = {}
        for edge in self.input_edges:
            input_sources[edge.destination_property] =\
                    edge.source_task.get_source_task_and_name(
                            edge.source_property)
        return input_sources

    def _fetch_input(self, color_list, source_data):
        (task, property_name) = source_data

        s = object_session(self)
        return s.query(result.Result
                ).filter_by(task=task, name=property_name
                ).filter(result.Result.color.in_(color_list)).one()

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
