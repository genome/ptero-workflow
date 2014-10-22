from .. import result
from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm.session import object_session
import logging
import requests


LOG = logging.getLogger(__name__)


__all__ = ['InputConnector']


class InputConnector(Task):
    __tablename__ = 'input_connector'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'input connector',
    }

    def resolve_output_source(self, session, name, parallel_depths):
        return self.parent.resolve_input_source(session, name, parallel_depths)

    def create_input_sources(self, session, parallel_depths):
        pass

    @property
    def input_names(self):
        return self.parent.input_names
