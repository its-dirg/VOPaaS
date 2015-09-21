from satosa.backends.base import BackendBase

__author__ = 'mathiashedstrom'


class VOPaaSBackendBase(BackendBase):
    def get_metadata_desc(self):
        raise NotImplementedError()
