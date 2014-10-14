import method_base
from .shell_command import *

METHOD_SUBCLASSES = {
        'ShellCommand': ShellCommand,
        }

def new_method(**kwargs):
    service = kwargs['service']
    if service in METHOD_SUBCLASSES:
        return METHOD_SUBCLASSES[service](**kwargs)
    else:
        raise TypeError("Could not determine subclass from service (%s)" %
                service)
