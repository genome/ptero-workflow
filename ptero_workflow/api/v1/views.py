from flask import g, request, url_for
from flask.ext.restful import Resource


class WorkflowListView(Resource):
    def post(self):
        workflow_id = g.backend.create_workflow(request.get_json())
        return '', 201, {
            'Location': url_for('workflow-detail', workflow_id=workflow_id)
        }


class WorkflowDetailView(Resource):
    def get(self, workflow_id):
        return g.backend.get_workflow(workflow_id), 200
