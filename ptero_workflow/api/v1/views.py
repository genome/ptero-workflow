from . import reports
from . import validators
from ...implementation import exceptions
from flask import g, request, url_for
from flask.ext.restful import Resource
from jsonschema import ValidationError

import pkg_resources
import logging
import urllib


LOG = logging.getLogger(__file__)


class WorkflowListView(Resource):
    def post(self):
        try:
            data = validators.get_workflow_post_data()
            workflow_id = g.backend.create_workflow(data)
            return '', 201, {
                'Location': url_for('workflow-detail', workflow_id=workflow_id)
            }

        except ValidationError as e:
            LOG.exception(e)
            return {'error': e.message}, 400
        except exceptions.InvalidWorkflow as e:
            LOG.exception(e)
            return {'error': e.message}, 400
        except:
            LOG.exception('Unexpected exception posting workflow')
            raise


class WorkflowDetailView(Resource):
    def get(self, workflow_id):
        try:
            workflow_data = g.backend.get_workflow(workflow_id)

            workflow_data['reports'] = _generate_report_links(workflow_id)
            return workflow_data, 200

        except:
            LOG.exception('Unexpected exception getting workflow')
            raise


# XXX I think that the report generators should be instantiated here into a
#     static dict.  That will allow us to write a url generation function for
#     each one, so that they can put the necessary arguments into their query
#     strings.
def _generate_report_links(workflow_id):
    return {n: _report_url(workflow_id, n) for n in reports.report_names()}


def _report_url(workflow_id, report_type):
    base_url = url_for('report', report_type=report_type, _external=True)

    return '%s?%s' % (base_url, urllib.urlencode({'workflow_id': workflow_id}))


class TaskCallback(Resource):
    def put(self, task_id, callback_type):
        try:
            body_data = request.get_json()
            query_string_data = request.args
            g.backend.handle_task_callback(task_id, callback_type, body_data,
                    query_string_data)
            return ''

        except:
            LOG.exception('Unexpected exception responding to callback '
                    '(%s) on task (%s)', callback_type, task_id)
            raise


class MethodCallback(Resource):
    def put(self, method_id, callback_type):
        try:
            body_data = request.get_json()
            query_string_data = request.args
            g.backend.handle_method_callback(method_id, callback_type,
                    body_data, query_string_data)
            return ''

        except:
            LOG.exception('Unexpected exception responding to callback '
                    '(%s) on method (%s)', callback_type, method_id)
            raise


class ReportDetailView(Resource):
    def get(self, report_type):
        generator = reports.get_report_generator(report_type)
        return generator(**request.args)
