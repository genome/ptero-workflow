from dag import *  # noqa
from .method_base import *  # noqa
from .job import *  # noqa
from .block import *  # noqa
from .converge import *  # noqa

METHOD_SUBCLASSES = [DAG, Job, Block, Converge]


def _calculate_subclass_lookup():
    result = {}
    for subclass in METHOD_SUBCLASSES:
        service = subclass.service
        result[service] = subclass
    return result
SUBCLASS_LOOKUP = _calculate_subclass_lookup()
