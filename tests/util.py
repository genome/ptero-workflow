import os
import json

def environment():
    return json.dumps(environment_dict())

def environment_dict():
    return dict(os.environ)

def user():
    return os.environ.get('USER')

def working_directory():
    return os.environ['PTERO_WORKFLOW_TEST_SCRIPTS_DIR']

def lsf_url():
    return 'http://%s:%d/v1' % (
            os.environ['PTERO_LSF_HOST'],
            int(os.environ['PTERO_LSF_PORT']),
            )


def shell_command_url():
    return 'http://%s:%d/v1' % (
            os.environ['PTERO_SHELL_COMMAND_HOST'],
            int(os.environ['PTERO_SHELL_COMMAND_PORT']),
            )
