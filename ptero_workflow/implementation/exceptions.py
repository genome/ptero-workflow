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


class MissingResultError(RuntimeError):
    pass


class ValidationError(Exception):
    pass


class NonUniqueLinkError(ValidationError):
    pass


class NonUniqueNameError(ValidationError):
    pass


class MissingInputsError(ValidationError):
    pass


class UnknownIntegrityError(ValidationError):
    pass


class DAGCycleError(ValidationError):
    pass


class IllegalTaskNameError(ValidationError):
    pass


class InvalidExecutionUrlError(ValidationError):
    pass


class DuplicatePetriNetError(Exception):
    pass


class DuplicateJobError(Exception):
    pass


class UrlParseError(Exception):
    pass
