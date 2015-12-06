from ..base import BaseAPITest
import abc
import base64
import uuid


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

        url = initial_response.headers.get('Location')
        delete_response = self.delete(url)
        self.assertEqual(200, delete_response.status_code)


def _generate_uuid():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes)[:-2]

unique_name = _generate_uuid()


class NameFailure(PostDuplicateWorkflowFailure, BaseAPITest):
    expected_error_message = "Workflow with name '%s' already exists" % unique_name

    post_data = {
        'tasks': { },
        'links': [
            {
                'source': 'input connector',
                'destination': 'output connector',
                'dataFlow': {
                    'in_a': 'out_a'
                }
            },
        ],
        'inputs': {
            'in_a': 'kittens',
        },
        'name': unique_name,
    }
