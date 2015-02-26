from ..base import Base
from flask import url_for
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship
import os
import urllib


__all__ = ['Method']


class Method(Base):
    __tablename__ = 'method'
    service = 'NotImplementedError'

    __table_args__ = (
        UniqueConstraint('task_id', 'name'),
    )

    id = Column(Integer, primary_key=True)

    task_id = Column(Integer, ForeignKey('task.id'))
    task = relationship('Task')

    name = Column(Text)

    index = Column(Integer, nullable=True, index=True)

    type = Column(Text, nullable=False)
    __mapper_args__ = {
        'polymorphic_on': 'type',
    }

    VALID_CALLBACK_TYPES = set()

    def all_tasks_iterator(self):
        return []

    def handle_callback(self, callback_type, body_data, query_string_data):
        if callback_type in self.VALID_CALLBACK_TYPES:
            return getattr(self, callback_type)(body_data, query_string_data)
        else:
            raise RuntimeError('Invalid callback type (%s).  Allowed types: %s'
                    % (callback_type, self.VALID_CALLBACK_TYPES))

    def callback_url(self, callback_type, **params):
        if params:
            query_string = '?%s' % urllib.urlencode(params)
        else:
            query_string = ''

        # We cannot use url_for() here because this is called from outside the
        # Flask Application Context

        return 'http://%s:%d/v1/callbacks/methods/%d/callbacks/%s%s' % (
            os.environ.get('PTERO_WORKFLOW_HOST', 'localhost'),
            int(os.environ.get('PTERO_WORKFLOW_PORT', 80)),
            self.id,
            callback_type,
            query_string,
        )

    def execution_url(self, execution_id):
        return url_for('execution-detail', execution_id=execution_id,
                _external=True)

    def create_input_sources(self, session, parallel_depths):
        pass

    @property
    def parameters(self):
        raise NotImplementedError

    @property
    def as_dict(self):
        return {
            'name': self.name,
            'service': self.service,
            'parameters': self.parameters,
        }
