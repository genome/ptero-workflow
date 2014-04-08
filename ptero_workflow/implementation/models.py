from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
import simplejson
import sqlalchemy.ext.declarative


__all__ = ['Base', 'Workflow']


Base = sqlalchemy.ext.declarative.declarative_base()


class Workflow(Base):
    __tablename__ = 'workflow'

    id          = Column(Integer, primary_key=True)
    environment = Column(Text)
    inputs      = Column(Text)

    root_operation_id = Column(Integer,
            ForeignKey('operation.id'), nullable=False)

    root_operation = relationship('Operation', backref='workflow')

    @property
    def links(self):
        results = []

        for name,op in self.operations.iteritems():
            results.extend(op.input_links)

        return results

    @property
    def operations(self):
        return self.root_operation.children

    @property
    def as_dict(self):
        ops = {name: op.as_dict for name,op in self.operations.iteritems()
                if name not in ['input connector', 'output connector']}
        links = [l.as_dict for l in self.links]
        return {
            'operations': ops,
            'links': links,
            'inputs': simplejson.loads(self.inputs),
            'environment': simplejson.loads(self.environment),
        }


class Operation(Base):
    __tablename__ = 'operation'
    __table_args__ = (
        UniqueConstraint('parent_id', 'name'),
    )

    id        = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('operation.id'), nullable=True)
    name      = Column(Text, nullable=False)
    type      = Column(Text, nullable=False)

    parent = relationship('Operation')

    children = relationship('Operation',
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    @property
    def as_dict(self):
        return {
            'type': self.type,
        }


class Link(Base):
    __tablename__ = 'link'
    __table_args__ = (
        UniqueConstraint('destination_id', 'destination_property'),
    )

    id = Column(Integer, primary_key=True)

    source_id      = Column(Integer, ForeignKey('operation.id'), nullable=False)
    destination_id = Column(Integer, ForeignKey('operation.id'), nullable=False)

    source_property      = Column(Text, nullable=False)
    destination_property = Column(Text, nullable=False)

    parallel_by = Column(Boolean, nullable=False, default=False)

    source_operation = relationship('Operation',
            backref=backref('output_links'),
            foreign_keys=[source_id])

    destination_operation = relationship('Operation',
            backref=backref('input_links'),
            foreign_keys=[destination_id])

    @property
    def as_dict(self):
        data = {
            'source': self.source_operation.name,
            'destination': self.destination_operation.name,
            'source_property': self.source_property,
            'destination_property': self.destination_property,
        }

        if self.parallel_by:
            data['parallel_by'] = True

        return data
