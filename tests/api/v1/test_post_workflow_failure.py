from ..base import BaseAPITest
from tests.util import shell_command_url
import abc


class PostWorkflowFailure(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def post_data(self):
        pass

    def setUp(self):
        super(PostWorkflowFailure, self).setUp()
        self.response = self.post(self.post_url, self.post_data)


    def test_should_set_expected_error_message(self):
        self.assertEqual(400, self.response.status_code)
        self.assertEqual({'error': self.expected_error_message},
                self.response.DATA)


class BorkIsInvalidWebhookName(PostWorkflowFailure, BaseAPITest):
    expected_error_message = "JSON schema validation error: Additional properties are not allowed (u'bork' was unexpected)"

    @property
    def post_data(self):
        return {
            'webhooks': {
                'scheduled': 'http://localhost/example/webhook',
                'running': ['http://localhost/example/webhook', 'http://localhost/example/webhook'],
                'failed': ['http://localhost/example/webhook'],
                'errored': ['http://localhost/example/webhook'],
                'succeeded': ['http://localhost/example/webhook'],
                'failed': ['http://localhost/example/webhook'],
                'canceled': ['http://localhost/example/webhook'],
                'ended': ['http://localhost/example/webhook'],
                'bork': ['http://localhost/example/webhook'],
            },
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
                        'in_a': 'param'
                        }
                }, {
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


class InputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    expected_error_message = '"input connector" is an illegal task name'

    @property
    def post_data(self):
        return {
            'webhooks': {
                'running': ['http://localhost/example/webhook', 'http://localhost/example/webhook'],
            },
            'tasks': {
                'input connector': {
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
                        'in_a': 'param'
                        }
                }, {
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


class OutputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    expected_error_message = '"output connector" is an illegal task name'

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
                    'output connector': {
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
                            'in_a': 'param'
                            }
                        }, {
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


class NestedInputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    expected_error_message = '"input connector" is an illegal task name'

    @property
    def post_data(self):
        return {
            'tasks': {
                'Inner': {
                    'methods': [
                        {
                            'name': 'some_workflow',
                            'parameters': {
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
                                    'input connector': {
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
                                            'inner_input': 'param'
                                            }
                                    }, {
                                        'source': 'A',
                                        'destination': 'output connector',
                                        'dataFlow': {
                                            'result': 'inner_output'
                                            }
                                    },
                                ],
                            },
                            'service': 'workflow'
                        },
                    ],
                },
            },

            'links': [
                {
                    'source': 'input connector',
                    'destination': 'Inner',
                    'dataFlow': {
                        'outer_input': 'inner_input'
                        }
                }, {
                    'source': 'Inner',
                    'destination': 'output connector',
                    'dataFlow': {
                        'inner_output': 'outer_output'
                        }
                },
            ],
            'inputs': {
                'outer_input': 'kittens',
            },
        }


class NestedOutputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    expected_error_message = '"output connector" is an illegal task name'

    @property
    def post_data(self):
        return {
                'tasks': {
                    'Inner': {
                        'methods': [
                            {
                                'name': 'some_workflow',
                                'parameters': {
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
                                        'output connector': {
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
                                                'inner_input': 'param'
                                                }
                                            }, {
                                                'source': 'A',
                                                'destination': 'output connector',
                                                'dataFlow': {
                                                    'result': 'inner_output'
                                                    }
                                                },
                                            ],
                                    },
                                'service': 'workflow',
                                },
                            ],
                },
            },

            'links': [
                    {
                        'source': 'input connector',
                        'destination': 'Inner',
                        'dataFlow': {
                            'outer_input': 'inner_input'
                            }
                        }, {
                            'source': 'Inner',
                            'destination': 'output connector',
                            'dataFlow': {
                                'inner_output': 'outer_output'
                                }
                            },
                        ],
            'inputs': {
                    'outer_input': 'kittens',
                    },
            }


class MissingInputs(PostWorkflowFailure, BaseAPITest):
    expected_error_message = 'Missing required inputs: in_a'

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
                            'in_a': 'param'
                            }
                        }, {
                            'source': 'A',
                            'destination': 'output connector',
                            'dataFlow': {
                                'result': 'out_a'
                                }
                            },
                        ],
                'inputs': {
                    'in_b': 'kittens',
                    },
                }
