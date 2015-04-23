from ..base import BaseAPITest
import abc


class QueryWorkflow(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def workflows(self):
        pass

    def setUp(self):
        super(QueryWorkflow, self).setUp()


    def test_query_produces_expected_results(self):
        for workflow in self.workflows:
            response = self.post(self.post_url, self.expected_data[workflow])
            self.assertEqual(201, response.status_code)

        for query in self.queries:
            response = self.get(self.get_url, **query['args'])
            self.assertEqual(query['expected_code'], response.status_code)

            if response.status_code == 200:
                self.assertTrue('reports' in response.DATA)

            for key, val in self.expected_data[query['expected_data']].items():
                self.assertEqual(val, response.DATA[key])


class QueryByName(QueryWorkflow, BaseAPITest):
    queries = [
        {
            'args': {'name': 'bunnies'},
            'expected_code': 200,
            'expected_data': 'bunnies',
        }, {
            'args': {'name': 'walrus'},
            'expected_code': 200,
            'expected_data': 'walrus',
        }, {
            'args': {'name': 'elephant'},
            'expected_code': 404,
            'expected_data': 'elephant',
        }
    ]

    workflows = [ 'bunnies', 'walrus' ]

    expected_data = {
        'bunnies': {
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
            'name': 'bunnies',
        },
        'walrus': {
            'tasks': { },
            'links': [
                {
                    'source': 'input connector',
                    'destination': 'output connector',
                    'sourceProperty': 'in_z',
                    'destinationProperty': 'out_z',
                },
            ],
            'inputs': {
                'in_z': 'sea lion',
            },
            'name': 'walrus',
        },
        'elephant': {
            'error': 'Workflow with name elephant was not found.'
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
