from ..base import BaseAPITest
import logging
import os
from pprint import pformat
from tests import util

LOG = logging.getLogger(__name__)

NO_SUCH_ENTITY_STATUS_CODE = int(os.environ['PTERO_NO_SUCH_ENTITY_STATUS_CODE'])


class TestDeleteWorkflow(BaseAPITest):
    def setUp(self):
        super(TestDeleteWorkflow, self).setUp()
        self.running_listener = self.create_webhook_server([200])

    @property
    def post_data(self):
        return {
                'tasks': {
                    'A': {
                        'methods': [
                            {
                                'name': 'execute',
                                'service': 'job',
                                'serviceUrl': util.shell_command_url(),
                                'parameters': {
                                    'commandLine': ['sleep', '3600'],
                                    "user": util.user(),
                                    "workingDirectory": util.working_directory(),
                                    "environment": util.environment_dict(),
                                    },
                                'webhooks': {
                                    'running': self.running_listener.url,
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


    def test_can_delete(self):
        post_response = self.post(self.post_url, self.post_data)
        self.assertEqual(201, post_response.status_code)
        workflow_url = post_response.headers['Location']

        self.running_listener.stop()
        executions_url = post_response.json()['reports']['workflow-executions']
        job_url = self.get_job_url(executions_url)
        self.assert_status_code(job_url, 200)

        self.delete(workflow_url)
        self.assert_status_code(workflow_url, NO_SUCH_ENTITY_STATUS_CODE)
        self.assert_status_code(job_url, NO_SUCH_ENTITY_STATUS_CODE)

    def assert_status_code(self, job_url, status_code):
        response = self.get(job_url)
        self.assertEqual(status_code, response.status_code)

    def get_job_url(self, executions_url):
        executions_response = self.get(executions_url)
        execution_details = [self.get_execution_details(execution['detailsUrl'])
                for execution in executions_response.json()['executions']
                if 'detailsUrl' in execution]
        job_urls = [details['data']['jobUrl']
                for details in execution_details
                if ('data' in details) and ('jobUrl' in details['data'])]
        if len(job_urls) != 1:
            raise RuntimeError
        return job_urls[0]


    def get_execution_details(self, execution_details_url):
        response = self.get(execution_details_url)
        return response.json()
