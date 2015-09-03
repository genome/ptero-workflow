import os

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
