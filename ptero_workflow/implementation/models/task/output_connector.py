from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
from ptero_common import nicer_logging


LOG = nicer_logging.getLogger(__name__)


__all__ = ['OutputConnector']


class OutputConnector(Task):
    __tablename__ = 'output_connector'

    id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
            primary_key=True)

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
                'outputs': [self._pn('wait')],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('copy_outputs_to_parent'),
                    'response_places': {
                        'continue': self._pn('response'),
                    },
                },
            },
            {
                'inputs': [self._pn('wait'), self._pn('response')],
                'outputs': [self._pn('success')],
            },
        ])

        return self._pn('success'), None

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

        LOG.info('Notifying petri: output connector (%s) copied outputs '
                'to parent (%s) for workflow "%s"',
                self.id, self.parent.name, self.workflow.name,
                extra={'workflowName':self.workflow.name})
        self.http.delay('PUT', response_links['continue'])


def _get_parent_color(colors):
    if len(colors) == 1:
        return None

    else:
        return colors[-2]
