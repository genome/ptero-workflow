from flask.ext.restful import Api
from . import views


__all__ = ['api']


api = Api(default_mediatype='application/json')

api.add_resource(views.WorkflowListView, '/workflows', endpoint='workflow-list')

api.add_resource(views.WorkflowDetailView,
    '/workflows/<int:workflow_id>', endpoint='workflow-detail')

api.add_resource(views.OperationEventCallback,
    '/callbacks/operations/<int:operation_id>/events/<string:event_type>',
    endpoint='event-callback')

api.add_resource(views.ReportDetailView, '/reports/<string:report_type>',
        endpoint='report')
