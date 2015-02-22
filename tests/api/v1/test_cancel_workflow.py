from ..base import BaseAPITest


class TestCancelWorkflow(BaseAPITest):
    @property
    def post_data(self):
        return {
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
                        },
                    {
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


    def test_can_cancel(self):
        post_response = self.post(self.post_url, self.post_data)

        self.assertEqual(201, post_response.status_code)
        self.assertTrue(post_response.DATA.get('status') is None)

        workflow_url = post_response.headers['Location']
        self.patch(workflow_url, data={'is_canceled':True})

        get_response = self.get(workflow_url)
        self.assertEqual(200, get_response.status_code)
        self.assertEqual(get_response.DATA['status'], 'canceled')
