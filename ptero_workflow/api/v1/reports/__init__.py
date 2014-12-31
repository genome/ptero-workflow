from . import workflow_outputs

_REPORTS = {
    'workflow-outputs': workflow_outputs.report,
    }

def report_names():
    return _REPORTS.keys()

def get_report_generator(report_type):
    return _REPORTS[report_type]
