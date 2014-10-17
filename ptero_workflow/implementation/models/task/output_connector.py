from .connector_base import Connector
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['OutputConnector']


class OutputConnector(Connector):
    __tablename__ = 'output_connector'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'output connector',
    }

    @property
    def source(self):
        return self
