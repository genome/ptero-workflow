from ..base import BaseAPITest
import abc


class RoundTripSuccess(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def post_data(self):
        pass

    def setUp(self):
        super(RoundTripSuccess, self).setUp()
        self.response = self.post(self.post_url, self.post_data)

    def test_should_return_201(self):
        self.assertEqual(201, self.response.status_code)

    def test_should_set_location_header(self):
        self.assertIsNotNone(self.response.headers.get('Location'))

    def test_get_should_return_post_data(self):
        get_response = self.get(self.response.headers.get('Location'))
        key_names = ['tasks', 'links', 'inputs']
        for key in key_names:
            self.assertItemsEqual(self.post_data[key], get_response.DATA[key])


class SingleNodeWorkflow(RoundTripSuccess, BaseAPITest):
    post_data = {
        'tasks': {
            'A': {
                'methods': [
                    {
                        'name': 'execute',
                        'service': 'shell_command',
                        'parameters': {
                            'commandLine': ['cat']
                        }
                    }
                ]
            },
        },
        'links': [
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
    }


class NestedWorkflow(RoundTripSuccess, BaseAPITest):
    post_data = {
        'tasks': {
            'Inner': {
                'methods': [{
                    'tasks': {
                        'A': {
                            'methods': [
                                {
                                    'name': 'execute',
                                    'service': 'shell_command',
                                    'parameters': {
                                        'commandLine': ['cat']
                                    }
                                }
                            ]
                        },
                    },
                    'links': [
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
                }]
            },
        },

        'links': [
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
    }


class ParallelByTaskWorkflow(RoundTripSuccess, BaseAPITest):
    post_data = {
        'tasks': {
            'A': {
                'methods': [
                    {
                        'name': 'execute',
                        'service': 'shell_command',
                        'parameters': {
                            'commandLine': ['cat']
                        }
                    }
                ]
            },
        },
        'links': [
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
    }


class NestedParallelByTaskWorkflow(RoundTripSuccess, BaseAPITest):
    post_data = {
        'tasks': {
            'Inner': {
                'methods': [{
                    'tasks': {
                        'A': {
                            'methods': [
                                {
                                    'name': 'execute',
                                    'service': 'shell_command',
                                    'parameters': {
                                        'commandLine': ['cat']
                                    }
                                }
                            ]
                        },
                    },
                    'links': [
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
                }],
            },
        },

        'links': [
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
    }
