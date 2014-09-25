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

    net_key = Column(Text, unique=True)

    root_operation_id = Column(Integer, ForeignKey('operation.id',
        use_alter=True, name='fk_workflow_root_operation'))
    input_holder_operation_id = Column(Integer, ForeignKey('operation.id',
        use_alter=True, name='fk_input_holder_operation'))


    root_operation = relationship('Operation', post_update=True,
            foreign_keys=[root_operation_id])
    input_holder_operation = relationship('InputHolderOperation',
            post_update=True, foreign_keys=[input_holder_operation_id])

    @property
    def start_place_name(self):
        return self.root_operation.ready_place_name

    @property
    def edges(self):
        results = []

        for name,op in self.operations.iteritems():
            results.extend(op.input_edges)

        return results

    @property
    def operations(self):
        return self.root_operation.children

    @property
    def as_dict(self):
        ops = {name: op.as_dict for name,op in self.operations.iteritems()
                if name not in ['input connector', 'output connector']}
        edges = [l.as_dict for l in self.edges]

        try:
            outputs = self.root_operation.get_outputs(color=0)
        except:
            outputs = None

        data = {
            'operations': ops,
            'edges': edges,
            'inputs': self.root_operation.get_inputs(color=0),
            'outputs': outputs,
            'environment': simplejson.loads(self.environment),
        }
        if self.root_operation.status is not None:
            data['status'] = self.root_operation.status
        return data
