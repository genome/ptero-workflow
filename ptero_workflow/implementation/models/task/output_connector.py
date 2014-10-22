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
