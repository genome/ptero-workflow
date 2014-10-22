from sqlalchemy import Integer
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.dialects.postgresql import JSON as psqlJSON
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql.functions import GenericFunction
import json
import os


__all__ = ['JSON', 'get_data_element']


# This class (JSONEncodedDict) is taken from
# http://docs.sqlalchemy.org/en/rel_0_9/core/types.html#marshal-json-strings
class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::

        JSONEncodedDict(255)

    """

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


def get_data_element_brute_force(task, index):
    return task.data[index]

def get_data_element_postgres_extensions(task, index):
    s = object_session(task)
    tup = s.query(task.__class__.data[index]).filter_by(id=task.id).one()
    return tup[0]


def get_data_size_brute_force(task):
    return len(task.data)


class json_array_length(GenericFunction):
    type = Integer

def get_data_size_postgres_extensions(task):
    s = object_session(task)
    tup = s.query(json_array_length(task.__class__.data)
        ).filter_by(id=task.id).one()
    return tup[0]


def get_referenced_element_brute_force(task, index):
    from . import result
    element_result_id = task.reference_ids[index]

    s = object_session(task)
    r = s.query(result.Result).filter_by(id=element_result_id).one()
    return r.data

def get_referenced_element_postgres_extensions(task, index):
    from . import result
    s = object_session(task)
    r = s.query(result.Result
            ).join(result.Result.id == task.__class__.reference_ids[index]
            ).filter(task.__class__.id == task.id).one()
    return r.data


if os.environ.get('PTERO_WORKFLOW_DB_STRING', 'sqlite://'
        ).startswith('postgres'):

    JSON = psqlJSON
    get_data_element = get_data_element_postgres_extensions
    get_data_size = get_data_size_postgres_extensions
    get_referenced_element = get_referenced_element_brute_force

else:
    JSON = JSONEncodedDict(1000)
    get_data_element = get_data_element_brute_force
    get_data_size = get_data_size_brute_force
    get_referenced_element = get_referenced_element_brute_force
