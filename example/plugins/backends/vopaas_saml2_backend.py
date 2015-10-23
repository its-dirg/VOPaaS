#!/usr/bin/env python
# -*- coding: utf-8 -*-
from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_HTTP_POST
from saml2.entity_category.edugain import COC
from saml2.entity_category.swamid import RESEARCH_AND_EDUCATION, HEI, \
    SFS_1993_1153, NREN, EU
from saml2.extension.idpdisc import BINDING_DISCO
import os.path

# try:
#     from saml2.sigver import get_xmlsec_binary
# except ImportError:
#     get_xmlsec_binary = None
from satosa.plugin_base.endpoint import BackendModulePlugin
from vopaas.backends.saml2_backend import VOPaaSSamlBackend

xmlsec_path = '/usr/local/bin/xmlsec1'


def full_path(local_file):
    basedir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(basedir, local_file)


PROVIDER = "VOPaaSSaml2Backend"
MODULE = VOPaaSSamlBackend


class Saml2BackendModulePlugin(BackendModulePlugin):
    def __init__(self, base_url):
        module_base = "%s/%s" % (base_url, PROVIDER)
        sp_config = {
            "entityid": "%s/vopaas_saml2_backend.xml" % module_base,
            "description": "A SAML2 SP MODULE",
            "entity_category": [COC, RESEARCH_AND_EDUCATION, HEI, SFS_1993_1153, NREN,
                                EU],
            # "valid_for": 168,
            "service": {
                "sp": {
                    "allow_unsolicited": True,
                    "endpoints": {
                        "assertion_consumer_service": [
                            ("%s/acs/post" % module_base, BINDING_HTTP_POST),
                            ("%s/acs/redirect" % module_base, BINDING_HTTP_REDIRECT)
                        ],
                        "discovery_response": [
                            ("%s/disco" % module_base, BINDING_DISCO)
                        ]
                    }
                }
            },
            "debug": 1,
            "key_file": full_path("pki/new_server.key"),
            "cert_file": full_path("pki/new_server.crt"),
            "metadata": {
                "local": ["/Users/mathiashedstrom/work/DIRG/pysaml2/example/idp2/idp.xml",
                          "/Users/mathiashedstrom/work/DIRG/pysaml2/example/idp2/idp2.xml"],
            },
            "organization": {
                "display_name": "Example Identities",
                "name": "Example Identiteter",
                "url": "http://www.example.com",
            },
            "contact_person": [
                {
                    "contact_type": "technical",
                    "given_name": "Technical",
                    "email_address": "technical@example.com"
                }, {
                    "contact_type": "support",
                    "given_name": "Support",
                    "email_address": "support@example.com"
                },
            ],

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

        config = {
            "config": sp_config,
            "encryption_key": "INJxz3Seglf3",
            "disco_srv": "http://localhost:8080/role/idp.ds",
            "publish_metadata": "%s/metadata" % module_base,
        }

        super(Saml2BackendModulePlugin, self).__init__(MODULE, PROVIDER, config)
