from ..base import Base
from .. import result
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
import logging
import os
import urllib


__all__ = ['Node']


LOG = logging.getLogger(__file__)


class Node(Base):
    __tablename__ = 'node'
    __table_args__ = (
        UniqueConstraint('parent_id', 'name'),
    )

    VALID_CALLBACK_TYPES = set(['done'])

    id        = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('node.id'), nullable=True)
    name      = Column(Text, nullable=False)
    type      = Column(Text, nullable=False)
    workflow_id = Column(Integer, ForeignKey('workflow.id'), nullable=False)
    status = Column(Text)

    children = relationship('Node',
            backref=backref('parent', uselist=False, remote_side=[id]),
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    workflow = relationship('Workflow', foreign_keys=[workflow_id])

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
        d = self._as_dict_data
        d['type'] = self.type
        return d
    as_dict = to_dict

    @property
    def _as_dict_data(self):
        return {}

    @property
    def unique_name(self):
        return '-'.join(['node', str(self.id), self.name.replace(' ', '_')])

    @property
    def success_place_name(self):
        return '%s-success' % self.unique_name

    def success_place_pair_name(self, node):
        return '%s-success-for-%s' % (self.unique_name, node.unique_name)

    @property
    def ready_place_name(self):
        return '%s-ready' % self.unique_name

    def callback_url(self, callback_type, **params):
        if params:
            query_string = '?%s' % urllib.urlencode(params)
        else:
            query_string = ''

        return 'http://%s:%d/v1/callbacks/nodes/%d/callbacks/%s%s' % (
            os.environ.get('PTERO_WORKFLOW_HOST', 'localhost'),
            int(os.environ.get('PTERO_WORKFLOW_PORT', 80)),
            self.id,
            callback_type,
            query_string,
        )

    def get_petri_transitions(self):
        raise RuntimeError('Node is abstract')

    @property
    def input_nodes(self):
        source_ids = set([l.source_id for l in self.input_edges])
        if source_ids:
            s = object_session(self)
            return s.query(Node).filter(Node.id.in_(source_ids)).all()
        else:
            return []

    @property
    def output_nodes(self):
        destination_ids = set([l.destination_id for l in self.output_edges])
        if destination_ids:
            s = object_session(self)
            return s.query(Node).filter(
                    Node.id.in_(destination_ids)).all()
        else:
            return []

    def get_output(self, name, color):
        return self.get_outputs(color).get(name)

    def get_outputs(self, color):
        # XXX Broken -- does not even use color.
        return {o.name: o.data for o in self.results}

    def set_outputs(self, outputs, color):
        s = object_session(self)
        for name, value in outputs.iteritems():
            o = result.create_result(self, name, value, color)

    def get_inputs(self, colors, parallel_index):
        source_nodes = self._source_node_data()

        inputs = {}
        for property_name, source_data in source_nodes.iteritems():
            output_holder = self._fetch_input(colors, source_data)
            inputs[property_name] = self._convert_output(property_name,
                    output_holder, parallel_index)

        return inputs

    def _convert_output(self, property_name, output_holder, parallel_index):
        return output_holder.data

    def _source_node_data(self):
        source_nodes = {}
        for edge in self.input_edges:
            source_nodes[edge.destination_property] =\
                    edge.source_node.get_source_node_and_name(
                            edge.source_property)

        return source_nodes

    def get_source_node_and_name(self, output_param_name):
        return self, output_param_name

    def get_input_node_and_name(self, input_param_name):
        for edge in self.input_edges:
            if edge.destination_property == input_param_name:
                return edge.source_node.get_source_node_and_name(
                        edge.source_property)
        raise ValueError('Could not determine input node and name from (%s)'
                % input_param_name)

    def get_input_sources(self):
        input_sources = {}
        for edge in self.input_edges:
            input_sources[edge.destination_property] =\
                    edge.source_node.get_source_node_and_name(
                            edge.source_property)
        return input_sources

    def _fetch_input(self, color_list, source_data):
        (node, property_name) = source_data

        s = object_session(self)
        return s.query(result.Result
                ).filter_by(node=node, name=property_name
                ).filter(result.Result.color.in_(color_list)).one()

    def handle_callback(self, callback_type, body_data, query_string_data):
        if callback_type in self.VALID_CALLBACK_TYPES:
            return getattr(self, callback_type)(body_data, query_string_data)
        else:
            raise RuntimeError('Invalid callback type (%s).  Allowed types: %s'
                    % (callback_type, self.VALID_CALLBACK_TYPES))

    def done(self, body_data, query_string_data):
        self.status = 'success'
        s = object_session(self)
        s.commit()
