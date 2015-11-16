#!/usr/bin/env python
import copy
import logging
from saml2.config import IdPConfig
from saml2.server import Server
from satosa import service
from satosa.frontends.saml2 import SamlFrontend
from urllib.parse import urlparse

LOGGER = logging.getLogger(__name__)


class VOPaaSSamlFrontend(SamlFrontend):
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

    @staticmethod
    def _load_entity_id_to_config(proxy_entity_id, selftarget_entity_id, config):
        config["entityid"] = "{}/{}".format(proxy_entity_id, selftarget_entity_id)
        return config

    def _get_target_entity_id(self, context):
        return context.path.lstrip("/").split('/')[1]

    def _load_idp_dynamic_endpoints(self, context):
        target_entity_id = self._get_target_entity_id(context)
        context.internal_data["vopaas.target_entity_id"] = target_entity_id
        idp_conf_file = self._load_endpoints_to_config(self.config, self.endpoints, self.base, context._target_backend,
                                                       target_entity_id)
        idp_config = IdPConfig().load(idp_conf_file, metadata_construction=False)
        return Server(config=idp_config)

    def _load_idp_dynamic_entity_id(self, config, state):
        request_state = self.load_state(state)
        # Change the idp entity id dynamically
        idp_config_file = copy.deepcopy(config)
        idp_config_file = self._load_entity_id_to_config(config["entityid"], request_state["proxy_idp_entityid"],
                                                         idp_config_file)
        idp_config = IdPConfig().load(idp_config_file, metadata_construction=False)
        return Server(config=idp_config)

    def handle_authn_request(self, context, binding_in):
        idp = self._load_idp_dynamic_endpoints(context)
        return self._handle_authn_request(context, binding_in, idp)

    def save_state(self, context, _dict, _request, idp):
        state = super(VOPaaSSamlFrontend, self).save_state(context, _dict, _request, idp)
        state["proxy_idp_entityid"] = self._get_target_entity_id(context)
        return state

    def handle_backend_error(self, exception):
        idp = self._load_idp_dynamic_entity_id(self.config, exception.state)
        return self._handle_backend_error(exception, idp)

    def handle_authn_response(self, context, internal_response):
        idp = self._load_idp_dynamic_entity_id(self.config, context.state)
        return self._handle_authn_response(context, internal_response, idp)

    def register_endpoints(self, providers):
        self._validate_providers(providers)

        url_map = []

        for endp_category in self.endpoints:
            for binding, endp in self.endpoints[endp_category].items():
                valid_providers = ""
                for provider in providers:
                    valid_providers = "{}|^{}".format(valid_providers, provider)
                valid_providers = valid_providers.lstrip("|")
                parsed_endp = urlparse(endp)
                url_map.append(("(%s)/[\s\S]+/%s$" % (valid_providers, parsed_endp.path),
                                (self.handle_authn_request, service.BINDING_MAP[binding])))
                url_map.append(("(%s)/[\s\S]+/%s/(.*)$" % (valid_providers, parsed_endp.path),
                                (self.handle_authn_request, service.BINDING_MAP[binding])))

        return url_map
