from .base import Base
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection


class ResponseLink(Base):
    __tablename__ = 'response_link'

    job_id = Column(Integer, ForeignKey('job.id'), primary_key=True)
    name = Column(Text, primary_key=True)

    url = Column(Text, nullable=False)


class Job(Base):
    __tablename__ = 'job'

    __table_args__ = (
        UniqueConstraint('operation_id', 'method_id', 'color'),
    )

    id = Column(Integer, primary_key=True)

    job_id = Column(Text, index=True, nullable=False)
    operation_id = Column(Integer, ForeignKey('operation.id'), nullable=False)
    method_id = Column(Integer, ForeignKey('operation_command_method.id'),
            nullable=False)
    color = Column(Integer, nullable=False)

    operation = relationship('Operation', backref='jobs')
    method = relationship('Method')

    response_links = relationship(ResponseLink, backref='job',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')
