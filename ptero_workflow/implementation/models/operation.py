from .base import Base
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
import logging
import os


__all__ = ['Operation']


LOG = logging.getLogger(__file__)


class Operation(Base):
    __tablename__ = 'operation'
    __table_args__ = (
        UniqueConstraint('parent_id', 'name'),
    )

    id        = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('operation.id'), nullable=True)
    name      = Column(Text, nullable=False)
    type      = Column(Text, nullable=False)
    status = Column(Text)

    parent = relationship('Operation')

    children = relationship('Operation',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_on': 'type',
    }

    @classmethod
    def from_dict(cls, type, **kwargs):
        subclass = cls.subclass_for(type)
        return subclass(**kwargs)

    @classmethod
    def subclass_for(cls, type):
        mapper = inspect(cls)
        return mapper.polymorphic_map[type].class_

    @property
    def to_dict(self):
        result = self._as_dict_data
        result['type'] = self.type
        return result
    as_dict = to_dict

    @property
    def _as_dict_data(self):
        return {}

    @property
    def success_place_name(self):
        return 'op-%d-success' % self.id

    @property
    def ready_place_name(self):
        return 'op-%d-ready' % self.id

    @property
    def response_wait_place_name(self):
        return 'op-%d-response-wait' % self.id

    @property
    def response_callback_place_name(self):
        return 'op-%d-response-callback' % self.id

    def notify_callback_url(self, event):
        return 'http://%s:%d/v1/callbacks/operations/%d/events/%s' % (
            os.environ.get('PTERO_WORKFLOW_HOST', 'localhost'),
            int(os.environ.get('PTERO_WORKFLOW_PORT', 80)),
            self.id,
            event,
        )

    def get_petri_transitions(self):
        if self.type in ['input', 'output']:
            return []

        elif self.type == 'model':
            result = []
            result.append({
                'inputs': [o.success_place_name for o in self.real_child_ops],
                'outputs': [self.success_place_name],
                'action': {
                    'type': 'notify',
                    'url': self.notify_callback_url('done'),
                },
            })

            return result

        else:
            result = []

            # wait for all input ops
            result.append({
                'inputs': [o.success_place_name for o in self.input_ops],
                'outputs': [self.ready_place_name],
            })

            # send notification
            result.append({
                'inputs': [self.ready_place_name],
                'outputs': [self.response_wait_place_name],
                'action': {
                    'type': 'notify',
                    'url': self.notify_callback_url('execute'),
                    'response_places': {
                        'success': self.response_callback_place_name,
                    },
                }
            })

            # wait for response
            result.append({
                'inputs': [self.response_wait_place_name,
                    self.response_callback_place_name],
                'outputs': [self.success_place_name],
            })

            return result

    @property
    def input_ops(self):
        source_ids = set([l.source_id for l in self.input_links])
        s = object_session(self)
        return s.query(Operation).filter(Operation.id.in_(source_ids)).all()

    @property
    def real_child_ops(self):
        data = dict(self.children)
        del data['input connector']
        del data['output connector']
        return data.values()


class InputConnectorOperation(Operation):
    __tablename__ = 'operation_input_connector'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'input connector',
    }


class OutputConnectorOperation(Operation):
    __tablename__ = 'operation_output_connector'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'output connector',
    }


class ModelOperation(Operation):
    __tablename__ = 'operation_model'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'model',
    }


class CommandOperation(Operation):
    __tablename__ = 'operation_command'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'command',
    }
