import os


def lsf_url():
    if os.environ.get('PTERO_LSF_HOST') is not None:
        return 'http://%s:%d/v1' % (
            os.environ['PTERO_LSF_HOST'],
            int(os.environ['PTERO_LSF_PORT']),
            )
    else:
        return ''


def shell_command_url():
    return 'http://%s:%d/v1' % (
            os.environ['PTERO_SHELL_COMMAND_HOST'],
            int(os.environ['PTERO_SHELL_COMMAND_PORT']),
            )
