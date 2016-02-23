from ..base import BaseAPITest
from os import environ
from ptero_common.view_wrapper import NO_SUCH_ENTITY_STATUS_CODE


class TestCallbackHandlers(BaseAPITest):
    def test_callback_on_nonexistent_method(self):
        bad_endpoint = '/v1/callbacks/methods/55021/callbacks/errored'
        bad_url = '%s%s' % (self.base_url, bad_endpoint)
        response = self.post(bad_url, {})
        self.assertEqual(NO_SUCH_ENTITY_STATUS_CODE, response.status_code)

    def test_callback_on_nonexistent_task(self):
        bad_endpoint = '/v1/callbacks/tasks/55021/callbacks/errored'
        bad_url = '%s%s' % (self.base_url, bad_endpoint)
        response = self.post(bad_url, {})
        self.assertEqual(NO_SUCH_ENTITY_STATUS_CODE, response.status_code)
