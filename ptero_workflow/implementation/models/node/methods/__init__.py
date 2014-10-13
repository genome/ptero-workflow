import method_base
from .shell_command import *

METHOD_SUBCLASSES = [ShellCommand]

def new_method(**kwargs):
    service = kwargs['service']
    for subclass in METHOD_SUBCLASSES:
        if subclass.__mapper_args__['polymorphic_identity'] == service:
            return subclass(**kwargs)
    raise TypeError("No Subclass with polymorphic_identity 'service'=%s"
            % service)
