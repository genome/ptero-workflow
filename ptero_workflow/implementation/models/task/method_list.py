from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.collections import attribute_mapped_collection


__all__ = ['MethodList']


class MethodList(Task):
    __tablename__ = 'method_list'

    id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
            primary_key=True)

    methods = relationship('Method',
            collection_class=attribute_mapped_collection('name'),
            passive_deletes='all')

    method_list = relationship('Method', order_by='Method.index',
            passive_deletes='all')

    __mapper_args__ = {
        'polymorphic_identity': 'MethodList',
    }

    def attach_subclass_transitions(self, transitions, start_place):
        last_failure_place = start_place
        success_places = []
        for method in self.method_list:
            success_place, failure_place = method.attach_transitions(
                    transitions, last_failure_place)
            last_failure_place = failure_place
            success_places.append(success_place)

        for sp in success_places:
            transitions.append({
                'inputs': [sp],
                'outputs': [self._pn('success')],
            })

        return self._pn('success'), last_failure_place

    def create_input_sources(self, session, parallel_depths):
        super(MethodList, self).create_input_sources(session, parallel_depths)
        for method in self.method_list:
            method.create_input_sources(session, parallel_depths)

    def as_dict(self, detailed):
        result = {
            'methods': [m.as_dict(detailed=detailed)
                for m in self.method_list],
        }
        if self.parallel_by is not None:
            result['parallelBy'] = self.parallel_by
        webhooks = self.get_webhooks()
        if webhooks:
            result['webhooks'] = webhooks

        if detailed:
            result['executions'] = {
                    color: execution.as_dict(detailed=detailed)
                    for color, execution in self.executions.iteritems()}
        return result

    def as_dict_for_summary(self):
        execution_summary = self.execution_summary
        result = {
            'executionSummary': execution_summary,
            'name': self.name,
            'methods': [m.as_dict_for_summary() for m in self.method_list],
        }
        if self.parallel_by is not None:
            result['parallelBy'] = self.parallel_by
        return result

    @property
    def execution_summary(self):
        s = object_session(self)
        rows = s.execute("""
            SELECT status, count(status)
            FROM execution WHERE task_id = :id
            GROUP BY status;
        """, {"id": self.id})
        return {row[0]: row[1] for row in rows}

    def as_skeleton_dict(self):
        result = {
            'id': self.id,
            'methods': [m.as_skeleton_dict() for m in self.method_list],
            'topologicalIndex': self.topological_index,
        }
        if self.parallel_by is not None:
            result['parallelBy'] = self.parallel_by
        return result

    def cancel(self):
        super(MethodList, self).cancel()
        for method in self.method_list:
            method.cancel()

    def issue_job_delete_requests(self):
        for method in self.method_list:
            method.issue_job_delete_requests()

    def set_status_running(self, color, group):
        # Task executions are automatically put into 'running' state
        execution = self.get_or_create_execution(color, group)
