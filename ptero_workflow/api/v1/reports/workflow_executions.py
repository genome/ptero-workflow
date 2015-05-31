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
        format_str = '%Y-%m-%d %H:%M:%S.%f'
        url_query_string_args['since'] = timestamp.strftime(format_str)
    else:
        url_query_string_args['since'] = since

    url = '%s?%s' % (base_url, urllib.urlencode(url_query_string_args))

    return {
            'updateUrl': url,
            'executions': executions,
    }
