from ..base import BaseAPITest
import logging
from pprint import pformat
from tests import util

LOG = logging.getLogger(__name__)


class TestSavingServiceData(BaseAPITest):
    def setUp(self):
        super(TestSavingServiceData, self).setUp()
        self.ended_listener = self.create_webhook_server([200])

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
                                'serviceDataToSave': ['exitCode'],
                                'parameters': {
                                    'commandLine': ['echo', 'saving_service_data_test'],
                                    "user": util.user(),
                                    "workingDirectory": util.working_directory(),
                                    "environment": util.environment_dict(),
                                    },
                                'webhooks': {
                                    'ended': self.ended_listener.url,
                                    }
                                }
                            ]
                        },
                    },
                'links': [
                    {
                        'source': 'input connector',
                        'destination': 'A',
                        },
                    {
                        'source': 'A',
                        'destination': 'output connector',
                        },
                    ],
                'inputs': {
                    },
                }


    def test_found_saved_data(self):
        post_response = self.post(self.post_url, self.post_data)

        self.assertEqual(201, post_response.status_code)

        workflow_url = post_response.headers['Location']

        self.ended_listener.stop()

        details_url = post_response.json()['reports']['workflow-details']
        details_response = self.get(details_url)
        self.assertEqual(200, details_response.status_code)

        body_data = details_response.json()

        LOG.warning(pformat(body_data))

        self.assertEqual('0', body_data['tasks']['A']['methods'][0]['executions']['0']['data']['exitCode'])

        delete_response = self.delete(workflow_url)
        self.assertEqual(200, delete_response.status_code)
