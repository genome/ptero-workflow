from .base import Base
from .json_type import JSON
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import backref, relationship


__all__ = ['Execution']


class Execution(Base):
    __tablename__ = 'execution'

    __table_args__ = (
        UniqueConstraint('method_id', 'color'),
    )

    id = Column(Integer, primary_key=True)

    method_id = Column(Integer, ForeignKey('method.id'), nullable=False)
    method = relationship('Method', backref='executions')

    color = Column(Integer, index=True, nullable=False)

    data = Column(JSON)
