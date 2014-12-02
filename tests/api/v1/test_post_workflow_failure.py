from ..base import BaseAPITest
import abc


class PostWorkflowFailure(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def post_data(self):
        pass

    def setUp(self):
        super(PostWorkflowFailure, self).setUp()
        self.response = self.post(self.post_url, self.post_data)


    def test_should_return_400(self):
        self.assertEqual(400, self.response.status_code)


class InputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    post_data = {
        'tasks': {
            'input connector': {
                'methods': [
                    {
                        'name': 'execute',
                        'service': 'ShellCommand',
                        'parameters': {
                            'commandLine': ['cat']
                        }
                    }
                ]
            },
            'A': {
                'methods': [
                    {
                        'name': 'execute',
                        'service': 'ShellCommand',
                        'parameters': {
                            'commandLine': ['cat']
                        }
                    }
                ]
            },
        },
        'edges': [
            {
                'source': 'input connector',
                'destination': 'A',
                'sourceProperty': 'in_a',
                'destinationProperty': 'param',
            }, {
                'source': 'A',
                'destination': 'output connector',
                'sourceProperty': 'result',
                'destinationProperty': 'out_a',
            },
        ],
        'inputs': {
            'in_a': 'kittens',
        },
        'environment': {},
    }


class OutputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    post_data = {
        'tasks': {
            'A': {
                'methods': [
                    {
                        'name': 'execute',
                        'service': 'ShellCommand',
                        'parameters': {
                            'commandLine': ['cat']
                        }
                    }
                ]
            },
            'output connector': {
                'methods': [
                    {
                        'name': 'execute',
                        'service': 'ShellCommand',
                        'parameters': {
                            'commandLine': ['cat']
                        }
                    }
                ]
            },
        },
        'edges': [
            {
                'source': 'input connector',
                'destination': 'A',
                'sourceProperty': 'in_a',
                'destinationProperty': 'param',
            }, {
                'source': 'A',
                'destination': 'output connector',
                'sourceProperty': 'result',
                'destinationProperty': 'out_a',
            },
        ],
        'inputs': {
            'in_a': 'kittens',
        },
        'environment': {},
    }

class NestedInputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    post_data = {
        'tasks': {
            'Inner': {
                'methods': [
                    {
                        'tasks': {
                            'A': {
                                'methods': [
                                    {
                                        'name': 'execute',
                                        'service': 'ShellCommand',
                                        'parameters': {
                                            'commandLine': ['cat']
                                        }
                                    }
                                ]
                            },
                            'input connector': {
                                'methods': [
                                    {
                                        'name': 'execute',
                                        'service': 'ShellCommand',
                                        'parameters': {
                                            'commandLine': ['cat']
                                        }
                                    }
                                ]
                            },
                        },
                        'edges': [
                            {
                                'source': 'input connector',
                                'destination': 'A',
                                'sourceProperty': 'inner_input',
                                'destinationProperty': 'param',
                            }, {
                                'source': 'A',
                                'destination': 'output connector',
                                'sourceProperty': 'result',
                                'destinationProperty': 'inner_output',
                            },
                        ],
                    },
                ],
            },
        },

        'edges': [
            {
                'source': 'input connector',
                'destination': 'Inner',
                'sourceProperty': 'outer_input',
                'destinationProperty': 'inner_input',
            }, {
                'source': 'Inner',
                'destination': 'output connector',
                'sourceProperty': 'inner_output',
                'destinationProperty': 'outer_output',
            },
        ],
        'inputs': {
            'outer_input': 'kittens',
        },
        'environment': {},
    }

class NestedOutputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    post_data = {
        'tasks': {
            'Inner': {
                'methods': [
                    {
                        'tasks': {
                            'A': {
                                'methods': [
                                    {
                                        'name': 'execute',
                                        'service': 'ShellCommand',
                                        'parameters': {
                                            'commandLine': ['cat']
                                        }
                                    }
                                ]
                            },
                            'output connector': {
                                'methods': [
                                    {
                                        'name': 'execute',
                                        'service': 'ShellCommand',
                                        'parameters': {
                                            'commandLine': ['cat']
                                        }
                                    }
                                ]
                            },
                        },
                        'edges': [
                            {
                                'source': 'input connector',
                                'destination': 'A',
                                'sourceProperty': 'inner_input',
                                'destinationProperty': 'param',
                            }, {
                                'source': 'A',
                                'destination': 'output connector',
                                'sourceProperty': 'result',
                                'destinationProperty': 'inner_output',
                            },
                        ],
                    },
                ],
            },
        },

        'edges': [
            {
                'source': 'input connector',
                'destination': 'Inner',
                'sourceProperty': 'outer_input',
                'destinationProperty': 'inner_input',
            }, {
                'source': 'Inner',
                'destination': 'output connector',
                'sourceProperty': 'inner_output',
                'destinationProperty': 'outer_output',
            },
        ],
        'inputs': {
            'outer_input': 'kittens',
        },
        'environment': {},
    }
