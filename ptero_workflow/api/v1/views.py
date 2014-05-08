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
        workflow_data = g.backend.get_workflow(workflow_id)

        workflow_data['reports'] = _generate_report_links(workflow_id)
        return workflow_data, 200


_REPORTS = [
    'workflow-outputs',
]
def _generate_report_links(workflow_id):
    return {n: _report_url(workflow_id, n) for n in _REPORTS}


def _report_url(workflow_id, report_type):
    return url_for('report', report_type=report_type, workflow_id=workflow_id,
            _external=True)


class OperationEventCallback(Resource):
    def put(self, operation_id, event_type):
        request_data = request.get_json()
        g.backend.event(operation_id, event_type,
                color=request_data['token_color'],
                color_group=request_data['color_group'],
                response_links=request_data.get('response_links'))
        return ''


class ReportDetailView(Resource):
    def get(self, report_type, workflow_id):
        return {'outputs': {'out_a': 'kittens'}}
