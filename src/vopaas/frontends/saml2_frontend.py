#!/usr/bin/env python
import copy
import logging
from saml2.config import IdPConfig
from saml2.server import Server
from satosa.frontends.saml2 import SamlFrontend

LOGGER = logging.getLogger(__name__)


class VOPaaSSamlFrontend(SamlFrontend):
    def _get_target_entity_id(self, context):
        return context.path.lstrip("/").split('/')[1]

    @staticmethod
    def _load_endpoints_to_config(frontend_config, frontend_endpoints, url_base, provider, target_entity_id):
        idp_conf_file = copy.deepcopy(frontend_config)
        idp_endpoints = []
        for endp_category in frontend_endpoints.keys():
            for func, endpoint in frontend_endpoints[endp_category].items():
                endpoint = "{base}/{provider}/{target_id}/{endpoint}".format(
                    base=url_base, provider=provider,
                    target_id=target_entity_id, endpoint=endpoint)
                idp_endpoints.append((endpoint, func))
            idp_conf_file["service"]["idp"]["endpoints"][endp_category] = idp_endpoints
        return idp_conf_file

    def _load_idp_dynamic_endpoints(self, context):
        target_entity_id = self._get_target_entity_id(context)
        context.internal_data["vopaas.target_entity_id"] = target_entity_id

        # idp_conf_file = copy.deepcopy(config)
        # idp_endpoints = []
        # for endp_category in self.endpoints.keys():
        #     for func, endpoint in self.endpoints[endp_category].items():
        #         endpoint = "{base}/{provider}/{target_id}/{endpoint}".format(
        #             base=self.base, provider=context.target_backend,
        #             target_id=target_entity_id, endpoint=endpoint)
        #         idp_endpoints.append((endpoint, func))
        #     idp_conf_file["service"]["idp"]["endpoints"][endp_category] = idp_endpoints

        idp_conf_file = self._load_endpoints_to_config(self.config, self.endpoints, self.base, context.target_backend,
                                                       target_entity_id)
        idp_config = IdPConfig().load(idp_conf_file, metadata_construction=False)

        return Server(config=idp_config)

    def handle_authn_request(self, context, binding_in):
        idp = self._load_idp_dynamic_endpoints(context)
        return self._handle_authn_request(context, binding_in, idp)

    def save_state(self, context, _dict, _request):
        state = super(VOPaaSSamlFrontend, self).save_state(context, _dict, _request)
        state["proxy_idp_entityid"] = self._get_target_entity_id(context)

    def _load_idp_dynamic_entity_id(self, config, state):
        request_state = self.load_state(state)
        # Change the idp entity id dynamically
        idp_config_file = copy.deepcopy(config)
        idp_config_file["entityid"] = request_state["proxy_idp_entityid"]
        idp_config = IdPConfig().load(idp_config_file, metadata_construction=False)

        return Server(config=idp_config)

    def handle_authn_response(self, context, internal_response, state):
        idp = self._load_idp_dynamic_entity_id(self.config, state)
        return self._handle_authn_response(context, internal_response, state, idp)

    def register_endpoints(self, providers):
        self._validate_providers(providers)
        return self._register_endpoints(providers)
