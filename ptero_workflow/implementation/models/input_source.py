from . import result
from .base import Base
from .json_type import JSON
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.exc import NoResultFound
from ..exceptions import MissingResultError
from ptero_common import nicer_logging


__all__ = ['InputSource']


LOG = nicer_logging.getLogger(__name__)


class InputSource(Base):
    __tablename__ = 'input_source'
    __table_args__ = (
        UniqueConstraint('destination_id', 'destination_property'),
    )

    id = Column(Integer, primary_key=True)

    source_id      = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
            index=True, nullable=False)
    destination_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
            index=True, nullable=False)

    source_property      = Column(Text, nullable=False, index=True)
    destination_property = Column(Text, nullable=False, index=True)

    parallel_depths = Column(JSON, nullable=False)

    source_task = relationship('Task', foreign_keys=[source_id])
    destination_task = relationship('Task', backref=backref('input_sources',
            passive_deletes='all'),
            foreign_keys=[destination_id])

    workflow_id = Column(Integer, ForeignKey('workflow.id', ondelete='CASCADE'),
        nullable=False, index=True)
    workflow = relationship('Workflow', foreign_keys=[workflow_id],
            backref=backref('all_input_sources', passive_deletes='all'))

    def parallel_indexes(self, colors, begins):
        indexes = []
        for depth in self.parallel_depths:
            if depth >= len(colors):
                return indexes
            indexes.append(colors[depth] - begins[depth])
        return indexes

    def get_data(self, colors, begins):
        s = object_session(self)

        try:
            r = s.query(result.Result
                    ).filter_by(task=self.source_task, name=self.source_property
                    ).filter(result.Result.color.in_(colors)).one()
        except NoResultFound:
            raise MissingResultError("No result found for task (%s:%s) with "
                    "name (%s) and color one of %s" % (
                    self.source_task.name, self.source_task.id,
                    self.source_property, str(colors)))

        indexes = self.parallel_indexes(colors, begins)
        return r.get_data(indexes)

    def get_size(self, colors, begins):
        indexes = self.parallel_indexes(colors, begins)
        s = object_session(self)
        r = s.query(result.Result
                ).filter_by(task=self.source_task, name=self.source_property
                ).filter(result.Result.color.in_(colors)).one()
        return r.get_size(indexes)
