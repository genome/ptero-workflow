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

    root_node_id = Column(Integer, ForeignKey('node.id',
        use_alter=True, name='fk_workflow_root_node'))
    input_holder_id = Column(Integer, ForeignKey('input_holder.id',
        use_alter=True, name='fk_input_holder'))


    root_node = relationship('Node', post_update=True,
            foreign_keys=[root_node_id])
    input_holder = relationship('InputHolder',
            post_update=True, foreign_keys=[input_holder_id])

    @property
    def start_place_name(self):
        return self.root_node.ready_place_name

    @property
    def edges(self):
        results = []

        for name,node in self.nodes.iteritems():
            results.extend(node.input_edges)

        return results

    @property
    def nodes(self):
        return self.root_node.children

    @property
    def as_dict(self):
        nodes = {name: node.as_dict for name,node in self.nodes.iteritems()
                if name not in ['input connector', 'output connector']}
        edges = [l.as_dict for l in self.edges]

        try:
            outputs = self.root_node.get_outputs(color=0)
        except:
            outputs = None

        data = {
            'nodes': nodes,
            'edges': edges,
            'inputs': self.root_node.get_inputs(colors=[0], parallel_index=0),
            'outputs': outputs,
            'environment': simplejson.loads(self.environment),
        }
        if self.root_node.status is not None:
            data['status'] = self.root_node.status
        return data
