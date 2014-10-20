from .task_base import Task
import logging


LOG = logging.getLogger(__name__)


class Connector(Task):
    VALID_CALLBACK_TYPES = Task.VALID_CALLBACK_TYPES.union(
            set(['make_result_pointers']))

    def attach_subclass_transitions(self, transitions, start_place):
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

        return self.pointers_made_place, None

    @property
    def pointers_made_place(self):
        return '%s-pointers-made' % self.unique_name

    @property
    def make_result_pointers_wait_place(self):
        return '%s-make-result-pointers-wait' % self.unique_name

    @property
    def make_result_pointers_done_place(self):
        return '%s-make-result-pointers-done' % self.unique_name
