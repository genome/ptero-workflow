from flask import g, request, url_for
from flask.ext.restful import Resource


class WorkflowListView(Resource):
    def post(self):
        return '', 201, {
            'Location': url_for('workflow-detail', workflow_id=0)
        }


class WorkflowDetailView(Resource):
    pass
