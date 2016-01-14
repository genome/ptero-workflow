from flask.ext.restful import Api
from . import views
from ptero_workflow.urls import ENDPOINT_INFO


__all__ = ['api']

api = Api(default_mediatype='application/json')

RESOURCES = {
        'workflow-list': views.WorkflowListView,
        'workflow-detail': views.WorkflowDetailView,
        'execution-detail': views.ExecutionDetailView,
        'task-callback': views.TaskCallback,
        'method-callback': views.MethodCallback,
        'report': views.ReportDetailView,
        'server-info': views.ServerInfo,
}

for endpoint_name, resource in RESOURCES.items():
    info = ENDPOINT_INFO[endpoint_name]
    api.add_resource(resource, info['url'], endpoint=endpoint_name)
