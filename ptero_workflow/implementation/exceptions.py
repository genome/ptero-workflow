class InvalidWorkflow(Exception):
    pass

class UpdateError(Exception):
    pass

class ImmutableUpdateError(UpdateError):
    pass

class OutputsAlreadySet(ImmutableUpdateError):
    pass

class MissingOutputError(UpdateError):
    pass

class InvalidStatusError(RuntimeError):
    pass

class NoSuchEntityError(RuntimeError):
    pass

