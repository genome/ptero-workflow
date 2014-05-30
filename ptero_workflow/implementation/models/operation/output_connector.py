from .operation_base import Operation
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['OutputConnectorOperation']


class OutputConnectorOperation(Operation):
    __tablename__ = 'operation_output_connector'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'output connector',
    }

    def get_outputs(self, color):
        source_data = self.get_input_sources()
        valid_color_list = self._valid_color_list(color, self.workflow)
        result = {}
        for property_name, source in source_data.iteritems():
            source_op, source_name = source
            result[property_name] = source_op.get_output(source_name, color)
        return result

    def get_source_op_and_name(self, output_param_name):
        op, name = self.get_input_op_and_name(output_param_name)
        return op.get_source_op_and_name(name)

    def get_petri_transitions(self):
        return []
