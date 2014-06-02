from ...color_group import ColorGroup
from .petri import OperationPetriMixin
from sqlalchemy import Column, Text
from sqlalchemy.orm.session import object_session
import requests
import simplejson


class ParallelPetriMixin(OperationPetriMixin):
    parallel_by = Column(Text, nullable=False)

    @property
    def split_size_wait_place_name(self):
        return '%s-split-size-wait' % self.unique_name

    @property
    def split_size_place_name(self):
        return '%s-split-size' % self.unique_name

    @property
    def create_color_group_place_name(self):
        return '%s-create-color-group-place' % self.unique_name

    @property
    def color_group_created_place_name(self):
        return '%s-color-group-created-place' % self.unique_name

    @property
    def split_place_name(self):
        return '%s-split' % self.unique_name

    @property
    def joined_place_name(self):
        return '%s-joined' % self.unique_name

    def get_split_size(self, data):
        color = data['color']
        response_links = data['response_links']

        source_data = self.get_input_op_and_name(self.parallel_by)
        valid_color_list = self._valid_color_list(color)
        output = self._fetch_input(color, valid_color_list, source_data)
        response = requests.put(response_links['send_data'],
                data=simplejson.dumps({'color_group_size': output.size}),
                headers={'Content-Type': 'application/json'})
        return response

    def color_group_created(self, data):
        workflow = self.workflow
        group = data['group']

        cg = ColorGroup.create(workflow, group)
        s = object_session(self)
        s.add(cg)
        s.commit()
        return cg

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
                    'url': self.event_url('get_split_size'),
                    'requested_data': ['color_group_size'],
                    'response_places': {
                        'send_data': self.split_size_place_name,
                    },
                },
            },

            {
                'inputs': [self.split_size_wait_place_name,
                    self.split_size_place_name],
                'outputs': [self.create_color_group_place_name],
            },

            # XXX add color group creation ack callback
            {
                'inputs': [self.create_color_group_place_name],
                'outputs': [self.color_group_created_place_name],
                'action': {
                    'type': 'create-color-group',
                    'url': self.event_url('color_group_created'),
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

    def _convert_output(self, property_name, output_holder, color):
        if property_name == self.parallel_by:
            cg = self._get_color_group(color)
            index = color - cg.begin
            return output_holder.get_element(index)
        else:
            return output_holder.data
