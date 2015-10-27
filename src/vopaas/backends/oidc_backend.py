from satosa.backends.openid_connect import OpenIdBackend
from vopaas.backends.backend_base import VOPaaSBackendModule, get_metadata_desc_for_oidc_backend

__author__ = 'mathiashedstrom'


class VOPaaSOpenIdBackend(OpenIdBackend, VOPaaSBackendModule):
    def __init__(self, auth_callback_func, config):
        self.oidc_backend_config = config
        super(VOPaaSOpenIdBackend, self).__init__(auth_callback_func, config)

    def get_metadata_desc(self):
        return get_metadata_desc_for_oidc_backend(self.oidc_backend_config)
