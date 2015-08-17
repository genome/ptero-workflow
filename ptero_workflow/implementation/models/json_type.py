from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import JSON as psqlJSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql.functions import GenericFunction


__all__ = ['JSON', 'get_data_element']


def get_data_element_postgres_extensions(task, indexes):
    if indexes:
        q = task.__class__.data[indexes]
    else:
        q = task.__class__.data

    s = object_session(task)
    tup = s.query(q).filter_by(id=task.id).one()
    return tup[0]


class json_array_length(GenericFunction):
    type = Integer


def get_data_size_postgres_extensions(task, indexes):
    if indexes:
        q = task.__class__.data[indexes]
    else:
        q = task.__class__.data

    s = object_session(task)
    tup = s.query(json_array_length(q)).filter_by(id=task.id).one()
    return tup[0]

MutableJSONDict = MutableDict.as_mutable(psqlJSON)
JSON = psqlJSON
get_data_element = get_data_element_postgres_extensions
get_data_size = get_data_size_postgres_extensions
