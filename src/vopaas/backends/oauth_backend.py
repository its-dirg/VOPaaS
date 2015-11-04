from satosa.backends.oauth import OAuthBackend
from vopaas.backends.backend_base import VOPaaSBackendModule, get_metadata_desc_for_oidc_backend

__author__ = 'mathiashedstrom'


class VOPaaSOAuthBackend(OAuthBackend, VOPaaSBackendModule):
    def __init__(self, auth_callback_func, internal_attributes, config, type):
        self.oidc_backend_config = config
        super(VOPaaSOAuthBackend, self).__init__(auth_callback_func, internal_attributes, config, type)

    def get_metadata_desc(self):
        return get_metadata_desc_for_oidc_backend(self.oidc_backend_config)
