from ptero_workflow.implementation.models.execution import Execution
from sqlalchemy.orm.session import object_session
from .. import result

__all__ = ['MethodExecution']

class MethodExecution(Execution):
    __mapper_args__ = {
        'polymorphic_identity': 'MethodExecution',
    }

    @property
    def name(self):
        return "%s.%s.%s" % (
                self.method.task.name,
                self.method.name,
                self.id,
        )

    @property
    def parent(self):
        return self.method

    def get_inputs(self):
        return self.method.task.get_inputs(colors=self.colors,
                begins=self.begins)

    def get_outputs(self):
        return self.method.task.get_outputs(color=self.color)
