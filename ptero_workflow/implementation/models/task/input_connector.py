from .connector_base import Connector
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['InputConnector']


class InputConnector(Connector):
    __tablename__ = 'input_connector'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'input connector',
    }

    @property
    def source(self):
        return self.parent
