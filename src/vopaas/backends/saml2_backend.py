#!/usr/bin/env python
import logging
from base64 import urlsafe_b64decode, urlsafe_b64encode
from saml2.extension.ui import NAMESPACE as UI_NAMESPACE
from satosa.backends.saml2 import SamlBackend
from vopaas.backends.backend_base import VOPaaSBackendModule
from vopaas.metadata_creation.description import MetadataDescription, OrganizationDesc, ContactPersonDesc, UIInfoDesc

logger = logging.getLogger(__name__)

class VOPaaSSamlBackend(SamlBackend, VOPaaSBackendModule):
    def start_auth(self, context, request_info):
        entity_id = context.internal_data["vopaas.target_entity_id"]
        entity_id = urlsafe_b64decode(entity_id).decode("utf-8")
        return self.authn_request(context, entity_id, request_info)

    def get_metadata_desc(self):
        # TODO Only get IDPs
        metadata_desc = []
        for metadata_file in self.sp.metadata.metadata:
            metadata_file = self.sp.metadata.metadata[metadata_file]
            entity_id = metadata_file.entity_descr.entity_id
            entity = metadata_file.entity

            description = MetadataDescription(urlsafe_b64encode(entity_id.encode("utf-8")).decode("utf-8"))

            # Add organization info
            try:
                organization = OrganizationDesc()
                organization_info = entity[entity_id]['organization']

                for name_info in organization_info.get("organization_name", []):
                    organization.add_name(name_info["text"], name_info["lang"])
                for display_name_info in organization_info.get("organization_display_name", []):
                    organization.add_display_name(display_name_info["text"], display_name_info["lang"])
                for url_info in organization_info.get("organization_url", []):
                    organization.add_url(url_info["text"], url_info["lang"])

                description.set_organization(organization)
            except:
                pass

            # Add contact person info
            try:
                contact_persons = entity[entity_id]['contact_person']
                for cont_pers in contact_persons:
                    person = ContactPersonDesc()

                    if 'contact_type' in cont_pers:
                        person.contact_type = cont_pers['contact_type']
                    for address in cont_pers.get('email_address', []):
                        person.add_email_address(address["text"])
                    if 'given_name' in cont_pers:
                        person.given_name = cont_pers['given_name']['text']
                    if 'sur_name' in cont_pers:
                        person.sur_name = cont_pers['sur_name']['text']

                    description.add_contact_person(person)
            except KeyError:
                pass

            # Add ui info
            try:
                for idpsso_desc in entity[entity_id]["idpsso_descriptor"]:
                    # TODO Can have more than one ui info?
                    ui_elements = idpsso_desc["extensions"]["extension_elements"]
                    ui_info = UIInfoDesc()

                    for element in ui_elements:
                        if not element["__class__"] == "%s&UIInfo" % UI_NAMESPACE:
                            continue
                        for desc in element.get("description", []):
                            ui_info.add_description(desc["text"], desc["lang"])
                        for name in element.get("display_name", []):
                            ui_info.add_display_name(name["text"], name["lang"])
                        for logo in element.get("logo", []):
                            ui_info.add_logo(logo["text"], logo["width"], logo["height"], logo["lang"])

                    description.set_ui_info(ui_info)
            except KeyError:
                pass

            metadata_desc.append(description)
        return metadata_desc
