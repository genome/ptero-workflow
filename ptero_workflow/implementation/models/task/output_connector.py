from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
import logging


LOG = logging.getLogger(__name__)


__all__ = ['OutputConnector']


class OutputConnector(Task):
    __tablename__ = 'output_connector'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'OutputConnector',
    }

    VALID_CALLBACK_TYPES = Task.VALID_CALLBACK_TYPES.union({
        'copy_outputs_to_parent',
    })

    def attach_subclass_transitions(self, transitions, start_place):
        transitions.extend([
            {
                'inputs': [start_place],
                'outputs': [self.wait_place_name],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('copy_outputs_to_parent'),
                    'response_places': {
                        'continue': self.response_place_name,
                    },
                },
            },
            {
                'inputs': [self.wait_place_name, self.response_place_name],
                'outputs': [self.success_place_name],
            },
        ])

        return self.success_place_name, None

    @property
    def wait_place_name(self):
        return '%s-wait' % self.unique_name

    @property
    def response_place_name(self):
        return '%s-response' % self.unique_name

    def copy_outputs_to_parent(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']
        response_links = body_data['response_links']

        colors = group.get('color_lineage', []) + [color]
        begins = group.get('begin_lineage', []) + [group['begin']]
        parent_color = _get_parent_color(colors)

        data = self.get_inputs(colors, begins)

        self.parent.task.set_outputs(data, color, parent_color)
        s = object_session(self)
        s.commit()

        self.http.delay('PUT', response_links['continue'])


def _get_parent_color(colors):
    if len(colors) == 1:
        return None

    else:
        return colors[-2]
