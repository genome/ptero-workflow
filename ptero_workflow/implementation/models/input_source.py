from . import result
from .base import Base
from .json_type import JSON
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session
import logging


__all__ = ['InputSource']


LOG = logging.getLogger(__name__)


class InputSource(Base):
    __tablename__ = 'input_source'
    __table_args__ = (
        UniqueConstraint('destination_id', 'destination_property'),
    )

    id = Column(Integer, primary_key=True)

    source_id      = Column(Integer, ForeignKey('task.id'), nullable=False)
    destination_id = Column(Integer, ForeignKey('task.id'), nullable=False)

    source_property      = Column(Text, nullable=False)
    destination_property = Column(Text, nullable=False)

    parallel_depths = Column(JSON, nullable=None)

    source_task = relationship('Task', foreign_keys=[source_id])
    destination_task = relationship('Task', backref='input_sources',
            foreign_keys=[destination_id])

    def get_data(self, colors, begins):
        LOG.debug('get_data %s[%s] -> %s[%s] with parallel_depths=%s, '
                'colors=%s, begins=%s',
                self.destination_task.name, self.destination_property,
                self.source_task.name, self.source_property,
                self.parallel_depths, colors, begins)
        s = object_session(self)

        r = s.query(result.Result
                ).filter_by(task=self.source_task, name=self.source_property
                ).filter(result.Result.color.in_(colors)).one()

        if self.parallel_depths:
            # XXX This will not work for parallel nesting.  Multiple indexes
            # will need to be calculated from colors, begins and
            # self.parallel_depths.
            return r.get_element(colors[-1] - begins[-1])

        else:
            return r.data

    def get_size(self, colors, begins):
        s = object_session(self)

        r = s.query(result.Result
                ).filter_by(task=self.source_task, name=self.source_property
                ).filter(result.Result.color.in_(colors)).one()
        return r.size
