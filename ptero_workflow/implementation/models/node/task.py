from ..base import Base
from .node_base import Node
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
import requests
import simplejson


__all__ = ['Task']


class Task(Node):
    __tablename__ = 'task'

    id = Column(Integer, ForeignKey('node.id'), primary_key=True)
    parallel_by = Column(Text, nullable=True)

    methods = relationship('Method',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    method_list = relationship('Method', order_by='Method.index')

    __mapper_args__ = {
        'polymorphic_identity': 'task',
    }

    VALID_CALLBACK_TYPES = Node.VALID_CALLBACK_TYPES.union(['get_split_size'])

    def get_petri_transitions(self):
        transitions = []

        input_deps_place = self._attach_input_deps(transitions)

        if self.parallel_by is None:
            join_place = self._attach_action(transitions, input_deps_place)
        else:
            split_place = self._attach_split(transitions, input_deps_place)
            action_place = self._attach_action(transitions, split_place)
            join_place = self._attach_join(transitions, action_place)

        self._attach_output_deps(transitions, join_place)

        return transitions

    def _attach_input_deps(self, transitions):
        transitions.append({
            'inputs': [o.success_place_pair_name(self) for o in self.input_nodes],
            'outputs': [self.ready_place_name],
        })

        return self.ready_place_name

    def _attach_output_deps(self, transitions, internal_success_place):
        success_outputs = [self.success_place_pair_name(o) for o in self.output_nodes]
        success_outputs.append(self.success_place_pair_name(self.parent))
        transitions.append({
            'inputs': [internal_success_place],
            'outputs': success_outputs,
        })

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
        if self.parallel_by is None:
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
