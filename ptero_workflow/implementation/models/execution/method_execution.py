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

    @property
    def child_workflow_urls(self):
        return [w.url for w in self.child_workflows]

    def get_inputs(self):
        return self.method.task.get_inputs(colors=self.colors,
                begins=self.begins)

    def get_outputs(self):
        return self.method.task.get_outputs(color=self.color)

    @property
    def missing_outputs(self):
        outputs = self.get_outputs()
        if outputs is not None:
            return self.method.task.output_names - set(self.get_outputs())
        else:
            return self.method.task.output_names
