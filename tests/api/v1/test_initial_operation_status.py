from ..base import BaseAPITest


URL = '/v1/workflows'


class SimpleWorkflowPostInitialStatusTest(BaseAPITest):
    def setUp(self):
        super(SimpleWorkflowPostInitialStatusTest, self).setUp()
        self.post_data = {
            'operations': {
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
        self.response = self.post(URL, self.post_data)

    def test_should_return_201(self):
        self.assertEqual(201, self.response.status_code)

    def test_should_set_location_header(self):
        self.assertIsNotNone(self.response.headers.get('Location'))

    def test_get_should_return_post_data(self):
        get_response = self.get(self.response.headers.get('Location'))
        key_names = ['operations', 'links', 'inputs', 'environment']
        for key in key_names:
            self.assertItemsEqual(self.post_data[key], get_response.DATA[key])
