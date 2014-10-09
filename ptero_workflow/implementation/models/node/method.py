from ..base import Base
from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
import simplejson

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

    serialized_command_line = Column(Text, nullable=False)

    @property
    def command_line(self):
        return simplejson.loads(self.serialized_command_line)

    @command_line.setter
    def command_line(self, new_value):
        self.serialized_command_line = simplejson.dumps(new_value)
