from ..base import BaseAPITest


class TestServerInfoEndpoint(BaseAPITest):
    def test_endpoint(self):
        url = 'http://%s:%s/v1/server-info' % (self.api_host, self.api_port)
        get_response = self.get(url)

        self.assertEqual(200, get_response.status_code)
