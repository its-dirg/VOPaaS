#!/usr/bin/env python
# =============================================================================
# Script that creates a VOPaaS proxy metadata file from a SATOSAConfig file
# =============================================================================
import argparse
import copy
import logging
import os
import sys
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

from satosa.plugin_base.endpoint import BackendModulePlugin, FrontendModulePlugin
from satosa.plugin_loader import backend_filter, _load_plugins, _load_endpoint_modules, frontend_filter
from satosa.satosa_config import SATOSAConfig
from vopaas.frontends.saml2_frontend import VOPaaSSamlFrontend

LOGGER = logging.getLogger("")
handler = logging.StreamHandler()
logFormatter = logging.Formatter("[%(name)-12.12s] [%(levelname)-5.5s]  %(message)s")
handler.setFormatter(logFormatter)
LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)

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
    """
    Combines metadata str to one str

    :type metadata_files: list[str]
    :rtype: str

    :param metadata_files: All metadata that should be combined
    :return: A combined metadata str
    """
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
    """
    Creates metadata from the given idp config

    :type config_dict: dict[str, Any]
    :type option: vopaas.metadata_creation.make_vopaas_metadata.MetadataOption
    :rtype: str

    :param config_dict: Frontend IDP config
    :param option: metadata creation settings
    :return: A xml string
    """
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


def create_config_file(frontend_config, frontend_endpoints, url_base, metadata_desc, backend_name):
    """
    Returns a copy of the frontend_config updated with the given metadata_desc

    :type frontend_config: dict[str, Any]
    :type frontend_endpoints: dict[str, dict[str, str]]
    :type url_base: str
    :type metadata_desc: vopaas.metadata_creation.description.MetadataDescription
    :type backend_name: str
    :rtype: dict[str, Any]

    :param frontend_config: Frontend idp config
    :param frontend_endpoints: Frontend endpoints
    :param url_base: proxy base url
    :param metadata_desc: one metadata description of a backend
    :param backend_name: backend name
    :return: An updated frontend idp config
    """
    cnf = copy.deepcopy(frontend_config)
    metadata_desc = metadata_desc.to_dict()
    proxy_id = cnf["entityid"]
    entity_id = metadata_desc["entityid"]

    cnf = _join_dict(cnf, metadata_desc)

    # TODO Only supports the VOPaaSSaml2Frontend
    cnf = VOPaaSSamlFrontend._load_endpoints_to_config(cnf, frontend_endpoints, url_base, backend_name, entity_id)
    cnf = VOPaaSSamlFrontend._load_entity_id_to_config(proxy_id, entity_id, cnf)
    return cnf


def _join_dict(dict_a, dict_b):
    """
    Joins two dicts
    :type dict_a: dict[Any, Any]
    :type dict_b: dict[Any, Any]
    :param dict_a: base dict
    :param dict_b: overriding dict
    :return: A joined dict
    """
    for key, value in dict_b.items():
        if key not in dict_a:
            dict_a[key] = value
        elif not isinstance(value, dict):
            dict_a[key] = value
        else:
            dict_a[key] = _join_dict(dict_a[key], dict_b[key])
    return dict_a


def make_vopaas_metadata(option):
    """
    Creates metadata files from a VOPaaS proxy config
    :type option: vopaas.metadata_creation.make_vopaas_metadata.MetadataOption
    :param option: The creation settings
    """
    conf_mod = SATOSAConfig(option.config_file)

    frontend_plugins = _load_plugins(conf_mod.PLUGIN_PATH, conf_mod.FRONTEND_MODULES, frontend_filter,
                                     FrontendModulePlugin.__name__, conf_mod.BASE)
    backend_plugins = _load_plugins(conf_mod.PLUGIN_PATH, conf_mod.BACKEND_MODULES, backend_filter,
                                    BackendModulePlugin.__name__, conf_mod.BASE)
    backend_modules = _load_endpoint_modules(backend_plugins, None, conf_mod.INTERNAL_ATTRIBUTES)

    frontend_names = [p.name for p in frontend_plugins]
    backend_names = [p.name for p in backend_plugins]
    LOGGER.info("Loaded frontend plugins: {}".format(frontend_names))
    LOGGER.info("Loaded backend plugins: {}".format(backend_names))

    metadata = {}
    for frontend in frontend_plugins:
        metadata[frontend.name] = []
        frontend_config = frontend.config["idp_config"]
        frontend_endpoints = frontend.config["endpoints"]
        url_base = conf_mod.BASE

        for plugin in backend_plugins:
            provider = plugin.name
            LOGGER.info("Creating metadata for frontend '{}' and backend '{}'".format(frontend.name, provider))
            meta_desc = backend_modules[provider].get_metadata_desc()
            for desc in meta_desc:
                xml = _make_metadata(
                    create_config_file(frontend_config, frontend_endpoints, url_base, desc, provider),
                    option
                )
                metadata[frontend.name].append(
                    {"xml": xml, "plugin_name": plugin.name, "entity_id": desc.entity_id}
                )

    for frontend in metadata:
        front = 0
        for meta in metadata[frontend]:
            path = "{}/{}_{}.xml".format(args.output, meta["plugin_name"], meta["entity_id"])
            LOGGER.info("Writing metadata '{}".format(path))
            out_file = open(path, 'w')
            out_file.write(meta["xml"])
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
    """
    Class that holds teh settings for the metadata creation
    """
    def __init__(self, config_file, valid=None, cert=None, id=None, keyfile=None, name="", sign=None, xmlsec=None,
                 output=None):
        """
        :type config_file: str
        :type valid: str
        :type cert: str
        :type id: str
        :type keyfile: str
        :type name: str
        :type sign: bool
        :type xmlsec: str
        :type output: str

        :param config_file: Path to VOPaaS proxy config file
        :param valid: How long, in days, the metadata is valid from the time of creation
        :param cert: Path to cert file
        :param id: The ID of the entities descriptor
        :param keyfile: A file with a key to sign the metadata with
        :param name: entities name
        :param sign: sign the metadata
        :param xmlsec: xmlsec binaries to be used for the signing
        :param output: Where to write metadata files
        """
        self.config_file = config_file
        self.valid = int(valid) * 24 if valid else 0
        self.cert = cert
        self.id = id
        self.keyfile = keyfile
        self.name = name
        self.sign = sign
        self.xmlsec = xmlsec
        self.output = output

    def __str__(self):
        return str(self.__dict__)


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
    parser.add_argument('-o', dest='output', default=".", help="Where to write metadata files")
    parser.add_argument(dest="config")
    args = parser.parse_args()

    LOGGER.info("Generating metadata for proxy config: '{}'".format(args.config))
    option = MetadataOption(args.config, args.valid, args.cert, args.id, args.keyfile, args.name, args.sign, args.xmlsec,
                            args.output)
    LOGGER.info("Settings: {}".format(option))
    make_vopaas_metadata(option)
