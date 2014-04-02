from . import backend

__all__ = ['Factory']


class Factory(object):
    def __init__(self):
        self._initialized = False

    def create_backend(self):
        self._initialize()
        return backend.Backend()

    def purge(self):
        self._initialize()

    def _initialize(self):
        # Lazy initialize to be pre-fork friendly.
        if not self._initialized:
            self._initialized = True
