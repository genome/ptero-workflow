from .base import Base
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
import base64
import logging
import json
import uuid


__all__ = ['Workflow']


LOG = logging.getLogger(__file__)



def _generate_net_key():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes)[:-2]


class Workflow(Base):
    __tablename__ = 'workflow'

    id          = Column(Integer, primary_key=True)
    environment = Column(Text)

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

        return results

    @property
    def tasks(self):
        return self.root_task.method_list[0].children

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
        if self.root_task.status is not None:
            data['status'] = self.root_task.status
        return data

    def get_petri_transitions(self):
        transitions = []
        success_place, failure_place = self.root_task.attach_transitions(
                transitions, self.start_place_name)
        return transitions

    def get_outputs(self):
        return self.root_task.get_outputs(0)
