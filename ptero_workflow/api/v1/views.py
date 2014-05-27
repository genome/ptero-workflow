from ...implementation import exceptions
from flask import g, request, url_for
from flask.ext.restful import Resource

import pkg_resources
import urllib


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


# XXX I think that the report generators should be instantiated here into a
#     static dict.  That will allow us to write a url generation function for
#     each one, so that they can put the necessary arguments into their query
#     strings.
_REPORTS = [ep.name for ep in pkg_resources.iter_entry_points('reports')]
def _generate_report_links(workflow_id):
    return {n: _report_url(workflow_id, n) for n in _REPORTS}


def _report_url(workflow_id, report_type):
    base_url = url_for('report', report_type=report_type, _external=True)

    return '%s?%s' % (base_url, urllib.urlencode({'workflow_id': workflow_id}))


class OperationEventCallback(Resource):
    def put(self, operation_id, event_type):
        request_data = request.get_json()
        g.backend.event(operation_id, event_type, **request_data)
        return ''


class ReportDetailView(Resource):
    def get(self, report_type):
        generator = _get_report_generator(report_type)
        return generator(**request.args)

def _get_report_generator(report_type):
    return pkg_resources.load_entry_point('ptero_workflow', 'reports',
            report_type)
