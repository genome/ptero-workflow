from dag import *
from .method_base import *
from .shell_command import *

METHOD_SUBCLASSES = [DAG, ShellCommand]

def _calculate_subclass_lookup():
    result = {}
    for subclass in METHOD_SUBCLASSES:
        service = subclass.service
        result[service] = subclass
    return result
SUBCLASS_LOOKUP = _calculate_subclass_lookup()
