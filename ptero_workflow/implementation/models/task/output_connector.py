from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['OutputConnector']


class OutputConnector(Task):
    __tablename__ = 'output_connector'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'output connector',
    }

    def get_outputs(self, color):
        source_data = self.get_input_sources()
        result = {}
        for property_name, source in source_data.iteritems():
            source_task, source_name = source
            result[property_name] = source_task.get_output(source_name, color)
        return result

    def get_source_task_and_name(self, output_param_name):
        task, name = self.get_input_task_and_name(output_param_name)
        return task.get_source_task_and_name(name)

    def attach_subclass_transitions(self, transitions, start_place):
        # XXX DAG should be responsible for ordering tasks and looking at
        # links, not OC
        return start_place, self.failure_place_name
