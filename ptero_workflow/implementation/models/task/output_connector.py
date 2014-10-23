from .. import result
from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
import logging
import requests


LOG = logging.getLogger(__name__)


__all__ = ['OutputConnector']


class OutputConnector(Task):
    __tablename__ = 'output_connector'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'output connector',
    }
