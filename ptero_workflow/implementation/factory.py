from . import backend
from . import models
import sqlalchemy
import time


__all__ = ['Factory']


class Factory(object):
    def __init__(self, connection_string, celery_app=None):
        self.connection_string = connection_string
        self._engine = None
        self._Session = None
        self.celery_app = celery_app

    def create_backend(self):
        self._initialize()
        return backend.Backend(self._Session(), self.celery_app)

    def _initialize(self):
        # Lazy initialize to be pre-fork friendly.
        if not self._engine:
            self._initialize_sqlalchemy()

        if not self.celery_app:
            self._initialize_celery()

    def _initialize_sqlalchemy(self):
        self._engine = sqlalchemy.create_engine(self.connection_string)
        for i in xrange(3):
            try:
                models.Base.metadata.create_all(self._engine)
                break
            except sqlalchemy.exc.SQLAlchemyError:
                time.sleep(0.5)

        self._Session = sqlalchemy.orm.sessionmaker(bind=self._engine)

    def _initialize_celery(self):
        from . import celery_app
        self.celery_app = celery_app.app
