#!/usr/bin/env python
import argparse
import copy
import os
import sys
from saml2.attribute_converter import ac_factory
from saml2.mdstore import MetaDataFile, MetadataStore
from saml2.metadata import entity_descriptor, metadata_tostring_fix
from saml2.metadata import entities_descriptor
from saml2.metadata import sign_entity_descriptor

from saml2.sigver import security_context
from saml2.validate import valid_instance
from saml2.config import Config

from saml2 import saml
from saml2 import md
from saml2.extension import dri
from saml2.extension import idpdisc
from saml2.extension import mdattr
from saml2.extension import mdrpi
from saml2.extension import mdui
from saml2.extension import shibmd
from saml2.extension import ui
from saml2 import xmldsig
from saml2 import xmlenc

# =============================================================================
# Script that creates a VOPaaS proxy metadata file from a SATOSAConfig file
# =============================================================================
from satosa.plugin_loader import backend_filter, _load_plugins, _load_endpoint_modules, frontend_filter
from satosa.satosa_config import SATOSAConfig
from vopaas.frontends.saml2_frontend import VOPaaSSamlFrontend

NSPAIR = {"xs": "http://www.w3.org/2001/XMLSchema"}

ONTS = {
    saml.NAMESPACE: saml,
    mdui.NAMESPACE: mdui,
    mdattr.NAMESPACE: mdattr,
    mdrpi.NAMESPACE: mdrpi,
    dri.NAMESPACE: dri,
    ui.NAMESPACE: ui,
    idpdisc.NAMESPACE: idpdisc,
    md.NAMESPACE: md,
    xmldsig.NAMESPACE: xmldsig,
    xmlenc.NAMESPACE: xmlenc,
    shibmd.NAMESPACE: shibmd
}

def create_combined_metadata(metadata_files):
    mds = MetadataStore(ONTS.values(), None, None)
    key = 1
    for data in metadata_files:
        kwargs = {}
        metad = MetaDataFile(ONTS.values(), None, filename="no_file", **kwargs)
        assert metad.parse_and_check_signature(data)
        mds.metadata["data_{}".format(key)] = metad
        key += 1

    return mds.dumps()


def _make_metadata(config_dict, option):
    eds = []
    cnf = Config()
    cnf.load(copy.deepcopy(config_dict), metadata_construction=True)

    if option.valid:
        cnf.valid_for = option.valid
    eds.append(entity_descriptor(cnf))

    conf = Config()
    conf.key_file = option.keyfile
    conf.cert_file = option.cert
    conf.debug = 1
    conf.xmlsec_binary = option.xmlsec
    secc = security_context(conf)

    if option.id:
        desc, xmldoc = entities_descriptor(eds, option.valid, option.name, option.id,
                                           option.sign, secc)
        valid_instance(desc)
        print(desc.to_string(NSPAIR))
    else:
        for eid in eds:
            if option.sign:
                assert conf.key_file
                assert conf.cert_file
                eid, xmldoc = sign_entity_descriptor(eid, option.id, secc)
            else:
                xmldoc = None

            valid_instance(eid)
            xmldoc = metadata_tostring_fix(eid, NSPAIR, xmldoc).decode()
            return xmldoc


def create_config_file(frontend_config, frontend_endpoints, url_base, metadata_desc, name):
    cnf = copy.deepcopy(frontend_config)
    metadata_desc = metadata_desc.to_dict()
    proxy_id = cnf["entityid"]
    entity_id = metadata_desc["entityid"]

    cnf = _join_dict(cnf, metadata_desc)

    # TODO Only supports the VOPaaSSaml2Frontend
    cnf = VOPaaSSamlFrontend._load_endpoints_to_config(cnf, frontend_endpoints, url_base, name, entity_id)
    cnf = VOPaaSSamlFrontend._load_entity_id_to_config(proxy_id, entity_id, cnf)
    return cnf


def _join_dict(dict_a, dict_b):
    for key, value in dict_b.items():
        if key not in dict_a:
            dict_a[key] = value
        elif not isinstance(value, dict):
            dict_a[key] = value
        else:
            dict_a[key] = _join_dict(dict_a[key], dict_b[key])
    return dict_a


def make_vopaas_metadata(option):
    conf_mod = SATOSAConfig(option.config_file)

    frontend_plugins = _load_plugins(conf_mod.PLUGIN_PATH, conf_mod.FRONTEND_MODULES, frontend_filter, conf_mod.BASE)

    backend_plugins = _load_plugins(conf_mod.PLUGIN_PATH, conf_mod.BACKEND_MODULES, backend_filter, conf_mod.BASE)
    backend_modules = _load_endpoint_modules(backend_plugins, None)

    metadata = {}
    for frontend in frontend_plugins:
        metadata[frontend.name] = []
        frontend_config = frontend.config["idp_config"]
        frontend_endpoints = frontend.config["endpoints"]
        url_base = conf_mod.BASE

        for plugin in backend_plugins:
            provider = plugin.name
            meta_desc = backend_modules[provider].get_metadata_desc()
            for desc in meta_desc:
                metadata[frontend.name].append(
                    _make_metadata(
                        create_config_file(frontend_config, frontend_endpoints, url_base, desc, provider), option))

    for frontend in metadata:
        front = 0
        for meta in metadata[frontend]:
            out_file = open("{}/proxy_front{}_metadata.xml".format(args.output, front), 'w')
            out_file.write(meta)
            out_file.close()
            front += 1

        # combined_metadata = create_combined_metadata(metadata[frontend])
        # if option.output:
        #     out_file = open(option.output, 'w')
        #     out_file.write(combined_metadata)
        #     out_file.close()
        # else:
        #     print(combined_metadata)


class MetadataOption(object):
    def __init__(self, config_file, valid=None, cert=None, id=None, keyfile=None, name="", sign=None, xmlsec=None,
                 output=None):
        self.config_file = config_file
        self.valid = int(valid) * 24 if valid else 0
        self.cert = cert
        self.id = id
        self.keyfile = keyfile
        self.name = name
        self.sign = sign
        self.xmlsec = xmlsec
        self.output = output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', dest='valid',
                        help="How long, in days, the metadata is valid from the time of creation")
    parser.add_argument('-c', dest='cert', help='certificate')
    parser.add_argument('-i', dest='id',
                        help="The ID of the entities descriptor")
    parser.add_argument('-k', dest='keyfile',
                        help="A file with a key to sign the metadata with")
    parser.add_argument('-n', dest='name', default="")
    parser.add_argument('-s', dest='sign', action='store_true',
                        help="sign the metadata")
    parser.add_argument('-x', dest='xmlsec',
                        help="xmlsec binaries to be used for the signing")
    parser.add_argument('-o', dest='output', default=".")
    parser.add_argument(dest="config", nargs='+')
    args = parser.parse_args()

    for filespec in args.config:
        bas, fil = os.path.split(filespec)
        if bas != "":
            sys.path.insert(0, bas)
        option = MetadataOption(fil, args.valid, args.cert, args.id, args.keyfile, args.name, args.sign, args.xmlsec,
                                args.output)
        make_vopaas_metadata(option)
