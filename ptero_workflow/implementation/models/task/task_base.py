from ..base import Base
from .. import result
from .. import input_source
from ..petri_mixin import PetriMixin
from ..execution.task_execution import TaskExecution
from .. import webhook
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import ForeignKey, Integer, Text, Boolean
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
import celery
from ptero_common import nicer_logging
import urllib
from ptero_common import statuses
from ptero_workflow.implementation import exceptions
from ptero_workflow.urls import url_for


__all__ = ['Task']


LOG = nicer_logging.getLogger(__name__)


class Task(Base, PetriMixin):
    __tablename__ = 'task'
    __table_args__ = (
        UniqueConstraint('parent_id', 'name'),
    )

    VALID_CALLBACK_TYPES = set([
        'create_array_result',
        'get_split_size',
        'succeeded',
        'failed',
    ])

    id        = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('dag.id', use_alter=True,
            ondelete='CASCADE'), nullable=True, index=True)
    name      = Column(Text, nullable=False)
    type      = Column(Text, nullable=False)
    is_canceled = Column(Boolean, default=False)
    parallel_by = Column(Text, nullable=True)
    topological_index = Column(Integer, nullable=False)

    workflow_id = Column(Integer, ForeignKey('workflow.id',
            ondelete='CASCADE'), nullable=False, index=True)
    workflow = relationship('Workflow', foreign_keys=[workflow_id],
            backref=backref('all_tasks', passive_deletes='all'))

    __mapper_args__ = {
        'polymorphic_on': 'type',
    }

    executions = relationship('TaskExecution',
            backref=backref('task', uselist=False),
            passive_deletes='all',
            collection_class=attribute_mapped_collection('color'))

    def __init__(self, *args, **kwargs):
        Base.__init__(self, *args, **kwargs)

    def status(self, color):
        try:
            return self.executions[color].status
        except KeyError:
            # if task hasn't created any Executions of this color yet
            return None

    def get_webhooks(self, name=None):
        if name is not None:
            return webhook.get_webhooks_for_task(self, name)
        else:
            return webhook.get_sorted_webhook_dict(self)

    def cancel(self):
        if self.parent is not None:
            parent_info = " in DAG ID:%s with name (%s)" %\
                    (self.parent.id, self.parent.name)
        else:
            parent_info = ''
        LOG.info("Canceling task ID:%s with name (%s)%s",
            self.id, self.name, parent_info,
            extra={'workflowName':self.workflow.name})
        self.is_canceled = True
        for execution in self.executions.values():
            execution.cancel()

    def issue_job_delete_requests(self):
        if self.parent is not None:
            parent_info = " in DAG ID:%s with name (%s)" %\
                    (self.parent.id, self.parent.name)
        else:
            parent_info = ''
        LOG.info("Issuing job delete requests for Task ID:%s with name (%s)%s",
            self.id, self.name, parent_info,
            extra={'workflowName':self.workflow.name})
        for execution in self.executions.values():
            execution.issue_job_delete_requests()

    def _pn(self, *args):
        name_base = '-'.join(['task', str(self.id), self.name.replace(' ','_')])
        return '-'.join([name_base] + list(args))

    def as_dict(self, detailed):
        raise NotImplementedError

    def as_dict_for_summary(self):
        raise NotImplementedError

    def attach_transitions(self, transitions, start_place):

        if self.parallel_by is None:
            action_success, action_failure = \
                    self.attach_subclass_transitions(transitions,
                            start_place)
        else:
            split, split_failure = self._attach_split_transitions(
                    transitions, start_place)
            subclass_success, subclass_failure = \
                    self.attach_subclass_transitions(transitions, split)
            update_success, update_failure = self._attach_status_update_actions(
                    transitions, subclass_success, subclass_failure, 'inner')
            action_success, join_failure = \
                    self._attach_join_transitions(transitions,
                            update_success, update_failure)
            action_failure = \
                    self.attach_or_transitions(transitions,
                            split_failure, join_failure)

        success, failure = self._attach_status_update_actions(
                transitions, action_success, action_failure, 'outer')


        return success, failure

    def attach_subclass_transitions(self, transitions, start_place):
        return start_place, None

    def _attach_split_transitions(self, transitions, start_place):
        transitions.extend([
            {
                'inputs': [start_place],
                'outputs': [self._pn('split_size_wait'),
                    self._pn('join_fail_wait')],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('get_split_size'),
                    'requested_data': ['color_group_size'],
                    'response_places': {
                        'send_data': self._pn('split_size_success'),
                        'failure': self._pn('split_size_failure'),
                    },
                },
            },

            {
                'inputs': [self._pn('split_size_wait'),
                    self._pn('split_size_success')],
                'outputs': [self._pn('color_group_created')],
                'action': {
                    'type': 'create-color-group',
                },
            },

            {
                'inputs': [self._pn('split_size_wait'),
                    self._pn('split_size_failure')],
                'outputs': [self._pn('split_failure')],
            },

            {
                'inputs': [self._pn('color_group_created')],
                'outputs': [self._pn('split')],
                'action': {
                    'type': 'split',
                },
            },
        ])

        return self._pn('split'), self._pn('split_failure')


    def _attach_join_transitions(self, transitions, subclass_success_place,
            subclass_failure_place):
        transitions.extend([
            {
                'inputs': [subclass_success_place],
                'outputs': [self._pn('joined')],
                'type': 'barrier',
                'action': {
                    'type': 'join',
                }
            },
            {
                'inputs': [self._pn('joined')],
                'outputs': [self._pn('array_result_wait')],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('create_array_result'),
                    'response_places': {
                        'created': self._pn('array_result_callback'),
                    }
                },
            },
            {
                'inputs': [self._pn('array_result_wait'),
                    self._pn('array_result_callback')],
                'outputs': [self._pn('join_success')],
            },

            {
                'inputs': [subclass_failure_place],
                'outputs': [self._pn('join_fail_convert')],
                'action': {
                    'type': 'convert-to-parent-color',
                },
            },
            {
                'inputs': [self._pn('join_fail_convert'),
                    self._pn('join_fail_wait')],
                'outputs': [self._pn('join_fail')],
            },
        ])

        return self._pn('join_success'), self._pn('join_fail')

    def _attach_status_update_actions(self, transitions, action_success_place,
            action_failure_place, name):
        transitions.append({
                'inputs': [action_success_place],
                'outputs': [self._pn('update_status_success', name)],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('succeeded'),
                }})
        success_place = self._pn('update_status_success', name)


        if action_failure_place is None:
            failure_place = action_failure_place

        else:
            transitions.append({
                'inputs': [action_failure_place],
                    'outputs': [self._pn('update_status_failure', name)],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('failed'),
                }})
            failure_place = self._pn('update_status_failure', name)

        return success_place, failure_place

    def attach_or_transitions(self, transitions, *place_names):
        result_place = self._pn('or', *place_names)
        for place_name in place_names:
            transitions.extend([
                {
                    'inputs': [place_name],
                    'outputs': [result_place],
                },
            ])
        return result_place

    @property
    def parallel_depth(self):
        increment = 0
        if self.parallel_by:
            increment = 1

        if self.parent:
            return self.parent.task.parallel_depth + increment

        else:
            return increment

    def get_split_size(self, body_data, query_string_data):

        execution = self.get_or_create_execution(body_data['color'],
                body_data['group'])

        color = body_data['color']
        group = body_data['group']
        response_links = body_data['response_links']

        colors = group.get('color_lineage', []) + [color]
        begins = group.get('begin_lineage', []) + [group['begin']]

        s = object_session(self)
        try:
            source = s.query(input_source.InputSource
                    ).filter_by(destination_task=self,
                            destination_property=self.parallel_by
                    ).one()
            size = source.get_size(colors, begins)
        except Exception as e:
            s.rollback()
            LOG.exception('%s - Failed to get split size',
                    self.workflow_id)
            LOG.info('Notifying petri: execution "%s" failed to compute '
                    'split size for workflow "%s"',
                    execution.name, self.workflow.name,
                    extra={'workflowName':self.workflow.name})
            self.http.delay('PUT', response_links['failure'])

            execution.data['error'] = \
                'Failed to get split size: %s' % e.message
            s.commit()
            return

        LOG.info('Notifying petri: execution "%s" has split size %s for'
                ' workflow "%s"', execution.name, size, self.workflow.name,
                extra={'workflowName':self.workflow.name})
        self.http.delay('PUT', response_links['send_data'],
                color_group_size=size)


    def create_array_result(self, body_data, query_string_data):

        color = body_data['color']
        group = body_data['group']
        parent_color = group.get('parent_color')
        response_links = body_data['response_links']

        s = object_session(self)
        for output_name in self.output_names:
            source, name, parallel_depths = self.resolve_output_source(s,
                    output_name, [])
            results = s.query(result.Result
                    ).filter_by(task=source, name=name, parent_color=color
                    ).order_by('result.color'
                    ).all()

            array_result = result.Result(task=source, name=name,
                    color=color, parent_color=parent_color,
                    data=[r.data for r in results])
            s.add(array_result)

        s.commit()

        LOG.info('Notifying petri: created array result for task (%s) for'
                ' workflow "%s"', self.name, self.workflow.name,
                extra={'workflowName':self.workflow.name})
        self.http.delay('PUT', response_links['created'])

    @property
    def input_names(self):
        result = set()
        for link in self.input_links:
            for entry in link.data_flow_entries:
                result.add(entry.destination_property)
        return result

    @property
    def output_names(self):
        result = set()
        for link in self.output_links:
            for entry in link.data_flow_entries:
                result.add(entry.source_property)
        return result

    @classmethod
    def from_dict(cls, type, **kwargs):
        subclass = cls.subclass_for(type)
        return subclass(**kwargs)

    @classmethod
    def subclass_for(cls, type):
        mapper = inspect(cls)
        return mapper.polymorphic_map[type].class_

    def callback_url(self, callback_type, **params):
        if params:
            query_string = '?%s' % urllib.urlencode(params)
        else:
            query_string = ''

        base_url = url_for('task-callback',
                task_id=self.id, callback_type=callback_type)
        return base_url + query_string

    @property
    def input_tasks(self):
        source_ids = set([l.source_id for l in self.input_links])
        if source_ids:
            s = object_session(self)
            return s.query(Task).filter(Task.id.in_(source_ids)).all()
        else:
            return []

    @property
    def output_tasks(self):
        destination_ids = set([l.destination_id for l in self.output_links])
        if destination_ids:
            s = object_session(self)
            return s.query(Task).filter(
                    Task.id.in_(destination_ids)).all()
        else:
            return []

    def set_outputs(self, outputs, color, parent_color):
        for output_name in self.output_names:
            if output_name not in outputs.keys():
                raise exceptions.MissingOutputError(
                        "No value specified for output (%s) on task (%s:%s), "
                        "outputs specified were: %s" % (output_name, self.name,
                            self.id, str(outputs.keys())))
            else:
                result.Result(task=self, name=output_name,
                        data=outputs[output_name], color=color,
                        parent_color=parent_color)

    def get_inputs(self, colors, begins):
        inputs = {}
        for source in self.input_sources:
            inputs[source.destination_property] = source.get_data(
                    colors, begins)

        LOG.debug('Got inputs for Task (%s:%s), colors=%s in workflow %s: %s',
                self.name, self.id, colors, self.workflow.name, inputs)

        return inputs

    def handle_callback(self, callback_type, body_data, query_string_data):
        if callback_type in self.VALID_CALLBACK_TYPES:
            return getattr(self, callback_type)(body_data, query_string_data)
        else:
            raise RuntimeError('Invalid callback type (%s).  Allowed types: %s'
                    % (callback_type, self.VALID_CALLBACK_TYPES))

    def get_or_create_execution(self, color, group):
        s = object_session(self)

        try:
            execution = s.query(TaskExecution).filter(
                    TaskExecution.task==self,
                    TaskExecution.color==color).one()
            created_execution = False
        except NoResultFound:
            colors = group.get('color_lineage', []) + [color]
            begins = group.get('begin_lineage', []) + [group['begin']]
            parent_color = _get_parent_color(colors)

            execution = TaskExecution(task=self, color=color,
                    colors=colors, begins=begins,
                    workflow_id=self.workflow_id,
                    parent_color=parent_color,
            )
            s.add(execution)
            try:
                s.commit()
                created_execution = True
            except IntegrityError:
                s.rollback()
                execution = s.query(TaskExecution).filter(
                        TaskExecution.task==self,
                        TaskExecution.color==color).one()
                created_execution = False

        if created_execution:
            execution.status = statuses.scheduled
            s.flush()
            execution.status = statuses.running
            s.flush()

        if self.is_canceled:
            execution.status = statuses.canceled

        s.commit()

        return execution

    def succeeded(self, body_data, query_string_data):
        self._ended(body_data, query_string_data, statuses.succeeded)

    def failed(self, body_data, query_string_data):
        self._ended(body_data, query_string_data, statuses.failed)

    def _ended(self, body_data, query_string_data, status):

        s = object_session(self)

        execution = self.get_or_create_execution(body_data['color'],
                body_data['group'])
        execution.status = status

        s.commit()

    def resolve_input_source(self, session, name, parallel_depths):
        if self.parallel_by == name:
            pdepths = [self.parallel_depth] + parallel_depths

        else:
            pdepths = parallel_depths

        for input_link in self.input_links:
            for source, destination_list in input_link.data_flow.iteritems():
                if name in destination_list:
                    return input_link.source_task.resolve_output_source(session,
                            source, pdepths)

    def resolve_output_source(self, session, name, parallel_depths):
        return self, name, parallel_depths

    def create_input_sources(self, session, parallel_depths):
        LOG.debug('Creating input sources for Task %s:%s in workflow %s',
                self.name, self.id, self.workflow.name,
                extra={'workflowName':self.workflow.name})
        for input_link in self.input_links:
            for entry in input_link.data_flow_entries:
                source_task, source_property, source_parallel_depths = \
                        self.resolve_input_source(session, entry.destination_property,
                                parallel_depths)
                LOG.debug('Found input source %s:%s[%s] = %s:%s[%s]: '
                        'parallel_depths=%s in workflow %s',
                        self.workflow_id, self.name, self.id,
                        entry.destination_property,
                        source_task.name, source_task.id, entry.source_property,
                        source_parallel_depths,
                        extra={'workflowName':self.workflow.name})

                in_source = input_source.InputSource(
                        source_task=source_task,
                        source_property=source_property,
                        destination_task=self,
                        destination_property=entry.destination_property,
                        parallel_depths=source_parallel_depths,
                        workflow=self.workflow,
                )
                session.add(in_source)

    @property
    def http(self):
        return celery.current_app.tasks[
                'ptero_common.celery.http.HTTP']

    def get_outputs(self, color):
        s = object_session(self)
        results = s.query(result.Result).filter_by(task=self, color=color).all()
        if results:
            return {r.name: r.data for r in results}


def _get_parent_color(colors):
    if len(colors) == 1:
        return None

    else:
        return colors[-2]
