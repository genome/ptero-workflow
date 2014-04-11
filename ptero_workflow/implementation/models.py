from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
import os
import simplejson
import sqlalchemy.ext.declarative


__all__ = ['Base', 'Workflow']


Base = sqlalchemy.ext.declarative.declarative_base()


class Workflow(Base):
    __tablename__ = 'workflow'

    id          = Column(Integer, primary_key=True)
    environment = Column(Text)
    inputs      = Column(Text)

    root_operation_id = Column(Integer,
            ForeignKey('operation.id'), nullable=False)

    root_operation = relationship('Operation', backref='workflow')

    net_key = Column(Text, unique=True)

    @property
    def start_place_name(self):
        return self.root_operation.children['input connector'
                ].success_place_name

    @property
    def links(self):
        results = []

        for name,op in self.operations.iteritems():
            results.extend(op.input_links)

        return results

    @property
    def operations(self):
        return self.root_operation.children

    @property
    def as_dict(self):
        ops = {name: op.as_dict for name,op in self.operations.iteritems()
                if name not in ['input connector', 'output connector']}
        links = [l.as_dict for l in self.links]
        data = {
            'operations': ops,
            'links': links,
            'inputs': simplejson.loads(self.inputs),
            'environment': simplejson.loads(self.environment),
        }
        if self.root_operation.status is not None:
            data['status'] = self.root_operation.status
        return data


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

    @property
    def as_dict(self):
        return {
            'type': self.type,
        }

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

class Link(Base):
    __tablename__ = 'link'
    __table_args__ = (
        UniqueConstraint('destination_id', 'destination_property'),
    )

    id = Column(Integer, primary_key=True)

    source_id      = Column(Integer, ForeignKey('operation.id'), nullable=False)
    destination_id = Column(Integer, ForeignKey('operation.id'), nullable=False)

    source_property      = Column(Text, nullable=False)
    destination_property = Column(Text, nullable=False)

    parallel_by = Column(Boolean, nullable=False, default=False)

    source_operation = relationship('Operation',
            backref=backref('output_links'),
            foreign_keys=[source_id])

    destination_operation = relationship('Operation',
            backref=backref('input_links'),
            foreign_keys=[destination_id])

    @property
    def as_dict(self):
        data = {
            'source': self.source_operation.name,
            'destination': self.destination_operation.name,
            'source_property': self.source_property,
            'destination_property': self.destination_property,
        }

        if self.parallel_by:
            data['parallel_by'] = True

        return data
