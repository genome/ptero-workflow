from flask import g


def report(workflow_id):
    return g.backend.get_workflow_summary(workflow_id)
