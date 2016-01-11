from flask import g, url_for
import urllib
from ptero_common import nicer_logging
import os

LOG = nicer_logging.getLogger(__name__)
LIMIT = os.environ.get("PTERO_WORKFLOW_DEFAULT_STATUS_UPDATES_LIMIT", 500)


def report(workflow_id, since=None, limit=LIMIT):
    updates, timestamp, num_remaining = g.backend.get_limited_workflow_status_updates(
            workflow_id=workflow_id, since=since, limit=int(limit))

    base_url = url_for('.report', report_type='limited-workflow-status-updates',
            _external=True)

    url_query_string_args = {'workflow_id': workflow_id, 'limit':limit}

    if timestamp is not None:
        format_str = '%Y-%m-%d %H:%M:%S.%f'
        url_query_string_args['since'] = timestamp.strftime(format_str)
    else:
        url_query_string_args['since'] = since

    url = '%s?%s' % (base_url, urllib.urlencode(url_query_string_args))

    return {
            'updateUrl': url,
            'statusUpdates': updates,
            'numRemaining': num_remaining,
    }
