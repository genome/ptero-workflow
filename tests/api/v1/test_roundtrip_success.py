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
        key_names = ['operations', 'links', 'inputs', 'environment']
        for key in key_names:
            self.assertItemsEqual(self.post_data[key], get_response.DATA[key])


class SingleOperationWorkflow(RoundTripSuccess, BaseAPITest):
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
        },
        'links': [
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


class NestedOperationWorkflow(RoundTripSuccess, BaseAPITest):
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
                },
                'links': [
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

        'links': [
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


class ParallelByOperationWorkflow(RoundTripSuccess, BaseAPITest):
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
        },
        'links': [
            {
                'source': 'input connector',
                'destination': 'A',
                'source_property': 'in_a',
                'destination_property': 'param',
                'parallel_by': True,
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


class ParallelByNestedOperationWorkflow(RoundTripSuccess, BaseAPITest):
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
                },
                'links': [
                    {
                        'source': 'input connector',
                        'destination': 'A',
                        'source_property': 'inner_input',
                        'destination_property': 'param',
                        'parallel_by': True,
                    }, {
                        'source': 'A',
                        'destination': 'output connector',
                        'source_property': 'result',
                        'destination_property': 'inner_output',
                    },
                ],
            },
        },

        'links': [
            {
                'source': 'input connector',
                'destination': 'Inner',
                'source_property': 'outer_input',
                'destination_property': 'inner_input',
                'parallel_by': True,
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
