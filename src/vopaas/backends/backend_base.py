from base64 import urlsafe_b64encode
from satosa.backends.base import BackendModule
from vopaas.metadata_creation.description import MetadataDescription, ContactPersonDesc, OrganizationDesc, UIInfoDesc

__author__ = 'mathiashedstrom'


class VOPaaSBackendModule(BackendModule):
    def get_metadata_desc(self):
        raise NotImplementedError()


def get_metadata_desc_for_oidc_backend(config, entity_id=None):
    metadata_description = []
    if entity_id is None:
        entity_id = config["op_url"]
    entity_id = urlsafe_b64encode(entity_id.encode("utf-8")).decode("utf-8")
    description = MetadataDescription(entity_id)

    if "op_info" in config:
        op_info = config["op_info"]

        # Add contact person information
        for contact_person in op_info.get("contact_person"):
            person = ContactPersonDesc()
            if 'contact_type' in contact_person:
                person.contact_type = contact_person['contact_type']
            for address in contact_person.get('email_address', []):
                person.add_email_address(address)
            if 'given_name' in contact_person:
                person.given_name = contact_person['given_name']
            if 'sur_name' in contact_person:
                person.sur_name = contact_person['sur_name']

            description.add_contact_person(person)

        # Add organization information
        if "organization" in op_info:
            organization_info = op_info["organization"]
            organization = OrganizationDesc()

            for name_info in organization_info.get("organization_name", []):
                organization.add_name(name_info[0], name_info[1])
            for display_name_info in organization_info.get("organization_display_name", []):
                organization.add_display_name(display_name_info[0], display_name_info[1])
            for url_info in organization_info.get("organization_url", []):
                organization.add_url(url_info[0], url_info[1])

            description.set_organization(organization)

        # Add ui information
        if "ui_info" in op_info:
            ui_info = op_info["ui_info"]
            ui_description = UIInfoDesc()
            for desc in ui_info.get("description", []):
                ui_description.add_description(desc[0], desc[1])
            for name in ui_info.get("display_name", []):
                ui_description.add_display_name(name[0], name[1])
            for logo in ui_info.get("logo", []):
                ui_description.add_logo(logo["url"], logo["width"], logo["height"], logo["lang"])

            description.set_ui_info(ui_description)

    metadata_description.append(description)
    return metadata_description