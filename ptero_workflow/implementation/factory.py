from . import backend
import sqlalchemy
import os
import logging
from ptero_workflow.utils import base_dir
from alembic.config import Config
from alembic import command


alembic_cfg = Config()
versions_dir = os.path.join(base_dir(), 'alembic', 'versions')
alembic_cfg.set_main_option('version_locations', versions_dir)
scripts_dir = os.path.join(base_dir(), 'alembic')
alembic_cfg.set_main_option('script_location', scripts_dir)
alembic_cfg.set_main_option('url', os.environ['PTERO_WORKFLOW_DB_STRING'])


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
        logging.getLogger('sqlalchemy.engine').setLevel(getattr(logging,
                os.environ.get('PTERO_WORKFLOW_ORM_LOG_LEVEL', 'WARN').upper()))
        self._engine = sqlalchemy.create_engine(self.connection_string)

        with self._engine.begin() as connection:

            alembic_cfg.attributes['connection'] = connection
            command.upgrade(alembic_cfg, "head")

        self._Session = sqlalchemy.orm.sessionmaker(bind=self._engine)

    def _initialize_celery(self):
        from . import celery_app
        self.celery_app = celery_app.app
