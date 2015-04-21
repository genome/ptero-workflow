from dag import *
from .method_base import *
from .shell_command import *
from .block import *
from .converge import *

METHOD_SUBCLASSES = [DAG, ShellCommand, Block, Converge]

def _calculate_subclass_lookup():
    result = {}
    for subclass in METHOD_SUBCLASSES:
        service = subclass.service
        result[service] = subclass
    return result
SUBCLASS_LOOKUP = _calculate_subclass_lookup()
