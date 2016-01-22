import os
import re

HOST = os.environ['PTERO_WORKFLOW_HOST']
PORT = int(os.environ['PTERO_WORKFLOW_PORT'])

ENDPOINT_INFO = {
        'workflow-list': {
            'url': '/workflows',
            'format': '/workflows',
        },
        'workflow-detail': {
            'url': '/workflows/<int:workflow_id>',
            'format': '/workflows/%(workflow_id)d',
            'parser': '/workflows/(?P<workflow_id>\d+)',
        },
        'execution-detail': {
            'url': '/executions/<int:execution_id>',
            'format': '/executions/%(execution_id)d',
            'parser': '/executions/(?P<execution_id>\d+)',
        },
        'task-callback': {
            'url': '/callbacks/tasks/<int:task_id>/callbacks/<string:callback_type>',
            'format': '/callbacks/tasks/%(task_id)d/callbacks/%(callback_type)s',
            'parser': '/callbacks/tasks/(?P<task_id>\d+)/callbacks/(P?<callback_type>\s+)',
        },
        'method-callback': {
            'url': '/callbacks/methods/<int:method_id>/callbacks/<string:callback_type>',
            'format': '/callbacks/methods/%(method_id)d/callbacks/%(callback_type)s',
            'parser': '/callbacks/methods/(?P<method_id>\d+)/callbacks/(?P<callback_type>\s+)',
        },
        'report': {
            'url': '/reports/<string:report_type>',
            'format': '/reports/%(report_type)s',
            'parser': '/reports/(?P<report_type>\s+)',
        },
        'server-info': {
            'url': '/server-info',
            'format': '/server-info',
        },
}

PETRI_HOST = os.environ['PTERO_PETRI_HOST']
PETRI_PORT = int(os.environ['PTERO_PETRI_PORT'])

PETRI_ENDPOINT_INFO = {
        'net-detail': {
            'format': '/nets/%(net_key)s',
        },
}


def url_parse(endpoint_name, url):
    route_regex = ENDPOINT_INFO[endpoint_name]['parser']
    regex = "http://%s:%s/v1%s" % (HOST, PORT, route_regex)
    match = re.match(regex, url)
    if match is not None:
        return match.groupdict()


def url_for(endpoint_name, **kwargs):
    endpoint_info = ENDPOINT_INFO[endpoint_name]
    route = endpoint_info['format'] % kwargs
    return "http://%s:%s/v1%s" % (HOST, PORT, route)


def petri_url_for(endpoint_name, **kwargs):
    endpoint_info = PETRI_ENDPOINT_INFO[endpoint_name]
    route = endpoint_info['format'] % kwargs
    return "http://%s:%s/v1%s" % (PETRI_HOST, PETRI_PORT, route)
