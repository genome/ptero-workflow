from ..base import BaseAPITest


class TestCallbackHandlers(BaseAPITest):
    def test_callback_on_nonexistent_method(self):
        bad_endpoint = '/v1/callbacks/methods/55021/callbacks/errored'
        bad_url = '%s%s' % (self.base_url, bad_endpoint)
        response = self.post(bad_url, {})
        self.assertEqual(404, response.status_code)
