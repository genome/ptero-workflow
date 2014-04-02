from flask import g, request, url_for
from flask.ext.restful import Resource


class WorkflowListView(Resource):
    def post(self):
        return '', 201
