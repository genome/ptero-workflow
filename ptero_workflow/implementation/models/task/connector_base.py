from .task_base import Task
import logging


LOG = logging.getLogger(__name__)


class Connector(Task):
    def attach_subclass_transitions(self, transitions, start_place):
        return start_place, None
