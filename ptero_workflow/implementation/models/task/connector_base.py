from ..result import Pointer
from .task_base import Task
from sqlalchemy.orm.session import object_session
import requests

class Connector(Task):
    VALID_CALLBACK_TYPES = Task.VALID_CALLBACK_TYPES.union(
            set(['make_result_pointers']))

    @property
    def source(self):
        raise NotImplementedError("Abstract")

    def attach_subclass_transitions(self, *args, **kwargs):
        return self.attach_make_result_pointer_transitions(*args, **kwargs), None

    def attach_make_result_pointer_transitions(self, transitions, start_place):
        transitions.extend([
            {
                'inputs': [start_place],
                'outputs': [self.make_result_pointers_wait_place],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('make_result_pointers'),
                    'response_places': {
                        'done': self.make_result_pointers_done_place,
                    },
                },
            },
            {
                'inputs': [self.make_result_pointers_wait_place,
                    self.make_result_pointers_done_place],
                'outputs': [self.pointers_made_place],
            },
        ])
        return self.pointers_made_place

    @property
    def pointers_made_place(self):
        return '%s-pointers-made' % self.unique_name

    @property
    def make_result_pointers_wait_place(self):
        return '%s-make-result-pointers-wait' % self.unique_name

    @property
    def make_result_pointers_done_place(self):
        return '%s-make-result-pointers-done' % self.unique_name

    def make_result_pointers(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']

        colors = group['color_lineage'] + [color]

        s = object_session(self)
        results = self.source.get_input_results(colors)

        for name, result in results.iteritems():
            pointer = Pointer(task=self, name=name, color=color,
                    parent_color=parent_color, target=result)
            s.add(pointer)
        s.commit()

        return requests.put(body_data['response_links']['done'])
