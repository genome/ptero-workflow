from ptero_workflow.api import application
import requests
import json
import os
import unittest

__all__ = ['BaseAPITest']


class BaseAPITest(unittest.TestCase):
    def setUp(self):
        self.api_host = os.environ['PTERO_WORKFLOW_HOST']
        self.api_port = int(os.environ['PTERO_WORKFLOW_PORT'])

    @property
    def post_url(self):
        return 'http://%s:%s/v1/workflows' % (self.api_host, self.api_port)

    def get(self, url, **kwargs):
        return _deserialize_response(requests.get(url, params=kwargs))

    def patch(self, url, data):
        return _deserialize_response(requests.patch(url,
            headers={'content-type': 'application/json'},
            data=json.dumps(data)))

    def post(self, url, data):
        return _deserialize_response(requests.post(url,
            headers={'content-type': 'application/json'},
            data=json.dumps(data)))

    def put(self, url, data):
        return _deserialize_response(requests.put(url,
            headers={'content-type': 'application/json'},
            data=json.dumps(data)))


def _deserialize_response(response):
    response.DATA = response.json()
    return response
