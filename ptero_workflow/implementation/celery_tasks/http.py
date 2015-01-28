import celery
import logging
import requests
import json
from ptero_common.logging_configuration import logged_request

__all__ = ['HTTP']


LOG = logging.getLogger(__name__)


class HTTP(celery.Task):
    ignore_result = True

    def run(self, method, url, **kwargs):
        response = getattr(logged_request, method.lower())(url, data=self.body(kwargs),
                headers={'Content-Type': 'application/json'}, logger=LOG)

        if response.status_code >= 500:
            raise celery.exceptions.Retry('status_code == %s'
                    % response.status_code)

    def body(self, kwargs):
        return json.dumps(kwargs)
