from ..base import BaseAPITest
import abc


class PostDuplicateWorkflowFailure(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def post_data(self):
        pass

    def setUp(self):
        super(PostDuplicateWorkflowFailure, self).setUp()


    def test_should_set_expected_error_message(self):
        initial_response = self.post(self.post_url, self.post_data)
        self.assertEqual(201, initial_response.status_code)
        duplicate_response = self.post(self.post_url, self.post_data)
        self.assertEqual(400, duplicate_response.status_code)
        self.assertEqual({'error': self.expected_error_message},
                duplicate_response.DATA)


class NameFailure(PostDuplicateWorkflowFailure, BaseAPITest):
    expected_error_message = "Workflow with name 'foxes' already exists"
    post_data = {
        'tasks': { },
        'links': [
            {
                'source': 'input connector',
                'destination': 'output connector',
                'sourceProperty': 'in_a',
                'destinationProperty': 'out_a',
            },
        ],
        'inputs': {
            'in_a': 'kittens',
        },
        'name': 'foxes',
    }
