import celery


__all__ = ['SubmitNet']


class SubmitNet(celery.Task):
    ignore_result = True

    def run(self, workflow_id):
        backend = celery.current_app.factory.create_backend()
        backend.submit_net(workflow_id)
        backend.cleanup()
