from . import reports
from . import validators
from . import utils
from ...implementation import exceptions
from flask import g, request, url_for
from flask.ext.restful import Resource
from jsonschema import ValidationError
from ...implementation.exceptions import ValidationError as PteroValidationError
from functools import wraps
import uuid

from ptero_common import nicer_logging
from ptero_common.nicer_logging import logged_response
import urllib


LOG = nicer_logging.getLogger(__name__)


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
    def get(self):
        given_keys = set(request.args.keys())
        valid_keys = set(['name'])
        invalid_keys = given_keys - valid_keys

        if not given_keys:
            error = 'No query arguments provided'
            return { 'error': error }, 400

        if invalid_keys:
            error = 'Invalid query arguments: %s' % ', '.join(invalid_keys)
            return { 'error': error }, 400

        if 'name' in request.args:
            workflow_id, workflow_as_dict = g.backend.get_workflow_by_name(
                        request.args['name'])
            request.workflow_id = workflow_id
            return _prepare_workflow_data(workflow_id, workflow_as_dict), 200

    @logged_response(logger=LOG)
    @sends_404
    def post(self):
        if 'name' in request.json:
            name = request.json['name']
        else:
            name = str(uuid.uuid4())

        name_part = ' for workflow "%s"' % name

        LOG.info("Handling workflow POST from %s%s",
                request.access_route[0], name_part,
                extra={'workflowName':name})

        try:
            LOG.debug("Validating JSON body of request%s", name_part,
                extra={'workflowName':name})
            data = validators.get_workflow_post_data()
            data['name'] = name
        except ValidationError as e:
            LOG.exception("Exception occured while validating JSON "
                "body of workflow POST from %s%s", request.access_route[0],
                name_part, extra={'workflowName':name})
            LOG.info("Responding 400 to workflow POST %s",
                    name_part, extra={'workflowName':name})
            msg = "JSON schema validation error: %s" % e.message
            return {'error': msg}, 400

        try:
            if 'parentExecutionUrl' in data:
                parent_execution_id = get_execution_id_from_url(
                        data['parentExecutionUrl'])
                workflow_id, workflow_as_dict = g.backend.create_spawned_workflow(data,
                    parent_execution_id=parent_execution_id)
            else:
                workflow_id, workflow_as_dict = g.backend.create_workflow(data)
        except PteroValidationError as e:
            LOG.exception('Exception occured while validating '
                'specification of workflow "%s"', name,
                extra={'workflowName':name})
            LOG.info("Responding 400 to workflow POST %s",
                    name_part, extra={'workflowName':name})
            return {'error': e.message}, 400

        LOG.info("Responding 201 to workflow POST%s",
                name_part, extra={'workflowName':name})
        return _prepare_workflow_data(workflow_id, workflow_as_dict), 201, {
            'Location': url_for('workflow-detail', workflow_id=workflow_id,
                _external=True)
        }


def get_execution_id_from_url(url):
    (endpoint, params) = utils.split_url(url, method='GET')
    return params['execution_id']


class WorkflowDetailView(Resource):
    @logged_response(logger=LOG)
    @sends_404
    def get(self, workflow_id):
        request.workflow_id = workflow_id
        workflow_as_dict = g.backend.get_workflow(workflow_id)
        return _prepare_workflow_data(workflow_id, workflow_as_dict), 200

    @logged_response(logger=LOG)
    @sends_404
    def patch(self, workflow_id):
        request.workflow_id = workflow_id
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
        except exceptions.UpdateError as e:
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
    def post(self, task_id, callback_type):
        body_data = request.get_json()
        query_string_data = request.args
        g.backend.handle_task_callback(task_id, callback_type, body_data,
                query_string_data)
        return {"message": "Completed task callback"}, 200


class MethodCallback(Resource):
    @logged_response(logger=LOG)
    @sends_404
    def post(self, method_id, callback_type):
        body_data = request.get_json()
        query_string_data = request.args
        g.backend.handle_method_callback(method_id, callback_type,
                body_data, query_string_data)
        return {"message": "Completed method callback"}, 200


class ReportDetailView(Resource):
    @logged_response(logger=LOG)
    @sends_404
    def get(self, report_type):
        request.workflow_id = request.args['workflow_id']
        generator = reports.get_report_generator(report_type)
        return generator(**request.args.to_dict(flat=True)), 200
