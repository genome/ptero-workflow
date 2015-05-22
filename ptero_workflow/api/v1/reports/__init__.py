from . import workflow_details
from . import workflow_outputs
from . import workflow_status
from . import workflow_skeleton

_REPORTS = {
    'workflow-details': workflow_details.report,
    'workflow-outputs': workflow_outputs.report,
    'workflow-status': workflow_status.report,
    'workflow-skeleton': workflow_skeleton.report,
    }

def report_names():
    return _REPORTS.keys()

def get_report_generator(report_type):
    return _REPORTS[report_type]
