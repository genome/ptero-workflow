from ptero_workflow.implementation.models.execution import Execution
from sqlalchemy.orm.session import object_session
from .. import result

__all__ = ['TaskExecution']


class TaskExecution(Execution):
    __mapper_args__ = {
        'polymorphic_identity': 'TaskExecution',
    }

    @property
    def name(self):
        return "%s.%s" % (
                self.task.name,
                self.id,
        )

    @property
    def parent(self):
        return self.task

    def get_inputs(self):
        return self.task.get_inputs(colors=self.colors,
                begins=self.begins)

    def get_outputs(self):
        return self.task.get_outputs(color=self.color)
