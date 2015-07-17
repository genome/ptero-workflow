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
        s = object_session(self)
        query_results = s.query(result.Result).filter_by(task=self.task,
            color=self.color, parent_color=self.parent_color).all()
        return {r.name: r.data for r in query_results}
