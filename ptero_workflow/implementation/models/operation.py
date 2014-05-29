from .base import Base
from . import output
from .petri import ColorGroup
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
import logging
import os
import simplejson


__all__ = ['Operation', 'InputHolderOperation']


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

    children = relationship('Operation',
            backref=backref('parent', uselist=False, remote_side=[id]),
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

    @property
    def response_wait_place_name(self):
        return '%s-response-wait' % self.unique_name

    @property
    def response_callback_place_name(self):
        return '%s-response-callback' % self.unique_name

    def notify_callback_url(self, event):
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

    def get_workflow(self):
        root = self.get_root()
        return root.workflow

    def get_root(self):
        parent = self.parent
        if parent is None:
            return self

        while parent.parent:
            parent = parent.parent

        return parent

    def get_output(self, name, color):
        return self.get_outputs(color).get(name)

    def get_outputs(self, color):
        # XXX Broken -- does not even use color.
        return {o.name: o.data for o in self.outputs}

    def set_outputs(self, outputs, color):
        s = object_session(self)
        for name, value in outputs.iteritems():
            o = output.create_output(self, name, value, color)

    def get_inputs(self, color):
        workflow = self.get_workflow()
        valid_colors = self._valid_color_list(color, workflow)

        source_operations = self._source_op_data()

        result = {}
        for property_name, source_data in source_operations.iteritems():
            output_holder = self._fetch_input(color, valid_colors, source_data)
            result[property_name] = self._convert_output(property_name,
                    output_holder, color)

        return result

    def _convert_output(self, property_name, output_holder, color):
        return output_holder.data

    def _valid_color_list(self, color, workflow):
        s = object_session(self)
        cg = s.query(ColorGroup).filter_by(workflow=workflow).filter(
            ColorGroup.begin <= color, color < ColorGroup.end
        ).one()

        result = [color]
        while cg.parent_color is not None:
            result.append(cg.parent_color)
            cg = cg.parent_color_group

        return result

    def _source_op_data(self):
        result = {}
        for link in self.input_links:
            result[link.destination_property] =\
                    link.source_operation.get_source_op_and_name(
                            link.source_property)

        return result

    def get_source_op_and_name(self, output_param_name):
        return self, output_param_name

    def get_input_op_and_name(self, input_param_name):
        for link in self.input_links:
            if link.destination_property == input_param_name:
                return link.source_operation.get_source_op_and_name(
                        link.source_property)

    def get_input_sources(self):
        result = {}
        for link in self.input_links:
            result[link.destination_property] = link.source_operation.get_source_op_and_name(
                    link.source_property)
        return result

    def _fetch_input(self, color, valid_color_list, source_data):
        (operation, property_name) = source_data

        s = object_session(self)
        result = s.query(output.Output
                ).filter_by(operation=operation, name=property_name
                ).filter(output.Output.color.in_(valid_color_list)).one()
        return result

    def get_input(self, name, color):
        return self.get_inputs(color)[name]

    def execute(self, inputs):
        pass


class OperationPetriMixin(object):
    def get_petri_transitions(self):
        transitions = []

        input_deps_place = self._attach_input_deps(transitions)

        split_place = self._attach_split(transitions, input_deps_place)
        action_place = self._attach_action(transitions, split_place)
        join_place = self._attach_join(transitions, action_place)

        self._attach_output_deps(transitions, join_place)

        return transitions

    def _attach_input_deps(self, transitions):
        transitions.append({
            'inputs': [o.success_place_pair_name(self) for o in self.input_ops],
            'outputs': [self.ready_place_name],
        })

        return self.ready_place_name

    def _attach_output_deps(self, transitions, internal_success_place):
        success_outputs = [self.success_place_pair_name(o) for o in self.output_ops]
        success_outputs.append(self.success_place_pair_name(self.parent))
        transitions.append({
            'inputs': [internal_success_place],
            'outputs': success_outputs,
        })

    def _attach_split(self, transitions, ready_place):
        return ready_place

    def _attach_join(self, transitions, action_done_place):
        return action_done_place

    def _attach_action(self, transitions, action_ready_place):
        # send notification
        transitions.append({
            'inputs': [action_ready_place],
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
        transitions.append({
            'inputs': [self.response_wait_place_name,
                self.response_callback_place_name],
            'outputs': [self.success_place_name],
        })

        return self.success_place_name


class ParallelPetriMixin(OperationPetriMixin):
    parallel_by = Column(Text, nullable=False)

    @property
    def split_size_wait_place_name(self):
        return '%s-split-size-wait' % self.unique_name

    @property
    def split_size_place_name(self):
        return '%s-split-size' % self.unique_name

    @property
    def create_color_group_place_name(self):
        return '%s-create-color-group-place' % self.unique_name

    @property
    def color_group_created_place_name(self):
        return '%s-color-group-created-place' % self.unique_name

    @property
    def split_place_name(self):
        return '%s-split' % self.unique_name

    @property
    def joined_place_name(self):
        return '%s-joined' % self.unique_name

    def get_split_size(self, color):
        source_data = self.get_input_op_and_name(self.parallel_by)
        valid_color_list = self._valid_color_list(color, self.get_workflow())
        output = self._fetch_input(color, valid_color_list, source_data)
        return output.size

    def get_outputs(self, color):
        grouped = {}
        for o in self.outputs:
            if o.name not in grouped:
                grouped[o.name] = []
            grouped[o.name].append(o)

        results = {}
        for name, outputs in grouped.iteritems():
            results[name] = [o.data
                    for o in sorted(outputs, key=lambda x: x.color)]
        return results

    def _attach_split(self, transitions, ready_place):
        transitions.extend([
            {
                'inputs': [ready_place],
                'outputs': [self.split_size_wait_place_name],
                'action': {
                    'type': 'notify',
                    'url': self.notify_callback_url('get_split_size'),
                    'requested_data': ['color_group_size'],
                    'response_places': {
                        'send_data': self.split_size_place_name,
                    },
                },
            },

            {
                'inputs': [self.split_size_wait_place_name,
                    self.split_size_place_name],
                'outputs': [self.create_color_group_place_name],
            },

            # XXX add color group creation ack callback
            {
                'inputs': [self.create_color_group_place_name],
                'outputs': [self.color_group_created_place_name],
                'action': {
                    'type': 'create-color-group',
                    'url': self.notify_callback_url('color_group_created'),
                },
            },

            {
                'inputs': [self.color_group_created_place_name],
                'outputs': [self.split_place_name],
                'action': {
                    'type': 'split',
                },
            },
        ])

        return self.split_place_name

    def _attach_join(self, transitions, action_done_place):
        transitions.append({
            'inputs': action_done_place,
            'outputs': self.joined_place_name,
            'type': 'barrier',
            'action': {
                'type': 'join',
            }
        })
        return self.joined_place_name

    def _convert_output(self, property_name, output_holder, color):
        if property_name == self.parallel_by:
            workflow = self.get_workflow()
            s = object_session(self)
            cg = s.query(ColorGroup).filter_by(workflow=workflow).filter(
                    ColorGroup.begin <= color, ColorGroup.end > color).one()
            index = color - cg.begin
            return output_holder.get_element(index)
        else:
            return output_holder.data


class InputHolderOperation(Operation):
    __tablename__ = 'operation_input_holder'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': '__input_holder',
    }

    def get_inputs(self, color):
        raise RuntimeError()

    def get_input(self, name, color):
        raise RuntimeError()

    def get_petri_transitions(self):
        return []


class InputConnectorOperation(Operation):
    __tablename__ = 'operation_input_connector'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'input connector',
    }

    def get_source_op_and_name(self, output_param_name):
        op, name = self.parent.get_input_op_and_name(output_param_name)
        return op.get_source_op_and_name(name)

    def get_output(self, name, color):
        return self.get_inputs(color).get(name)

    def get_outputs(self, color):
        return self.get_inputs(color)

    def get_inputs(self, color):
        return self.parent.get_inputs(color)

    def get_input(self, name, color):
        return self.parent.get_input(name, color)

    def get_petri_transitions(self):
        return [
            {
                'inputs': [self.parent.ready_place_name],
                'outputs': [self.success_place_name],
            },
            {
                'inputs': [self.success_place_name],
                'outputs': [self.success_place_pair_name(o) for o in self.output_ops],
            }
        ]


class OutputConnectorOperation(Operation):
    __tablename__ = 'operation_output_connector'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'output connector',
    }

    def get_outputs(self, color):
        source_data = self.get_input_sources()
        valid_color_list = self._valid_color_list(color, self.get_workflow())
        result = {}
        for property_name, source in source_data.iteritems():
            source_op, source_name = source
            result[property_name] = source_op.get_output(source_name, color)
        return result

    def get_source_op_and_name(self, output_param_name):
        op, name = self.get_input_op_and_name(output_param_name)
        return op.get_source_op_and_name(name)

    def get_petri_transitions(self):
        return []


class ModelOperation(Operation):
    __tablename__ = 'operation_model'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'model',
    }

    @property
    def real_child_ops(self):
        data = dict(self.children)
        del data['input connector']
        del data['output connector']
        return data.values()

    def get_outputs(self, color):
        return self.children['output connector'].get_outputs(color)

    def get_source_op_and_name(self, output_param_name):
        oc = self.children['output connector']
        return oc.get_source_op_and_name(output_param_name)

    def get_petri_transitions(self):
        result = []

        if self.input_ops:
            result.append({
                'inputs': [o.success_place_pair_name(self) for o in self.input_ops],
                'outputs': [self.ready_place_name],
            })

        if self.output_ops:
            success_outputs = [self.success_place_pair_name(o) for o in self.output_ops]
            if self.parent:
                success_outputs.append(self.success_place_pair_name(self.parent))
            result.append({
                'inputs': [self.success_place_name],
                'outputs': success_outputs,
            })

        result.append({
            'inputs': [o.success_place_pair_name(self)
                for o in self.real_child_ops],
            'outputs': [self.success_place_name],
            'action': {
                'type': 'notify',
                'url': self.notify_callback_url('done'),
            },
        })

        for child in self.children.itervalues():
            result.extend(child.get_petri_transitions())

        return result


class CommandOperation(OperationPetriMixin, Operation):
    __tablename__ = 'operation_command'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'command',
    }


class ParallelByCommandOperation(ParallelPetriMixin, Operation):
    __tablename__ = 'operation_command_parallel'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'parallel-by-command',
    }


class PassThroughOperation(OperationPetriMixin, Operation):
    __tablename__ = 'operation_pass_through'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'pass-through',
    }

    def execute(self, color, group):
        self.set_outputs(self.get_inputs(color), color)


class ParallelByPassThroughOperation(ParallelPetriMixin, Operation):
    __tablename__ = 'operation_pass_through_parallel'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'parallel-by-pass-through',
    }

    def execute(self, color, group):
        self.set_outputs(self.get_inputs(color), color)


def _parallel_index(color, group):
    try:
        return int(color) - int(group['begin'])
    except:
        return None
