#!/usr/bin/env python
import logging
from base64 import urlsafe_b64decode, urlsafe_b64encode
from saml2.extension.ui import NAMESPACE as UI_NAMESPACE
from satosa.backends.saml2 import SamlBackend
from vopaas.backends.backend_base import VOPaaSBackendModule

logger = logging.getLogger(__name__)


class ContactPerson(object):
    def __init__(self):
        self.contact_type = None
        self._email_address = []
        self.given_name = None
        self.sur_name = None

    def add_email_address(self, address):
        self._email_address.append(address)

    def to_dict(self):
        person = {}
        if self.contact_type:
            person["contact_type"] = self.contact_type
        if self._email_address:
            person["email_address"] = self._email_address
        if self.given_name:
            person["given_name"] = self.given_name
        if self.sur_name:
            person["sur_name"] = self.sur_name
        return person


class UIInfo(object):
    def __init__(self):
        self._description = []
        self._display_name = []
        self._logos = []

    def add_description(self, text, lang):
        self._description.append({"text": text, "lang": lang})

    def add_display_name(self, text, lang):
        self._display_name.append({"text": text, "lang": lang})

    def add_logo(self, text, width, height, lang):
        self._logos.append({"text": text, "width": width, "height": height, "lang": lang})

    def to_dict(self):
        ui_info = {}
        if self._description:
            ui_info["description"] = self._description
        if self._display_name:
            ui_info["display_name"] = self._display_name
        if self._logos:
            ui_info["logos"] = self._logos
        return {"service": {"idp": {"ui_info": ui_info}}} if ui_info else {}


class Organization(object):
    def __init__(self):
        self._display_name = []
        self._name = []
        self._url = []

    def add_display_name(self, name, lang):
        self._display_name.append((name, lang))

    def add_name(self, name, lang):
        self._name.append((name, lang))

    def add_url(self, url, lang):
        self._url.append((url, lang))

    def to_dict(self):
        org = {}
        if self._display_name:
            org["display_name"] = self._display_name
        if self._name:
            org["name"] = self._name
        if self._url:
            org["url"] = self._url
        return {"organization": org} if org else {}


class MetadataDescription(object):
    def __init__(self, entity_id):
        self.entity_id = entity_id
        self._organization = None
        self._contact_person = []
        self._ui_info = None

    def set_organization(self, organization):
        assert isinstance(organization, Organization)
        self._organization = organization

    def add_contact_person(self, person):
        assert isinstance(person, ContactPerson)
        self._contact_person.append(person)

    def set_ui_info(self, ui_info):
        assert isinstance(ui_info, UIInfo)
        self._ui_info = ui_info
        
    def to_dict(self):
        description = {}
        description["entity_id"] = self.entity_id
        if self._organization:
            description.update(self._organization.to_dict())
        if self._contact_person:
            description['contact_person'] = []
            for person in self._contact_person:
                description['contact_person'].append(person.to_dict())
        if self._ui_info:
            description.update(self._ui_info.to_dict())


class VOPaaSSamlBackend(SamlBackend, VOPaaSBackendModule):
    def start_auth(self, context, request_info, state):
        entity_id = context.internal_data["vopaas.target_entity_id"]
        entity_id = urlsafe_b64decode(entity_id).decode("utf-8")
        return self.authn_request(context, entity_id, request_info, state)

    def get_metadata_desc(self):
        # TODO Only get IDPs
        metadata_desc = []
        for metadata_file in self.sp.metadata.metadata:
            # desc = {}
            metadata_file = self.sp.metadata.metadata[metadata_file]
            entity_id = metadata_file.entity_descr.entity_id
            entity = metadata_file.entity

            description = MetadataDescription(urlsafe_b64encode(entity_id.encode("utf-8")).decode("utf-8"))

            # Add organization info
            try:
                organization = Organization()
                organization_info = entity[entity_id]['organization']

                if "organization_name" in organization_info:
                    name = organization_info["organization_name"]["text"]
                    lang = organization_info["organization_name"]["lang"]
                    organization.add_name(name, lang)
                if "organization_display_name" in organization_info:
                    name = organization_info["organization_display_name"]["text"]
                    lang = organization_info["organization_display_name"]["lang"]
                    organization.add_display_name(name, lang)
                if "organization_url" in organization_info:
                    name = organization_info["organization_url"]["text"]
                    lang = organization_info["organization_url"]["lang"]
                    organization.add_url(name, lang)

                description.set_organization(organization)
            except:
                pass

            # Add contact person info
            try:
                contact_persons = entity[entity_id]['contact_person']
                for cont_pers in contact_persons:
                    person = ContactPerson()

                    if 'contact_type' in cont_pers:
                        person.contact_type = cont_pers['contact_type']
                    if 'email_address' in cont_pers:
                        for address in cont_pers['email_address']:
                            person.add_email_address(address["text"])
                    if 'given_name' in cont_pers:
                        person.given_name = cont_pers['given_name']['text']
                    if 'sur_name' in cont_pers:
                        person.sur_name = cont_pers['sur_name']

                    description.add_contact_person(person)
            except KeyError:
                pass

            # Add ui info
            try:
                for idpsso_desc in entity[entity_id]["idpsso_descriptor"]:
                    ui_elements = idpsso_desc["extensions"]["extension_elements"]
                    ui_info = UIInfo()

                    for element in ui_elements:
                        if not element["__class__"] == "%s&UIInfo" % UI_NAMESPACE:
                            continue
                        for desc in element.get("description", []):
                            ui_info.add_description(desc["text"], desc["lang"])
                        for name in element.get("display_name", []):
                            ui_info.add_display_name(name["text"], name["lang"])
                        for logo in element.get("logo", []):
                            ui_info.add_logo(logo["text"], logo["width"], logo["height"], logo["lang"])
            except KeyError:
                pass

            metadata_desc.append(description)
        return metadata_desc



    # def get_metadata_desc(self):
    #     # TODO Only get IDPs
    #     metadata_desc = []
    #     for metadata_file in self.sp.metadata.metadata:
    #         desc = {}
    #         metadata_file = self.sp.metadata.metadata[metadata_file]
    #         entity_id = metadata_file.entity_descr.entity_id
    #         entity = metadata_file.entity
    #         desc["entityid"] = urlsafe_b64encode(entity_id.encode("utf-8")).decode("utf-8")
    #
    #         # Add organization info
    #         try:
    #             organization = entity[entity_id]['organization']
    #             desc['organization'] = {}
    #             organization_params = [('display_name', 'organization_display_name'),
    #                                    ('name', 'organization_name'), ('url', 'organization_url')]
    #             for config_param, param in organization_params:
    #                 try:
    #                     value = []
    #                     for obj in organization[param]:
    #                         value.append((obj["text"], obj["lang"]))
    #                     desc['organization'][config_param] = value
    #                 except KeyError:
    #                     pass
    #         except:
    #             pass
    #
    #         # Add contact person info
    #         try:
    #             contact_persons = entity[entity_id]['contact_person']
    #             desc['contact_person'] = []
    #             for cont_pers in contact_persons:
    #                 person = {}
    #                 try:
    #                     person['contact_type'] = cont_pers['contact_type']
    #                 except KeyError:
    #                     pass
    #                 try:
    #                     email_address = cont_pers['email_address']
    #                     person['email_address'] = []
    #                     for address in email_address:
    #                         person['email_address'].append(address['text'])
    #                 except KeyError:
    #                     pass
    #                 try:
    #                     person['given_name'] = cont_pers['given_name']['text']
    #                 except KeyError:
    #                     pass
    #                 try:
    #                     person['sur_name'] = cont_pers['sur_name']['text']
    #                 except KeyError:
    #                     pass
    #                 desc['contact_person'].append(person)
    #         except KeyError:
    #             pass
    #
    #         # Add ui info
    #         try:
    #             for idpsso_desc in entity[entity_id]["idpsso_descriptor"]:
    #                 ui_elements = idpsso_desc["extensions"]["extension_elements"]
    #                 params = ["description", "display_name"]
    #                 ui_info = {}
    #
    #                 for element in ui_elements:
    #                     if not element["__class__"] == "%s&UIInfo" % UI_NAMESPACE:
    #                         continue
    #                     for param in params:
    #                         try:
    #                             value = []
    #                             for data in element[param]:
    #                                 value.append({"text": data["text"], "lang": data["lang"]})
    #                             ui_info[param] = value
    #                         except KeyError:
    #                             pass
    #                     try:
    #                         logos = []
    #                         for logo in element["logo"]:
    #                             logos.append({"text": logo["text"], "width": logo["width"],
    #                                           "height": logo["height"], "lang": logo["lang"]})
    #                         ui_info["logo"] = logos
    #                     except KeyError:
    #                         pass
    #                 if ui_info:
    #                     desc["service"] = {"idp": {"ui_info": ui_info}}
    #         except KeyError:
    #             pass
    #
    #         metadata_desc.append(desc)
    #     return metadata_desc
