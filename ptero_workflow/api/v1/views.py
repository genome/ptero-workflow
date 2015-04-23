from . import reports
from . import validators
from ...implementation import exceptions
from flask import g, request, url_for
from flask.ext.restful import Resource
from jsonschema import ValidationError
from ptero_common.logging_configuration import logged_response
from functools import wraps

import logging
import urllib


LOG = logging.getLogger(__name__)


def sends_404(target):
    @wraps(target)
    def wrapper(*args, **kwargs):
        try:
            result = target(*args, **kwargs)
        except exceptions.NoSuchEntityError as e:
            return {'error': e.message}, 404
        return result
    return wrapper


class WorkflowListView(Resource):
    @logged_response(logger=LOG)
    @sends_404
    def post(self):
        try:
            data = validators.get_workflow_post_data()
            workflow_id, workflow_as_dict = g.backend.create_workflow(data)
            return _prepare_workflow_data(workflow_id, workflow_as_dict), 201, {
                'Location': url_for('workflow-detail', workflow_id=workflow_id)
            }

        except ValidationError as e:
            LOG.exception(e)
            return {'error': e.message}, 400
        except exceptions.InvalidWorkflow as e:
            LOG.exception(e)
            return {'error': e.message}, 400


class WorkflowDetailView(Resource):
    @logged_response(logger=LOG)
    @sends_404
    def get(self, workflow_id):
        workflow_as_dict = g.backend.get_workflow(workflow_id)
        return _prepare_workflow_data(workflow_id, workflow_as_dict), 200

    @logged_response(logger=LOG)
    @sends_404
    def patch(self, workflow_id):
        update_data = request.get_json()
        forbidden_fields = set(update_data.keys()) - set(['is_canceled'])
        if forbidden_fields:
            msg = 'Cannot patch workflow fields: %s' % str(forbidden_fields)
            return msg, 409
        elif ('is_canceled' in update_data and update_data['is_canceled']):
            g.backend.cancel_workflow(workflow_id)

            workflow_as_dict = g.backend.get_workflow(workflow_id)
            return _prepare_workflow_data(workflow_id, workflow_as_dict), 200


class ExecutionDetailView(Resource):
    @logged_response(logger=LOG)
    @sends_404
    def get(self, execution_id):
        execution_data = g.backend.get_execution(execution_id)
        return execution_data, 200

    @logged_response(logger=LOG)
    @sends_404
    def patch(self, execution_id):
        update_data = request.get_json()
        try:
            execution_data = g.backend.update_execution(execution_id,
                    update_data=update_data)
            return execution_data, 200
        except exceptions.ImmutableUpdateError as e:
            LOG.exception('ImmutableUpdateError occured while updating '
                'execution (%d) with update_data=%s', execution_id, update_data)
            return e.message, 409


def _prepare_workflow_data(workflow_id, workflow_as_dict):
    result = workflow_as_dict.copy()  # do not modify the passed in arg
    result['reports'] = _generate_report_links(workflow_id)
    return result


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
    @logged_response(logger=LOG)
    @sends_404
    def put(self, task_id, callback_type):
        body_data = request.get_json()
        query_string_data = request.args
        g.backend.handle_task_callback(task_id, callback_type, body_data,
                query_string_data)
        return ''


class MethodCallback(Resource):
    @logged_response(logger=LOG)
    @sends_404
    def put(self, method_id, callback_type):
        body_data = request.get_json()
        query_string_data = request.args
        g.backend.handle_method_callback(method_id, callback_type,
                body_data, query_string_data)
        return ''


class ReportDetailView(Resource):
    @logged_response(logger=LOG)
    @sends_404
    def get(self, report_type):
        generator = reports.get_report_generator(report_type)
        return generator(**request.args), 200
