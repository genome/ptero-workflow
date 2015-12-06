from ..base import BaseAPITest
from tests.util import shell_command_url
import requests
import json
import zlib


class TestGzippedWorkflow(BaseAPITest):
    @property
    def post_data(self):
        return {
                'tasks': {
                    'A': {
                        'methods': [
                            {
                                'name': 'execute',
                                'service': 'job',
                                'serviceUrl': shell_command_url(),
                                'parameters': {
                                    'commandLine': ['cat'],
                                    'user': 'testuser',
                                    'workingDirectory': '/test/working/directory'
                                    }
                                }
                            ]
                        },
                    },
                'links': [
                    {
                        'source': 'input connector',
                        'destination': 'A',
                        'dataFlow': {
                            'in_a': 'param',
                            },
                        },
                    {
                        'source': 'A',
                        'destination': 'output connector',
                        'dataFlow': {
                            'result': 'out_a',
                            },
                        },
                    ],
                'inputs': {
                    'in_a': 'kittens',
                    },
                }

    def post(self, url, data):
        json_data = json.dumps(data)
        data = zlib.compress(json_data)
        return _deserialize_response(requests.post(url,
            headers={
                'content-type': 'application/json',
                'Content-Encoding': 'gzip'
            },
            data=data))


    def test_can_cancel(self):
        post_response = self.post(self.post_url, self.post_data)
        self.assertEqual(201, post_response.status_code)

        # cancel the workflow, so it doesn't continue to consume
        # resources
        workflow_url = post_response.headers['Location']
        patch_response = self.patch(workflow_url, data={'is_canceled':True})

        self.assertEqual(200, patch_response.status_code)

        delete_response = self.delete(workflow_url)
        self.assertEqual(200, delete_response.status_code)


def _deserialize_response(response):
    response.DATA = response.json()
    return response
