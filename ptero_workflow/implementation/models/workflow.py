from .base import Base
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
import logging
import simplejson


__all__ = ['Workflow']


LOG = logging.getLogger(__file__)


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
        LOG.debug('root_op: %d', self.root_operation.id)
        LOG.debug('root input_connector: %d',
                self.root_operation.children['input connector'].id)
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
