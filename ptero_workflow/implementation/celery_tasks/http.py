import celery
import logging
import requests
import simplejson


__all__ = ['HTTP']


LOG = logging.getLogger(__name__)


class HTTP(celery.Task):
    ignore_result = True

    def run(self, method, url, **kwargs):
        response = requests.request(method, url, data=self.body(kwargs),
                headers={'Content-Type': 'application/json'})

        if response.status_code >= 500:
            LOG.info('HTTP %s failed for url %s.  Scheduling retry.',
                    method, url)
            raise celery.exceptions.Retry('status_code == %s'
                    % response.status_code)

    def body(self, kwargs):
        return simplejson.dumps(kwargs)
