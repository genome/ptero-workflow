from sqlalchemy.orm import relationship
from ptero_workflow.implementation.models.execution import Execution
from sqlalchemy.orm.session import object_session
from .. import result

class MethodExecution(Execution):
    method = relationship('Method', backref='executions')

    __mapper_args__ = {
        'polymorphic_identity': 'MethodExecution',
    }

    def get_inputs(self):
        return self.method.task.get_inputs(colors=self.colors,
                begins=self.begins)

    def get_outputs(self):
        s = object_session(self)
        query_results = s.query(result.Result).filter_by(task=self.method.task,
            color=self.color, parent_color=self.parent_color).all()
        return {r.name: r.data for r in query_results}
