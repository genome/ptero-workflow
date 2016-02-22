from ..base import BaseAPITest
from os import environ
import abc

import base64
import uuid


def _generate_uuid():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes)[:-2]


def _generate_unique_name(prefix):
    return prefix + _generate_uuid()

bunnies = _generate_unique_name('bunnies')
walrus = _generate_unique_name('walrus')
elephant = _generate_unique_name('elephant')


no_such_entity_status_code = int(environ.get(
            'PTERO_NO_SUCH_ENTITY_STATUS_CODE', 404))


class QueryWorkflow(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def workflows(self):
        pass

    def setUp(self):
        super(QueryWorkflow, self).setUp()


    def test_query_produces_expected_results(self):
        workflow_urls = []
        for workflow in self.workflows:
            response = self.post(self.post_url, self.submission_data[workflow])
            self.assertEqual(201, response.status_code)
            workflow_urls.append(response.headers.get('Location'))

        for query in self.queries:
            response = self.get(self.get_url, **query['args'])
            self.assertEqual(query['expected_code'], response.status_code)

            if response.status_code == 200:
                self.assertTrue('reports' in response.DATA)

            for key, val in self.expected_data[query['expected_data']].items():
                self.assertEqual(val, response.DATA[key])

        for workflow_url in workflow_urls:
            delete_response = self.delete(workflow_url)
            self.assertEqual(200, delete_response.status_code)


class QueryByName(QueryWorkflow, BaseAPITest):
    queries = [
        {
            'args': {'name': bunnies},
            'expected_code': 200,
            'expected_data': 'bunnies',
        }, {
            'args': {'name': walrus},
            'expected_code': 200,
            'expected_data': 'walrus',
        }, {
            'args': {'name': elephant},
            'expected_code': no_such_entity_status_code,
            'expected_data': 'elephant',
        }
    ]

    workflows = [ 'bunnies', 'walrus' ]

    submission_data = {
        'bunnies': {
            'tasks': { },
            'links': [
                {
                    'source': 'input connector',
                    'destination': 'output connector',
                    'dataFlow': {
                        'in_a': 'out_a',
                    },
                },
            ],
            'inputs': {
                'in_a': 'kittens',
            },
            'name': bunnies,
        },
        'walrus': {
            'tasks': { },
            'links': [
                {
                    'source': 'input connector',
                    'destination': 'output connector',
                    'dataFlow': {
                        'in_z': 'out_z',
                    },
                },
            ],
            'inputs': {
                'in_z': 'sea lion',
            },
            'name': walrus,
        },
        'elephant': {
            'error': 'Workflow with name %s was not found.' % elephant
        }
    }

    expected_data = {
        'bunnies': {
            'name': bunnies,
        },
        'walrus': {
            'name': walrus,
        },
        'elephant': {
            'error': 'Workflow with name %s was not found.' % elephant
        }
    }


class InvalidQuery(QueryWorkflow, BaseAPITest):
    queries = [
        {
            'args': {'pizza': 'burger'},
            'expected_code': 400,
            'expected_data': 'error',
        }
    ]

    workflows = [ ]

    expected_data = {
        'error': {
            'error': 'Invalid query arguments: pizza'
        }
    }


class NullQuery(QueryWorkflow, BaseAPITest):
    queries = [
        {
            'args': { },
            'expected_code': 400,
            'expected_data': 'error',
        }
    ]

    workflows = [ ]

    expected_data = {
        'error': {
            'error': 'No query arguments provided'
        }
    }
