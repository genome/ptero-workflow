This test runs a command that fails to set a required output.  The method
should end up in the 'errored' state with a message in the execution data
explaining the error.  This will cause the task to end up in the 'failed'
state.  The workflow should end up 'failed' as well.
