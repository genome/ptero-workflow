from .base import Base
from sqlalchemy import Column, UniqueConstraint, Index
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
from collections import defaultdict
from ptero_common.utils import format_dict_of_lists

import logging


__all__ = ['Link', 'DataFlowEntry']


LOG = logging.getLogger(__name__)


class Link(Base):
    __tablename__ = 'link'
    __table_args__ = (
        UniqueConstraint('source_id', 'destination_id'),
    )

    id = Column(Integer, primary_key=True)

    source_id = Column(Integer, ForeignKey('task.id'), index=True,
            nullable=False)
    destination_id = Column(Integer, ForeignKey('task.id'), index=True,
            nullable=False)

    source_task = relationship('Task',
            backref=backref('output_links'),
            foreign_keys=[source_id])

    destination_task = relationship('Task',
            backref=backref('input_links'),
            foreign_keys=[destination_id])

    def as_dict(self, detailed=False):
        data = {
            'source': self.source_task.name,
            'destination': self.destination_task.name,
        }
        if self.data_flow:
            data['dataFlow'] = format_dict_of_lists(self.data_flow)
        return data

    @property
    def data_flow(self):
        result = defaultdict(list)

        for entry in self.data_flow_entries:
            result[entry.source_property].append(entry.destination_property)

        return result

    as_skeleton_dict = as_dict


class DataFlowEntry(Base):
    __tablename__ = 'data_flow_entry'
    __table_args__ = (
        UniqueConstraint('link_id', 'source_property', 'destination_property'),
    )

    id = Column(Integer, primary_key=True)

    link_id = Column(Integer, ForeignKey('link.id'), index=True,
            nullable=False)

    source_property = Column(Text, nullable=False)
    destination_property = Column(Text, nullable=False)

    link = relationship('Link', backref=backref('data_flow_entries', lazy='joined'))
