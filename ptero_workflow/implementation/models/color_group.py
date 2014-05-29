from .base import Base
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session


__all__ = ['ColorGroup']


class ColorGroup(Base):
    __tablename__ = 'color_group'
    __table_args__ = (
        UniqueConstraint('workflow_id', 'index'),
    )

    id = Column(Integer, primary_key=True)

    workflow_id = Column(Integer, ForeignKey('workflow.id'), nullable=False)
    index = Column(Integer, nullable=False, index=True)

    begin = Column(Integer, nullable=False, index=True)
    end = Column(Integer, nullable=False, index=True)

    parent_color = Column(Integer, nullable=True, index=True)
    parent_color_group_id = Column(Integer, ForeignKey('color_group.id'),
            nullable=True)

    workflow = relationship('Workflow', uselist=False)
    parent_color_group = relationship('ColorGroup', uselist=False)

    @classmethod
    def create(cls, workflow, group):
        self = cls(workflow=workflow, index=group['idx'],
                begin=group['begin'], end=group['end'],
                parent_color=group['parent_color'])

        s = object_session(workflow)
        parent_cg = s.query(ColorGroup).filter_by(workflow=workflow,
                index=group['parent_color_group_idx']).one()
        self.parent_color_group = parent_cg

        return self
