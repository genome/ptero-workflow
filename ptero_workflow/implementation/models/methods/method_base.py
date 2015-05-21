from ..base import Base
from ..execution.method_execution import MethodExecution
from .. import webhook
from flask import url_for
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
import celery
import os
import urllib


__all__ = ['Method']


class Method(Base):
    __tablename__ = 'method'
    service = 'NotImplementedError'

    __table_args__ = (
        UniqueConstraint('task_id', 'name'),
    )

    VALID_CALLBACK_TYPES = set([
        'create_execution',
    ])

    id = Column(Integer, primary_key=True)

    task_id = Column(Integer, ForeignKey('task.id'), index=True)
    task = relationship('Task')

    name = Column(Text)

    index = Column(Integer, nullable=True, index=True)

    executions = relationship('MethodExecution',
            backref=backref('method', uselist=False),
            collection_class=attribute_mapped_collection('color'),
            cascade='all, delete-orphan')

    workflow_id = Column(Integer, ForeignKey('workflow.id'),
        nullable=False, index=True)
    workflow = relationship('Workflow', foreign_keys=[workflow_id])

    type = Column(Text, nullable=False, index=True)
    __mapper_args__ = {
        'polymorphic_on': 'type',
    }


    def _pn(self, *args):
        name_base = '-'.join(['method', str(self.id), self.name.replace(' ','_')])
        return '-'.join([name_base] + list(args))

    def attach_transitions(self, transitions, start_place):
        execution_created_place = \
                self.attach_execution_transitions(transitions, start_place)

        return self.attach_subclass_transitions(transitions,
                        execution_created_place)

    def attach_execution_transitions(self, transitions, start_place):
        transitions.extend([
            {
                'inputs': [start_place],
                'outputs': [self._pn('create_execution_wait')],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url('create_execution'),
                    'response_places': {
                        'created': self._pn('create_execution_success'),
                    },
                },
            },

            {
                'inputs': [self._pn('create_execution_wait'),
                    self._pn('create_execution_success')],
                'outputs': [self._pn('execution_created_success')],
            },
        ])
        return self._pn('execution_created_success')

    def create_execution(self, body_data, query_string_data):
        color = body_data['color']
        group = body_data['group']

        colors = group.get('color_lineage', []) + [color]
        begins = group.get('begin_lineage', []) + [group['begin']]
        parent_color = _get_parent_color(colors)

        s = object_session(self)
        execution = MethodExecution(method=self, color=color,
                colors=colors, begins=begins,
                parent_color=parent_color,
                workflow_id=self.workflow_id,
                data={
                    'petri_response_links': body_data['response_links']
        })
        s.add(execution)
        s.commit()

        response_links = body_data['response_links']
        self.http.delay('PUT', response_links['created'])

    def get_webhooks(self, name=None):
        if name is not None:
            return webhook.get_webhooks_for_method(self, name)
        else:
            return webhook.get_sorted_webhook_dict(self)

    @property
    def http(self):
        return celery.current_app.tasks[
                'ptero_common.celery.http.HTTP']

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

    def as_dict(self, detailed):
        result = {
            'name': self.name,
            'service': self.service,
            'parameters': self.get_parameters(detailed=detailed),
        }

        if detailed:
            result['executions'] = {
                    color: execution.as_dict(detailed=detailed)
                    for color, execution in self.executions.iteritems()}

        return result

def _get_parent_color(colors):
    if len(colors) == 1:
        return None

    else:
        return colors[-2]
