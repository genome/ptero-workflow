from flask import g


def report(workflow_id):
    workflow_data = g.backend.get_workflow(workflow_id)
    return {'outputs': workflow_data['outputs']}
