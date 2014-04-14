from ...implementation import exceptions
from flask import g, request, url_for
from flask.ext.restful import Resource


class WorkflowListView(Resource):
    def post(self):
        try:
            workflow_id = g.backend.create_workflow(request.get_json())
            return '', 201, {
                'Location': url_for('workflow-detail', workflow_id=workflow_id)
            }
        except exceptions.InvalidWorkflow as e:
            return {'error': e.message}, 400


class WorkflowDetailView(Resource):
    def get(self, workflow_id):
        return g.backend.get_workflow(workflow_id), 200


class OperationEventCallback(Resource):
    def put(self, operation_id, event_type):
        request_data = request.get_json()
        g.backend.event(operation_id, event_type,
                color=request_data['token_color'],
                color_group=request_data['color_group'],
                response_links=request_data.get('response_links'))
        return ''
