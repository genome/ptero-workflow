from ..base import BaseAPITest
import abc


URL = '/v1/workflows'


class PostWorkflowFailure(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def post_data(self):
        pass

    def setUp(self):
        super(PostWorkflowFailure, self).setUp()
        self.response = self.post(URL, self.post_data)

    def test_should_return_400(self):
        self.assertEqual(400, self.response.status_code)


class InputConnectorIsInvalidOperationName(PostWorkflowFailure, BaseAPITest):
    post_data = {
        'operations': {
            'input connector': {
                'type': 'dummy-operation',
            },
            'A': {
                'type': 'dummy-operation',
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


class OutputConnectorIsInvalidOperationName(PostWorkflowFailure, BaseAPITest):
    post_data = {
        'operations': {
            'A': {
                'type': 'dummy-operation',
            },
            'output connector': {
                'type': 'dummy-operation',
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
