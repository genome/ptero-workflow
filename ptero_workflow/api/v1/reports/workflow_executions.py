from flask import g, url_for
import urllib
import logging

LOG = logging.getLogger(__name__)

def report(workflow_id, since=None):
    executions, timestamp = g.backend.get_workflow_executions(
            workflow_id=workflow_id, since=since)

    base_url = url_for('report', report_type='workflow-executions', _external=True)

    url_query_string_args = {'workflow_id': workflow_id}
    if timestamp is not None:
        url_query_string_args['since'] = timestamp
    url = '%s?%s' % (base_url, urllib.urlencode(url_query_string_args))

    return {
            'update_url': url,
            'executions': executions,
    }
