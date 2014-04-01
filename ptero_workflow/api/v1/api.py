from flask.ext.restful import Api
from . import views

__all__ = ['api']


api = Api(default_mediatype='application/json')

api.add_resource(views.WorkflowListView, '/workflows', endpoint='workflow-list')
