from ptero_workflow.implementation.models.execution import Execution
from ptero_common import nicer_logging
from ptero_common import statuses

__all__ = ['MethodExecution']


LOG = nicer_logging.getLogger(__name__)


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

    def cancel(self):
        self.status = statuses.canceled
        for child_workflow in self.child_workflows:
            child_workflow.cancel()

        if 'jobUrl' in self.data:
            url = self.data['jobUrl']
            LOG.info("Sending PATCH request to cancel job at %s",
                   url, extra={'workflowName':self.workflow.name})
            self.method.http.delay('PATCH', url, status=statuses.canceled)
