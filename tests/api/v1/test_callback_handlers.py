from ..base import BaseAPITest
from os import environ


no_such_entity_status_code = int(environ.get(
        'PTERO_NO_SUCH_ENTITY_STATUS_CODE', 404))


class TestCallbackHandlers(BaseAPITest):
    def test_callback_on_nonexistent_method(self):
        bad_endpoint = '/v1/callbacks/methods/55021/callbacks/errored'
        bad_url = '%s%s' % (self.base_url, bad_endpoint)
        response = self.post(bad_url, {})
        self.assertEqual(no_such_entity_status_code, response.status_code)

    def test_callback_on_nonexistent_task(self):
        bad_endpoint = '/v1/callbacks/tasks/55021/callbacks/errored'
        bad_url = '%s%s' % (self.base_url, bad_endpoint)
        response = self.post(bad_url, {})
        self.assertEqual(no_such_entity_status_code, response.status_code)
