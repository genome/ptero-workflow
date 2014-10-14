from ..base import Base
from .node_base import Node
from .mixins.task import TaskPetriMixin
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
import requests
import simplejson


__all__ = ['Task']


class Task(TaskPetriMixin, Node):
    __tablename__ = 'task'

    id = Column(Integer, ForeignKey('node.id'), primary_key=True)

    methods = relationship('Method',
            collection_class=attribute_mapped_collection('name'),
            backref='task', cascade='all, delete-orphan')

    method_list = relationship('Method', order_by='Method.index')

    __mapper_args__ = {
        'polymorphic_identity': 'task',
    }

    VALID_CALLBACK_TYPES = Node.VALID_CALLBACK_TYPES.union(['execute', 'ended'])


class ParallelByTask(TaskPetriMixin, Node):

    __tablename__ = 'parallel_by_task'

    id = Column(Integer, ForeignKey('node.id'), primary_key=True)
    parallel_by = Column(Text, nullable=False)

    methods = relationship('Method',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    method_list = relationship('Method', order_by='Method.index')

    __mapper_args__ = {
        'polymorphic_identity': 'parallel-by-task',
    }

    VALID_CALLBACK_TYPES = Node.VALID_CALLBACK_TYPES.union(
            ['execute', 'ended', 'get_split_size'])

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

    def get_split_size(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']
        response_links = body_data['response_links']

        colors = group.get('color_lineage', []) + [color]

        source_data = self.get_input_node_and_name(self.parallel_by)
        output = self._fetch_input(colors, source_data)
        response = requests.put(response_links['send_data'],
                data=simplejson.dumps({'color_group_size': output.size}),
                headers={'Content-Type': 'application/json'})
        return response

    def get_outputs(self, color):
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

    def _attach_split(self, transitions, ready_place):
        transitions.extend([
            {
                'inputs': [ready_place],
                'outputs': [self.split_size_wait_place_name],
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

    def _attach_join(self, transitions, action_done_place):
        transitions.append({
            'inputs': action_done_place,
            'outputs': self.joined_place_name,
            'type': 'barrier',
            'action': {
                'type': 'join',
            }
        })
        return self.joined_place_name

    def _convert_output(self, property_name, output_holder, parallel_index):
        if property_name == self.parallel_by:
            return output_holder.get_element(parallel_index)
        else:
            return output_holder.data
