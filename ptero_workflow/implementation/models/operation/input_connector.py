from .operation_base import Operation
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['InputConnectorOperation']


class InputConnectorOperation(Operation):
    __tablename__ = 'operation_input_connector'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'input connector',
    }

    def get_source_op_and_name(self, output_param_name):
        op, name = self.parent.get_input_op_and_name(output_param_name)
        return op.get_source_op_and_name(name)

    def get_output(self, name, color):
        return self.get_inputs(color).get(name)

    def get_outputs(self, color):
        return self.get_inputs(color)

    def get_inputs(self, color):
        return self.parent.get_inputs(color)

    def get_input(self, name, color):
        return self.parent.get_input(name, color)

    def get_petri_transitions(self):
        return [
            {
                'inputs': [self.parent.ready_place_name],
                'outputs': [self.success_place_name],
            },
            {
                'inputs': [self.success_place_name],
                'outputs': [self.success_place_pair_name(o) for o in self.output_ops],
            }
        ]
