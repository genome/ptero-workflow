from ..base import BaseAPITest
from .test_roundtrip_success import RoundTripSuccess
import os
import abc
import pwd
from pprint import pformat


class WebhookTest(RoundTripSuccess):
    __metaclass__ = abc.ABCMeta

    def setUp(self):
        self.webhook_server = self.create_webhook_server(
                self.webhook_server_responses)
        super(WebhookTest, self).setUp()

    @abc.abstractproperty
    def webhook_server_responses(self):
        pass

    @abc.abstractmethod
    def evaluate_webhook_data(self, webhook_data):
        pass

    @property
    def user(self):
        return pwd.getpwuid(os.getuid())[0]

    @property
    def working_directory(self):
        return os.environ['PTERO_WORKFLOW_TEST_SCRIPTS_DIR']

    def test_webhooks_data(self):
        webhook_data = self.webhook_server.stop()
        self.evaluate_webhook_data(webhook_data)


class NestedWorkflowWithWebhooks(WebhookTest, BaseAPITest):
    webhook_server_responses = [200 for i in range(50)]

    def evaluate_webhook_data(self, webhook_data):
        print pformat(webhook_data)
        self.assertEqual(len(webhook_data), 25)

    @property
    def post_data(self):
        return {
                'webhooks': {
                    'scheduled': self.webhook_server.url,
                    'running': [self.webhook_server.url, self.webhook_server.url],
                    'succeeded': self.webhook_server.url,
                    'failed': self.webhook_server.url,
                    'errored': self.webhook_server.url,
                    'canceled': self.webhook_server.url,
                    'ended': self.webhook_server.url,
                    },
                'tasks': {
                    'Inner': {
                        'webhooks': {
                            'scheduled': self.webhook_server.url,
                            'running': [self.webhook_server.url, self.webhook_server.url],
                            'succeeded': self.webhook_server.url,
                            'failed': self.webhook_server.url,
                            'errored': self.webhook_server.url,
                            'canceled': self.webhook_server.url,
                            'ended': self.webhook_server.url,
                            },
                        'methods': [{
                            'name': 'some_workflow',
                            'parameters': {
                                'webhooks': {
                                    'scheduled': self.webhook_server.url,
                                    'running': [self.webhook_server.url, self.webhook_server.url],
                                    'succeeded': self.webhook_server.url,
                                    'failed': self.webhook_server.url,
                                    'errored': self.webhook_server.url,
                                    'canceled': self.webhook_server.url,
                                    'ended': self.webhook_server.url,
                                    },
                                'tasks': {
                                    'A': {
                                        'webhooks': {
                                            'scheduled': self.webhook_server.url,
                                            'running': [self.webhook_server.url, self.webhook_server.url],
                                            'succeeded': self.webhook_server.url,
                                            'failed': self.webhook_server.url,
                                            'errored': self.webhook_server.url,
                                            'canceled': self.webhook_server.url,
                                            'ended': self.webhook_server.url,
                                            },
                                        'methods': [
                                            {
                                                'name': 'execute',
                                                'service': 'shell-command',
                                                'parameters': {
                                                    'webhooks': {
                                                        'scheduled': self.webhook_server.url,
                                                        'running': [self.webhook_server.url, self.webhook_server.url],
                                                        'succeeded': self.webhook_server.url,
                                                        'failed': self.webhook_server.url,
                                                        'errored': self.webhook_server.url,
                                                        'canceled': self.webhook_server.url,
                                                        'ended': self.webhook_server.url,
                                                        },
                                                    'commandLine': ['./echo_command'],
                                                    'environment': dict(os.environ),
                                                    'user': self.user,
                                                    'workingDirectory': self.working_directory,
                                                    }
                                                }
                                            ]
                                        },
                                    },
                                'links': [
                                    {
                                        'source': 'A',
                                        'destination': 'output connector',
                                        'dataFlow': {
                                            'param': 'inner_output'
                                            }
                                        }, {
                                            'source': 'input connector',
                                            'destination': 'A',
                                            'dataFlow': {
                                                'inner_input': 'param'
                                                }
                                            },
                                        ],
                                },
                        'service': 'workflow',
                    }]
                },
            },

            'links': [
                    {
                        'source': 'Inner',
                        'destination': 'output connector',
                        'dataFlow': {
                            'inner_output': 'outer_output'
                            }
                        }, {
                            'source': 'input connector',
                            'destination': 'Inner',
                            'dataFlow': {
                                'outer_input': 'inner_input'
                                }
                            },
                        ],
            'inputs': {
                    'outer_input': 'kittens',
                    },
            }
