from ..base import Base
from ..json_type import JSON
from .mixins.method import MethodPetriMixin
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
import simplejson

__all__ = ['Method']

class Method(MethodPetriMixin, Base):
    __tablename__ = 'method'

    __table_args__ = (
        UniqueConstraint('node_id', 'name'),
    )

    id = Column(Integer, primary_key=True)

    node_id = Column(Integer, ForeignKey('node.id'))
    name = Column(Text)

    index = Column(Integer, nullable=False, index=True)

    parameters = Column(JSON, nullable=False)

    @property
    def command_line(self):
        return self.parameters['commandLine']
