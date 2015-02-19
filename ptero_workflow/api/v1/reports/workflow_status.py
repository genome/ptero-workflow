from flask import g


def report(workflow_id):
    return {'status': g.backend.get_workflow_status(workflow_id)}
