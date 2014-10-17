from flask import g


def report(workflow_id):
    return {'outputs': g.backend.get_workflow_outputs(workflow_id)}
