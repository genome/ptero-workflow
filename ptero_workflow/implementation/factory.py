from . import backend
from . import models
import sqlalchemy


__all__ = ['Factory']


class Factory(object):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self._initialized = False
        self._engine = None
        self._Session = None

    def create_backend(self):
        self._initialize()
        return backend.Backend(self._get_session())

    def purge(self):
        self._initialize()
        s = self._get_session()
        s.query(models.Link).delete()
        s.query(models.Operation).delete()
        s.query(models.Workflow).delete()
        s.commit()

    def _get_session(self):
        if self._Session is None:
            self._initialize_session()

        return self._Session()

    def _initialize(self):
        # Lazy initialize to be pre-fork friendly.
        if not self._initialized:
            self._engine = sqlalchemy.create_engine(self.connection_string)
            models.Base.metadata.create_all(self._engine)
            self._Session = sqlalchemy.orm.sessionmaker(bind=self._engine)
            self._initialized = True
