from ..base import BaseAPITest
import abc
import difflib
import json
import sys


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
        del(get_response.DATA['reports'])
        self.assertTrue(self.compareDictAsJSON(expected=self.post_data,
            actual=get_response.DATA))

    def _to_json(self, data):
        return json.dumps( data, indent=4, sort_keys=True, default=str )

    def compareDictAsJSON(self, expected, actual):
        is_ok = 1
        expected_json = self._to_json(expected).splitlines(1)
        actual_json = self._to_json(actual).splitlines(1)
        for line in difflib.unified_diff(expected_json, actual_json,
                fromfile='Expected', tofile='Actual'):
            is_ok = 0
            sys.stdout.write(line)
        return is_ok

class SingleNodeWorkflow(RoundTripSuccess, BaseAPITest):
    post_data = {
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
                    'name': 'some_workflow',
                    'parameters': {
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
                    'service': 'workflow',
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
                    'name': 'some_workflow',
                    'parameters': {
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
                    'service': 'workflow',
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
