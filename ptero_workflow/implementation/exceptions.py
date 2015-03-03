class InvalidWorkflow(Exception):
    pass

class ImmutableUpdateError(Exception):
    pass

class OutputsAlreadySet(ImmutableUpdateError):
    pass

class InvalidStatusError(RuntimeError):
    pass
