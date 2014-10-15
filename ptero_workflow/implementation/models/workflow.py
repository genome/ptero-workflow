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

    root_task_id = Column(Integer, ForeignKey('task.id',
        use_alter=True, name='fk_workflow_root_task'))
    input_holder_id = Column(Integer, ForeignKey('input_holder.id',
        use_alter=True, name='fk_input_holder'))


    root_task = relationship('Task', post_update=True,
            foreign_keys=[root_task_id])
    input_holder = relationship('InputHolder',
            post_update=True, foreign_keys=[input_holder_id])

    @property
    def start_place_name(self):
        return self.root_task.ready_place_name

    @property
    def edges(self):
        results = []

        for name,task in self.tasks.iteritems():
            results.extend(task.input_edges)

        return results

    @property
    def tasks(self):
        return self.root_task.children

    @property
    def as_dict(self):
        tasks = {name: task.as_dict for name,task in self.tasks.iteritems()
                if name not in ['input connector', 'output connector']}
        edges = [l.as_dict for l in self.edges]

        try:
            outputs = self.root_task.get_outputs(color=0)
        except:
            outputs = None

        data = {
            'tasks': tasks,
            'edges': edges,
            'inputs': self.root_task.get_inputs(colors=[0], parallel_index=0),
            'outputs': outputs,
            'environment': simplejson.loads(self.environment),
        }
        if self.root_task.status is not None:
            data['status'] = self.root_task.status
        return data

    def get_petri_transitions(self):
        return self.root_task.get_petri_transitions()
