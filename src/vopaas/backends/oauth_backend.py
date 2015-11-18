"""
Base module for all oauth backends for VOPaaS
"""
from satosa.backends.oauth import FacebookBackend
from vopaas.backends.backend_base import VOPaaSBackendModule, get_metadata_desc_for_oidc_backend

__author__ = 'mathiashedstrom'


class VOPaaSOFacebookBackend(FacebookBackend, VOPaaSBackendModule):
    def __init__(self, auth_callback_func, internal_attributes, config):
        """
        :param auth_callback_func: Callback should be called by the module after the authorization in the
        backend is done.
        :param internal_attributes: Mapping dictionary between SATOSA internal attribute names and
        the names returned by underlying IdP's/OP's as well as what attributes the calling SP's and
        RP's expects namevice.
        :param config: Configuration parameters for the module.

        :type auth_callback_func:
        (satosa.context.Context, satosa.internal_data.InternalResponse) -> satosa.response.Response
        :type internal_attributes: dict[string, dict[str, str | list[str]]]
        :type config: dict[str, dict[str, str] | list[str]]
        """
        self.oauth_backend_config = config
        super(VOPaaSOFacebookBackend, self).__init__(auth_callback_func, internal_attributes, config)

    def get_metadata_desc(self):
        """
        See super class vopaas.backends.backend_base.VOPaaSBackendModule#get_metadata_desc
        :rtype: vopaas.metadata_creation.description.MetadataDescription
        """
        return get_metadata_desc_for_oidc_backend(self.oauth_backend_config,
                                                  self.oauth_backend_config["server_info"]["authorization_endpoint"])
