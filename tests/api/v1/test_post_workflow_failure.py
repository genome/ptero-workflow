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


class InputConnectorIsInvalidOperationName(PostWorkflowFailure, BaseAPITest):
    post_data = {
        'operations': {
            'input connector': {
                'methods': [
                    {
                        'name': 'execute',
                        'command_line': ['cat']
                    }
                ]
            },
            'A': {
                'methods': [
                    {
                        'name': 'execute',
                        'command_line': ['cat']
                    }
                ]
            },
        },
        'edges': [
            {
                'source': 'input connector',
                'destination': 'A',
                'source_property': 'in_a',
                'destination_property': 'param',
            }, {
                'source': 'A',
                'destination': 'output connector',
                'source_property': 'result',
                'destination_property': 'out_a',
            },
        ],
        'inputs': {
            'in_a': 'kittens',
        },
        'environment': {},
    }


class OutputConnectorIsInvalidOperationName(PostWorkflowFailure, BaseAPITest):
    post_data = {
        'operations': {
            'A': {
                'methods': [
                    {
                        'name': 'execute',
                        'command_line': ['cat']
                    }
                ]
            },
            'output connector': {
                'methods': [
                    {
                        'name': 'execute',
                        'command_line': ['cat']
                    }
                ]
            },
        },
        'edges': [
            {
                'source': 'input connector',
                'destination': 'A',
                'source_property': 'in_a',
                'destination_property': 'param',
            }, {
                'source': 'A',
                'destination': 'output connector',
                'source_property': 'result',
                'destination_property': 'out_a',
            },
        ],
        'inputs': {
            'in_a': 'kittens',
        },
        'environment': {},
    }

class NestedInputConnectorIsInvalidOperationName(PostWorkflowFailure, BaseAPITest):
    post_data = {
        'operations': {
            'Inner': {
                'operations': {
                    'A': {
                        'methods': [
                            {
                                'name': 'execute',
                                'command_line': ['cat']
                            }
                        ]
                    },
                    'input connector': {
                        'methods': [
                            {
                                'name': 'execute',
                                'command_line': ['cat']
                            }
                        ]
                    },
                },
                'edges': [
                    {
                        'source': 'input connector',
                        'destination': 'A',
                        'source_property': 'inner_input',
                        'destination_property': 'param',
                    }, {
                        'source': 'A',
                        'destination': 'output connector',
                        'source_property': 'result',
                        'destination_property': 'inner_output',
                    },
                ],
            },
        },

        'edges': [
            {
                'source': 'input connector',
                'destination': 'Inner',
                'source_property': 'outer_input',
                'destination_property': 'inner_input',
            }, {
                'source': 'Inner',
                'destination': 'output connector',
                'source_property': 'inner_output',
                'destination_property': 'outer_output',
            },
        ],
        'inputs': {
            'outer_input': 'kittens',
        },
        'environment': {},
    }

class NestedOutputConnectorIsInvalidOperationName(PostWorkflowFailure, BaseAPITest):
    post_data = {
        'operations': {
            'Inner': {
                'operations': {
                    'A': {
                        'methods': [
                            {
                                'name': 'execute',
                                'command_line': ['cat']
                            }
                        ]
                    },
                    'output connector': {
                        'methods': [
                            {
                                'name': 'execute',
                                'command_line': ['cat']
                            }
                        ]
                    },
                },
                'edges': [
                    {
                        'source': 'input connector',
                        'destination': 'A',
                        'source_property': 'inner_input',
                        'destination_property': 'param',
                    }, {
                        'source': 'A',
                        'destination': 'output connector',
                        'source_property': 'result',
                        'destination_property': 'inner_output',
                    },
                ],
            },
        },

        'edges': [
            {
                'source': 'input connector',
                'destination': 'Inner',
                'source_property': 'outer_input',
                'destination_property': 'inner_input',
            }, {
                'source': 'Inner',
                'destination': 'output connector',
                'source_property': 'inner_output',
                'destination_property': 'outer_output',
            },
        ],
        'inputs': {
            'outer_input': 'kittens',
        },
        'environment': {},
    }
