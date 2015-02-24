from .base import Base
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
import base64
import logging
import json
import uuid


__all__ = ['Workflow']


LOG = logging.getLogger(__name__)



def _generate_net_key():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes)[:-2]


class Workflow(Base):
    __tablename__ = 'workflow'

    id          = Column(Integer, primary_key=True)

    net_key = Column(Text, unique=True, default=_generate_net_key)

    root_task_id = Column(Integer, ForeignKey('task.id',
        use_alter=True, name='fk_workflow_root_task'))
    input_holder_id = Column(Integer, ForeignKey('input_holder.id',
        use_alter=True, name='fk_input_holder'))


    root_task = relationship('Task', post_update=True,
            foreign_keys=[root_task_id])
    input_holder = relationship('InputHolder',
            post_update=True, foreign_keys=[input_holder_id])

    start_place_name = 'workflow-start-place'

    @property
    def links(self):
        results = []

        for name,task in self.tasks.iteritems():
            results.extend(task.input_links)

        return sorted(results,
                key=lambda l: l.source_task.name\
                    + l.destination_task.name\
                    + l.source_property\
                    + l.destination_property)
        return results

    @property
    def tasks(self):
        return self.root_task.method_list[0].children

    @property
    def status(self):
        return self.root_task.status

    def all_tasks_iterator(self):
        yield self.root_task
        for task in self.root_task.all_tasks_iterator():
            yield task

    @property
    def is_canceled(self):
        return self.root_task.is_canceled

    def cancel(self):
        if self.is_canceled:
            return
        else:
            for task in self.all_tasks_iterator():
                task.cancel()

    @property
    def as_dict(self):
        tasks = {name: task.as_dict for name,task in self.tasks.iteritems()
                if name not in ['input connector', 'output connector']}
        links = [l.as_dict for l in self.links]

        data = {
            'tasks': tasks,
            'links': links,
            'inputs': self.root_task.get_inputs(colors=[0], begins=[0]),
        }
        if self.status is not None:
            data['status'] = self.status

        return data

    def get_petri_transitions(self):
        transitions = []
        success_place, failure_place = self.root_task.attach_transitions(
                transitions, self.start_place_name)
        return transitions

    def get_outputs(self):
        return self.root_task.get_outputs(0)
