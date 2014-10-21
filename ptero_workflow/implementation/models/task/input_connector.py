from .. import result
from .connector_base import Connector
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
import logging
import requests


LOG = logging.getLogger(__name__)


__all__ = ['InputConnector']


class InputConnector(Connector):
    __tablename__ = 'input_connector'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'input connector',
    }

    def make_result_pointers(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']
        parent_color = group.get('parent_color')

        colors = group['color_lineage'] + [color]

        s = object_session(self)

        for name, r in self.parent.get_input_results(colors):
            if name == self.parent.parallel_by:
                parallel_index = color - group.get('begin', color)
                pointer = result.ElementPointer(task=self, name=name,
                        color=color, parent_color=parent_color,
                        index=parallel_index, target_id=r.target_id)

            else:
                pointer = result.Pointer(task=self, name=name, color=color,
                        parent_color=parent_color, target_id=r.target_id)
            s.add(pointer)

        s.commit()

        return requests.put(body_data['response_links']['done'])

    def resolve_input_source(self, session, name, parallel_depths):
        return self.parent.resolve_input_source(session, name, parallel_depths)

    def resolve_output_source(self, session, name, parallel_depths):
        return self.resolve_input_source(session, name, parallel_depths)
