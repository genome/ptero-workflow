from ...base import Base
from ...json_type import JSON
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint


__all__ = ['Method']


class Method(Base):
    __tablename__ = 'method'

    __table_args__ = (
        UniqueConstraint('node_id', 'name'),
    )

    id = Column(Integer, primary_key=True)

    node_id = Column(Integer, ForeignKey('node.id'))
    name = Column(Text)

    index = Column(Integer, nullable=False, index=True)

    parameters = Column(JSON, nullable=False)

    service = Column(Text, nullable=False)
    __mapper_args__ = {
        'polymorphic_on': 'service',
    }

