from ..base import BaseAPITest
import logging
from pprint import pformat

LOG = logging.getLogger(__name__)


class TestCancelWorkflow(BaseAPITest):
    @property
    def post_data(self):
        return {
                'tasks': {
                    'A': {
                        'methods': [
                            {
                                'name': 'execute',
                                'service': 'shell-command',
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
                            'in_a': 'param'
                            }
                        },
                    {
                        'source': 'A',
                        'destination': 'output connector',
                        'dataFlow': {
                            'result': 'out_a'
                            }
                        },
                    ],
                'inputs': {
                    'in_a': 'kittens',
                    },
                }


    def test_can_cancel(self):
        post_response = self.post(self.post_url, self.post_data)

        self.assertEqual(201, post_response.status_code)

        workflow_url = post_response.headers['Location']
        self.patch(workflow_url, data={'is_canceled':True})

        details_url = post_response.json()['reports']['workflow-details']
        details_response = self.get(details_url)
        self.assertEqual(200, details_response.status_code)
        LOG.warning(pformat(details_response.json()))

        status_url = post_response.json()['reports']['workflow-status']
        status_response = self.get(status_url)
        self.assertEqual(200, status_response.status_code)
        self.assertEqual(status_response.json()['status'], 'canceled')
