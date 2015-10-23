import os
from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from satosa.plugin_base.endpoint import FrontendModulePlugin
from saml2.entity_category.edugain import COC
from saml2.entity_category.swamid import RESEARCH_AND_EDUCATION, HEI, \
    SFS_1993_1153, NREN, EU
from saml2.saml import NAME_FORMAT_URI
from saml2.saml import NAMEID_FORMAT_TRANSIENT
from saml2.saml import NAMEID_FORMAT_PERSISTENT
from vopaas.frontends.saml2_frontend import VOPaaSSamlFrontend

__author__ = 'mathiashedstrom'


def full_path(local_file):
    basedir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(basedir, local_file)


xmlsec_path = '/usr/local/bin/xmlsec1'

MODULE = VOPaaSSamlFrontend
RECEIVER = "VOPaaSSaml2Frontend"
ENDPOINTS = {"single_sign_on_service": {BINDING_HTTP_REDIRECT: "sso/redirect",
                                        BINDING_HTTP_POST: "sso/post"}}


class Saml2FrontendModulePlugin(FrontendModulePlugin):
    def __init__(self, base_url):
        idpConfig = {
            "entityid": "%s/%s/vopaas_proxy.xml" % (base_url, RECEIVER),
            "description": "A SAML2SAML proxy",
            "entity_category": [COC, RESEARCH_AND_EDUCATION, HEI, SFS_1993_1153, NREN,
                                EU],
            # "valid_for": 168,
            "service": {
                "idp": {
                    "name": "Proxy IdP",
                    "endpoints": {
                        "single_sign_on_service": [
                            # The endpoints will be added later when registering endpoints in the
                            # module.
                        ],
                    },
                    "policy": {
                        "default": {
                            "lifetime": {"minutes": 15},
                            "attribute_restrictions": None,  # means all I have
                            "name_form": NAME_FORMAT_URI,
                            "entity_categories": ["edugain"],
                            "fail_on_missing_requested": False
                        },
                    },
                    "subject_data": "./idp.subject",
                    "name_id_format": [NAMEID_FORMAT_TRANSIENT,
                                       NAMEID_FORMAT_PERSISTENT],
                    "want_authn_requests_signed": False
                },
            },
            "debug": 1,
            "key_file": full_path("../../pki/new_server.key"),
            "cert_file": full_path("../../pki/new_server.crt"),
            "metadata": {
                "local": ["/Users/mathiashedstrom/work/DIRG/pysaml2/example/sp-wsgi/sp.xml"],
            },
            # This database holds the map between a subjects local identifier and
            # the identifier returned to a SP
            "xmlsec_binary": xmlsec_path,
            "logger": {
                "rotating": {
                    "filename": "idp.log",
                    "maxBytes": 500000,
                    "backupCount": 5,
                },
                "loglevel": "debug",
            }
        }

        config = {"idp_config": idpConfig,
                  "endpoints": ENDPOINTS,
                  "base": base_url,
                  }

        super(Saml2FrontendModulePlugin, self).__init__(MODULE, RECEIVER, config)
