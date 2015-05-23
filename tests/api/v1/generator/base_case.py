import abc
import collections
import errno
import itertools
import jinja2
import json
import os
import requests
import signal
import json
import subprocess
import sys
import time
import urllib
import urlparse
import yaml
import logging
import difflib
import re


_POLLING_DELAY = 0.5
_TERMINATE_WAIT_TIME = 0.05
_MAX_WAIT_TIME = 300

_MAX_RETRIES = 10
_RETRY_DELAY = 1.0

LOG = logging.getLogger(__name__)


def validate_json(text):
    data = json.loads(text)

FILTERS = [
        re.compile('"id".*:'),
        re.compile('"timestamp".*:'),
        re.compile('"name".*:'),
]

def get_lines_to_compare(struct):
    json_str = json.dumps(struct, indent=4, sort_keys=True, default=str)
    lines = []
    for line in json_str.splitlines(1):
        skip = False
        for f in FILTERS:
            if f.search(line) is not None:
                skip = True
                break
        if not skip:
            lines.append(line)
    return lines


class TestCaseMixin(object):
    __metaclass__ = abc.ABCMeta

    maxDiff = None

    @property
    def api_port(self):
        return int(os.environ['PTERO_WORKFLOW_PORT'])

    @property
    def api_host(self):
        return os.environ['PTERO_WORKFLOW_HOST']

    @abc.abstractproperty
    def directory(self):
        pass

    @abc.abstractproperty
    def test_name(self):
        pass


    def test_got_expected_result(self):
        workflow_url, workflow_data = self._submit_workflow()

        status_report_url = workflow_data['reports']['workflow-status']
        workflow_status = self._wait_for_completion(status_report_url)

        if workflow_status == 'succeeded':
            outputs_report_url = workflow_data['reports']['workflow-outputs']
            self._verify_result(outputs_report_url)
        else:
            LOG.info("Workflow failed... Checking expected details")
            self.assertTrue(self._expected_details is not None)

        if self._expected_details is not None:
            details_url = workflow_data['reports']['workflow-details']
            self._verify_workflow_details(details_url)

        url = workflow_data['reports']['workflow-skeleton']
        self._regenerate_skeleton_data(url)
        if self._expected_skeleton is not None:
            self._verify_workflow_skeleton(url)

    def _regenerate_skeleton_data(self, url):
        if os.environ.get('PTERO_REGENERATE_TEST_DATA'):
            actual_result = self._get_actual_result(url)
            with open(self._expected_skeleton_path, 'w') as ofile:
                ofile.write(self._to_json(actual_result))

    def _submit_workflow(self):
        response = _retry(requests.post, self._submit_url, self._workflow_body,
                headers={'content-type': 'application/json'})
        self.assertEqual(201, response.status_code)
        return response.headers['Location'], response.json()

    def _wait_for_completion(self, status_url):
        max_loops = int(_MAX_WAIT_TIME/_POLLING_DELAY)
        for iteration in xrange(max_loops):
            workflow_status = self._workflow_status(status_url)
            if workflow_status in ['succeeded', 'failed']:
                LOG.info("Workflow completed... checking outputs")
                return workflow_status
            time.sleep(_POLLING_DELAY)
        LOG.warning("Workflow failed to complete... ")
        self.assertTrue(False)

    def _verify_result(self, outputs_url):
        actual_result = self._get_actual_result(outputs_url)
        expected_result = self._expected_result

        self.assertTrue(self.compare_as_json(expected_result, actual_result))

    def _verify_workflow_details(self, details_url):
        actual_result = self._get_actual_result(details_url)
        expected_result = self._expected_details

        for name, task in expected_result['tasks'].iteritems():
            self._compare_task_details(task, actual_result['tasks'][name])

    def _verify_workflow_skeleton(self, url):
        actual_result = self._get_actual_result(url)
        expected_result = self._expected_skeleton

        self.assertTrue(self.compare_as_json(expected_result, actual_result))

    def _to_json(self, data):
        return json.dumps( data, indent=4, sort_keys=True, default=str )

    def compare_as_json(self, expected, actual):
        is_ok = True
        expected_json = get_lines_to_compare(expected)
        actual_json = get_lines_to_compare(actual)
        for line in difflib.unified_diff(expected_json, actual_json,
                fromfile='Expected', tofile='Actual'):
            is_ok = False
            sys.stdout.write(line)
        return is_ok

    @property
    def _submit_url(self):
        return 'http://%s:%d/v1/workflows' % (self.api_host, self.api_port)

    @property
    def _workflow_body(self):
        with open(self._workflow_file_path) as f:
            template = jinja2.Template(f.read())
            body = template.render(**self._template_data)
            validate_json(body)
        return body

    @property
    def _template_data(self):
        return {
            'user': os.environ.get('USER'),
            'workingDirectory': os.environ['PTERO_WORKFLOW_TEST_SCRIPTS_DIR'],
            'environment': json.dumps(dict(os.environ)),
        }

    @property
    def _workflow_file_path(self):
        return os.path.join(self.directory, 'submit.json')

    @property
    def _expected_result(self):
        with open(self._expected_result_path) as f:
            return json.load(f)

    @property
    def _expected_result_path(self):
        return os.path.join(self.directory, 'result.json')

    def _workflow_status(self, url):
        data = self._get_workflow_data(url)
        return data.get('status')

    def _get_workflow_data(self, url):
        response = _retry(requests.get, url)
        return response.json()

    def _get_actual_result(self, outputs_url):
        response = _retry(requests.get, outputs_url)
        return response.json()


    @property
    def _logdir(self):
        return os.path.join(self._repository_root_path, 'logs', self.test_name)

    @property
    def _repository_root_path(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__),
                '..', '..', '..', '..'))

    @property
    def _expected_details_path(self):
        return os.path.join(self.directory, 'workflow_details.json')

    @property
    def _expected_skeleton_path(self):
        return os.path.join(self.directory, 'workflow_skeleton.json')

    def _load_or_none(self, path):
        try:
            with open(path) as f:
                return json.load(f)
        except IOError:
            return None

    @property
    def _expected_details(self):
        return self._load_or_none(self._expected_details_path)

    @property
    def _expected_skeleton(self):
        return self._load_or_none(self._expected_skeleton_path)

    def _compare_task_details(self, expected, actual):
        self._compare_executions(expected, actual)

        for expected_method, actual_method in itertools.izip(
                expected['methods'], actual['methods']):
            self._compare_method_details(expected_method, actual_method)

    def _compare_method_details(self, expected, actual):
        self._compare_executions(expected, actual)

        if expected['service'] == 'workflow':
            expected_parameters = expected['parameters']
            actual_parameters = actual['parameters']
            for name, task in expected_parameters['tasks'].iteritems():
                self._compare_task_details(task,
                        actual_parameters['tasks'][name])

    def _compare_executions(self, expected, actual):
        actual_executions = actual['executions']
        for color, execution in expected.get('executions', {}).iteritems():
            self.assertTrue(color in actual_executions)
            for field in execution:
                self.assertEqual(execution[field],
                        actual_executions[color][field])


def _retry(func, *args, **kwargs):
    for attempt in xrange(_MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except:
            time.sleep(_RETRY_DELAY)
    error_msg = "Failed (%s) with args (%s) and kwargs (%s) %d times" % (
            func.__name__, args, kwargs, _MAX_RETRIES)
    raise RuntimeError(error_msg)
