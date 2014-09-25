from .node_base import Node
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['OutputConnector']


class OutputConnector(Node):
    __tablename__ = 'output_connector'

    id = Column(Integer, ForeignKey('node.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'output connector',
    }

    def get_outputs(self, color):
        source_data = self.get_input_sources()
        result = {}
        for property_name, source in source_data.iteritems():
            source_node, source_name = source
            result[property_name] = source_node.get_output(source_name, color)
        return result

    def get_source_node_and_name(self, output_param_name):
        node, name = self.get_input_node_and_name(output_param_name)
        return node.get_source_node_and_name(name)

    def get_petri_transitions(self):
        return []
