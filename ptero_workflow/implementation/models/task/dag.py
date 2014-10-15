from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['DAG']


class DAG(Task):
    __tablename__ = 'dag'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'dag',
    }

    @property
    def real_child_tasks(self):
        data = dict(self.children)
        del data['input connector']
        del data['output connector']
        return data.values()

    def get_outputs(self, color):
        return self.children['output connector'].get_outputs(color)

    def get_source_task_and_name(self, output_param_name):
        oc = self.children['output connector']
        return oc.get_source_task_and_name(output_param_name)

    def get_petri_transitions(self):
        result = []

        if self.input_tasks:
            result.append({
                'inputs': [o.success_place_pair_name(self) for o in self.input_tasks],
                'outputs': [self.ready_place_name],
            })

        if self.output_tasks:
            success_outputs = [self.success_place_pair_name(o) for o in self.output_tasks]
            if self.parent:
                success_outputs.append(self.success_place_pair_name(self.parent))
            result.append({
                'inputs': [self.success_place_name],
                'outputs': success_outputs,
            })

        result.append({
            'inputs': [o.success_place_pair_name(self)
                for o in self.real_child_tasks],
            'outputs': [self.success_place_name],
            'action': {
                'type': 'notify',
                'url': self.callback_url('done'),
            },
        })

        for child in self.children.itervalues():
            result.extend(child.get_petri_transitions())

        return result
