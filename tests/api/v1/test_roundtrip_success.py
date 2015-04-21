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
        del(get_response.DATA['status'])
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

class WorkflowWithConvergeOperation(RoundTripSuccess, BaseAPITest):
    post_data = {
        'tasks': {
            'Converge': {
                'methods': [
                    {
                        'name': 'converger',
                        'service': 'workflow-converge',
                        'parameters': {
                            'input_names': ['b', 'a'],
                            'output_name': 'c',
                        }
                    }
                ]
            },
        },
        'links': [
            {
                'source': 'Converge',
                'destination': 'output connector',
                'sourceProperty': 'c',
                'destinationProperty': 'result',
            }, {
                'source': 'input connector',
                'destination': 'Converge',
                'sourceProperty': 'in_a',
                'destinationProperty': 'a',
            }, {
                'source': 'input connector',
                'destination': 'Converge',
                'sourceProperty': 'in_b',
                'destinationProperty': 'b',
            },
        ],
        'inputs': {
            'in_a': 'kittens',
            'in_b': 'puppies',
        },
    }

class WorkflowWithBlockOperation(RoundTripSuccess, BaseAPITest):
    post_data = {
        'tasks': {
            'Block': {
                'methods': [
                    {
                        'name': 'blocker',
                        'service': 'workflow-block',
                        'parameters': {
                        }
                    }
                ]
            },
        },
        'links': [
            {
                'source': 'Block',
                'destination': 'output connector',
                'sourceProperty': 'result',
                'destinationProperty': 'result',
            }, {
                'source': 'input connector',
                'destination': 'Block',
                'sourceProperty': 'in_a',
                'destinationProperty': 'in_a',
            },
        ],
        'inputs': {
            'in_a': 'kittens',
        },
    }

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
                'source': 'A',
                'destination': 'output connector',
                'sourceProperty': 'result',
                'destinationProperty': 'out_a',
            }, {
                'source': 'input connector',
                'destination': 'A',
                'sourceProperty': 'in_a',
                'destinationProperty': 'param',
            },
        ],
        'inputs': {
            'in_a': 'kittens',
        },
    }


class NestedWorkflowWithWebhooks(RoundTripSuccess, BaseAPITest):
    post_data = {
        'webhooks': {
            'running': 'http://localhost/example/webhook/outer_dag',
            'errored': ['http://localhost/example/webhook/outer_dag', 'http://localhost/example/webhook/outer_dag/2']
        },
        'tasks': {
            'Inner': {
                'webhooks': {
                    'running': 'http://localhost/example/webhook/outer_task',
                    'errored': ['http://localhost/example/webhook/outer_task', 'http://localhost/example/webhook/outer_task/2']
                },
                'methods': [{
                    'name': 'some_workflow',
                    'parameters': {
                        'webhooks': {
                            'running': 'http://localhost/example/webhook/inner_dag',
                            'errored': ['http://localhost/example/webhook/inner_dag', 'http://localhost/example/webhook/inner_dag/2']
                        },
                        'tasks': {
                            'A': {
                                'webhooks': {
                                    'running': 'http://localhost/example/webhook/inner_task',
                                    'errored': ['http://localhost/example/webhook/inner_task', 'http://localhost/example/webhook/inner_task/2']
                                },
                                'methods': [
                                    {
                                        'name': 'execute',
                                        'service': 'shell-command',
                                        'parameters': {
                                            'commandLine': ['cat'],
                                            'user': 'testuser',
                                            'workingDirectory': '/test/working/directory',
                                            'webhooks': {
                                                'running': 'http://localhost/example/webhook/shell-command',
                                                'errored': ['http://localhost/example/webhook/shell-command', 'http://localhost/example/webhook/shell-command/2']
                                            },
                                        }
                                    }
                                ]
                            },
                        },
                        'links': [
                            {
                                'source': 'A',
                                'destination': 'output connector',
                                'sourceProperty': 'result',
                                'destinationProperty': 'inner_output',
                            }, {
                                'source': 'input connector',
                                'destination': 'A',
                                'sourceProperty': 'inner_input',
                                'destinationProperty': 'param',
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
                'sourceProperty': 'inner_output',
                'destinationProperty': 'outer_output',
            }, {
                'source': 'input connector',
                'destination': 'Inner',
                'sourceProperty': 'outer_input',
                'destinationProperty': 'inner_input',
            },
        ],
        'inputs': {
            'outer_input': 'kittens',
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
                                'source': 'A',
                                'destination': 'output connector',
                                'sourceProperty': 'result',
                                'destinationProperty': 'inner_output',
                            }, {
                                'source': 'input connector',
                                'destination': 'A',
                                'sourceProperty': 'inner_input',
                                'destinationProperty': 'param',
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
                'sourceProperty': 'inner_output',
                'destinationProperty': 'outer_output',
            }, {
                'source': 'input connector',
                'destination': 'Inner',
                'sourceProperty': 'outer_input',
                'destinationProperty': 'inner_input',
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
                'source': 'A',
                'destination': 'output connector',
                'sourceProperty': 'result',
                'destinationProperty': 'out_a',
            }, {
                'source': 'input connector',
                'destination': 'A',
                'sourceProperty': 'in_a',
                'destinationProperty': 'param',
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
                                'source': 'A',
                                'destination': 'output connector',
                                'sourceProperty': 'result',
                                'destinationProperty': 'inner_output',
                            }, {
                                'source': 'input connector',
                                'destination': 'A',
                                'sourceProperty': 'inner_input',
                                'destinationProperty': 'param',
                            },
                        ],
                    },
                    'service': 'workflow',
                }],
            },
        },

        'links': [
            {
                'source': 'Inner',
                'destination': 'output connector',
                'sourceProperty': 'inner_output',
                'destinationProperty': 'outer_output',
            }, {
                'source': 'input connector',
                'destination': 'Inner',
                'sourceProperty': 'outer_input',
                'destinationProperty': 'inner_input',
            },
        ],
        'inputs': {
            'outer_input': 'kittens',
        },
    }
