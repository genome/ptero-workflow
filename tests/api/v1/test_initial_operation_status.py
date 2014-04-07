from ..base import BaseAPITest


URL = '/v1/workflows'


class SimpleWorkflowPostInitialStatusTest(BaseAPITest):
    def setUp(self):
        super(SimpleWorkflowPostInitialStatusTest, self).setUp()
        self.post_data = {
        }
        self.response = self.post(URL, self.post_data)

    def test_should_return_201(self):
        self.assertEqual(201, self.response.status_code)

    def test_should_set_location_header(self):
        self.assertIsNotNone(self.response.headers.get('Location'))
