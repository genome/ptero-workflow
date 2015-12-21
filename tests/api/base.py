import requests
import json
import os
import subprocess
import time
import unittest

__all__ = ['BaseAPITest']


class WebhookServer:
    def __init__(self, response_codes):
        self._response_codes = response_codes
        self._webserver = None

    def start(self):
        if self._webserver:
            raise RuntimeError('Cannot start multiple webservers in one test')
        command_line = ['python', self._path,
                        '--stop-after', str(self._timeout), '--response-codes']
        command_line.extend(map(str, self._response_codes))
        self._webserver = subprocess.Popen(
            command_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._wait()
        self._port = int(self._webserver.stderr.readline().rstrip())

    def stop(self):
        while self._webserver is not None:
            exit_code = self._webserver.poll()
            if exit_code is not None:
                if exit_code == 0:
                    stdout, stderr = self._webserver.communicate()
                    self._webserver = None
                    self._webhook_stdout = stdout
                    self._webhook_stderr = stderr

                    if stdout:
                        return map(json.loads, stdout.split('\n')[:-1])
                    else:
                        return []
                elif exit_code == -14:
                    raise RuntimeError("Webhook listener timed out after (%s) seconds" %
                            self._timeout)
                else:
                    raise RuntimeError("Webhook listener exited non-zero (%s)" %
                            exit_code)
            else:
                self._wait()

    def _wait(self):
        time.sleep(1)

    @property
    def url(self):
        return 'http://localhost:%d/' % self._port

    @property
    def _path(self):
        return os.path.join(os.path.dirname(__file__), 'logging_webserver.py')

    @property
    def _timeout(self):
        return 25




class BaseAPITest(unittest.TestCase):
    def setUp(self):
        self.api_host = os.environ['PTERO_WORKFLOW_HOST']
        self.api_port = int(os.environ['PTERO_WORKFLOW_PORT'])

    def create_webhook_server(self, response_codes):
        server = WebhookServer(response_codes)
        server.start()
        return server

    @property
    def post_url(self):
        return 'http://%s:%s/v1/workflows' % (self.api_host, self.api_port)

    @property
    def get_url(self):
        return self.post_url

    def get(self, url, **kwargs):
        return _deserialize_response(requests.get(url, params=kwargs))

    def patch(self, url, data):
        return _deserialize_response(requests.patch(url,
            headers={'content-type': 'application/json'},
            data=json.dumps(data)))

    def post(self, url, data):
        return _deserialize_response(requests.post(url,
            headers={'content-type': 'application/json'},
            data=json.dumps(data)))

    def put(self, url, data):
        return _deserialize_response(requests.put(url,
            headers={'content-type': 'application/json'},
            data=json.dumps(data)))

    def delete(self, url, data=None):
        if data is not None:
            return _deserialize_response(requests.delete(url,
                headers={'content-type': 'application/json'},
                data=json.dumps(data)))
        else:
            return _deserialize_response(requests.delete(url))


def _deserialize_response(response):
    try:
        response.DATA = response.json()
    except ValueError:
        print "No JSON could be decoded from response to %s %s" % (
                response.request.method, response.request.url)
    return response
