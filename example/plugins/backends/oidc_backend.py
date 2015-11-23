#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path

from satosa.backends.openid_connect import OpenIdBackend
from satosa.plugin_base.endpoint import BackendModulePlugin
from vopaas.backends.oidc_backend import VOPaaSOpenIdBackend

XMLSEC_PATH = '/usr/local/bin/xmlsec1'


def full_path(local_file):
    basedir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(basedir, local_file)


PROVIDER = "openid_connect"
MODULE = VOPaaSOpenIdBackend


class OpenidPlugin(BackendModulePlugin):
    def __init__(self, base_url):
        module_base = "%s/%s/" % (base_url, PROVIDER)
        config = {
            "authz_page": PROVIDER,
            "acr_values": ["PASSWORD"],
            "verify_ssl": False,
            "op_url": "https://localhost:8092",
            "state_encryption_key": "Qrn9IQ5hr9uUnIdNQe2e0KxsmR3CusyARs3RKLjp",
            "state_id": "OpenID_Qrn9R3Cus",
            "client": {
                "srv_discovery_url": "https://localhost:8092",
                "client_info": {
                    "application_type": "web",
                    "application_name": "SATOSA",
                    "contacts": ["ops@example.com"],
                    "redirect_uris": ["%sauthz_cb" % module_base],
                    "post_logout_redirect_uris": ["%slogout" % module_base],
                    "response_types": ["code"],
                    "subject_type": "pairwise"
                },
                "behaviour": {
                    "response_type": "code",
                    "scope": ["openid", "profile", "email", "address", "phone"],
                }
            },
            "op_info": {
                "contact_person": [
                    {
                        "contact_type": "technical",
                        "given_name": "Test",
                        "sur_name": "OP",
                        "email_address": ["technical@example.com", "support@example.com"],

                    }, {
                        "contact_type": "support",
                        "given_name": "Support",
                        "email_address": ["support@example.com"]
                    },
                ],
                "organization": {
                    "display_name": [("OP Identities", "en")],
                    "name": [("En test-OP", "se"), ("A test OP", "en")],
                    "url": [("http://www.example.com", "en"), ("http://www.example.se", "se")],
                },
                "ui_info": {
                    "display_name": [("OP - TEST", "en")],
                    "description": [("This is a test OP", "en")],
                    "logo": [
                        {
                            "url": "https://inacademia.org/static/logo.png",
                            "width": "120",
                            "height": "60",
                            "lang": "en"
                        }
                    ],
                },
            }
        }
        super(OpenidPlugin, self).__init__(MODULE, PROVIDER, config)
