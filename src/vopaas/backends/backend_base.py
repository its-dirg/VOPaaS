from satosa.backends.base import BackendModule

__author__ = 'mathiashedstrom'


class VOPaaSBackendModule(BackendModule):
    def get_metadata_desc(self):
        raise NotImplementedError()
