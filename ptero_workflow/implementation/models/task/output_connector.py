from .. import result
from .connector_base import Connector
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
import logging
import requests


LOG = logging.getLogger(__name__)


__all__ = ['OutputConnector']


class OutputConnector(Connector):
    __tablename__ = 'output_connector'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'output connector',
    }

    def make_result_pointers(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']
        parent_color = group.get('parent_color')

        colors = group['color_lineage'] + [color]

        s = object_session(self)

        for name, r in self.get_input_results(colors):
            pointer = result.Pointer(task=self.parent, name=name, color=color,
                    parent_color=parent_color, target_id=r.target_id)
            s.add(pointer)
        s.commit()

        return requests.put(body_data['response_links']['done'])
