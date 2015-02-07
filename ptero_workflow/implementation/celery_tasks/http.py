import celery
import logging
import requests
import json
from requests.exceptions import ConnectionError
from ptero_common.logging_configuration import logged_request

__all__ = ['HTTP']


LOG = logging.getLogger(__name__)


class HTTP(celery.Task):
    ignore_result = True

    def run(self, method, url, **kwargs):
        try:
            response = getattr(logged_request, method.lower())(
                url, data=self.body(kwargs),
                headers={'Content-Type': 'application/json'},
                timeout=10, logger=LOG)
        except ConnectionError as exc:
            LOG.info("A ConnectionError occured while attempting to send %s  %s, retrying in 60 seconds.", method.upper(), url)
            self.retry(exc=exc, countdown=60)

        if response.status_code >= 500:
            LOG.info("Got response (%s), retrying after 3 minutes.",
                    response.status_code)
            raise celery.exceptions.Retry('status_code == %s'
                    % response.status_code)

    def body(self, kwargs):
        return json.dumps(kwargs)
