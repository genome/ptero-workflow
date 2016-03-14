from ..base import BaseAPITest
import logging
from tests import util

LOG = logging.getLogger(__name__)


class TestWorkflowWithBadJobParameters(BaseAPITest):
    def setUp(self):
        super(TestWorkflowWithBadJobParameters, self).setUp()
        self.errored_listener = self.create_webhook_server([200])

    @property
    def post_data(self):
        return {
                'tasks': {
                    'Bad Job Task': {
                        'methods': [
                            {
                                'name': 'Bad Job',
                                'service': 'job',
                                'serviceUrl': util.shell_command_url(),
                                'parameters': {
                                    # should be commandLine (capital L)
                                    'commandline': ['true'],
                                    "user": util.user(),
                                    "workingDirectory": util.working_directory(),
                                    "environment": util.environment_dict(),
                                    },
                                'webhooks': {
                                    'errored': self.errored_listener.url,
                                    }
                                }
                            ]
                        },
                    },
                'links': [
                    {
                        'source': 'input connector',
                        'destination': 'Bad Job Task',
                        },
                    {
                        'source': 'Bad Job Task',
                        'destination': 'output connector',
                        },
                    ],
                'inputs': {
                    },
                }


    def test_errored_state_is_reached(self):
        post_response = self.post(self.post_url, self.post_data)

        self.assertEqual(201, post_response.status_code)

        workflow_url = post_response.headers['Location']

        self.errored_listener.stop()

        delete_response = self.delete(workflow_url)
        self.assertEqual(200, delete_response.status_code)
