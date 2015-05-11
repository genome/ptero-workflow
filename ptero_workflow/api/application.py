from . import v1
from ..implementation.factory import Factory
from flask import request
import zlib
import flask
import os


__all__ = ['create_app']


def create_app():
    factory = Factory(os.environ.get('PTERO_WORKFLOW_DB_STRING', 'sqlite://'))

    app = _create_app_from_blueprints()

    _attach_factory_to_app(factory, app)

    return app


def _create_app_from_blueprints():
    app = flask.Flask('PTero Workflow Service')
    app.register_blueprint(v1.blueprint, url_prefix='/v1')

    return app

def _attach_factory_to_app(factory, app):
    @app.before_request
    def before_request():
        flask.g.backend = factory.create_backend()
        if request.headers.get('content-encoding', 'identity') == 'gzip':
            request._cached_data = zlib.decompress(request.data)

    @app.teardown_request
    def teardown_request(exception):
        flask.g.backend.cleanup()
