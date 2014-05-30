from ..base import Base
from .. import result
from ..color_group import ColorGroup
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import backref, relationship
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
    workflow_id = Column(Integer, ForeignKey('workflow.id'), nullable=False)
    status = Column(Text)

    children = relationship('Operation',
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
        return '-'.join(['op', str(self.id), self.name.replace(' ', '_')])

    @property
    def success_place_name(self):
        return '%s-success' % self.unique_name

    def success_place_pair_name(self, op):
        return '%s-success-for-%s' % (self.unique_name, op.unique_name)

    @property
    def ready_place_name(self):
        return '%s-ready' % self.unique_name

    def event_url(self, event):
        return 'http://%s:%d/v1/callbacks/operations/%d/events/%s' % (
            os.environ.get('PTERO_WORKFLOW_HOST', 'localhost'),
            int(os.environ.get('PTERO_WORKFLOW_PORT', 80)),
            self.id,
            event,
        )

    def get_petri_transitions(self):
        raise RuntimeError('Operation is abstract')

    @property
    def input_ops(self):
        source_ids = set([l.source_id for l in self.input_links])
        if source_ids:
            s = object_session(self)
            return s.query(Operation).filter(Operation.id.in_(source_ids)).all()
        else:
            return []

    @property
    def output_ops(self):
        destination_ids = set([l.destination_id for l in self.output_links])
        if destination_ids:
            s = object_session(self)
            return s.query(Operation).filter(
                    Operation.id.in_(destination_ids)).all()
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

    def get_inputs(self, color):
        valid_colors = self._valid_color_list(color, self.workflow)

        source_operations = self._source_op_data()

        inputs = {}
        for property_name, source_data in source_operations.iteritems():
            output_holder = self._fetch_input(color, valid_colors, source_data)
            inputs[property_name] = self._convert_output(property_name,
                    output_holder, color)

        return inputs

    def _convert_output(self, property_name, output_holder, color):
        return output_holder.data

    def _valid_color_list(self, color, workflow):
        s = object_session(self)
        cg = s.query(ColorGroup).filter_by(workflow=workflow).filter(
            ColorGroup.begin <= color, color < ColorGroup.end
        ).one()

        color_list = [color]
        while cg.parent_color is not None:
            color_list.append(cg.parent_color)
            cg = cg.parent_color_group

        return color_list

    def _get_color_group(self, color):
        s = object_session(self)
        return s.query(ColorGroup).filter_by(workflow=self.workflow).filter(
                ColorGroup.begin <= color, ColorGroup.end > color).one()

    def _source_op_data(self):
        source_ops = {}
        for link in self.input_links:
            source_ops[link.destination_property] =\
                    link.source_operation.get_source_op_and_name(
                            link.source_property)

        return source_ops

    def get_source_op_and_name(self, output_param_name):
        return self, output_param_name

    def get_input_op_and_name(self, input_param_name):
        for link in self.input_links:
            if link.destination_property == input_param_name:
                return link.source_operation.get_source_op_and_name(
                        link.source_property)

    def get_input_sources(self):
        input_sources = {}
        for link in self.input_links:
            input_sources[link.destination_property] =\
                    link.source_operation.get_source_op_and_name(
                            link.source_property)
        return input_sources

    def _fetch_input(self, color, valid_color_list, source_data):
        (operation, property_name) = source_data

        s = object_session(self)
        return s.query(result.Result
                ).filter_by(operation=operation, name=property_name
                ).filter(result.Result.color.in_(valid_color_list)).one()

    def get_input(self, name, color):
        return self.get_inputs(color)[name]

    def execute(self, inputs):
        pass
