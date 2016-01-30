from flask import g


def report(workflow_id):
    reports = g.backend.get_spawned_workflows(workflow_id)
    return {
           "spawnedWorkflows": reports
    }
