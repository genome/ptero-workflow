from .method_base import Method
from ..mixins.shell_command import ShellCommandPetriMixin
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['ShellCommand']


class ShellCommand(ShellCommandPetriMixin, Method):
    __tablename__ = 'shell_command'

    id = Column(Integer, ForeignKey('method.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'ShellCommand',
    }

    @property
    def command_line(self):
        return self.parameters['commandLine']
