#!/usr/bin/env python
import logging
from base64 import urlsafe_b64decode, urlsafe_b64encode
from saml2.extension.ui import NAMESPACE as UI_NAMESPACE
from satosa.backends.saml2 import SamlBackend
from vopaas.backends.backend_base import VOPaaSBackendModule

logger = logging.getLogger(__name__)


class VOPaaSSamlBackend(SamlBackend, VOPaaSBackendModule):
    def start_auth(self, context, request_info, state):
        entity_id = context.internal_data["vopaas.target_entity_id"]
        entity_id = urlsafe_b64decode(entity_id).decode("utf-8")
        return self.authn_request(context, entity_id, request_info, state)

    def get_metadata_desc(self):
        # TODO Only get IDPs
        metadata_desc = []
        for metadata_file in self.sp.metadata.metadata:
            desc = {}
            metadata_file = self.sp.metadata.metadata[metadata_file]
            entity_id = metadata_file.entity_descr.entity_id
            entity = metadata_file.entity
            desc["entityid"] = urlsafe_b64encode(entity_id.encode("utf-8")).decode("utf-8")

            # Add organization info
            try:
                organization = entity[entity_id]['organization']
                desc['organization'] = {}
                organization_params = [('display_name', 'organization_display_name'),
                                       ('name', 'organization_name'), ('url', 'organization_url')]
                for config_param, param in organization_params:
                    try:
                        value = []
                        for obj in organization[param]:
                            value.append((obj["text"], obj["lang"]))
                        desc['organization'][config_param] = value
                    except KeyError:
                        pass
            except:
                pass

            # Add contact person info
            try:
                contact_persons = entity[entity_id]['contact_person']
                desc['contact_person'] = []
                for cont_pers in contact_persons:
                    person = {}
                    try:
                        person['contact_type'] = cont_pers['contact_type']
                    except KeyError:
                        pass
                    try:
                        email_address = cont_pers['email_address']
                        person['email_address'] = []
                        for address in email_address:
                            person['email_address'].append(address['text'])
                    except KeyError:
                        pass
                    try:
                        person['given_name'] = cont_pers['given_name']['text']
                    except KeyError:
                        pass
                    try:
                        person['sur_name'] = cont_pers['sur_name']['text']
                    except KeyError:
                        pass
                    desc['contact_person'].append(person)
            except KeyError:
                pass

            # Add ui info
            try:
                for idpsso_desc in entity[entity_id]["idpsso_descriptor"]:
                    ui_elements = idpsso_desc["extensions"]["extension_elements"]
                    params = ["description", "display_name"]
                    ui_info = {}

                    for element in ui_elements:
                        if not element["__class__"] == "%s&UIInfo" % UI_NAMESPACE:
                            continue
                        for param in params:
                            try:
                                value = []
                                for data in element[param]:
                                    value.append({"text": data["text"], "lang": data["lang"]})
                                ui_info[param] = value
                            except KeyError:
                                pass
                        try:
                            logos = []
                            for logo in element["logo"]:
                                logos.append({"text": logo["text"], "width": logo["width"],
                                              "height": logo["height"], "lang": logo["lang"]})
                            ui_info["logo"] = logos
                        except KeyError:
                            pass
                    if ui_info:
                        desc["service"] = {"idp": {"ui_info": ui_info}}
            except KeyError:
                pass

            metadata_desc.append(desc)
        return metadata_desc
