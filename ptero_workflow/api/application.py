from . import v1
from ..implementation.factory import Factory
from flask import request, jsonify
import zlib
import flask
import os
from ptero_common import nicer_logging


LOG = nicer_logging.getLogger(__name__)


__all__ = ['create_app']


def create_app():
    factory = Factory(os.environ['PTERO_WORKFLOW_DB_STRING'])

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
        try:
            flask.g.backend = factory.create_backend()
        except:
            LOG.exception("Exception occured while creating backend")
            return jsonify({"error": "Internal Server Error: could not create backend"}), 500

        if request.headers.get('content-encoding', 'identity') == 'gzip':
            request._cached_data = zlib.decompress(request.data,
                    zlib.MAX_WBITS | 32)

    @app.teardown_request
    def teardown_request(exception):
        if hasattr(flask.g, 'backend'):
            flask.g.backend.cleanup()
