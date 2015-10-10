import celery


__all__ = ['SubmitNet']


class SubmitNet(celery.Task):
    ignore_result = True

    def run(self, workflow_name):
        backend = celery.current_app.factory.create_backend()
        backend.submit_net(workflow_name)
        backend.cleanup()
