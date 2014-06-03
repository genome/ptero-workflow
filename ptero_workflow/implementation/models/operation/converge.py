from .mixins.base import BasePetriMixin
from .operation_base import Operation
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm.session import object_session
import simplejson


__all__ = ['ConvergeOperation']


class ConvergeOperation(BasePetriMixin, Operation):
    __tablename__ = 'operation_converge'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    serialized_input_order = Column(Text, nullable=False)
    output_name = Column(Text, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'converge',
    }

    VALID_EVENT_TYPES = Operation.VALID_EVENT_TYPES.union(['converge_inputs'])

    @property
    def input_order(self):
        return simplejson.loads(self.serialized_input_order)

    @input_order.setter
    def input_order(self, new_value):
        self.serialized_input_order = simplejson.dumps(new_value)

    def _attach_action(self, transitions, action_ready_place):
        wait_place_name = self._place_name('wait')
        done_callback_place_name = self._place_name('done-callback')
        success_place_name = self._place_name('success')

        transitions.extend([
            {
                'inputs': [action_ready_place],
                'outputs': [wait_place_name],
                'action': {
                    'type': 'notify',
                    'url': self.event_url('converge_inputs'),
                    'response_places': {
                        'done': done_callback_place_name,
                    },
                },
            },

            {
                'inputs': [wait_place_name, done_callback_place_name],
                'outputs': [success_place_name],
            },
        ])

        return success_place_name

    def _place_name(self, text):
        return '%s-%s' % (self.unique_name, text)

    def converge_inputs(self, body_data, query_string_data):
        color = body_data['color']
        inputs = self.get_inputs(color)

        output = []
        for name in self.input_order:
            output.append(inputs[name])

        self.set_outputs({self.output_name: output}, color)

        s = object_session(self)
        s.commit()
