from ..base import Base
from ..result import Result, Json, GenericArray
from collections import defaultdict
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


LOG = logging.getLogger(__file__)


class Task(Base):
    __tablename__ = 'task'
    __table_args__ = (
        UniqueConstraint('parent_id', 'name'),
    )

    VALID_CALLBACK_TYPES = set(['get_split_size', 'done'])

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
            success_place, failure_place = self.attach_subclass_transitions(
                    transitions, start_place)

        else:
            split_place = self._attach_split_transitions(
                    transitions, start_place)
            subclass_success_place, subclass_failure_place = \
                    self.attach_subclass_transitions(transitions, split_place)
            join_success_place, failure_place = self._attach_join_transitions(
                    transitions, subclass_success_place, subclass_failure_place)
            success_place = self._attach_make_array_results_transitions(
                    transitions, join_success_place)

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

    def _attach_make_array_results_transitions(self, transitions,
            split_success_place):
        transitions.extend([
            {
                'inputs': [split_success_place],
                'outputs': [self.make_array_results_wait_place],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('make_array_results'),
                    'response_places': {
                        'done': self.make_array_results_done_place,
                    },
                },
            },
            {
                'inputs': [self.make_array_results_wait_place,
                    self.make_array_results_done_place],
                'outputs': [self.success_place_name],
            },
        ])
        return self.success_place_name

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

        result = self.get_input_result(colors=colors, name=self.parallel_by)
        response = requests.put(response_links['send_data'],
                data=simplejson.dumps({'color_group_size': result.size}),
                headers={'Content-Type': 'application/json'})
        return response

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

    def handle_callback(self, callback_type, body_data, query_string_data):
        if callback_type in self.VALID_CALLBACK_TYPES:
            return getattr(self, callback_type)(body_data, query_string_data)
        else:
            raise RuntimeError('Invalid callback type (%s).  Allowed types: %s'
                    % (callback_type, self.VALID_CALLBACK_TYPES))

    def done(self, body_data, query_string_data):
        self.status = 'success'
        s = object_session(self)
        s.commit()

    def make_array_results(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']
        parent_color = group['color_lineage'][-1]

        s = object_session(self)
        results = s.query(Result).filter_by(task=self, parent_color=color
                ).order_by('name', 'color').all()

        grouped_results = defaultdict(list)
        for result in results:
            grouped_results[result.name].append(result)

        for name, result_group in grouped_results.iteritems():
            array_result = GenericArray(task=self, name=name, color=color,
                    parent_color=parent_color, elements=result_group)
            s.add(array_result)
        s.commit()

        return requests.put(
                execution.data['petri_response_links']['done'])

    @property
    def failure_place_name(self):
        return '%s-failure' % self.unique_name

    def get_outputs(self, color):
        s = object_session(self)
        results = s.query(Result).filter_by(task=self, color=color).all()
        return {r.name:r.data for r in results}

    def set_outputs(self, outputs, color, parent_color):
        for name, value in outputs.iteritems():
            result = Json(task=self, name=name, color=color,
                    parent_color=parent_color, data=value)

    def get_inputs(self, color_list, parallel_index):
        if self.parallel_by is not None:
            inputs = {r.name:r.data for r in self.get_input_results(color_list)
                    if r.name != self.parallel_by}
            inputs[self.parallel_by] = self.get_input_result(
                color_list=color_list, name=self.parallel_by).get_element(parallel_index)
        else:
            inputs = {r.name:r.data for r in self.get_input_results(color_list)}
        return inputs

    def get_input_result(self, color_list, name):
        s = object_session(self)
        return s.query(Result
                ).filter_by(task=self, name=name
                ).filter(Result.color.in_(color_list)).one()

    def get_input_results(self, color_list):
        s = object_session(self)
        results = s.query(Result
                ).filter_by(task=self
                ).filter(Result.color.in_(color_list)).all()

        grouped_results = {}
        for result in results:
            if result.name in grouped_results:
                raise RuntimeError("Found more than one result on task (%s:%s)"
                        "with name (%s): OLD:%s NEW:%s" % (self.name, self.id,
                            result.name, grouped_results[result.name], result))
            else:
                grouped_results[result.name] = result
        return grouped_results
