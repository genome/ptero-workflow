import os
import psutil
import signal
import time


STARTUP_WAIT = int(os.environ.get('PTERO_WORKFLOW_TEST_STARTUP_WAIT', 15))
SERVICE_COMMAND = ['./devserver', '--num-workers', '2', '--logdir', 'var/log']


instance = None


def cleanup():
    instance.send_signal(signal.SIGINT)
    try:
        instance.wait(timeout=10)
    except psutil.TimeoutExpired:
        instance.send_signal(signal.SIGKILL)


def setUp():
    global instance

    if not os.environ.get('PTERO_WORKFLOW_TEST_SKIP_PROCFILE'):
        instance = psutil.Popen(SERVICE_COMMAND, shell=False)
        time.sleep(STARTUP_WAIT)
        if instance.poll() is not None:
            raise RuntimeError("honcho instance terminated prematurely")


def tearDown():
    if not os.environ.get('PTERO_WORKFLOW_TEST_SKIP_PROCFILE'):
        cleanup()
